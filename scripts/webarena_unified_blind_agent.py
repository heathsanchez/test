#!/usr/bin/env python3
"""Bounded multi-site blind agent: only intent + start URL enter the agent.

The official task identifier, template, instantiation, and evaluator remain
exclusively in the external harness. Capabilities are reused unchanged.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from webarena_reddit_blind_router import route as reddit_route
from webarena_reddit_submit_v3 import AUTH as REDDIT_AUTH
from webarena_gitlab_rss_token import find_feed_token
from webarena_gitlab_personal_project_stars import (
    login as gitlab_login, list_projects, project_id, select as select_stars,
)
from webarena_gitlab_commit_counts import (
    BASE as GITLAB_BASE, sign_in, period_bounds, count_commits,
)
from webarena_gitlab_to_reddit_promote import fetch_project, submit_url_post


REDDIT_BASE = "http://localhost:9999"
GITLAB_ROOT = "http://localhost:8023"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def site_from_start(start_url: str) -> str:
    if start_url.startswith("__REDDIT__"):
        return "reddit"
    if start_url.startswith("__GITLAB__"):
        return "gitlab"
    url = urlparse(start_url)
    if (url.hostname, url.port) == ("localhost", 9999):
        return "reddit"
    if (url.hostname, url.port) == ("localhost", 8023):
        return "gitlab"
    raise ValueError(f"unsupported initial site: {start_url!r}")


def gitlab_intent(intent: str):
    text = clean(intent)
    if text.casefold() == "get me my rss feed token":
        return "rss", {}
    m = re.fullmatch(
        r"Get the project ID\(s\) of my personal project\(s\) that received (.+)",
        text, re.I,
    )
    if m:
        return "personal_project_stars", {"description": m.group(1)}
    m = re.fullmatch(
        r"How many commits did (.+?) make (.+) in the current repository\?",
        text, re.I,
    )
    if m:
        # Strict period grammar is enforced by the reused verified parser.
        period_bounds(m.group(2))
        return "commit_count", {"author": m.group(1), "period": m.group(2)}
    raise ValueError(f"unsupported GitLab intent: {text!r}")


def cross_site_intent(intent: str):
    text=clean(intent)
    m=re.fullmatch(
        r"Promote ([^\s]+/[^\s]+) in the discussion forum ([^\s]+) "
        r"by creating a post with the project description as the title\.",
        text,re.I,
    )
    if not m:
        return None
    repo,forum=m.groups()
    if repo.count("/")!=1 or any(part in ("",".","..") for part in repo.split("/")):
        raise ValueError("invalid GitLab project path")
    return {"repo":repo,"forum":forum}


async def execute_cross_site(page, context, parsed):
    await sign_in(page)
    project=await fetch_project(page,parsed["repo"])
    post_url=f"{GITLAB_ROOT}/{project['path']}"
    target=await context.new_page()
    post=await submit_url_post(target,parsed["forum"],project["description"],post_url)
    response={"task_type":"MUTATE","status":"SUCCESS",
              "retrieved_data":None,"error_details":None}
    evidence={
        "capability":"gitlab_retrieve_to_reddit_post",
        "project":project,"target_forum":parsed["forum"],
        "posted_link":post_url,"network_post":post,
    }
    return response,evidence


def actual_start(start_url: str) -> str:
    return (start_url
        .replace("__REDDIT__", REDDIT_BASE)
        .replace("__GITLAB__", GITLAB_ROOT))


async def execute_gitlab(page, intent: str, start_url: str):
    capability, args = gitlab_intent(intent)
    if capability == "rss":
        await sign_in(page)
        token, links = await find_feed_token(page)
        response = {"task_type":"RETRIEVE","status":"SUCCESS",
                    "retrieved_data":[token],"error_details":None}
        return response, {"capability":capability,"observed_links":links}

    if capability == "personal_project_stars":
        await gitlab_login(page, GITLAB_ROOT)
        projects = await list_projects(page, GITLAB_ROOT)
        for project in projects:
            project["id"] = await project_id(page,GITLAB_ROOT,project["path"])
        chosen = select_stars(projects, args["description"])
        response = {
            "task_type":"RETRIEVE",
            "status":"SUCCESS" if chosen else "NOT_FOUND_ERROR",
            "retrieved_data":[p["id"] for p in chosen] if chosen else None,
            "error_details":None,
        }
        return response, {
            "capability":capability,"projects":projects,
            "selected":chosen,"description":args["description"],
        }

    if capability == "commit_count":
        start = urlparse(actual_start(start_url)).path.rstrip("/")
        if len([part for part in start.split("/") if part]) < 2:
            raise ValueError("commit count requires a repository start URL")
        begin, end = period_bounds(args["period"])
        await sign_in(page)
        count, detail = await count_commits(page,start,args["author"],begin,end)
        response = {"task_type":"RETRIEVE","status":"SUCCESS",
                    "retrieved_data":[count],"error_details":None}
        return response, {
            "capability":capability,"repo":start,"author":args["author"],
            "period":args["period"],"start":begin.isoformat(),
            "end_exclusive":end.isoformat(),"detail":detail,
        }
    raise RuntimeError(f"unreachable capability {capability!r}")


async def run(intent: str, start_url: str, output_dir: Path):
    site=site_from_start(start_url)
    cross_site=cross_site_intent(intent)
    if cross_site and site!="reddit":
        raise ValueError("GitLab-to-Reddit composition requires a Reddit starting site")
    output_dir.mkdir(parents=True,exist_ok=True)
    har=output_dir/"network.har"
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        context=await browser.new_context(
            extra_http_headers=REDDIT_AUTH if site=="reddit" else {},
            record_har_path=str(har) if site=="reddit" else None,
            record_har_mode="full",
        )
        page=await context.new_page()
        try:
            if cross_site:
                response,evidence=await execute_cross_site(page,context,cross_site)
            elif site=="reddit":
                evidence=await reddit_route(page,REDDIT_BASE,intent,start_url)
                response={"task_type":"MUTATE","status":"SUCCESS",
                          "retrieved_data":None,"error_details":None}
            else:
                response,evidence=await execute_gitlab(page,intent,start_url)
        finally:
            await context.close()
            await browser.close()
    (output_dir/"agent_response.json").write_text(
        json.dumps(response,indent=2,ensure_ascii=False)+"\n")
    (output_dir/"capability_evidence.json").write_text(
        json.dumps({"site":site,"intent":intent,"start_url":start_url,
                    "evidence":evidence},indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"site":site,"response":response,"evidence":evidence},
                     ensure_ascii=False))
    return response


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
