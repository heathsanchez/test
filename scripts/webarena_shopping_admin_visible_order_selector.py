#!/usr/bin/env python3
"""Visible-grid order selector for WebArena-Verified template 366.

Selects by status and recency, then returns only attributes already visible in
the Magento order grid: order ID, billing name, and purchase date.
"""

from __future__ import annotations
import argparse, asyncio, json, re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

ORDER_GRID="/sales/order/"

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

def status_class(s):
    s=clean(s).lower()
    if s in {"canceled","cancelled"}: return "cancelled"
    if s in {"complete","completed"}: return "complete"
    if s=="pending": return "pending"
    return s

def parse_selector(intent):
    low=intent.lower()
    direction="recent" if any(x in low for x in ["most recent","newest"]) else "oldest"
    if "cancelled" in low or "canceled" in low: status="cancelled"
    elif "pending" in low: status="pending"
    elif "complete" in low or "completed" in low: status="complete"
    else: raise ValueError(f"unsupported status: {intent}")
    if "billing name" in low: attr="billing_name"
    elif "purchase date and order id" in low: attr="purchase_date_and_order_id"
    elif re.search(r"\border id\b",low): attr="order_id"
    elif re.search(r"\bdate\b",low): attr="date"
    else: raise ValueError(f"unsupported visible attribute: {intent}")
    return {"direction":direction,"status":status,"attribute":attr}

def iso_date(text):
    value=clean(text)
    for fmt in ("%B %d, %Y %I:%M:%S %p","%b %d, %Y %I:%M:%S %p"):
        try:
            return datetime.strptime(value,fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"unsupported Magento date format: {value!r}")

async def live_table(page):
    tables=page.locator("table:visible")
    for i in range(await tables.count()):
        table=tables.nth(i)
        th=table.locator("thead th")
        headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
        lower=[h.lower() for h in headers]
        if {"id","purchase date","bill-to name","status"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
            return table,headers
    raise RuntimeError("live order grid not found")

async def first_id(table,headers):
    idx=[h.lower() for h in headers].index("id")
    row=table.locator("tbody tr").first
    if not await row.count(): return None
    td=row.locator("td")
    return clean(await td.nth(idx).inner_text()) if await td.count()>idx else None

async def rewind_first(page):
    # Magento persists grid paging state across visits. Rewind to page 1 so
    # "newest"/"most recent" means global recency, independent of prior tasks.
    for _ in range(20):
        table,headers=await live_table(page)
        wraps=page.locator(".admin__data-grid-pager-wrap:visible")
        prev=None
        for i in range(await wraps.count()):
            cand=wraps.nth(i).locator("button.action-previous")
            if await cand.count():
                prev=cand
                break
        if prev is None or not await prev.is_enabled():
            return
        before=await first_id(table,headers)
        await prev.click(force=True)
        moved=False
        for _ in range(80):
            await page.wait_for_timeout(100)
            table2,headers2=await live_table(page)
            current=await first_id(table2,headers2)
            if before and current and current!=before:
                moved=True
                break
        if not moved:
            raise RuntimeError("Magento pager failed to rewind to previous page")
    raise RuntimeError("Magento pager did not reach page 1 within bound")


async def advance(page,table,headers):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    button=None
    for i in range(await wraps.count()):
        cand=wraps.nth(i).locator("button.action-next")
        if await cand.count() and await cand.is_enabled():
            button=cand; break
    if button is None: return False
    before=await first_id(table,headers)
    await button.click(force=True)
    for _ in range(80):
        await page.wait_for_timeout(100)
        table2,headers2=await live_table(page)
        current=await first_id(table2,headers2)
        if before and current and current!=before: return True
    return False

async def scan(page):
    out=[]; seen=set()
    for _ in range(20):
        table,headers=await live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","purchase date","bill-to name","status"]}
        rows=table.locator("tbody tr")
        for r in range(await rows.count()):
            td=rows.nth(r).locator("td")
            if await td.count()<=max(ix.values()): continue
            oid=clean(await td.nth(ix["id"]).inner_text())
            if not oid or oid in seen: continue
            seen.add(oid)
            st=clean(await td.nth(ix["status"]).inner_text())
            out.append({
                "order_id":oid,
                "purchase_date_raw":clean(await td.nth(ix["purchase date"]).inner_text()),
                "billing_name":clean(await td.nth(ix["bill-to name"]).inner_text()),
                "status_text":st,
                "status_class":status_class(st),
            })
        if not await advance(page,table,headers): break
    return out

def make_response(rows,selector):
    matches=[r for r in rows if r["status_class"]==selector["status"]]
    if not matches:
        return {"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None},None
    row=matches[0] if selector["direction"]=="recent" else matches[-1]
    attr=selector["attribute"]
    if attr=="billing_name": data=[row["billing_name"]]
    elif attr=="order_id": data=[int(row["order_id"])]
    elif attr=="date": data=[iso_date(row["purchase_date_raw"])]
    elif attr=="purchase_date_and_order_id":
        data=[{"purchase_date":iso_date(row["purchase_date_raw"]),"order_id":row["order_id"]}]
    else: raise ValueError(attr)
    return {"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None},row

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    selector=parse_selector(task["intent"])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+ORDER_GRID,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("order grid navigation failed")
        await rewind_first(page)
        rows=await scan(page)
        response,selected=make_response(rows,selector)
        await browser.close()
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"selector":selector,"rows_scanned":len(rows),"selected":selected},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"response":response,"selector":selector,"rows_scanned":len(rows),"selected":selected},indent=2))

if __name__=="__main__":
    asyncio.run(main())
