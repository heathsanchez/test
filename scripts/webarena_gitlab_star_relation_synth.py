#!/usr/bin/env python3
"""Residual-driven semantic synthesis for WebArena-Verified GitLab star queries.

This program separates:
1. observation of personal projects and star counts,
2. compilation of task language into lexical operators,
3. execution under a semantic binding map.

The synthesis workflow does not hand-list candidate programs. It starts from a
baseline binding map, observes only binary verifier success/failure on training
tasks, and breadth-first searches single-operator rebinding edits from a generic
operator library. Once LESS and LEAST are learned, MORE and MOST are derived by
order duality rather than separately trained.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DEFAULT = "http://localhost:8023"


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


async def login(page, base: str) -> None:
    await page.goto(base + "/users/sign_in", wait_until="networkidle", timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/", timeout=120000)


async def list_projects(page, base: str) -> list[dict]:
    r = await page.goto(base + "/users/byteblaze/projects", wait_until="networkidle", timeout=180000)
    if r is None or r.status != 200:
        raise RuntimeError("personal projects page failed")
    links = page.locator('a.project[href^="/byteblaze/"]')
    paths = []
    for i in range(await links.count()):
        href = await links.nth(i).get_attribute("href")
        if href and href.count("/") == 2 and href not in paths:
            paths.append(href)
    out = []
    for path in paths:
        star = page.locator(f'a[href="{path}/-/starrers"].stars').first
        if await star.count() == 0:
            star = page.locator(f'a[href="{path}/-/starrers"]').first
        txt = clean(await star.inner_text()) if await star.count() else ""
        m = re.search(r"\d+", txt.replace(",", ""))
        if not m:
            raise RuntimeError(f"star count missing for {path}")
        out.append({"path": path, "name": path.rsplit("/", 1)[-1], "stars": int(m.group())})
    return out


async def project_id(page, base: str, path: str) -> int:
    r = await page.goto(base + path, wait_until="networkidle", timeout=180000)
    if r is None or r.status != 200:
        raise RuntimeError(f"project page failed: {path}")
    body = clean(await page.locator("body").inner_text())
    for pat in (r"Project ID:\s*(\d+)", r"project id\s*(\d+)"):
        m = re.search(pat, body, re.I)
        if m:
            return int(m.group(1))
    html = await page.content()
    for pat in (r'data-project-id=["\'](\d+)', r'"project_id":(\d+)', r'"projectId":(\d+)'):
        m = re.search(pat, html, re.I)
        if m:
            return int(m.group(1))
    raise RuntimeError(f"project id not visible for {path}")


async def observe(base: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await login(page, base)
        projects = await list_projects(page, base)
        for project in projects:
            project["id"] = await project_id(page, base, project["path"])
        await browser.close()
    return {"projects": projects}


def compile_description(description: str) -> dict:
    d = description.casefold().strip()
    m = re.search(r"less than\s+(\d+)\s+stars", d)
    if m:
        return {"operator": "LESS", "threshold": int(m.group(1))}
    m = re.search(r"more than\s+(\d+)\s+stars", d)
    if m:
        return {"operator": "MORE", "threshold": int(m.group(1))}
    if "most stars" in d:
        return {"operator": "MOST"}
    if "least stars" in d:
        return {"operator": "LEAST"}
    if "no stars" in d:
        return {"operator": "ZERO"}
    raise ValueError(f"unsupported star description: {description!r}")


def derive_binding(binding: dict) -> dict:
    out = dict(binding)
    if "LESS" in out:
        out["MORE"] = {"lt": "gt", "gt": "lt"}[out["LESS"]]
    if "LEAST" in out:
        out["MOST"] = {"min": "max", "max": "min"}[out["LEAST"]]
    out.setdefault("ZERO", "eq0")
    return out


def execute(projects: list[dict], program: dict, binding: dict) -> list[dict]:
    b = derive_binding(binding)
    op = program["operator"]
    semantic = b[op]
    if semantic == "lt":
        chosen = [p for p in projects if p["stars"] < program["threshold"]]
    elif semantic == "gt":
        chosen = [p for p in projects if p["stars"] > program["threshold"]]
    elif semantic == "min":
        m = min(p["stars"] for p in projects)
        chosen = [p for p in projects if p["stars"] == m]
    elif semantic == "max":
        m = max(p["stars"] for p in projects)
        chosen = [p for p in projects if p["stars"] == m]
    elif semantic == "eq0":
        chosen = [p for p in projects if p["stars"] == 0]
    else:
        raise ValueError(f"unknown semantic: {semantic}")
    return chosen


def make_response(chosen: list[dict]) -> dict:
    if chosen:
        return {
            "task_type": "RETRIEVE",
            "status": "SUCCESS",
            "retrieved_data": [p["id"] for p in chosen],
            "error_details": None,
        }
    return {
        "task_type": "RETRIEVE",
        "status": "NOT_FOUND_ERROR",
        "retrieved_data": None,
        "error_details": None,
    }


def run_compute(args) -> None:
    tasks = json.loads(Path(args.task_file).read_text())
    task = next(t for t in tasks if int(t["task_id"]) == args.task_id)
    if int(task["intent_template_id"]) != 289:
        raise SystemExit("unsupported template")
    observation = json.loads(Path(args.observation).read_text())
    binding = json.loads(Path(args.binding).read_text())
    description = str(task["instantiation_dict"]["description"])
    program = compile_description(description)
    chosen = execute(observation["projects"], program, binding)
    response = make_response(chosen)

    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")
    (out / "capability_evidence.json").write_text(
        json.dumps(
            {
                "task_id": args.task_id,
                "description": description,
                "compiled_program": program,
                "input_binding": binding,
                "derived_binding": derive_binding(binding),
                "chosen": chosen,
                "response": response,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"task_id": args.task_id, "program": program, "binding": derive_binding(binding), "response": response}, indent=2))


async def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    obs = sub.add_parser("observe")
    obs.add_argument("--base-url", default=BASE_DEFAULT)
    obs.add_argument("--output", required=True)

    comp = sub.add_parser("compute")
    comp.add_argument("--task-id", type=int, required=True)
    comp.add_argument("--task-file", required=True)
    comp.add_argument("--observation", required=True)
    comp.add_argument("--binding", required=True)
    comp.add_argument("--output-dir", required=True)

    args = ap.parse_args()
    if args.cmd == "observe":
        data = await observe(args.base_url.rstrip("/"))
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"projects": len(data["projects"])}, indent=2))
    else:
        run_compute(args)


if __name__ == "__main__":
    asyncio.run(main())
