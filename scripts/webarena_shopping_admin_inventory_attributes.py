#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

PRODUCTS="/catalog/product/index/"

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

def parse_qty(text):
    t=clean(text).replace(",","")
    m=re.search(r"-?\d+(?:\.\d+)?",t)
    return float(m.group(0)) if m else None

def qty_rule(token):
    token=str(token).strip()
    m=re.fullmatch(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)",token)
    if m:
        lo,hi=map(float,m.groups())
        return lambda x: x is not None and lo<=x<=hi
    target=float(token)
    return lambda x: x is not None and x==target

async def live_table(page):
    tables=page.locator("table:visible")
    for i in range(await tables.count()):
        table=tables.nth(i)
        th=table.locator("thead th")
        headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
        lower=[h.lower() for h in headers]
        if {"name","sku","salable quantity"}.issubset(set(lower)) and await table.locator("tbody tr").count()>0:
            return table,headers
    raise RuntimeError("live product grid with Salable Quantity not found")

async def first_sku(table,headers):
    idx=[h.lower() for h in headers].index("sku")
    row=table.locator("tbody tr").first
    if not await row.count(): return None
    td=row.locator("td")
    return clean(await td.nth(idx).inner_text()) if await td.count()>idx else None

async def rewind_first(page):
    for _ in range(50):
        table,headers=await live_table(page)
        wraps=page.locator(".admin__data-grid-pager-wrap:visible")
        prev=None
        for i in range(await wraps.count()):
            cand=wraps.nth(i).locator("button.action-previous")
            if await cand.count():
                prev=cand; break
        if prev is None or not await prev.is_enabled(): return
        before=await first_sku(table,headers)
        await prev.click(force=True)
        for _ in range(100):
            await page.wait_for_timeout(100)
            table2,headers2=await live_table(page)
            cur=await first_sku(table2,headers2)
            if before and cur and cur!=before: break
        else: raise RuntimeError("product pager failed to rewind")
    raise RuntimeError("product pager did not reach first page")

async def advance(page,table,headers):
    wraps=page.locator(".admin__data-grid-pager-wrap:visible")
    nxt=None
    for i in range(await wraps.count()):
        cand=wraps.nth(i).locator("button.action-next")
        if await cand.count() and await cand.is_enabled():
            nxt=cand; break
    if nxt is None: return False
    before=await first_sku(table,headers)
    await nxt.click(force=True)
    for _ in range(100):
        await page.wait_for_timeout(100)
        t,h=await live_table(page)
        cur=await first_sku(t,h)
        if before and cur and cur!=before: return True
    raise RuntimeError("product pager next did not change grid")

async def scan_products(page):
    await rewind_first(page)
    out=[]; seen=set()
    for _ in range(80):
        table,headers=await live_table(page)
        lower=[h.lower() for h in headers]
        ix={k:lower.index(k) for k in ["name","sku","salable quantity"]}
        rows=table.locator("tbody tr")
        for ri in range(await rows.count()):
            row=rows.nth(ri); cells=row.locator("td")
            if await cells.count()<=max(ix.values()): continue
            sku=clean(await cells.nth(ix["sku"]).inner_text())
            if not sku or sku in seen: continue
            seen.add(sku)
            links=row.locator('a[href*="/catalog/product/edit/"]')
            href=await links.first.get_attribute("href") if await links.count() else None
            out.append({
                "name":clean(await cells.nth(ix["name"]).inner_text()),
                "sku":sku,
                "qty":parse_qty(await cells.nth(ix["salable quantity"]).inner_text()),
                "href":href,
            })
        if not await advance(page,table,headers): break
    if not out: raise RuntimeError("no products collected")
    return out

async def field_value(page,label):
    labels=page.locator("label.admin__field-label")
    target=None
    for i in range(await labels.count()):
        if clean(await labels.nth(i).inner_text()).lower()==label.lower():
            target=labels.nth(i); break
    if target is None: return None
    fid=await target.get_attribute("for")
    if not fid: return None
    control=page.locator(f'[id="{fid}"]')
    if await control.count()==0: return None
    tag=(await control.evaluate("(e)=>e.tagName.toLowerCase()"))
    if tag=="select":
        selected=control.locator("option:checked")
        vals=[clean(await selected.nth(i).inner_text()) for i in range(await selected.count())]
        vals=[v for v in vals if v and v not in {"-- Please Select --","Please Select"}]
        return ", ".join(vals) if vals else None
    try:
        return clean(await control.input_value())
    except Exception:
        return clean(await control.inner_text())

async def enrich(page,product,attributes):
    if not product["href"]:
        raise RuntimeError(f"no edit link for SKU {product['sku']}")
    await page.goto(product["href"],wait_until="networkidle",timeout=120000)
    values={}
    for attr in attributes:
        values[attr]=await field_value(page,attr.capitalize())
    return values

def mode(task):
    attr=str(task["instantiation_dict"]["Attribute"]).lower()
    if attr=="sku": attrs=["sku"]
    elif "name and color" in attr: attrs=["name","color"]
    elif attr=="material": attrs=["material"]
    elif "names" in attr and "sizes" in attr: attrs=["name","size"]
    else: raise ValueError(attr)
    return attrs,qty_rule(task["instantiation_dict"]["N"])

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    attrs,rule=mode(task)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+PRODUCTS,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("product grid navigation failed")
        products=await scan_products(page)
        matches=[x for x in products if rule(x["qty"])]
        rows=[]
        for product in matches:
            record={"name":product["name"],"sku":product["sku"]}
            need=[x for x in attrs if x not in {"name","sku"}]
            if need:
                record.update(await enrich(page,product,need))
            rows.append(record)
        await browser.close()
    if not rows:
        response={"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    elif attrs==["sku"]:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[r["sku"] for r in rows],"error_details":None}
    elif attrs==["material"]:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[r["material"] for r in rows if r.get("material")],"error_details":None}
    else:
        data=[{k:r.get(k) for k in attrs} for r in rows]
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"products_scanned":len(products),"matching_products":len(rows),"attributes":attrs,"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
