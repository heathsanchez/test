#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_shopping_order_history_probe import AUTH_HEADER, clean

def money(s):
    m=re.search(r"\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",clean(s))
    if not m: raise ValueError(f"no money in {s!r}")
    return Decimal(m.group(1).replace(",",""))

async def orders(page,base):
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
            out.append({"order_no":vals[0],"date":dt,"total":money(vals[2]),"status":vals[3]})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    out.sort(key=lambda x:x["date"],reverse=True)
    return out

def status_norm(s):
    x=clean(s).casefold()
    if x in {"canceled","cancelled"}: return "canceled"
    if x=="complete": return "complete"
    if x=="pending": return "pending"
    return x

def task_response(task,rows):
    tid=int(task["intent_template_id"])
    if tid==193:
        latest=rows[0]
        return {"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[{"status":status_norm(latest["status"]),"arrival_date":None}],"error_details":None}

    if tid==197:
        # Intent fixes "Today is June 12, 2023" and asks for the past year.
        start=datetime(2022,6,12); end=datetime(2023,6,12,23,59,59)
        chosen=[r for r in rows if start<=r["date"]<=end and status_norm(r["status"])=="complete"]
        amount=sum((r["total"] for r in chosen),Decimal("0")).quantize(Decimal("0.01"))
        return {"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[{"order_count":len(chosen),"amount":float(amount)}],"error_details":None}

    if tid in {213,214}:
        raw=str(task["instantiation_dict"]["status"]).casefold()
        if "processing" in raw: wanted="processing"
        elif "under delivery" in raw: wanted="under delivery"
        elif "complete" in raw: wanted="complete"
        elif "cancel" in raw: wanted="canceled"
        elif "pending" in raw: wanted="pending"
        else: wanted=clean(raw)
        matches=[r for r in rows if status_norm(r["status"])==wanted]
        if not matches:
            return {"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
        latest=matches[0]
        if tid==213:
            data=[latest["order_no"]]
        else:
            data=[float(latest["total"])]
        return {"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}
    raise ValueError(f"unsupported template {tid}")

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH_HEADER)
        page=await ctx.new_page()
        rows=await orders(page,a.base_url)
        await b.close()
    response=task_response(task,rows)
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"orders_seen":len(rows),"latest":{**rows[0],"date":rows[0]["date"].date().isoformat(),"total":str(rows[0]["total"])},"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,default=str)+"\n")
    print(json.dumps(evidence,indent=2,default=str))

if __name__=="__main__": asyncio.run(main())
