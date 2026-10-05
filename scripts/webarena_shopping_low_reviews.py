#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",s).strip()

def rating_stars(text):
    t=clean(text)
    m=re.search(r"(\d+(?:\.\d+)?)\s*%",t)
    if m: return float(m.group(1))/20.0
    m=re.search(r"(\d+(?:\.\d+)?)\s*(?:out of\s*)?5",t,re.I)
    if m: return float(m.group(1))
    return None

async def collect_page(page):
    items=page.locator(".review-item")
    out=[]
    for i in range(await items.count()):
        item=items.nth(i)
        title_el=item.locator(".review-title").first
        rating_el=item.locator(".rating-result").first
        if await title_el.count()==0 or await rating_el.count()==0: continue
        title=clean(await title_el.inner_text())
        raw=await rating_el.get_attribute("title") or clean(await rating_el.inner_text())
        stars=rating_stars(raw)
        if title and stars is not None:
            out.append({"title":title,"stars":stars})
    return out

async def collect_reviews(page):
    out=[]; seen=set()
    for _ in range(20):
        rows=await collect_page(page)
        for r in rows:
            key=(r["title"],r["stars"])
            if key not in seen: seen.add(key); out.append(r)
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        before=page.url
        await nxt.click()
        await page.wait_for_load_state("networkidle",timeout=120000)
        if page.url==before: break
    return out

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=136: raise SystemExit("unsupported template")
    start=str(task["start_urls"][0]).replace("__SHOPPING__",a.base_url.rstrip("/"))
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        r=await page.goto(start,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError("product page failed")
        reviews=await collect_reviews(page)
        await browser.close()
    titles=[r["title"] for r in reviews if r["stars"]<=2.0]
    if titles:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":titles,"error_details":None}
    else:
        response={"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"start_url":start,"reviews":reviews,"response":response},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"review_count":len(reviews),"response":response},indent=2))
if __name__=="__main__": asyncio.run(main())
