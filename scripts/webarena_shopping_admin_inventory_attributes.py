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
    table,headers=await live_table(page)
    pager=page.locator('.admin__data-grid-pager:visible').first
    current=pager.locator('input[data-ui-id="current-page-input"]')
    if await current.count()==0:
        return
    value=(await current.input_value()).strip()
    if value=="1":
        return
    before=await first_sku(table,headers)
    await current.fill("1")
    await current.press("Enter")
    for _ in range(100):
        await page.wait_for_timeout(100)
        table2,headers2=await live_table(page)
        now=(await current.input_value()).strip()
        first=await first_sku(table2,headers2)
        if now=="1" and first and first!=before:
            return
    raise RuntimeError("product pager failed to set current page to 1")

async def advance(page,table,headers):
    pager=page.locator('.admin__data-grid-pager:visible').first
    current=pager.locator('input[data-ui-id="current-page-input"]')
    nxt=pager.locator("button.action-next")
    if await nxt.count()==0 or not await nxt.is_enabled():
        return False
    before_page=int((await current.input_value()).strip()) if await current.count() else None
    await nxt.click(force=True)
    for _ in range(120):
        await page.wait_for_timeout(100)
        await live_table(page)
        if await current.count():
            now=(await current.input_value()).strip()
            if now.isdigit() and before_page is not None and int(now)==before_page+1:
                return True
    if not await nxt.is_enabled():
        return False
    raise RuntimeError("product pager next did not advance current page")

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

async def read_control_value(control):
    tag=(await control.evaluate("(e)=>e.tagName.toLowerCase()"))
    if tag=="select":
        selected=control.locator("option:checked")
        vals=[clean(await selected.nth(i).inner_text()) for i in range(await selected.count())]
        vals=[v for v in vals if v and v not in {"-- Please Select --","Please Select"}]
        return ", ".join(vals) if vals else None
    try:
        value=clean(await control.input_value())
        return value or None
    except Exception:
        value=clean(await control.inner_text())
        return value or None

async def field_value(page,label):
    labels=page.locator("label.admin__field-label")
    target=None
    for i in range(await labels.count()):
        if clean(await labels.nth(i).inner_text()).lower()==label.lower():
            target=labels.nth(i); break
    if target is not None:
        fid=await target.get_attribute("for")
        if fid:
            control=page.locator(f'[id="{fid}"]')
            if await control.count():
                value=await read_control_value(control.first)
                if value:
                    return value

    # Magento product EAV controls can be present without a currently visible
    # label. Fall back to the stable attribute code in the form control name.
    code=label.strip().lower().replace(" ","_")
    controls=page.locator(f'[name="product[{code}]"]')
    if await controls.count():
        for i in range(await controls.count()):
            value=await read_control_value(controls.nth(i))
            if value:
                return value
    return None

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

def parent_name_for_variant(name):
    value=clean(name)
    m=re.match(r"^(.*)-([^-]+)-([^-]+)$",value)
    return clean(m.group(1)) if m else None

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
            if "material" in need and not record.get("material"):
                base=parent_name_for_variant(product["name"])
                parent=next((p for p in products if base and clean(p["name"]).casefold()==base.casefold()),None)
                if parent and parent.get("href"):
                    record.update(await enrich(page,parent,["material"]))
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
