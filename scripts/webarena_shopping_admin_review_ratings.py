#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

REVIEWS="/review/product/"

def clean(s): return re.sub(r"\s+"," ",s).strip()
def norm(s): return clean(s).casefold()
def product_terms(s):
    stop={"product","products","item","items"}
    out=[]
    for t in re.findall(r"[a-z0-9]+",norm(s)):
        if len(t)<2 or t in stop: continue
        # Family descriptions are commonly plural while catalog names are
        # singular ("tanks products" -> "tank"). Keep this deliberately small.
        if len(t)>3 and t.endswith("s") and not t.endswith("ss"):
            t=t[:-1]
        out.append(t)
    return out

def term_match(term,text):
    words=re.findall(r"[a-z0-9]+",norm(text))
    return any(w==term or (len(term)>3 and (w.startswith(term) or term.startswith(w))) for w in words)

async def live_table(page):
    for _ in range(100):
        tables=page.locator("table:visible")
        for i in range(await tables.count()):
            table=tables.nth(i); th=table.locator("thead th")
            headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
            lower=[h.lower() for h in headers]
            if {"id","title","nickname","product"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
                return table,headers
        await page.wait_for_timeout(100)
    raise RuntimeError("live review grid not found")

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
    raise RuntimeError("review pager failed to normalize")

async def next_page(page):
    pager=page.locator('.admin__data-grid-pager:visible').first
    current=pager.locator('input[data-ui-id="current-page-input"]')
    nxt=pager.locator("button.action-next")
    if await nxt.count()==0 or not await nxt.is_enabled(): return False
    before=int((await current.input_value()).strip()) if await current.count() else None
    await nxt.click(force=True)
    for _ in range(120):
        await page.wait_for_timeout(100)
        await live_table(page)
        if await current.count():
            now=(await current.input_value()).strip()
            if now.isdigit() and before is not None and int(now)==before+1: return True
    raise RuntimeError("review pager next did not advance")

async def apply_product_filter(page,product):
    row=page.locator('tr.data-grid-filters[data-role="filter-form"]')
    if await row.count()==0:
        raise RuntimeError("legacy review filter row not found")
    cell=row.locator('td[data-column="name"]')
    control=cell.locator('input.admin__control-text')
    if await control.count()==0:
        raise RuntimeError("legacy Product filter input not found")
    await control.first.fill(product)
    search=page.locator('button[data-action="grid-filter-apply"]')
    if await search.count()==0:
        search=page.get_by_role("button",name="Search")
    if await search.count()==0:
        raise RuntimeError("legacy review Search button not found")
    await search.first.click()
    for _ in range(120):
        await page.wait_for_timeout(100)
        try:
            return await live_table(page)
        except Exception:
            pass
    raise RuntimeError("filtered review grid did not render")

async def matching_reviews(page,product):
    terms=product_terms(product)
    if not terms: raise RuntimeError("empty product query")
    table,headers=await apply_product_filter(page,terms[0])
    out=[]; seen=set()
    lower=[h.lower() for h in headers]
    ix={k:lower.index(k) for k in ["id","title","nickname","product"]}
    rows=table.locator("tbody tr")
    for ri in range(await rows.count()):
        row=rows.nth(ri); cells=row.locator("td")
        if await cells.count()<=max(ix.values()): continue
        rid=clean(await cells.nth(ix["id"]).inner_text())
        if not rid or rid in seen: continue
        seen.add(rid)
        pname=clean(await cells.nth(ix["product"]).inner_text())
        if not all(term_match(term,pname) for term in terms): continue
        links=row.locator('a[href*="/review/product/edit/"]')
        href=await links.first.get_attribute("href") if await links.count() else None
        out.append({
            "review_id":rid,
            "product":pname,
            "title":clean(await cells.nth(ix["title"]).inner_text()),
            "nickname":clean(await cells.nth(ix["nickname"]).inner_text()),
            "href":href,
        })
    return out

async def star_value(page,href):
    if not href: raise RuntimeError("review edit link missing")
    resp=await page.goto(href,wait_until="networkidle",timeout=120000)
    if resp is None or resp.status!=200: raise RuntimeError("review edit navigation failed")
    checked=page.locator('input[type="radio"][name^="ratings["]:checked')
    stars=[]
    for i in range(await checked.count()):
        rid=await checked.nth(i).get_attribute("id")
        if rid:
            m=re.search(r"_(\d+)$",rid)
            if m: stars.append(int(m.group(1)))
    if not stars: raise RuntimeError("selected review rating not found")
    if len(set(stars))!=1:
        raise RuntimeError(f"multiple disagreeing rating dimensions: {stars}")
    return stars[0]

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text()); task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    tid=int(task["intent_template_id"]); product=str(task["instantiation_dict"]["product"])
    if tid not in {245,249}: raise SystemExit("unsupported review-rating template")
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        grid=await ctx.new_page()
        resp=await grid.goto(a.base_url.rstrip("/")+REVIEWS,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("review grid navigation failed")
        rows=await matching_reviews(grid,product)
        detail=await ctx.new_page(); qualified=[]
        for row in rows:
            stars=await star_value(detail,row["href"])
            if stars<=3:
                qualified.append({**row,"stars":stars})
        await browser.close()
    if not qualified:
        response={"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    elif tid==245:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[r["nickname"] for r in qualified],"error_details":None}
    else:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[{"title":r["title"],"rating":str(r["stars"])} for r in qualified],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"product":product,"reviews_seen":len(rows),"qualified":qualified,"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__": asyncio.run(main())
