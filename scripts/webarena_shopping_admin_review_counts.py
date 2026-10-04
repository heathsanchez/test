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
        "%B %d, %Y, %I:%M:%S %p",
        "%b %d, %Y, %I:%M:%S %p",
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

async def click_grid_button(page,button):
    try:
        async with page.expect_response(lambda r: "/mui/index/render" in r.url, timeout=15000):
            await button.click(force=True)
    except Exception:
        # If the response races ahead of the waiter, fall back to a bounded UI settle.
        await button.click(force=True)
    await page.wait_for_timeout(500)
    return await live_table(page)

async def rewind_first(page):
    for _ in range(50):
        wraps=page.locator(".admin__data-grid-pager-wrap:visible")
        prev=None
        for i in range(await wraps.count()):
            cand=wraps.nth(i).locator("button.action-previous")
            if await cand.count():
                prev=cand
                break
        if prev is None or not await prev.is_enabled():
            return await live_table(page)
        await click_grid_button(page,prev)
    raise RuntimeError("review pager did not reach first page")

async def next_page(page):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    nxt=None
    for i in range(await wraps.count()):
        cand=wraps.nth(i).locator("button.action-next")
        if await cand.count() and await cand.is_enabled():
            nxt=cand
            break
    if nxt is None:
        return None
    return await click_grid_button(page,nxt)

async def set_large_page_size(page):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    if await wraps.count()==0:
        return
    wrap=wraps.first
    toggle=wrap.locator("button.selectmenu-toggle")
    if await toggle.count()==0:
        return
    await toggle.click()
    custom=wrap.get_by_role("button",name="Custom")
    if await custom.count()==0:
        await toggle.click()
        return
    await custom.click()
    field=wrap.locator(".selectmenu-item-edit input.admin__control-text:visible").last
    if await field.count()==0:
        raise RuntimeError("review pager custom size field not found")
    await field.fill("999")
    save=wrap.locator(".selectmenu-item-edit button.action-save:visible").last
    try:
        async with page.expect_response(lambda r: "/mui/index/render" in r.url, timeout=15000):
            await save.click()
    except Exception:
        await save.click()
    await page.wait_for_timeout(750)
    await live_table(page)

async def scan_all(page):
    await rewind_first(page)
    out=[]; seen=set()
    for _ in range(80):
        table,headers=await live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["id","created","title","review"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells=rows.nth(ri).locator("td")
            if await cells.count()<=max(ix.values()): continue
            rid=clean(await cells.nth(ix["id"]).inner_text())
            if not rid or rid in seen: continue
            seen.add(rid)
            links=rows.nth(ri).locator('a[href*="/review/product/edit/"]')
            edit_href=await links.first.get_attribute("href") if await links.count() else None
            out.append({
                "review_id":rid,
                "created_raw":clean(await cells.nth(ix["created"]).inner_text()),
                "title":clean(await cells.nth(ix["title"]).inner_text()),
                "detail":clean(await cells.nth(ix["review"]).inner_text()),
                "edit_href":edit_href,
            })
        if await next_page(page) is None:
            break
    if not out:
        raise RuntimeError("no reviews collected")
    return out

async def filtered_term_count(page,term):
    row=page.locator('tr.data-grid-filters[data-role="filter-form"]')
    if await row.count()==0:
        raise RuntimeError("legacy review filter row not found")
    cell=row.locator('td[data-column="detail"]')
    control=cell.locator('input.admin__control-text')
    if await control.count()==0:
        raise RuntimeError("legacy Review filter input not found")
    await control.first.fill(term)
    search=page.locator('button[data-action="grid-filter-apply"]')
    if await search.count()==0:
        search=page.get_by_role("button",name="Search")
    if await search.count()==0:
        raise RuntimeError("legacy review Search button not found")
    await search.first.click()
    for _ in range(120):
        await page.wait_for_timeout(100)
        total=page.locator('#reviewGrid-total-count')
        if await total.count():
            txt=clean(await total.inner_text())
            if txt.replace(",","").isdigit():
                return int(txt.replace(",",""))
    raise RuntimeError("filtered legacy review count not found")

async def filtered_date_count(page,mode):
    if mode["kind"]=="all":
        total=page.locator("#reviewGrid-total-count")
        if await total.count()==0:
            raise RuntimeError("review total count not found")
        txt=clean(await total.inner_text()).replace(",","")
        if not txt.isdigit():
            raise RuntimeError(f"invalid review total count: {txt!r}")
        return int(txt)

    if mode["kind"]=="month":
        y,m=mode["year"],mode["month"]
        start=f"{m}/1/{y}"
        end=f"{m}/{calendar.monthrange(y,m)[1]}/{y}"
    elif mode["kind"]=="year":
        y=mode["year"]
        start=f"1/1/{y}"
        end=f"12/31/{y}"
    else:
        raise ValueError(mode)

    row=page.locator('tr.data-grid-filters[data-role="filter-form"]')
    cell=row.locator('td[data-column="created_at"]')
    frm=cell.locator('input[name="created_at[from]"]')
    to=cell.locator('input[name="created_at[to]"]')
    if await frm.count()==0 or await to.count()==0:
        raise RuntimeError("legacy Created date inputs not found")
    await frm.fill(start)
    await to.fill(end)
    search=page.locator('button[data-action="grid-filter-apply"]')
    if await search.count()==0:
        search=page.get_by_role("button",name="Search")
    if await search.count()==0:
        raise RuntimeError("legacy review Search button not found")
    await search.first.click()
    for _ in range(120):
        await page.wait_for_timeout(100)
        total=page.locator("#reviewGrid-total-count")
        if await total.count():
            txt=clean(await total.inner_text()).replace(",","")
            if txt.isdigit():
                return int(txt)
    raise RuntimeError("filtered review date count not found")

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

async def enrich_full_text(context,rows):
    page=await context.new_page()
    try:
        for row in rows:
            href=row.get("edit_href")
            if not href:
                raise RuntimeError(f"review {row['review_id']} has no edit link")
            resp=await page.goto(href,wait_until="networkidle",timeout=120000)
            if resp is None or resp.status!=200:
                raise RuntimeError(f"review detail navigation failed for {row['review_id']}")
            title=page.locator('input[name="title"]')
            detail=page.locator('textarea[name="detail"]')
            if await title.count()==0 or await detail.count()==0:
                raise RuntimeError(f"full review fields missing for {row['review_id']}")
            row["full_title"]=clean(await title.input_value())
            row["full_detail"]=clean(await detail.input_value())
    finally:
        await page.close()
    return rows

def count_rows(rows,mode):
    kind=mode["kind"]
    if kind=="term":
        needle=mode["term"].casefold()
        return sum(1 for r in rows if needle in (r.get("full_title",r["title"])+" "+r.get("full_detail",r["detail"])).casefold())
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
        if mode["kind"]=="term":
            count=await filtered_term_count(page,mode["term"])
            rows_scanned=None
        else:
            count=await filtered_date_count(page,mode)
            rows_scanned=None
        await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[count],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"mode":mode,"rows_scanned":rows_scanned,"count":count}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
