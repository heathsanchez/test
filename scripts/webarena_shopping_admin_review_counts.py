#!/usr/bin/env python3
"""Review-grid counting capability for WebArena-Verified templates 288 and 248.

Uses only the observable Magento product-review grid. Supports:
- count reviews whose title/detail mention a term;
- count reviews in a month/year or across all history.
"""

from __future__ import annotations
import argparse, asyncio, calendar, json, re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

REVIEW_GRID="/review/product/"

def clean(s:str)->str:
    return re.sub(r"\s+"," ",s).strip()

def parse_created(text:str):
    value=clean(text)
    fmts=(
        "%B %d, %Y %I:%M:%S %p",
        "%b %d, %Y %I:%M:%S %p",
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y",
    )
    for fmt in fmts:
        try: return datetime.strptime(value,fmt)
        except ValueError: pass
    raise ValueError(f"unsupported review date: {value!r}")

async def live_table(page):
    tables=page.locator("table:visible")
    for i in range(await tables.count()):
        table=tables.nth(i)
        th=table.locator("thead th")
        headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
        lower=[h.lower() for h in headers]
        if {"id","created","title","review"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
            return table,headers
    raise RuntimeError("live review grid not found")

async def first_id(table,headers):
    idx=[h.lower() for h in headers].index("id")
    row=table.locator("tbody tr").first
    if not await row.count(): return None
    cells=row.locator("td")
    return clean(await cells.nth(idx).inner_text()) if await cells.count()>idx else None

async def pager_state(page):
    pager=page.locator('.admin__data-grid-pager:visible').first
    current=pager.locator('input[data-ui-id="current-page-input"]')
    labels=pager.locator('label.admin__control-support-text')
    pages=1
    for i in range(await labels.count()):
        txt=clean(await labels.nth(i).inner_text())
        m=re.search(r"of\s+(\d+)",txt,re.I)
        if m:
            pages=int(m.group(1))
            break
    return pager,current,pages

async def goto_page(page,target:int,previous_first=None):
    table,headers=await live_table(page)
    pager,current,pages=await pager_state(page)
    if target<1 or target>pages:
        raise RuntimeError(f"review page {target} outside 1..{pages}")
    now=(await current.input_value()).strip()
    if now==str(target):
        return table,headers,pages
    await current.fill(str(target))
    await current.press("Enter")
    for _ in range(120):
        await page.wait_for_timeout(100)
        table2,headers2=await live_table(page)
        now=(await current.input_value()).strip()
        first=await first_id(table2,headers2)
        if now==str(target) and (previous_first is None or first!=previous_first):
            return table2,headers2,pages
    raise RuntimeError(f"review pager failed to reach page {target}")

async def scan_all(page):
    out=[]; seen=set()
    table,headers=await live_table(page)
    first=await first_id(table,headers)
    table,headers,pages=await goto_page(page,1,previous_first=None)
    for pageno in range(1,pages+1):
        if pageno>1:
            prev_first=await first_id(table,headers)
            table,headers,_=await goto_page(page,pageno,previous_first=prev_first)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","created","title","review"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells=rows.nth(ri).locator("td")
            if await cells.count()<=max(ix.values()): continue
            rid=clean(await cells.nth(ix["id"]).inner_text())
            if not rid or rid in seen: continue
            seen.add(rid)
            out.append({
                "review_id":rid,
                "created_raw":clean(await cells.nth(ix["created"]).inner_text()),
                "title":clean(await cells.nth(ix["title"]).inner_text()),
                "detail":clean(await cells.nth(ix["review"]).inner_text()),
            })
    if not out: raise RuntimeError("no reviews collected")
    return out

def task_mode(task):
    tid=int(task["intent_template_id"])
    inst=task.get("instantiation_dict",{})
    if tid==288:
        return {"kind":"term","term":str(inst["term"])}
    if tid==248:
        phrase=str(inst.get("time","")).strip().lower()
        m=re.fullmatch(r"in\s+([A-Za-z]+)\s+(\d{4})",phrase)
        if m:
            month=next(i for i in range(1,13) if calendar.month_abbr[i].lower()==m.group(1).lower() or calendar.month_name[i].lower()==m.group(1).lower())
            return {"kind":"month","month":month,"year":int(m.group(2))}
        m=re.fullmatch(r"during\s+(\d{4})",phrase)
        if m: return {"kind":"year","year":int(m.group(1))}
        if phrase in {"so far","from the beginning of the shop"}:
            return {"kind":"all"}
    raise ValueError(f"unsupported review-count task: {task['intent']!r}")

def count_rows(rows,mode):
    kind=mode["kind"]
    if kind=="term":
        needle=mode["term"].casefold()
        return sum(1 for r in rows if needle in (r["title"]+" "+r["detail"]).casefold())
    dated=[(r,parse_created(r["created_raw"])) for r in rows]
    if kind=="month":
        return sum(1 for _,d in dated if d.year==mode["year"] and d.month==mode["month"])
    if kind=="year":
        return sum(1 for _,d in dated if d.year==mode["year"])
    if kind=="all":
        return len(rows)
    raise ValueError(mode)

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    mode=task_mode(task)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+REVIEW_GRID,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("review grid navigation failed")
        rows=await scan_all(page)
        count=count_rows(rows,mode)
        await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[count],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"mode":mode,"rows_scanned":len(rows),"count":count}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
