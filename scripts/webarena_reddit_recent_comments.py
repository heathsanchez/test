#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",s).strip()
def norm(s): return re.sub(r"[^a-z0-9]+","",s.casefold())
def sim(a,b): return SequenceMatcher(None,norm(a),norm(b)).ratio()
def parse_score(s):
    m=re.search(r"-?\d+",clean(s).replace(",",""))
    return int(m.group()) if m else None

async def resolve_forum(page,base,wanted):
    best=(0.0,None)
    for n in range(1,6):
        r=await page.goto(f"{base}/forums/by_name/{n}",wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: continue
        links=page.locator('a[href^="/f/"]')
        for i in range(await links.count()):
            a=links.nth(i); txt=clean(await a.inner_text()); href=await a.get_attribute("href")
            if not txt or not href: continue
            sc=sim(wanted,txt)
            if sc>best[0]: best=(sc,(txt,href.split("/f/",1)[1].split("/",1)[0]))
    if best[0]<0.72:
        await page.goto(f"{base}/search?q={quote(wanted)}",wait_until="networkidle",timeout=120000)
        links=page.locator('a.submission__forum[href^="/f/"]')
        for i in range(await links.count()):
            a=links.nth(i); txt=clean(await a.inner_text()); href=await a.get_attribute("href")
            if not href: continue
            sc=sim(wanted,txt)
            if sc>best[0]: best=(sc,(txt,href.split("/f/",1)[1].split("/",1)[0]))
    if best[1] is None: raise RuntimeError("forum not found")
    return {"display":best[1][0],"slug":best[1][1],"score":best[0]}

async def newest(page,base,slug):
    r=await page.goto(f"{base}/f/{slug}/new",wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("new page failed")
    post=page.locator(".submission").first
    title=clean(await post.locator("a.submission__link").first.inner_text())
    user=clean(await post.locator("a.submission__submitter").first.inner_text())
    permalink=None
    links=post.locator("a.text-sm")
    for i in range(await links.count()):
        href=await links.nth(i).get_attribute("href")
        if href and f"/f/{slug}/" in href: permalink=href; break
    if not permalink: raise RuntimeError("permalink missing")
    return {"username":user,"title":title,"permalink":permalink}

async def count_bad(ctx,base,post):
    href=post["permalink"]
    if href.startswith("/"): href=base+href
    page=await ctx.new_page()
    try:
        r=await page.goto(href,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError("detail failed")
        comments=page.locator(".comment"); count=0
        for i in range(await comments.count()):
            c=comments.nth(i)
            u=c.locator('a[href^="/user/"]').first
            score=c.locator(".vote__net-score").first
            if await u.count()==0 or await score.count()==0: continue
            who=clean(await u.inner_text()); n=parse_score(await score.inner_text())
            if n is not None and n<0 and who.casefold()!=post["username"].casefold(): count+=1
        return count
    finally:
        await page.close()

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    forum=str(task["instantiation_dict"]["forum"]); base=a.base_url.rstrip("/")
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"})
        page=await ctx.new_page(); resolved=await resolve_forum(page,base,forum); post=await newest(page,base,resolved["slug"])
        count=await count_bad(ctx,base,post); await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[{"username":post["username"],"post_title":post["title"],"count":count}],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"forum":resolved,"post":post,"count":count},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"response":response},indent=2))
if __name__=="__main__": asyncio.run(main())
