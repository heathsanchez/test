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

def predicate(description):
    raw=clean(description)
    text=raw.casefold()
    max_stars=None
    m=re.search(r"\s+with\s+a\s+rating\s+of\s*(\d+(?:\.\d+)?)\s*or\s+less\s+stars\s*$",text)
    if m:
        max_stars=float(m.group(1))
        text=text[:m.start()].strip()

    explicit=False
    if re.search(r"\bexplicitly\b",text):
        explicit=True
        text=re.sub(r"\bexplicitly\b"," ",text)
        text=clean(text)

    # Relational language like "ear cups being small" or "price being unfair"
    # protects local semantic association, not global bag-of-words co-occurrence.
    m=re.fullmatch(r"(.+?)\s+being\s+(.+)",text)
    if m:
        left=[t for t in re.findall(r"[a-z0-9]+",m.group(1)) if len(t)>2]
        right=[t for t in re.findall(r"[a-z0-9]+",m.group(2)) if len(t)>2]
        return {"mode":"proximity","left":left,"right":right,"window":100},max_stars

    # "complain of X" protects the complained-about topic X; the verb itself
    # need not appear literally in natural review prose.
    text=re.sub(r"^complain\s+of\s+(?:the\s+)?","",text)

    stop={"with","the","for","product","on","current","page","mention","mentions","who","name","names","get","good","a","an","of"}
    tokens=[t for t in re.findall(r"[a-z0-9]+",text) if len(t)>2 and t not in stop]
    if explicit:
        return {"mode":"phrase","phrase":" ".join(tokens)},max_stars
    return {"mode":"all_tokens","tokens":tokens},max_stars

async def activate_reviews(page):
    tab=page.locator("#tab-label-reviews-title")
    if await tab.count():
        await tab.click()
    for _ in range(120):
        if await page.locator(".review-item").count()>0: return
        rc=page.locator(".reviews-actions [itemprop='reviewCount']")
        if await rc.count() and clean(await rc.inner_text())=="0": return
        await page.wait_for_timeout(100)

async def collect(page):
    out=[]; seen=set()
    for _ in range(30):
        items=page.locator(".review-item")
        for i in range(await items.count()):
            item=items.nth(i)
            author=item.locator('.review-author [itemprop="author"]').first
            content=item.locator(".review-content").first
            title=item.locator(".review-title").first
            rating=item.locator(".rating-result").first
            if await author.count()==0 or await content.count()==0: continue
            name=clean(await author.inner_text())
            text=clean(((await title.inner_text())+" " if await title.count() else "")+await content.inner_text())
            raw=(await rating.get_attribute("title") if await rating.count() else None) or (clean(await rating.inner_text()) if await rating.count() else "")
            stars=rating_stars(raw) if raw else None
            key=(name,text,stars)
            if key not in seen:
                seen.add(key); out.append({"author":name,"text":text,"stars":stars})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        before=page.url
        await nxt.click()
        await page.wait_for_load_state("networkidle",timeout=120000)
        if page.url==before: break
    return out

def matches(review,rule,max_stars):
    text=review["text"].casefold()
    if max_stars is not None and (review["stars"] is None or review["stars"]>max_stars):
        return False
    mode=rule["mode"]
    if mode=="phrase":
        return rule["phrase"] in text
    if mode=="all_tokens":
        return all(tok in text for tok in rule["tokens"])
    if mode=="proximity":
        left_positions=[]
        right_positions=[]
        for tok in rule["left"]:
            left_positions.extend(m.start() for m in re.finditer(re.escape(tok),text))
        for tok in rule["right"]:
            right_positions.extend(m.start() for m in re.finditer(re.escape(tok),text))
        if not left_positions or not right_positions:
            return False
        return min(abs(a-b) for a in left_positions for b in right_positions)<=rule["window"]
    raise ValueError(rule)

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:7770"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    desc=str(task["instantiation_dict"]["description"])
    rule,max_stars=predicate(desc)
    start=str(task["start_urls"][0]).replace("__SHOPPING__",a.base_url.rstrip("/"))
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        r=await page.goto(start,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError("product page failed")
        await activate_reviews(page)
        reviews=await collect(page)
        await b.close()
    names=[]
    for rev in reviews:
        if matches(rev,rule,max_stars) and rev["author"] not in names: names.append(rev["author"])
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":names,"error_details":None} if names else {"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"description":desc,"rule":rule,"max_stars":max_stars,"reviews":reviews,"response":response},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"rule":rule,"max_stars":max_stars,"review_count":len(reviews),"response":response},indent=2))
if __name__=="__main__": asyncio.run(main())
