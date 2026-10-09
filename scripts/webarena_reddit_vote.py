#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH
from webarena_reddit_recent_comments import resolve_forum

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

async def vote_submission(page,sub,direction):
    target="up" if direction>0 else "down"
    button=sub.locator(f'button[data-vote-target="{target}"]').first
    if await button.count()==0:
        button=sub.locator(f'[data-action="vote#{target}"]').first
    if await button.count()==0:
        raise RuntimeError(f"{target} vote control missing")
    async with page.expect_response(lambda r: r.request.method=="POST" and "/sv/" in r.url and r.url.endswith(".json"),timeout=30000) as info:
        await button.click()
    response=await info.value
    await response.finished()
    body=await response.text()
    if response.status!=200:
        raise RuntimeError(f"vote failed {response.status}: {body[:200]}")
    return {"url":response.url,"status":response.status,"body":body}

async def page_submissions(page):
    subs=page.locator(".submission")
    rows=[]
    for i in range(await subs.count()):
        sub=subs.nth(i)
        title_el=sub.locator("a.submission__link").first
        title=clean(await title_el.inner_text()) if await title_el.count() else ""
        user_el=sub.locator("a.submission__submitter").first
        user=clean(await user_el.inner_text()) if await user_el.count() else ""
        forum_el=sub.locator("a.submission__forum").first
        forum=clean(await forum_el.inner_text()) if await forum_el.count() else ""
        rows.append({"node":sub,"title":title,"user":user,"forum":forum})
    return rows

async def vote_ranked(page,base,slug,route,count,direction):
    r=await page.goto(base+route,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"ranking page failed: {route}")
    rows=await page_submissions(page)
    if len(rows)<count: raise RuntimeError(f"ranking page has only {len(rows)} submissions")
    events=[]
    selected=[]
    for row in rows[:count]:
        events.append(await vote_submission(page,row["node"],direction))
        selected.append({k:v for k,v in row.items() if k!="node"})
    return selected,events

async def vote_by_user(page,base,slug,user,direction):
    urls=[f"{base}/user/{user}/submissions",f"{base}/f/{slug}/new"]
    seen_posts=set(); selected=[]; events=[]
    for start in urls:
        url=start; seen_pages=set(); found_here=0
        for _ in range(80):
            if url in seen_pages: break
            seen_pages.add(url)
            r=await page.goto(url,wait_until="networkidle",timeout=120000)
            if r is None or r.status!=200: break
            rows=await page_submissions(page)
            for row in rows:
                if row["user"].casefold()!=user.casefold(): continue
                if row["forum"] and row["forum"].casefold()!=slug.casefold(): continue
                key=(row["title"],row["user"],row["forum"])
                if key in seen_posts: continue
                seen_posts.add(key)
                events.append(await vote_submission(page,row["node"],direction))
                selected.append({k:v for k,v in row.items() if k!="node"})
                found_here+=1
            more=page.get_by_role("link",name=re.compile("^more$",re.I)).first
            if await more.count()==0:
                more=page.locator('a[rel="next"]').first
            if await more.count()==0 or not await more.is_visible(): break
            href=await more.get_attribute("href")
            if not href: break
            url=urljoin(base,href)
        if found_here: break
    if not selected: raise RuntimeError(f"no submissions by {user} in {slug}")
    return selected,events

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    tid=int(task["intent_template_id"]); inst=task["instantiation_dict"]; base=a.base_url.rstrip("/")
    direction=-1 if tid in (24,1510) else 1
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        forum=str(inst.get("forum",""))
        resolved=await resolve_forum(page,base,forum)
        slug=resolved["slug"]
        if tid==22:
            selected,events=await vote_ranked(page,base,slug,f"/f/{slug}/new",1,direction)
        elif tid==24:
            selected,events=await vote_ranked(page,base,slug,f"/f/{slug}/top?t=all",int(inst["k"]),direction)
        elif tid in (25,1510):
            selected,events=await vote_by_user(page,base,slug,str(inst["user"]),direction)
        else:
            raise SystemExit(f"unsupported template {tid}")
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"template":tid,"forum":resolved,"direction":direction,"selected":selected,"events":events}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
