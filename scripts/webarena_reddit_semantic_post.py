#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH, submit
from webarena_reddit_forum_resolver import resolve_forum

def clean(s): return " ".join(str(s).split())

def compile_intent(task):
    tid=int(task["intent_template_id"]); inst=task["instantiation_dict"]
    if tid==6100:
        category=clean(inst["category"]); price=clean(inst["price"])
        return {
            "forum_description":category,
            "title":f"{category} recommendations",
            "body":f"I need recommendations for {category} within a budget of {price} please",
        }
    if tid==12:
        issue=clean(inst["issue"])
        return {"forum_description":f"relationships relationship advice {issue}","title":issue,"body":"Please help"}
    if tid==13:
        topic=clean(inst["topic"])
        return {"forum_description":topic,"title":topic,"body":"your opinion"}
    if tid==16:
        interest=clean(inst["interest"]); date=clean(inst["date"]); forum=clean(inst["forum"])
        return {
            "forum_description":f"{forum} {interest}",
            "title":f"{interest} Meet up!",
            "body":f"virtual meetup for {interest} on {date}",
        }
    if tid==3765:
        question=clean(inst["question"])
        return {"forum_description":question,"title":question,"body":None}
    raise SystemExit(f"unsupported semantic-post template {tid}")

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    compiled=compile_intent(task)
    base=a.base_url.rstrip("/")
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        forum=await resolve_forum(page,base,compiled["forum_description"])
        spec={"forum":forum["slug"],"title":compiled["title"],"body":compiled["body"]}
        action=await submit(page,base,spec)
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"compiled":compiled,"forum":forum,"spec":spec,"action":action}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
