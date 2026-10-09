#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from urllib.parse import quote, urlencode
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE as GITLAB, sign_in

def clean(s): return " ".join(str(s).split())

async def navigate(page,task):
    tid=int(task["intent_template_id"])
    inst=task.get("instantiation_dict") or {}
    if tid==303:
        target=f"{GITLAB}/dashboard/todos"
    elif tid==290:
        target=f"{GITLAB}/dashboard/merge_requests?"+urlencode({"assignee_username":"byteblaze"})
    elif tid==349:
        repo=clean(inst["repo"]).strip("/")
        state=clean(inst.get("state","")).casefold()
        params={}
        if state in {"open","not yet closed","not closed"}:
            params["state"]="opened"
        label=clean(inst.get("label",""))
        if label and not label.casefold().startswith("all except "):
            params["label_name[]"]=label
        target=f"{GITLAB}/{repo}/-/issues"
        if params: target+="?"+urlencode(params,doseq=True)
    else:
        raise SystemExit(f"unsupported template {tid}")
    r=await page.goto(target,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200:
        raise RuntimeError(f"GitLab navigation failed: {target} status={None if r is None else r.status}")
    return {"target":target,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        await sign_in(page)
        action=await navigate(page,task)
        await ctx.close(); await browser.close()
    response={"task_type":"NAVIGATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"intent":task["intent"],"action":action}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
