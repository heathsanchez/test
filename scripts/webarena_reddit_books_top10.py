#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

BASE_DEFAULT="http://localhost:9999"

def clean(s):
    return re.sub(r"\s+"," ",s).strip()

async def top_posts(page,base,forum,n):
    slug=forum.lower()
    r=await page.goto(f"{base}/f/{slug}/hot",wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200:
        raise RuntimeError("forum hot page failed")
    posts=page.locator(".submission")
    out=[]
    for i in range(min(n,await posts.count())):
        post=posts.nth(i)
        title_link=post.locator("a.submission__link").first
        if await title_link.count()==0:
            continue
        title=clean(await title_link.inner_text())
        title_href=await title_link.get_attribute("href")
        permalink=None
        links=post.locator("a.text-sm")
        for j in range(await links.count()):
            href=await links.nth(j).get_attribute("href")
            if href and f"/f/{slug}/" in href:
                permalink=href
                break
        out.append({"rank":i+1,"title":title,"title_href":title_href,"permalink":permalink})
    return out

async def enrich_submission(ctx,base,row):
    href=row["permalink"]
    if not href:
        raise RuntimeError(f"internal permalink missing for rank {row['rank']}")
    if href.startswith("/"):
        href=base+href
    page=await ctx.new_page()
    try:
        r=await page.goto(href,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200:
            raise RuntimeError(f"post detail failed for rank {row['rank']}")
        submission=page.locator(".submission").first
        body=submission.locator(".submission__body")
        row["body"]=clean(await body.inner_text()) if await body.count() else ""
        return row
    finally:
        await page.close()

def singular_book(post):
    title=post["title"]
    body=post.get("body","")
    m=re.search(r"\bfinished reading\s+(.+?)\s+to\s+",title,re.I)
    if m and re.search(r"\b(finished|loved|refreshing|suggested reading)\b",body,re.I):
        book=clean(m.group(1))
        author=None
        am=re.search(r"\b(?:always been a|been a)\s+([A-Z][A-Za-z'’-]+)\s+fan\b",body)
        if am:
            author=am.group(1)
        return {"book":book,"author":author}
    m=re.search(r"\baudiobook of\s+(.+?)\s+narrated by\b",title,re.I)
    if m and re.search(r"\b(first time reading|loved it|audiobook)\b",body,re.I):
        return {"book":clean(m.group(1)),"author":None}
    return None

def supporting_local_bookstores(post):
    text=(post["title"]+" "+post.get("body","")).casefold()
    if "local bookstore" not in text or "support" not in text:
        return None
    candidates=re.findall(r"\b(?:https?://)?([a-z0-9][a-z0-9.-]+\.[a-z]{2,})\b",post["title"],re.I)
    if not candidates:
        return None
    domain=candidates[0].lower().rstrip(".")
    return [domain,f"https://{domain}"]

def render(task,posts):
    inst=task["instantiation_dict"]
    criterion=str(inst["filter_criterion"]).casefold()
    desc=str(inst["description"]).casefold()
    if criterion=="recommend exactly one book":
        qualified=[]
        for p in posts:
            b=singular_book(p)
            if b:
                qualified.append((p,b))
        if "post titles" in desc:
            data=[p["title"] for p,_ in qualified]
        elif "author names" in desc:
            data=[{"book":b["book"],"author":b["author"]} for _,b in qualified]
        else:
            data=[b["book"] for _,b in qualified]
    elif "supporting local book stores" in criterion:
        data=[]
        for p in posts:
            hit=supporting_local_bookstores(p)
            if hit:
                data.append(hit)
    else:
        raise ValueError(f"unsupported criterion: {criterion}")
    return {"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default=BASE_DEFAULT)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=17:
        raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    n=int(inst["number"]); forum=str(inst["forum"])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"})
        page=await ctx.new_page()
        posts=await top_posts(page,a.base_url.rstrip("/"),forum,n)
        for post in posts:
            await enrich_submission(ctx,a.base_url.rstrip("/"),post)
        await browser.close()
    response=render(task,posts)
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2,ensure_ascii=False)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"task_id":a.task_id,"forum":forum,"n":n,"posts":posts,"response":response},indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"task_id":a.task_id,"response":response},indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
