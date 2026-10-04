#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

ORDER_GRID="/sales/order/"

def clean(s): return re.sub(r"\s+"," ",s).strip()
def status_class(s):
    s=clean(s).lower()
    if s in {"canceled","cancelled"}: return "cancelled"
    if s in {"complete","completed"}: return "complete"
    if s=="pending": return "pending"
    return s
def parse_money(text):
    m=re.search(r"-?\d[\d,]*(?:\.\d+)?",clean(text))
    if not m: raise ValueError(f"no price in {text!r}")
    return round(float(m.group(0).replace(",","")),2)
def parse_task(intent):
    low=intent.lower()
    direction="recent" if any(x in low for x in ["most recent","newest"]) else "oldest"
    if "cancelled" in low or "canceled" in low: status="cancelled"
    elif "complete" in low or "completed" in low: status="complete"
    elif "pending" in low: status="pending"
    else: raise ValueError(intent)
    if "customer email" in low: mode="email"
    elif "product name" in low and "price" in low: mode="items_price"
    else: raise ValueError(intent)
    return {"direction":direction,"status":status,"mode":mode}

async def live_table(page):
    for _ in range(100):
        tables=page.locator("table:visible")
        for i in range(await tables.count()):
            table=tables.nth(i); th=table.locator("thead th")
            headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
            lower=[h.lower() for h in headers]
            if {"id","purchase date","status"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
                return table,headers
        await page.wait_for_timeout(100)
    raise RuntimeError("live order grid not found")

async def first_id(table,headers):
    idx=[h.lower() for h in headers].index("id")
    row=table.locator("tbody tr").first; cells=row.locator("td")
    return clean(await cells.nth(idx).inner_text()) if await cells.count()>idx else None

async def rewind_first(page):
    table,headers=await live_table(page)
    pager=page.locator('.admin__data-grid-pager:visible').first
    current=pager.locator('input[data-ui-id="current-page-input"]')
    if await current.count()==0 or (await current.input_value()).strip()=="1": return
    before=await first_id(table,headers)
    await current.fill("1"); await current.press("Enter")
    for _ in range(100):
        await page.wait_for_timeout(100)
        t,h=await live_table(page)
        if (await current.input_value()).strip()=="1" and await first_id(t,h)!=before: return
    raise RuntimeError("order pager failed to normalize")

async def next_page(page,table,headers):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible"); nxt=None
    for i in range(await wraps.count()):
        cand=wraps.nth(i).locator("button.action-next")
        if await cand.count() and await cand.is_enabled(): nxt=cand; break
    if nxt is None: return False
    before=await first_id(table,headers); await nxt.click(force=True)
    for _ in range(100):
        await page.wait_for_timeout(100)
        t,h=await live_table(page)
        if before and await first_id(t,h)!=before: return True
    raise RuntimeError("order pager next did not change grid")

async def select_order(page,selector):
    await rewind_first(page); matches=[]
    for _ in range(30):
        table,headers=await live_table(page); lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","status"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            row=rows.nth(ri); cells=row.locator("td")
            if await cells.count()<=max(ix.values()): continue
            st=clean(await cells.nth(ix["status"]).inner_text())
            if status_class(st)!=selector["status"]: continue
            oid=clean(await cells.nth(ix["id"]).inner_text())
            links=row.locator('a[href*="/sales/order/view/"]')
            href=await links.first.get_attribute("href") if await links.count() else None
            matches.append({"order_id":oid,"href":href})
            if selector["direction"]=="recent": return matches[0]
        if not await next_page(page,table,headers): break
    return matches[-1] if matches else None

async def extract_email(page):
    table=page.locator("table.order-account-information-table")
    rows=table.locator("tr")
    for i in range(await rows.count()):
        row=rows.nth(i); th=row.locator("th"); td=row.locator("td")
        if await th.count() and clean(await th.first.inner_text()).lower()=="email":
            return clean(await td.first.inner_text())
    raise RuntimeError("order email not found")

async def extract_items(page):
    table=page.locator("table.edit-order-table")
    th=table.locator("thead th")
    headers=[clean(await th.nth(i).inner_text()).lower() for i in range(await th.count())]
    pix=headers.index("product"); prx=headers.index("price")
    rows=table.locator("tbody tr"); out=[]
    for i in range(await rows.count()):
        cells=rows.nth(i).locator("td")
        if await cells.count()<=max(pix,prx): continue
        product_cell=cells.nth(pix)
        title=product_cell.locator(".product-title")
        name=clean(await title.first.inner_text()) if await title.count() else clean(await product_cell.inner_text()).split(" SKU:")[0]
        if name: out.append({"name":name,"price":parse_money(await cells.nth(prx).inner_text())})
    if not out: raise RuntimeError("no order items")
    return sorted(out,key=lambda x:(x["price"],x["name"].casefold()))

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text()); task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    selector=parse_task(task["intent"])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+ORDER_GRID,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("order grid navigation failed")
        selected=await select_order(page,selector)
        if selected is None:
            response={"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
        else:
            if not selected["href"]: raise RuntimeError("selected order has no view link")
            resp=await page.goto(selected["href"],wait_until="networkidle",timeout=120000)
            if resp is None or resp.status!=200: raise RuntimeError("order detail navigation failed")
            data=[await extract_email(page)] if selector["mode"]=="email" else await extract_items(page)
            response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}
        await browser.close()
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"task_id":a.task_id,"selector":selector,"selected":selected,"response":response},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"selector":selector,"selected":selected,"response":response},indent=2))

if __name__=="__main__": asyncio.run(main())
