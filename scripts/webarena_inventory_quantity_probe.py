#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_shopping_admin_inventory_attributes import PRODUCTS, scan_products, qty_rule

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    selected=[t for t in tasks if int(t["task_id"]) in (185,186)]
    out={}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        r=await page.goto(a.base_url.rstrip("/")+PRODUCTS,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError("product grid navigation failed")
        products=await scan_products(page)
        for task in selected:
            rule=qty_rule(task["instantiation_dict"]["N"])
            out[str(task["task_id"])]=[
                {"name":x["name"],"sku":x["sku"],"qty":x["qty"],"href":x["href"]}
                for x in products if rule(x["qty"])
            ]
        await browser.close()
    Path(a.output).write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__": asyncio.run(main())
