#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_shopping_order_history_probe import AUTH_HEADER, clean
from webarena_shopping_category_spend import parse_time, in_time, order_rows, items

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    selected=[t for t in tasks if int(t["task_id"]) in (142,143)]
    result={}
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH_HEADER)
        page=await ctx.new_page()
        all_orders=await order_rows(page,a.base_url)
        for task in selected:
            inst=task["instantiation_dict"]
            spec=parse_time(inst["time"])
            relevant=[o for o in all_orders if in_time(o["date"],spec)]
            rows=[]
            for order in relevant:
                its=await items(page,order)
                rows.append({
                    "order_no":order["order_no"],
                    "date":order["date"].date().isoformat(),
                    "items":[{"name":x["name"],"subtotal":str(x["subtotal"])} for x in its],
                })
            result[str(task["task_id"])]={
                "category":clean(inst["category"]),
                "time":inst["time"],
                "orders":rows,
            }
        await b.close()
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
