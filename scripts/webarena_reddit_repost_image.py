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

def candidate_evidence(needle, rows):
    """Rank observed sources without consulting benchmark or expected output.

    An ambiguous top score is UNKNOWN, never permission to submit a mutation.
    """
    candidates=[]
    for row in rows:
        title=clean(row["title"])
        score=sim(needle,title)
        if needle.casefold() in title.casefold():
            score+=2
        if row.get("forum_verified"):
            score+=1
        candidates.append({**row,"score":score})
    candidates.sort(key=lambda row:(-row["score"],row["href"]))
    if not candidates or candidates[0]["score"]<1:
        raise RuntimeError("no supported source image observed")
    if len(candidates)>1 and abs(candidates[0]["score"]-candidates[1]["score"])<0.15:
        raise RuntimeError("source image identity ambiguous; refusing mutation")
    return candidates[0],candidates


async def find_source(page,base,needle):
    urls=[f"{base}/f/pics",f"{base}/search?q={quote(needle)}"]
    rows={}
    for url in urls:
        response=await page.goto(url,wait_until="networkidle",timeout=120000)
        if response is None or response.status!=200:
            continue
        posts=page.locator(".submission")
        for i in range(await posts.count()):
            post=posts.nth(i)
            link=post.locator("a.submission__link").first
            if await link.count()==0:
                continue
            title=clean(await link.inner_text())
            href=await link.get_attribute("href")
            forum=post.locator("a.submission__forum").first
            forum_text=clean(await forum.inner_text()) if await forum.count() else ""
            forum_href=(await forum.get_attribute("href")) if await forum.count() else ""
            if not href:
                continue
            absolute=urljoin(base,href)
            # Source identity is the observed media URL, not a repeated search hit.
            rows[absolute]={"title":title,"href":absolute,"forum":forum_text,
                            "forum_verified":("pics" in forum_text.casefold() or
                                              "/f/pics" in (forum_href or "").casefold())}
    selected,candidates=candidate_evidence(needle,list(rows.values()))
    return {**selected,"candidate_count":len(candidates),
            "candidate_evidence":candidates[:20]}

async def submit_url(page,base,forum,title,url):
    slug=forum_slug(forum)
    r=await page.goto(f"{base}/submit/{slug}",wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("destination submit page failed")
    form=page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count()==0: raise RuntimeError("submission form missing")
    await form.locator('[name="submission[title]"]').first.fill(title)
    await form.locator('[name="submission[url]"]').first.fill(url)
    forum_el=form.locator('[name="submission[forum]"]').first
    if await forum_el.count()==0: raise RuntimeError("destination forum not selected")
    forum_value=await forum_el.input_value()
    if not forum_value: raise RuntimeError("destination forum not selected")
    btn=form.get_by_role("button",name="Create submission").first
    if await btn.count()==0: raise RuntimeError("submit control missing")
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"forum":slug,"forum_value":forum_value,"final_url":page.url}

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
