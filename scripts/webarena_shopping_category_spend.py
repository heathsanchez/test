#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, calendar, json, re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
from webarena_shopping_order_history_probe import AUTH_HEADER, clean, product_match

def money(text):
    vals=re.findall(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)",clean(text))
    if not vals: raise ValueError(f"no money in {text!r}")
    return Decimal(vals[-1].replace(",",""))

def month_num(token):
    t=token.casefold().rstrip(".")
    for i in range(1,13):
        if t in {calendar.month_name[i].casefold(),calendar.month_abbr[i].casefold()}: return i
    raise ValueError(token)

def parse_time(text):
    s=clean(text)
    m=re.fullmatch(r"(?:during\s+)?([A-Za-z]+)\s+(\d{4})",s,re.I)
    if m:
        mon,y=m.groups(); y=int(y); mm=month_num(mon)
        return ("month",datetime(y,mm,1),None)
    m=re.fullmatch(r"(?:during\s+)?([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})",s,re.I)
    if m:
        mon,d,y=m.groups(); dt=datetime(int(y),month_num(mon),int(d))
        return ("day",dt,None)
    raise ValueError(f"unsupported time: {text!r}")

def in_time(dt,spec):
    mode,start,_=spec
    if mode=="month": return (dt.year,dt.month)==(start.year,start.month)
    return dt.date()==start.date()

async def catalog_names(page,base,query):
    url=base.rstrip("/")+"/catalogsearch/result/?q="+quote(query)
    seen=set(); names=[]
    for _ in range(40):
        if url in seen: break
        seen.add(url)
        r=await page.goto(url,wait_until="networkidle",timeout=180000)
        if r is None or r.status!=200: raise RuntimeError("catalog search failed")
        loc=page.locator(".product-item-link")
        for i in range(await loc.count()):
            name=clean(await loc.nth(i).inner_text())
            if name and name not in names: names.append(name)
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=urljoin(base,href)
    return names

async def order_rows(page,base):
    url=base.rstrip("/")+"/sales/order/history/"
    seen=set(); out=[]
    for _ in range(20):
        if url in seen: break
        seen.add(url)
        r=await page.goto(url,wait_until="networkidle",timeout=180000)
        if r is None or r.status!=200: raise RuntimeError("order history failed")
        rows=page.locator("#my-orders-table tbody tr")
        for i in range(await rows.count()):
            row=rows.nth(i); td=row.locator("td")
            if await td.count()<5: continue
            vals=[clean(await td.nth(j).inner_text()) for j in range(await td.count())]
            try: dt=datetime.strptime(vals[1],"%m/%d/%y")
            except ValueError: dt=datetime.strptime(vals[1],"%m/%d/%Y")
            link=row.locator("a.action.view, a[href*='/sales/order/view/']").first
            href=await link.get_attribute("href") if await link.count() else None
            if href: out.append({"order_no":vals[0],"date":dt,"href":href})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=urljoin(base,href)
    return out

async def items(page,order):
    r=await page.goto(order["href"],wait_until="networkidle",timeout=180000)
    if r is None or r.status!=200: raise RuntimeError("order detail failed")
    rows=page.locator(".table-order-items tbody tr, #my-orders-table tbody tr")
    out=[]
    for i in range(await rows.count()):
        row=rows.nth(i)
        name_el=row.locator(".product-item-name").first
        if await name_el.count()==0: continue
        name=clean(await name_el.inner_text())
        subtotal=row.locator("td.col.subtotal .price, .col.subtotal .price").first
        if await subtotal.count():
            amount=money(await subtotal.inner_text())
        else:
            amount=money(await row.inner_text())
        out.append({"name":name,"subtotal":amount})
    return out

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=162: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; category=clean(inst["category"]); time_spec=parse_time(inst["time"])
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); ctx=await b.new_context(extra_http_headers=AUTH_HEADER); page=await ctx.new_page()
        aliases=await catalog_names(page,a.base_url,category)
        orders=await order_rows(page,a.base_url)
        relevant=[o for o in orders if in_time(o["date"],time_spec)]
        matched=[]; total=Decimal("0")
        for order in relevant:
            for item in await items(page,order):
                if any(product_match(alias,item["name"]) for alias in aliases):
                    total+=item["subtotal"]
                    matched.append({"order_no":order["order_no"],"date":order["date"].date().isoformat(),"name":item["name"],"subtotal":str(item["subtotal"])})
        await b.close()
    total=total.quantize(Decimal("0.01"))
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[float(total)],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    evidence={"task_id":a.task_id,"category":category,"catalog_aliases":aliases,"orders_in_period":len(relevant),"matches":matched,"total":str(total)}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
