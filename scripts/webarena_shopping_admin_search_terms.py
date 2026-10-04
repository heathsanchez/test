#!/usr/bin/env python3
"""Search-term analytics capability for WebArena-Verified Shopping Admin.

Reads only the observable Magento Search Terms grid. Compiles:
- top-N search terms by Uses/popularity;
- top-N search terms with Results > 0.
"""

from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

SEARCH_TERMS="/search/term/index/"

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

def num(s):
    t=clean(s).replace(",","")
    m=re.search(r"-?\d+",t)
    if not m: raise ValueError(f"no integer in {s!r}")
    return int(m.group(0))

async def live_table(page):
    tables=page.locator("table:visible")
    for i in range(await tables.count()):
        table=tables.nth(i)
        th=table.locator("thead th")
        headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
        lower=[h.lower() for h in headers]
        if {"search query","results","uses"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
            return table,headers
    raise RuntimeError("live search-term grid not found")

async def first_query(table,headers):
    lower=[h.lower() for h in headers]
    idx=lower.index("search query")
    row=table.locator("tbody tr").first
    if not await row.count(): return None
    cells=row.locator("td")
    return clean(await cells.nth(idx).inner_text()) if await cells.count()>idx else None

async def goto_first(page):
    table,headers=await live_table(page)
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    if await wraps.count()==0: return
    pager=wraps.first
    inp=pager.locator('input[data-ui-id="current-page-input"]')
    if await inp.count():
        if (await inp.input_value()).strip()!="1":
            before=await first_query(table,headers)
            await inp.fill("1"); await inp.press("Enter")
            for _ in range(100):
                await page.wait_for_timeout(100)
                t,h=await live_table(page)
                now=(await inp.input_value()).strip()
                q=await first_query(t,h)
                if now=="1" and q and q!=before: return
            raise RuntimeError("search-term pager failed to reach page 1")

async def advance(page,table,headers):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    if await wraps.count()==0: return False
    nxt=wraps.first.locator("button.action-next")
    if not await nxt.count() or not await nxt.is_enabled(): return False
    before=await first_query(table,headers)
    await nxt.click(force=True)
    for _ in range(100):
        await page.wait_for_timeout(100)
        t,h=await live_table(page)
        q=await first_query(t,h)
        if before and q and q!=before: return True
    raise RuntimeError("search-term pager next did not change grid")

async def scan_all(page):
    await goto_first(page)
    out=[]; seen=set()
    for _ in range(50):
        table,headers=await live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["search query","results","uses"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells=rows.nth(ri).locator("td")
            if await cells.count()<=max(ix.values()): continue
            query=clean(await cells.nth(ix["search query"]).inner_text())
            if not query or query in seen: continue
            seen.add(query)
            out.append({
                "query":query,
                "results":num(await cells.nth(ix["results"]).inner_text()),
                "uses":num(await cells.nth(ix["uses"]).inner_text()),
                "ordinal":len(out),
            })
        if not await advance(page,table,headers): break
    if not out: raise RuntimeError("no search terms collected")
    return out

def mode(task):
    if int(task["intent_template_id"])==285:
        return {"n":int(task["instantiation_dict"]["n"]),"available_only":False}
    if int(task["intent_template_id"])==1001:
        return {"n":3,"available_only":True}
    raise ValueError(f"unsupported search-term task {task['task_id']}")

def answer(rows,m):
    pool=[r for r in rows if (not m["available_only"] or r["results"]>0)]
    # Primary semantics: descending Uses/popularity. Preserve observed grid order for ties.
    pool=sorted(pool,key=lambda r:(-r["uses"],r["ordinal"]))
    return [r["query"] for r in pool[:m["n"]]]

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    m=mode(task)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+SEARCH_TERMS,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("search-term grid navigation failed")
        rows=await scan_all(page)
        data=answer(rows,m)
        await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"mode":m,"rows_scanned":len(rows),"top_observed":sorted(rows,key=lambda r:(-r["uses"],r["ordinal"]))[:10],"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
