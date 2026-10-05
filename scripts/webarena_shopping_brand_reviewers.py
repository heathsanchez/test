#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

def rating_stars(text):
    t=clean(text)
    m=re.search(r"(\d+(?:\.\d+)?)\s*%",t)
    if m: return float(m.group(1))/20.0
    m=re.search(r"(\d+(?:\.\d+)?)\s*(?:out of\s*)?5",t,re.I)
    return float(m.group(1)) if m else None

def parse_intent(task):
    intent=clean(task["intent"])
    m=re.search(r"Who gave\s+(.+?)\s+for\s+(.+?)\s+from\s+(.+?)$",intent,re.I)
    if not m: raise ValueError(f"unsupported intent: {intent}")
    stars_text,category,brand=m.groups()
    allowed={int(x) for x in re.findall(r"\b([1-5])\b",stars_text)}
    if not allowed: raise ValueError(stars_text)
    return clean(category),clean(brand),allowed

async def search_products(page,base,category,brand):
    query=brand
    url=base.rstrip("/")+"/catalogsearch/result/?q="+quote(query)
    seen=set(); all_rows=[]
    for _ in range(30):
        if url in seen: break
        seen.add(url)
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"search failed: {url}")
        items=page.locator(".product-item")
        for i in range(await items.count()):
            item=items.nth(i)
            link=item.locator(".product-item-link").first
            if await link.count()==0: continue
            name=clean(await link.inner_text()); href=await link.get_attribute("href")
            if href:
                all_rows.append({"name":name,"href":urljoin(base,href)})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=urljoin(base,href)
    brand_tok=brand.casefold()
    cat_tokens=[t for t in re.findall(r"[a-z0-9]+",category.casefold()) if len(t)>2]
    strict=[r for r in all_rows if brand_tok in r["name"].casefold() and all((t in r["name"].casefold()) or (t.rstrip("s") in r["name"].casefold()) for t in cat_tokens)]
    if strict: return strict,all_rows
    brand_rows=[r for r in all_rows if brand_tok in r["name"].casefold()]
    if brand_rows: return brand_rows,all_rows
    return all_rows,all_rows

async def collect_reviews(page,href):
    r=await page.goto(href,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: return []
    tab=page.locator("#tab-label-reviews-title")
    if await tab.count():
        await tab.click()
        for _ in range(100):
            if await page.locator(".review-item").count()>0: break
            rc=page.locator(".reviews-actions [itemprop='reviewCount']")
            if await rc.count() and clean(await rc.inner_text())=="0": return []
            await page.wait_for_timeout(100)
    out=[]; seen=set()
    for _ in range(30):
        items=page.locator(".review-item")
        for i in range(await items.count()):
            item=items.nth(i)
            author=item.locator('.review-author [itemprop="author"]').first
            rating=item.locator(".rating-result").first
            if await author.count()==0 or await rating.count()==0: continue
            name=clean(await author.inner_text())
            raw=(await rating.get_attribute("title")) or clean(await rating.inner_text())
            stars=rating_stars(raw)
            key=(name,stars)
            if name and stars is not None and key not in seen:
                seen.add(key); out.append({"author":name,"stars":stars})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href2=await nxt.get_attribute("href")
        if not href2: break
        before=page.url
        await nxt.click(); await page.wait_for_load_state("networkidle",timeout=120000)
        if page.url==before: break
    return out

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=1356: raise SystemExit("unsupported template")
    category,brand,allowed=parse_intent(task)
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        products,observed=await search_products(page,a.base_url,category,brand)
        reviews=[]
        for product in products:
            for rev in await collect_reviews(page,product["href"]):
                reviews.append({**rev,"product":product["name"]})
        await b.close()
    names=[]
    for rev in reviews:
        if int(round(rev["stars"])) in allowed and rev["author"] not in names:
            names.append(rev["author"])
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":names,"error_details":None} if names else {"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"category":category,"brand":brand,"allowed_stars":sorted(allowed),"search_results":observed,"selected_products":products,"reviews":reviews,"response":response}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"products":len(products),"reviews":len(reviews),"response":response},indent=2))

if __name__=="__main__":
    asyncio.run(main())
