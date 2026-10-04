#!/usr/bin/env python3
"""Shopping Admin customer order-count capability for WebArena-Verified template 276.

Uses only the observable Magento order grid. It exposes the existing hidden
Customer Email column through Magento's Columns control, scans the complete
order history, groups rows by email, and applies the task's count/rank rule.
"""

from __future__ import annotations
import argparse, asyncio, json, re
from collections import Counter
from pathlib import Path
from playwright.async_api import async_playwright

ORDER_GRID="/sales/order/"

def clean(s: str) -> str:
    return re.sub(r"\s+"," ",s).strip()

def status_class(s: str) -> str:
    s=clean(s).lower()
    if s in {"canceled","cancelled"}: return "cancelled"
    if s in {"complete","completed"}: return "complete"
    if s=="pending": return "pending"
    return s

def parse_criterion(text: str) -> dict:
    low=clean(text).lower()
    m=re.search(r"have\s+(\d+)\s+orders?\s+in any state",low)
    if m:
        return {"kind":"exact_any","count":int(m.group(1))}
    ranks={
        "most":1,
        "second most":2,
        "third most":3,
        "fourth most":4,
        "fifth most":5,
    }
    for phrase,rank in sorted(ranks.items(),key=lambda kv:-len(kv[0])):
        if f"completed the {phrase} number of orders" in low:
            return {"kind":"completed_rank","rank":rank}
    raise ValueError(f"unsupported order criterion: {text!r}")

async def live_table(page, require_email: bool=True):
    tables=page.locator("table:visible")
    for i in range(await tables.count()):
        table=tables.nth(i)
        th=table.locator("thead th")
        headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
        lower=[h.lower() for h in headers]
        needed={"id","status"}
        if require_email:
            needed.add("customer email")
        if needed.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
            return table,headers
    raise RuntimeError("live order grid with Customer Email not found")

async def expose_customer_email(page):
    controls=page.locator(".admin__data-grid-action-columns:visible")
    if await controls.count()==0:
        raise RuntimeError("Magento Columns control not found")
    control=controls.first
    await control.locator("button.admin__action-dropdown").click()
    labels=control.locator("label.admin__field-label")
    target=None
    for i in range(await labels.count()):
        if clean(await labels.nth(i).inner_text()).lower()=="customer email":
            target=labels.nth(i)
            break
    if target is None:
        raise RuntimeError("Customer Email column option not found")
    input_id=await target.get_attribute("for")
    if not input_id:
        raise RuntimeError("Customer Email column checkbox has no id")
    box=page.locator("#"+input_id)
    if not await box.is_checked():
        await box.check(force=True)
    # Close the dropdown and wait for the grid to re-render.
    await control.locator("button.admin__action-dropdown").click()
    for _ in range(80):
        await page.wait_for_timeout(100)
        try:
            await live_table(page,require_email=True)
            return
        except Exception:
            pass
    raise RuntimeError("Customer Email column did not become visible")

async def first_id(table,headers):
    idx=[h.lower() for h in headers].index("id")
    row=table.locator("tbody tr").first
    if not await row.count(): return None
    cells=row.locator("td")
    return clean(await cells.nth(idx).inner_text()) if await cells.count()>idx else None

async def rewind_first(page):
    for _ in range(30):
        table,headers=await live_table(page)
        wraps=page.locator(".admin__data-grid-pager-wrap:visible")
        prev=None
        for i in range(await wraps.count()):
            cand=wraps.nth(i).locator("button.action-previous")
            if await cand.count():
                prev=cand; break
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
                moved=True; break
        if not moved:
            raise RuntimeError("pager failed to rewind")
    raise RuntimeError("pager did not reach first page")

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
        if before and current and current!=before:
            return True
    raise RuntimeError("pager next did not change grid")

async def scan_all(page):
    rows_out=[]; seen=set()
    for _ in range(50):
        table,headers=await live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","status","customer email"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells=rows.nth(ri).locator("td")
            if await cells.count()<=max(ix.values()): continue
            oid=clean(await cells.nth(ix["id"]).inner_text())
            if not oid or oid in seen: continue
            seen.add(oid)
            email=clean(await cells.nth(ix["customer email"]).inner_text())
            st=clean(await cells.nth(ix["status"]).inner_text())
            if email:
                rows_out.append({"order_id":oid,"email":email,"status_class":status_class(st),"status_text":st})
        if not await advance(page,table,headers): break
    if not rows_out:
        raise RuntimeError("no order rows collected")
    return rows_out

def answer(rows,criterion):
    if criterion["kind"]=="exact_any":
        counts=Counter(r["email"] for r in rows)
        emails=sorted(e for e,n in counts.items() if n==criterion["count"])
    elif criterion["kind"]=="completed_rank":
        counts=Counter(r["email"] for r in rows if r["status_class"]=="complete")
        distinct=sorted(set(counts.values()),reverse=True)
        rank=criterion["rank"]
        emails=[] if rank>len(distinct) else sorted(e for e,n in counts.items() if n==distinct[rank-1])
    else:
        raise ValueError(criterion)
    if not emails:
        return {"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    return {"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":emails,"error_details":None}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    criterion=parse_criterion(task["intent"])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+ORDER_GRID,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200:
            raise RuntimeError("order grid navigation failed")
        await expose_customer_email(page)
        await rewind_first(page)
        rows=await scan_all(page)
        response=answer(rows,criterion)
        await browser.close()
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={
        "task_id":a.task_id,
        "criterion":criterion,
        "rows_scanned":len(rows),
        "unique_customers":len(set(r["email"] for r in rows)),
        "response":response,
    }
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
