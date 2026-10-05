#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, calendar, json, re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

BASE="http://localhost:7770"
AUTH_HEADER={"X-M2-Customer-Auto-Login":"emma.lopez@gmail.com:Password.123"}

def clean(s): return re.sub(r"\s+"," ",s).strip()
def norm(s): return re.sub(r"[^a-z0-9]+","",s.casefold())

def parse_period(text):
    s=clean(text)
    m=re.fullmatch(r"in\s+(\d{4})",s,re.I)
    if m:
        y=int(m.group(1)); return (y,1),(y,12)
    m=re.fullmatch(r"([A-Za-z]+)\s+(\d{4})",s,re.I)
    if m:
        mon,y=m.groups(); y=int(y); token=mon.lower()
        mm=next(i for i in range(1,13) if token in {calendar.month_name[i].lower(),calendar.month_abbr[i].lower()})
        return (y,mm),(y,mm)
    raise ValueError(f"unsupported period {text!r}")

def in_period(dt,bounds):
    return bounds[0] <= (dt.year,dt.month) <= bounds[1]

def product_match(wanted,observed):
    w=norm(wanted.replace("artifical","artificial"))
    o=norm(observed.replace("artifical","artificial"))
    return w in o or o in w

def dims(text):
    m=re.search(r"(\d+(?:\.\d+)?)\s*[*x×]\s*(\d+(?:\.\d+)?)",text,re.I)
    if not m: return None
    return {"width":m.group(1)+" inch","height":m.group(2)+" inch"}

async def history(page,base):
    url=base+"/sales/order/history/"
    seen=set(); out=[]
    for _ in range(20):
        if url in seen: break
        seen.add(url)
        r=await page.goto(url,wait_until="networkidle",timeout=180000)
        if r is None or r.status!=200: raise RuntimeError("order history failed")
        rows=page.locator("#my-orders-table tbody tr")
        for i in range(await rows.count()):
            row=rows.nth(i); cells=row.locator("td")
            vals=[clean(await cells.nth(j).inner_text()) for j in range(await cells.count())]
            if len(vals)<4: continue
            try: dt=datetime.strptime(vals[1],"%m/%d/%y")
            except ValueError:
                try: dt=datetime.strptime(vals[1],"%m/%d/%Y")
                except ValueError: continue
            view=row.get_by_role("link",name=re.compile("^View Order$",re.I))
            href=await view.first.get_attribute("href") if await view.count() else None
            if href: out.append({"order_no":vals[0],"date":dt,"href":href})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    if not out: raise RuntimeError("no orders found")
    return out

async def order_items(page,href):
    r=await page.goto(href,wait_until="networkidle",timeout=180000)
    if r is None or r.status!=200: raise RuntimeError(f"order detail failed: {href}")
    rows=page.locator(".table-order-items tbody tr, #my-orders-table tbody tr")
    out=[]
    for i in range(await rows.count()):
        row=rows.nth(i)
        name_el=row.locator(".product-item-name").first
        if await name_el.count()==0: continue
        name=clean(await name_el.inner_text())
        opts={}
        dl=row.locator("dl.item-options").first
        if await dl.count():
            dts=dl.locator("dt"); dds=dl.locator("dd")
            for j in range(min(await dts.count(),await dds.count())):
                opts[clean(await dts.nth(j).inner_text()).casefold()]=clean(await dds.nth(j).inner_text())
        out.append({"name":name,"options":opts,"text":clean(await row.inner_text())})
    return out

def response_data(option,matches):
    vals=[]
    for m in matches:
        if option.casefold()=="size":
            raw=m["options"].get("size") or m["options"].get("color") or m["text"]
            v=dims(raw)
        else:
            v=m["options"].get(option.casefold())
            if v is None:
                for candidate in m["options"].values():
                    if candidate: v=candidate; break
        if v is not None and v not in vals: vals.append(v)
    return vals

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int)
    ap.add_argument("--task-file")
    ap.add_argument("--output-dir")
    ap.add_argument("--base-url",default=BASE)
    args=ap.parse_args()
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH_HEADER)
        page=await ctx.new_page()
        if args.task_id is None:
            r=await page.goto(args.base_url.rstrip("/")+"/sales/order/history/",wait_until="networkidle",timeout=180000)
            print(json.dumps({"status":r.status if r else None,"url":page.url,"title":await page.title(),"body":(await page.locator("body").inner_text())[:30000]},indent=2))
            await browser.close(); return
        tasks=json.loads(Path(args.task_file).read_text())
        task=next(t for t in tasks if int(t["task_id"])==args.task_id)
        inst=task["instantiation_dict"]; bounds=parse_period(inst["time"])
        orders=await history(page,args.base_url.rstrip("/"))
        relevant=[o for o in orders if in_period(o["date"],bounds)]
        matches=[]
        for o in relevant:
            for item in await order_items(page,o["href"]):
                if product_match(inst["product"],item["name"]):
                    matches.append({"order_no":o["order_no"],"date":o["date"].date().isoformat(),**item})
        data=response_data(inst["option"],matches)
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None} if data else {"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
        out=Path(args.output_dir)/str(args.task_id); out.mkdir(parents=True,exist_ok=True)
        (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
        (out/"capability_evidence.json").write_text(json.dumps({"matches":matches,"response":response},indent=2)+"\n")
        print(json.dumps({"task_id":args.task_id,"matches":matches,"response":response},indent=2))
        await browser.close()

if __name__=="__main__": asyncio.run(main())
