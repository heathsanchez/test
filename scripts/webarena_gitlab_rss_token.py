#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE, sign_in

async def find_feed_token(page):
    candidates=[
        BASE+"/",
        BASE+"/dashboard/activity",
        BASE+"/users/byteblaze/activity",
    ]
    seen=[]
    for url in candidates:
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status not in (200,302): continue
        links=page.locator('a[href*="feed_token"], link[href*="feed_token"]')
        for i in range(await links.count()):
            href=await links.nth(i).get_attribute("href")
            if not href: continue
            seen.append(href)
            token=parse_qs(urlparse(href).query).get("feed_token",[])
            if token and token[0]:
                return token[0],seen
    raise RuntimeError(f"RSS feed token not found; observed={seen}")

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=312: raise SystemExit("unsupported template")
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await sign_in(page)
        token,links=await find_feed_token(page)
        await b.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[token],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"task_id":a.task_id,"feed_token":token,"observed_links":links},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"feed_token":token},indent=2))

if __name__=="__main__": asyncio.run(main())
