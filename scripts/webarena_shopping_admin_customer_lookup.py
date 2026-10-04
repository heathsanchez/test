#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

CUSTOMERS="/customer/index/"

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

def digits(s):
    return "".join(ch for ch in s if ch.isdigit())

async def live_table(page):
    for _ in range(120):
        tables=page.locator("table:visible")
        for i in range(await tables.count()):
            table=tables.nth(i)
            th=table.locator("thead th")
            headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
            lower=[h.lower() for h in headers]
            if {"id","name","email","phone"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
                return table,headers
        await page.wait_for_timeout(100)
    raise RuntimeError("live customer grid not found after render wait")

async def first_id(table,headers):
    idx=[h.lower() for h in headers].index("id")
    row=table.locator("tbody tr").first
    if not await row.count(): return None
    cells=row.locator("td")
    return clean(await cells.nth(idx).inner_text()) if await cells.count()>idx else None

async def rewind_first(page):
    table,headers=await live_table(page)
    pager=page.locator('.admin__data-grid-pager:visible').first
    current=pager.locator('input[data-ui-id="current-page-input"]')
    if await current.count()==0:
        return
    value=(await current.input_value()).strip()
    if value=="1":
        return
    before=await first_id(table,headers)
    await current.fill("1")
    await current.press("Enter")
    for _ in range(100):
        await page.wait_for_timeout(100)
        table2,headers2=await live_table(page)
        now=(await current.input_value()).strip()
        first=await first_id(table2,headers2)
        if now=="1" and first and first!=before:
            return
    raise RuntimeError("customer pager failed to set current page to 1")

async def advance(page,table,headers):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    nxt=None
    for i in range(await wraps.count()):
        cand=wraps.nth(i).locator("button.action-next")
        if await cand.count() and await cand.is_enabled():
            nxt=cand; break
    if nxt is None: return False
    before=await first_id(table,headers)
    await nxt.click(force=True)
    for _ in range(80):
        await page.wait_for_timeout(100)
        table2,headers2=await live_table(page)
        current=await first_id(table2,headers2)
        if before and current and current!=before: return True
    raise RuntimeError("customer pager next did not change grid")

async def scan_all(page):
    await rewind_first(page)
    out=[]; seen=set()
    for _ in range(50):
        table,headers=await live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","name","email","phone"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells=rows.nth(ri).locator("td")
            if await cells.count()<=max(ix.values()): continue
            cid=clean(await cells.nth(ix["id"]).inner_text())
            if not cid or cid in seen: continue
            seen.add(cid)
            out.append({
                "id":cid,
                "name":clean(await cells.nth(ix["name"]).inner_text()),
                "email":clean(await cells.nth(ix["email"]).inner_text()),
                "phone":clean(await cells.nth(ix["phone"]).inner_text()),
            })
        if not await advance(page,table,headers): break
    return out

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    target=digits(task["instantiation_dict"]["PhoneNum"])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+CUSTOMERS,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("customer grid navigation failed")
        rows=await scan_all(page)
        await browser.close()
    matches=[{"name":r["name"],"email":r["email"]} for r in rows if digits(r["phone"])==target]
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":matches,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"target_phone_digits":target,"rows_scanned":len(rows),"match_count":len(matches),"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
