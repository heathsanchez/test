#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()
def norm(s): return re.sub(r"[^a-z0-9]+"," ",clean(s).casefold()).strip()
def sim(a,b): return SequenceMatcher(None,norm(a),norm(b)).ratio()
def parse_score(s):
    m=re.search(r"-?\d+",clean(s).replace(",",""))
    return int(m.group()) if m else 0

def query_phrase(post):
    s=re.sub(r"\s+with the lowest vote count\s*$","",post,flags=re.I)
    return clean(s)

async def candidates(page,base,post):
    q=query_phrase(post)
    r=await page.goto(base+"/search?q="+quote(q),wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("reddit search failed")
    rows=[]
    subs=page.locator(".submission")
    for i in range(await subs.count()):
        sub=subs.nth(i)
        link=sub.locator("a.submission__link").first
        if await link.count()==0: continue
        title=clean(await link.inner_text())
        submitter=sub.locator("a.submission__submitter").first
        username=clean(await submitter.inner_text()) if await submitter.count() else ""
        if username.casefold()!="MarvelsGrantMan136".casefold(): continue
        href=None
        links=sub.locator("a.text-sm")
        for j in range(await links.count()):
            h=await links.nth(j).get_attribute("href")
            if h and "/f/" in h:
                href=h; break
        if not href: continue
        score_el=sub.locator(".vote__net-score").first
        votes=parse_score(await score_el.inner_text()) if await score_el.count() else 0
        rows.append({"title":title,"href":urljoin(base,href),"votes":votes,"match":sim(q,title)})
    if not rows: raise RuntimeError(f"no owned post candidates for {q!r}")
    rows=[x for x in rows if x["match"]>=0.42] or rows
    if "lowest vote count" in post.casefold():
        rows.sort(key=lambda x:(x["votes"],-x["match"]))
    else:
        rows.sort(key=lambda x:(-x["match"],x["votes"]))
    return rows[0],rows[:10]

async def edit_post(page,target,content):
    r=await page.goto(target["href"],wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("post detail failed")
    edit=page.locator('a[href$="/edit"]').first
    if await edit.count()==0:
        edit=page.get_by_role("link",name=re.compile("edit",re.I)).first
    if await edit.count()==0: raise RuntimeError("edit link missing")
    href=await edit.get_attribute("href")
    if href:
        r=await page.goto(urljoin(page.url,href),wait_until="networkidle",timeout=120000)
    else:
        await edit.click(); await page.wait_for_load_state("networkidle",timeout=120000)
        r=None
    title=page.locator('[name="submission[title]"]').first
    body=page.locator('[name="submission[body]"]').first
    if await title.count()==0 or await body.count()==0: raise RuntimeError("edit form fields missing")
    old_title=await title.input_value()
    old_body=await body.input_value()
    new_body=old_body.rstrip()+"\n"+content
    await body.fill(new_body)
    form=title.locator("xpath=ancestor::form[1]")
    btn=form.get_by_role("button").last
    if await btn.count()==0: raise RuntimeError("edit submit control missing")
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"old_title":old_title,"old_body":old_body,"new_body":new_body,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=27: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    wanted=str(inst["post"]); content=str(inst["content"]); base=a.base_url.rstrip("/")
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        target,ranked=await candidates(page,base,wanted)
        action=await edit_post(page,target,content)
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"wanted":wanted,"content":content,"target":target,"candidates":ranked,"action":action}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
