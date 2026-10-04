#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

CUSTOMERS="/customer/index/"

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

def digits(s):
    d="".join(ch for ch in s if ch.isdigit())
    if len(d)==11 and d.startswith("1"):
        d=d[1:]
    return d

async def live_table(page):
    for _ in range(120):
        tables=page.locator("table:visible")
        for i in range(await tables.count()):
            table=tables.nth(i)
            th=table.locator("thead th")
            headers=[clean(await th.nth(j).inner_text()) for j in range(await th.count())]
            lower=[h.lower() for h in headers]
            rows=await table.locator("tbody tr").count()
            if {"name","email","phone"}.issubset(set(lower)) and rows>1:
                return table,headers
        await page.wait_for_timeout(100)
    raise RuntimeError("live customer grid not found after render wait")

async def scan_all(page):
    table,headers=await live_table(page)
    lower=[h.lower() for h in headers]
    ix={k:lower.index(k) for k in ["name","email","phone"]}
    out=[]; seen=set()
    rows=table.locator("tbody tr")
    for ri in range(await rows.count()):
        cells=rows.nth(ri).locator("td")
        if await cells.count()<=max(ix.values()):
            continue
        email=clean(await cells.nth(ix["email"]).inner_text())
        if not email or email in seen:
            continue
        seen.add(email)
        out.append({
            "name":clean(await cells.nth(ix["name"]).inner_text()),
            "email":email,
            "phone":clean(await cells.nth(ix["phone"]).inner_text()),
        })
    return out

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7780/admin")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    target=digits(task["instantiation_dict"]["PhoneNum"])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-M2-Admin-Auto-Login":"admin:admin1234"})
        page=await ctx.new_page()
        resp=await page.goto(a.base_url.rstrip("/")+CUSTOMERS,wait_until="networkidle",timeout=120000)
        if resp is None or resp.status!=200: raise RuntimeError("customer grid navigation failed")
        rows=await scan_all(page)
        await browser.close()
    matches=[{"name":r["name"],"email":r["email"]} for r in rows if digits(r["phone"])==target]
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":matches,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"target_phone_digits":target,"rows_scanned":len(rows),"match_count":len(matches),"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
