#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse, parse_qsl, urlunparse
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+",text.casefold()) if len(t)>1]

def with_sort(url,direction):
    p=urlparse(url)
    q=dict(parse_qsl(p.query,keep_blank_values=True))
    q["product_list_order"]="price"
    q["product_list_dir"]=direction
    return urlunparse((p.scheme,p.netloc,p.path,p.params,urlencode(q),p.fragment))

async def final_price(item):
    selectors=[
        '[data-price-type="finalPrice"] [data-price-amount]',
        '.price-final_price [data-price-amount]',
        '[data-price-amount]',
    ]
    for sel in selectors:
        loc=item.locator(sel)
        if await loc.count():
            raw=await loc.first.get_attribute("data-price-amount")
            try: return float(raw)
            except (TypeError,ValueError): pass
    txt=clean(await item.inner_text()).replace(",","")
    m=re.search(r"\$\s*(\d+(?:\.\d+)?)",txt)
    if not m: raise RuntimeError("price not found")
    return float(m.group(1))

async def first_sorted_price(page,search_url,direction):
    url=with_sort(search_url,direction)
    r=await page.goto(url,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"sorted search failed: {url}")
    item=page.locator(".product-item").first
    if await item.count()==0: raise RuntimeError("no products in sorted search")
    name_el=item.locator(".product-item-link").first
    name=clean(await name_el.inner_text()) if await name_el.count() else clean(await item.inner_text())
    return await final_price(item),{"url":url,"name":name}

def brand_match(name,brand):
    observed=tokens(name); wanted=tokens(brand)
    return bool(wanted) and all(any(o==w or o.startswith(w) or w.startswith(o) for o in observed) for w in wanted)

async def brand_prices(page,search_url,brand):
    url=search_url; seen=set(); values=[]; rows=[]; pages=0
    while url and url not in seen and pages<60:
        seen.add(url); pages+=1
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"search failed: {url}")
        items=page.locator(".product-item")
        for i in range(await items.count()):
            item=items.nth(i)
            link=item.locator(".product-item-link").first
            name=clean(await link.inner_text()) if await link.count() else clean(await item.inner_text())
            if not brand_match(name,brand): continue
            price=await final_price(item)
            values.append(price); rows.append({"name":name,"price":price})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=href
    if not values: raise RuntimeError(f"no brand products matched {brand!r}")
    return values,{"pages":pages,"matched":rows}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    tid=int(task["intent_template_id"]); inst=task["instantiation_dict"]
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        if tid==159:
            query=str(inst["product"])
            search=a.base_url.rstrip("/")+"/catalogsearch/result/?q="+quote(query)
            mn,lo=await first_sorted_price(page,search,"asc")
            mx,hi=await first_sorted_price(page,search,"desc")
            evidence={"mode":"search-sort","query":query,"low":lo,"high":hi,"min":mn,"max":mx}
        elif tid==370:
            brand=str(inst["brand"])
            search=a.base_url.rstrip("/")+"/catalogsearch/result/?q="+quote(brand)
            values,detail=await brand_prices(page,search,brand)
            mn=min(values); mx=max(values)
            evidence={"mode":"brand-membership","brand":brand,**detail,"min":mn,"max":mx}
        else:
            raise SystemExit("unsupported template")
        await b.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[{"min":mn,"max":mx}],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"task_id":a.task_id,**evidence},indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
