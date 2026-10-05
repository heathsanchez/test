#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
from webarena_shopping_order_history_probe import AUTH_HEADER, clean, product_match
from webarena_shopping_last_ordered_date import collect_history, item_names

async def catalog_aliases(page,base,query):
    r=await page.goto(base.rstrip("/")+"/catalogsearch/result/?q="+quote(query),wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: return []
    out=[]
    loc=page.locator(".product-item-link")
    for i in range(min(40,await loc.count())):
        name=clean(await loc.nth(i).inner_text())
        if name and name not in out: out.append(name)
    return out

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    wanted=clean(task["instantiation_dict"]["description"])
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH_HEADER)
        page=await ctx.new_page()
        aliases=[wanted]+await catalog_aliases(page,a.base_url,wanted)
        orders,pages=await collect_history(page,a.base_url)
        match=None; inspected=0
        for order in orders:
            names=await item_names(page,order["href"]); inspected+=1
            if any(any(product_match(alias,n) for alias in aliases) for n in names):
                match={"date_text":order["date_text"],"names":names,"href":order["href"]}
                break
        await b.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[match["date_text"] if match else None],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    evidence={"wanted":wanted,"aliases":aliases,"history_pages":pages,"orders_inspected":inspected,"match":match}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,default=str)+"\n")
    print(json.dumps({"task_id":a.task_id,**evidence},indent=2,default=str))
if __name__=="__main__": asyncio.run(main())
