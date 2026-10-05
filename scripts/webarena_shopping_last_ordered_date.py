#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",s).strip()

def parse_date(text):
    s=clean(text)
    for fmt in ("%m/%d/%Y","%B %d, %Y","%b %d, %Y"):
        try: return datetime.strptime(s,fmt)
        except ValueError: pass
    raise ValueError(f"unsupported order date: {s!r}")

async def collect_history(page,base):
    url=base.rstrip("/")+"/sales/order/history/"
    seen=set(); orders=[]; pages=0
    while url and url not in seen and pages<30:
        seen.add(url); pages+=1
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError("order history navigation failed")
        table=page.locator("table.table-order-items.history, table#my-orders-table").first
        if await table.count()==0: raise RuntimeError("order history table missing")
        rows=table.locator("tbody tr")
        for i in range(await rows.count()):
            row=rows.nth(i)
            date_el=row.locator(".col.date").first
            link=row.locator("a.action.view, a[href*='/sales/order/view/']").first
            if await date_el.count()==0 or await link.count()==0: continue
            date_text=clean(await date_el.inner_text())
            href=await link.get_attribute("href")
            if href:
                orders.append({"date_text":date_text,"date":parse_date(date_text),"href":href})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    orders.sort(key=lambda x:x["date"],reverse=True)
    return orders,pages

async def item_names(page,href):
    r=await page.goto(href,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"order detail failed: {href}")
    sels=[".product-item-name",".col.name .product-item-name",".order-details-items .product-item-name"]
    names=[]
    for sel in sels:
        loc=page.locator(sel)
        if await loc.count():
            for i in range(await loc.count()):
                t=clean(await loc.nth(i).inner_text())
                if t and t not in names: names.append(t)
            if names: break
    if not names:
        rows=page.locator("table tbody tr")
        for i in range(await rows.count()):
            txt=clean(await rows.nth(i).inner_text())
            if txt: names.append(txt)
    return names

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=169: raise SystemExit("unsupported template")
    wanted=clean(task["instantiation_dict"]["description"]).casefold()
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers={"X-M2-Customer-Auto-Login":"emma.lopez@gmail.com:Password.123"})
        page=await ctx.new_page()
        orders,pages=await collect_history(page,a.base_url)
        match=None; inspected=0
        for order in orders:
            names=await item_names(page,order["href"]); inspected+=1
            if any(wanted in n.casefold() for n in names):
                match={"date_text":order["date_text"],"names":names,"href":order["href"]}
                break
        await b.close()
    if match is None:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[None],"error_details":None}
    else:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[match["date_text"]],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"wanted":wanted,"history_pages":pages,"orders_inspected":inspected,"match":match},indent=2,default=str)+"\n")
    print(json.dumps({"task_id":a.task_id,"wanted":wanted,"orders_inspected":inspected,"match":match},indent=2,default=str))

if __name__=="__main__": asyncio.run(main())
