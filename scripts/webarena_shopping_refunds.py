#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, calendar, json, re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_shopping_order_history_probe import AUTH_HEADER, clean

def money(s):
    m=re.search(r"-?\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",clean(s))
    if not m: raise ValueError(f"no money in {s!r}")
    return Decimal(m.group(1).replace(",",""))

def month_num(token):
    t=token.lower()
    for i in range(1,13):
        if t in {calendar.month_name[i].lower(),calendar.month_abbr[i].lower()}: return i
    raise ValueError(token)

def period(text):
    s=clean(text)
    m=re.fullmatch(r"(\d{4})",s)
    if m:
        y=int(m.group(1)); return (y,1),(y,12)
    m=re.fullmatch(r"([A-Za-z]+)\s+(\d{4})",s)
    if m:
        mon,y=m.groups(); y=int(y); mm=month_num(mon); return (y,mm),(y,mm)
    raise ValueError(f"unsupported period: {text!r}")

def within(dt,b): return b[0] <= (dt.year,dt.month) <= b[1]

async def collect_orders(page,base):
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
            if href:
                out.append({"order_no":vals[0],"date":dt,"total":money(vals[2]),"status":vals[3],"href":href})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    return out

async def adjustment(page,order,conditions):
    low=conditions.casefold(); subtract=Decimal("0")
    evidence={"shipping":Decimal("0"),"kept_items":[]}
    r=await page.goto(order["href"],wait_until="networkidle",timeout=180000)
    if r is None or r.status!=200: raise RuntimeError("order detail failed")
    body=clean(await page.locator("body").inner_text())
    if "cannot get the shipping fee back" in low:
        m=re.search(r"Shipping\s*&\s*Handling\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",body,re.I)
        if not m: raise RuntimeError("shipping amount missing")
        shipping=Decimal(m.group(1).replace(",",""))
        subtract+=shipping; evidence["shipping"]=shipping

    kept_match=re.search(r"only kept the\s+(.+?)\s+and the shop",conditions,re.I)
    if kept_match:
        wanted=clean(kept_match.group(1)).casefold()
        rows=page.locator(".table-order-items tbody tr, #my-orders-table tbody tr")
        found=False
        for i in range(await rows.count()):
            row=rows.nth(i)
            name_el=row.locator(".product-item-name").first
            if await name_el.count()==0: continue
            name=clean(await name_el.inner_text())
            if wanted not in name.casefold(): continue
            vals=re.findall(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)",clean(await row.inner_text()))
            if not vals: raise RuntimeError(f"kept item amount unavailable: {name}")
            amount=Decimal(vals[-1].replace(",",""))
            subtract+=amount; evidence["kept_items"].append({"name":name,"amount":amount}); found=True
        if not found: raise RuntimeError(f"kept item not found: {wanted}")
    return subtract,evidence

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    inst=task["instantiation_dict"]; bounds=period(inst["time"]); conditions=str(inst.get("conditions",""))
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH_HEADER); page=await ctx.new_page()
        orders=await collect_orders(page,a.base_url)
        canceled=[o for o in orders if within(o["date"],bounds) and o["status"].casefold() in {"canceled","cancelled"}]
        refund=sum((o["total"] for o in canceled),Decimal("0")); adjustments=[]
        for o in canceled:
            sub,ev=await adjustment(page,o,conditions); refund-=sub
            adjustments.append({"order_no":o["order_no"],"subtract":sub,**ev})
        await b.close()
    refund=refund.quantize(Decimal("0.01"))
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[float(refund)],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    ev={"task_id":a.task_id,"canceled_orders":[{"order_no":o["order_no"],"date":o["date"].date().isoformat(),"total":str(o["total"])} for o in canceled],"adjustments":adjustments,"refund":str(refund)}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(ev,indent=2,default=str)+"\n")
    print(json.dumps(ev,indent=2,default=str))
if __name__=="__main__": asyncio.run(main())
