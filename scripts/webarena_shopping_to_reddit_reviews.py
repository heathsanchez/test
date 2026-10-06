#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
from playwright.async_api import async_playwright

SHOPPING="http://localhost:7770"
REDDIT="http://localhost:9999"
REDDIT_AUTH={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"}

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()
def norm(s): return re.sub(r"[^a-z0-9]+"," ",clean(s).casefold()).strip()

def words(s):
    stop={"the","a","an","related","discussion","forum","forums"}
    out=[]
    for w in re.findall(r"[a-z0-9]+",norm(s)):
        if w in stop: continue
        if w.endswith("ing") and len(w)>5: w=w[:-3]
        elif w.endswith("s") and len(w)>4: w=w[:-1]
        out.append(w)
    return out

def product_match(wanted,observed):
    wt=words(wanted); ot=words(observed)
    if norm(wanted)==norm(observed): return 1000
    score=0
    for w in wt:
        if any(w==o or w in o or o in w for o in ot): score+=1
    return score

def rating_stars(text):
    t=clean(text)
    m=re.search(r"(\d+(?:\.\d+)?)\s*%",t)
    if m: return float(m.group(1))/20.0
    m=re.search(r"(\d+(?:\.\d+)?)\s*(?:out of\s*)?5",t,re.I)
    return float(m.group(1)) if m else None

def rating_predicate(spec):
    s=clean(spec).casefold()
    m=re.fullmatch(r"(\d+)\s*stars?\s+and\s+less",s)
    if m:
        n=float(m.group(1)); return lambda x:x is not None and x<=n
    m=re.fullmatch(r"(\d+)\s*stars?",s)
    if m:
        n=float(m.group(1)); return lambda x:x is not None and x==n
    raise ValueError(f"unsupported rating spec: {spec}")

async def find_product(page,product):
    url=SHOPPING+"/catalogsearch/result/?q="+quote(product)
    seen=set(); candidates=[]
    for _ in range(20):
        if url in seen: break
        seen.add(url)
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"shopping search failed: {url}")
        links=page.locator(".product-item-link")
        for i in range(await links.count()):
            link=links.nth(i)
            name=clean(await link.inner_text()); href=await link.get_attribute("href")
            if href: candidates.append((product_match(product,name),name,urljoin(SHOPPING,href)))
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href=await nxt.get_attribute("href")
        if not href: break
        url=urljoin(SHOPPING,href)
    if not candidates: raise RuntimeError("no product search candidates")
    candidates.sort(key=lambda x:x[0],reverse=True)
    best=candidates[0]
    if best[0] < max(1,len(words(product))-1):
        raise RuntimeError(f"no sufficiently matching product: {best}")
    return {"name":best[1],"href":best[2],"score":best[0]}

async def collect_reviews(page,href):
    r=await page.goto(href,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"product page failed: {href}")
    tab=page.locator("#tab-label-reviews-title")
    if await tab.count():
        await tab.click()
        for _ in range(120):
            if await page.locator(".review-item").count()>0: break
            rc=page.locator(".reviews-actions [itemprop='reviewCount']")
            if await rc.count() and clean(await rc.inner_text())=="0": return []
            await page.wait_for_timeout(100)
    out=[]
    for _ in range(40):
        items=page.locator(".review-item")
        for i in range(await items.count()):
            item=items.nth(i)
            title_el=item.locator(".review-title").first
            rating_el=item.locator(".rating-result").first
            if await title_el.count()==0 or await rating_el.count()==0: continue
            title=clean(await title_el.inner_text())
            raw=(await rating_el.get_attribute("title")) or clean(await rating_el.inner_text())
            stars=rating_stars(raw)
            if title and stars is not None: out.append({"title":title,"stars":stars})
        nxt=page.locator(".pages-item-next a").first
        if await nxt.count()==0 or not await nxt.is_visible(): break
        href2=await nxt.get_attribute("href")
        if not href2: break
        before=page.url
        await nxt.click(); await page.wait_for_load_state("networkidle",timeout=120000)
        if page.url==before: break
    return out

def forum_score(description,label,slug):
    q=words(description); t=words(label+" "+slug)
    return sum(2 if a==b else 1 for a in q for b in t if a==b or a in b or b in a)

async def choose_forum(page,description):
    r=await page.goto(REDDIT,wait_until="networkidle",timeout=120000)
    if r is None or r.status not in (200,302): raise RuntimeError("reddit home failed")
    links=page.locator('a[href^="/f/"]')
    rows=[]; seen=set()
    for i in range(await links.count()):
        href=await links.nth(i).get_attribute("href")
        if not href: continue
        parts=[p for p in urlparse(href).path.split("/") if p]
        if len(parts)<2 or parts[0]!="f": continue
        slug=parts[1]
        if slug in seen: continue
        seen.add(slug)
        label=clean(await links.nth(i).inner_text())
        rows.append((forum_score(description,label,slug),label,slug))
    if not rows: raise RuntimeError("no discussion forums discovered")
    rows.sort(key=lambda x:x[0],reverse=True)
    if rows[0][0]<=0: raise RuntimeError(f"no relevant forum: {rows[:10]}")
    return {"score":rows[0][0],"label":rows[0][1],"slug":rows[0][2],"candidates":rows[:10]}

async def submit(page,forum,title,body):
    url=REDDIT+"/submit/"+forum["slug"]
    r=await page.goto(url,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"submit page failed: {url}")
    form=page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count()==0: raise RuntimeError("submission form missing")
    await form.locator('[name="submission[title]"]').first.fill(title)
    await form.locator('[name="submission[body]"]').first.fill(body)
    forum_value=await form.locator('[name="submission[forum]"]').first.input_value()
    btn=form.get_by_role("button",name="Create submission").first
    if await btn.count()==0: raise RuntimeError("submit control missing")
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"submit_url":url,"forum_value":forum_value,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=101: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; product=clean(inst["product"]); pred=rating_predicate(inst["rating"])
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        shop=await browser.new_page()
        product_row=await find_product(shop,product)
        reviews=await collect_reviews(shop,product_row["href"])
        selected=[r for r in reviews if pred(r["stars"])]
        if not selected: raise RuntimeError("no qualifying reviews")
        title=f"real user feedback on {product}"
        body="\n".join(f'- "{r["title"]}"' for r in selected)
        reddit_ctx=await browser.new_context(extra_http_headers=REDDIT_AUTH,record_har_path=str(har),record_har_mode="full")
        reddit=await reddit_ctx.new_page()
        forum=await choose_forum(reddit,"game related discussion forum")
        post=await submit(reddit,forum,title,body)
        await reddit_ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    ev={"task_id":a.task_id,"product":product,"resolved_product":product_row,"reviews":reviews,"selected":selected,"forum":forum,"title":title,"body":body,**post}
    (out/"capability_evidence.json").write_text(json.dumps(ev,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"task_id":a.task_id,"selected_count":len(selected),"forum":forum,"post":post},indent=2,ensure_ascii=False))

if __name__=="__main__": asyncio.run(main())
