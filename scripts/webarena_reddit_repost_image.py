#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH, clean, forum_slug

def norm(s): return re.sub(r"[^a-z0-9]+","",str(s).casefold())
def sim(a,b): return SequenceMatcher(None,norm(a),norm(b)).ratio()

async def find_source(page,base,needle):
    urls=[f"{base}/f/pics",f"{base}/search?q={quote(needle)}"]
    best=None
    for url in urls:
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: continue
        posts=page.locator(".submission")
        for i in range(await posts.count()):
            post=posts.nth(i)
            title_link=post.locator("a.submission__link").first
            if await title_link.count()==0: continue
            title=clean(await title_link.inner_text())
            href=await title_link.get_attribute("href")
            forum=post.locator("a.submission__forum").first
            forum_text=clean(await forum.inner_text()) if await forum.count() else ""
            score=sim(needle,title)
            if needle.casefold() in title.casefold(): score+=2
            if "pics" in forum_text.casefold() or "/f/pics" in (await forum.get_attribute("href") if await forum.count() else ""):
                score+=1
            if href and (best is None or score>best["score"]):
                best={"score":score,"title":title,"href":urljoin(base,href),"forum":forum_text}
    if best is None or best["score"]<1:
        raise RuntimeError(f"source image post not found for {needle!r}")
    return best

async def submit_url(page,base,forum,title,url):
    slug=forum_slug(forum)
    r=await page.goto(f"{base}/submit/{slug}",wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("destination submit page failed")
    form=page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count()==0: raise RuntimeError("submission form missing")
    await form.locator('[name="submission[title]"]').first.fill(title)
    await form.locator('[name="submission[url]"]').first.fill(url)
    forum_el=form.locator('[name="submission[forum]"]').first
    if await forum_el.count()==0 or not await forum_el.input_value(): raise RuntimeError("destination forum not selected")
    btn=form.get_by_role("button",name="Create submission").first
    if await btn.count()==0: raise RuntimeError("submit control missing")
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"forum":slug,"forum_value":await forum_el.input_value(),"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True); ap.add_argument("--base-url",default="http://localhost:9999"); ap.add_argument("--output-dir",required=True); a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=11: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; needle=str(inst["content"]); dest=str(inst["forum"]); base=a.base_url.rstrip("/")
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); ctx=await b.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full"); page=await ctx.new_page()
        source=await find_source(page,base,needle)
        post=await submit_url(page,base,dest,"from /f/pics",source["href"])
        await ctx.close(); await b.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    ev={"task_id":a.task_id,"source":source,"destination":post}
    (out/"capability_evidence.json").write_text(json.dumps(ev,indent=2)+"\n")
    print(json.dumps(ev,indent=2))
if __name__=="__main__": asyncio.run(main())
