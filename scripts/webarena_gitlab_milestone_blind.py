#!/usr/bin/env python3
"""Task-ID-blind GitLab project milestone mutation with visible form evidence."""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE,sign_in
from webarena_gitlab_milestone import date_range

def clean(s):
    return re.sub(r"\s+"," ",str(s)).strip()

def parse_intent(intent,start_url):
    text=clean(intent)
    m=re.fullmatch(
        r'Create a milestone in the current repo with title "([^"]+)" '
        r'for the upcoming (.+?) starting on ([A-Za-z]+ \d{1,2}, \d{4}) '
        r'and ending (on [A-Za-z]+ \d{1,2}, \d{4}|in \d+ days? \(inclusive\))',
        text,re.I,
    )
    if not m:
        raise ValueError(f"unsupported milestone intent: {intent!r}")
    title,event,start,end=m.groups()
    if not start_url.startswith("__GITLAB__/"):
        raise ValueError("project start required")
    repo=start_url[len("__GITLAB__/"):].strip("/")
    if len(repo.split("/"))!=2 or any(part in ("",".","..") for part in repo.split("/")):
        raise ValueError("project path not resolvable")
    first,last=date_range({"start_date":start,"end_date":end})
    return {"title":title,"event":event,"repo":repo,"start_date":first,"due_date":last}

async def create_milestone(page,spec):
    await sign_in(page)
    target=f"{BASE}/{spec['repo']}/-/milestones/new"
    r=await page.goto(target,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200:
        raise RuntimeError("milestone form not available")
    title=page.locator('[name="milestone[title]"]').first
    start=page.locator('[name="milestone[start_date]"]').first
    due=page.locator('[name="milestone[due_date]"]').first
    if not await title.count() or not await start.count() or not await due.count():
        raise RuntimeError("milestone form fields unavailable")
    await title.fill(spec["title"])
    await start.fill(spec["start_date"])
    await due.fill(spec["due_date"])
    form=title.locator("xpath=ancestor::form[1]")
    async with page.expect_navigation(wait_until="networkidle",timeout=30000):
        await form.evaluate("(f)=>f.requestSubmit()")
    if "/-/milestones/" not in page.url:
        raise RuntimeError("milestone submission did not reach details page")
    return {"observed_url":page.url,"spec":spec}

async def run(intent,start_url,out):
    spec=parse_intent(intent,start_url)
    out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(record_har_path=str(out/"network.har"),record_har_mode="full")
        page=await ctx.new_page()
        try:
            evidence=await create_milestone(page,spec)
        finally:
            await ctx.close()
            await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--intent",required=True)
    ap.add_argument("--start-url",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))

if __name__=="__main__":
    main()
