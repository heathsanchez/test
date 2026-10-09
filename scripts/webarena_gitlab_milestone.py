#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE as GITLAB, sign_in

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

def iso_date(s):
    raw=clean(s)
    raw=re.sub(r"^(on|starting on|starting)\s+","",raw,flags=re.I)
    for fmt in ("%B %d, %Y","%B %d %Y","%b %d, %Y","%b %d %Y"):
        try: return datetime.strptime(raw,fmt).date()
        except ValueError: pass
    raise ValueError(f"unsupported date: {s}")

def date_range(inst):
    start=iso_date(inst["start_date"])
    end_raw=clean(inst["end_date"])
    m=re.search(r"in\s+(\d+)\s+days?\s*\(inclusive\)",end_raw,re.I)
    if m:
        end=start+timedelta(days=int(m.group(1))-1)
    else:
        end=iso_date(end_raw)
    return start.isoformat(),end.isoformat()

def repo_from_start(task):
    raw=str(task["start_urls"][0])
    path=raw.split("__GITLAB__",1)[-1].strip("/")
    if not path or "/" not in path: raise ValueError("GitLab repo start URL required")
    return path

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=339: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; repo=repo_from_start(task); start,end=date_range(inst)
    title=clean(inst["title"])
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page(); await sign_in(page)
        url=f"{GITLAB}/{repo}/-/milestones/new"
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"new milestone page failed: {url}")
        title_field=page.locator('[name="milestone[title]"]').first
        start_field=page.locator('[name="milestone[start_date]"]').first
        due_field=page.locator('[name="milestone[due_date]"]').first
        if await title_field.count()==0 or await start_field.count()==0 or await due_field.count()==0:
            raise RuntimeError("milestone form contract missing")
        await title_field.fill(title)
        await start_field.fill(start)
        await due_field.fill(end)
        form=title_field.locator("xpath=ancestor::form[1]")
        async with page.expect_navigation(wait_until="networkidle",timeout=30000):
            await form.evaluate("(f)=>f.requestSubmit()")
        final=page.url
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"repo":repo,"title":title,"start_date":start,"due_date":end,"final_url":final}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
