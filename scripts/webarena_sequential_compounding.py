#!/usr/bin/env python3
"""Sequential verifier-selected capability composition on WebArena-Verified template 117.

This executable exposes exactly two semantic capabilities:
A. title_source: use the live GitLab project description vs use the repo path.
B. forum_mode: use the task-requested Reddit forum vs a fixed LifeProTips forum.

The workflow learns A first, freezes it, then learns B while reusing frozen A.
Only after both freezes are untouched sibling tasks executed.

The candidate consumes a sanitized task file that contains no evaluator fields.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright


GITLAB = "http://localhost:8023"
REDDIT = "http://localhost:9999"
REDDIT_AUTH = {"X-Postmill-Auto-Login": "MarvelsGrantMan136:test1234"}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


async def gitlab_sign_in(page) -> None:
    await page.goto(GITLAB + "/users/sign_in", wait_until="networkidle", timeout=180_000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/", timeout=120_000)


async def api_json(page, url: str) -> object:
    payload = await page.evaluate(
        """async (url) => {
          const r = await fetch(url, {credentials: 'same-origin'});
          return {status: r.status, text: await r.text()};
        }""",
        url,
    )
    if payload["status"] != 200:
        raise RuntimeError(f"GitLab API failed {payload['status']}: {payload['text'][:500]}")
    return json.loads(payload["text"])


async def fetch_project(page, repo: str) -> dict:
    project_id = quote(repo.strip("/"), safe="")
    data = await api_json(page, f"{GITLAB}/api/v4/projects/{project_id}")
    if not isinstance(data, dict):
        raise RuntimeError(f"project payload is not an object for {repo}")
    path = clean(data.get("path_with_namespace", repo))
    description = clean(data.get("description", ""))
    if not description:
        raise RuntimeError(f"project description missing for {repo}")
    return {"path": path, "description": description}


async def submit_url_post(page, forum: str, title: str, url: str) -> dict:
    target = REDDIT + "/submit/" + forum
    response = await page.goto(target, wait_until="networkidle", timeout=120_000)
    if response is None or response.status != 200:
        raise RuntimeError(f"Reddit submit page failed: {target}")

    form = page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count() == 0:
        raise RuntimeError("submission form missing")

    title_input = form.locator('[name="submission[title]"]').first
    url_input = form.locator('[name="submission[url]"]').first
    forum_input = form.locator('[name="submission[forum]"]').first
    if await title_input.count() == 0 or await url_input.count() == 0 or await forum_input.count() == 0:
        raise RuntimeError("URL submission form contract missing")

    await title_input.fill(title)
    await url_input.fill(url)
    forum_value = await forum_input.input_value()
    if not forum_value:
        raise RuntimeError("forum was not preselected")

    button = form.get_by_role("button", name="Create submission").first
    if await button.count() == 0:
        raise RuntimeError("submit control missing")
    await button.click()
    await page.wait_for_load_state("networkidle", timeout=120_000)
    return {"submit_url": target, "forum_value": forum_value, "final_url": page.url}


def load_task(path: str, task_id: int) -> dict:
    tasks = json.loads(Path(path).read_text())
    task = next((t for t in tasks if int(t["task_id"]) == task_id), None)
    if task is None:
        raise SystemExit(f"task {task_id} not found")
    if int(task.get("intent_template_id")) != 117:
        raise SystemExit(f"task {task_id} is not template 117")
    forbidden = {"eval", "reference_answer", "results_schema"}
    present = sorted(forbidden.intersection(task))
    if present:
        raise SystemExit(f"candidate task must be sanitized; forbidden fields present: {present}")
    return task


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", type=int, required=True)
    ap.add_argument("--task-file", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--title-source", choices=("description", "repo_path"), required=True)
    ap.add_argument("--forum-mode", choices=("requested", "fixed_lifeprotips"), required=True)
    args = ap.parse_args()

    task = load_task(args.task_file, args.task_id)
    inst = task["instantiation_dict"]
    repo = clean(inst["repo"])
    requested_forum = clean(inst["forum"])
    effective_forum = requested_forum if args.forum_mode == "requested" else "LifeProTips"

    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    har_path = out / "network.har"

    stage = "start"
    diagnostic = {
        "task_id": args.task_id,
        "repo": repo,
        "requested_forum": requested_forum,
        "title_source": args.title_source,
        "forum_mode": args.forum_mode,
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            stage = "gitlab"
            git_context = await browser.new_context()
            git_page = await git_context.new_page()
            await gitlab_sign_in(git_page)
            project = await fetch_project(git_page, repo)
            await git_context.close()

            title = project["description"] if args.title_source == "description" else project["path"]
            post_url = f"{GITLAB}/{project['path']}"

            stage = "reddit"
            reddit_context = await browser.new_context(
                extra_http_headers=REDDIT_AUTH,
                record_har_path=str(har_path),
                record_har_mode="full",
            )
            reddit_page = await reddit_context.new_page()
            post = await submit_url_post(reddit_page, effective_forum, title, post_url)
            await reddit_context.close()
            await browser.close()

    except Exception as exc:
        diagnostic.update({"stage": stage, "exception_type": type(exc).__name__, "exception": str(exc)})
        (out / "failure_evidence.json").write_text(
            json.dumps(diagnostic, indent=2, ensure_ascii=False) + "\n"
        )
        print(json.dumps(diagnostic, indent=2, ensure_ascii=False))
        raise

    response = {
        "task_type": "MUTATE",
        "status": "SUCCESS",
        "retrieved_data": None,
        "error_details": None,
    }

    protected_contract = {
        "title_matches_live_gitlab_description": title == project["description"],
        "effective_forum_matches_requested_forum": effective_forum.casefold() == requested_forum.casefold(),
        "post_url_matches_requested_repo": project["path"].casefold() == repo.casefold()
        and post_url == f"{GITLAB}/{repo}",
        "response_shape_is_mutate_success_null": response
        == {
            "task_type": "MUTATE",
            "status": "SUCCESS",
            "retrieved_data": None,
            "error_details": None,
        },
    }
    protected_contract["all_pass"] = all(protected_contract.values())

    evidence = {
        "task_id": args.task_id,
        "repo": repo,
        "requested_forum": requested_forum,
        "effective_forum": effective_forum,
        "title_source": args.title_source,
        "forum_mode": args.forum_mode,
        "project": project,
        "chosen_title": title,
        "post_url": post_url,
        "protected_contract": protected_contract,
        **post,
    }

    (out / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")
    (out / "capability_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
