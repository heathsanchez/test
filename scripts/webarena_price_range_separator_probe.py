#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
import webarena_shopping_price_range_v2 as base

def stem(w):
    w=re.sub(r"[^a-z0-9]","",w.casefold())
    if w.endswith("ies") and len(w)>5: return w[:-3]+"y"
    if w.endswith("ing") and len(w)>6: return w[:-3]
    if w.endswith("s") and len(w)>4 and not w.endswith("ss"): return w[:-1]
    return w

def coverage(query,name):
    q=[stem(x) for x in re.findall(r"[a-z0-9]+",query.casefold())]
    n=[stem(x) for x in re.findall(r"[a-z0-9]+",name.casefold())]
    hits=sum(1 for w in q if w in n)
    return hits,len(q)

async def collect(page,base_url,query):
    url=base_url.rstrip("/")+"/catalogsearch/result/?q="+quote(query)
    seen=set(); rows=[]
    for _ in range(100):
        if url in seen: break
        seen.add(url)
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError("search failed")
        items=page.locator(".product-item")
        for i in range(await items.count()):
            item=items.nth(i)
            link=item.locator(".product-item-link").first
            name=base.clean(await link.inner_text()) if await link.count() else base.clean(await item.inner_text())
            price=await base.final_price(item)
            h,total=coverage(query,name)
            rows.append({"name":name,"price":price,"hits":h,"total":total})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    return rows

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--task-file",required=True); ap.add_argument("--output",required=True); ap.add_argument("--base-url",default="http://localhost:7770"); a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    out={}
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        for tid in (124,125):
            task=next(t for t in tasks if int(t["task_id"])==tid)
            query=str(task["instantiation_dict"]["product"])
            rows=await collect(page,a.base_url,query)
            total=max((r["total"] for r in rows),default=0)
            bands={}
            for k in range(1,total+1):
                subset=[r for r in rows if r["hits"]>=k]
                if subset:
                    bands[str(k)]={"count":len(subset),"min":min(r["price"] for r in subset),"max":max(r["price"] for r in subset),
                      "min_items":[r for r in subset if r["price"]==min(x["price"] for x in subset)][:5],
                      "max_items":[r for r in subset if r["price"]==max(x["price"] for x in subset)][:5]}
            out[str(tid)]={"query":query,"rows":len(rows),"bands":bands}
        await b.close()
    Path(a.output).write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=="__main__": asyncio.run(main())
