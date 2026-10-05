#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",s).strip()

def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+",text.casefold()) if len(t)>1]

async def page_prices(page,query,match_mode="product"):
    values=[]
    wanted=tokens(query)
    items=page.locator(".product-item")
    for i in range(await items.count()):
        item=items.nth(i)
        name_el=item.locator(".product-item-link").first
        name=clean(await name_el.inner_text()) if await name_el.count() else clean(await item.inner_text())
        hay=name.casefold()
        if match_mode=="product" and wanted and not all(t in hay for t in wanted):
            continue
        nums=[]
        priced=item.locator('[data-price-amount]')
        for j in range(await priced.count()):
            raw=await priced.nth(j).get_attribute("data-price-amount")
            if raw is None: continue
            try: nums.append(float(raw))
            except ValueError: pass
        if not nums:
            prices=item.locator(".price")
            for j in range(await prices.count()):
                txt=clean(await prices.nth(j).inner_text()).replace(",","")
                m=re.search(r"(\d+(?:\.\d+)?)",txt)
                if m: nums.append(float(m.group(1)))
        if nums:
            # Product cards can expose regular + special price; both are visible
            # market prices and therefore part of the observed range.
            values.extend(nums)
    return values

async def collect_all(page,start_url,query,match_mode):
    url=start_url
    seen_urls=set(); values=[]; pages=0
    while url and url not in seen_urls and pages<50:
        seen_urls.add(url); pages+=1
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"search page failed: {url}")
        values.extend(await page_prices(page,query,match_mode))
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible():
            break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    if not values: raise RuntimeError("no product prices observed")
    return values,pages

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    tid=int(task["intent_template_id"])
    if tid==159:
        query=str(task["instantiation_dict"]["product"])
        match_mode="product"
    elif tid==370:
        query=str(task["instantiation_dict"]["brand"])
        match_mode="brand"
    else:
        raise SystemExit("unsupported template")
    start=a.base_url.rstrip("/")+"/catalogsearch/result/?q="+quote(query)
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        page=await b.new_page()
        values,pages=await collect_all(page,start,query,match_mode)
        await b.close()
    mn=min(values); mx=max(values)
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[{"min":mn,"max":mx}],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"query":query,"match_mode":match_mode,"pages_scanned":pages,"price_observations":len(values),"min":mn,"max":mx}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,**evidence},indent=2))

if __name__=="__main__": asyncio.run(main())
