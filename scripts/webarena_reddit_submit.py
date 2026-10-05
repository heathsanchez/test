#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

AUTH={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"}

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

def forum_slug(raw):
    s=clean(raw)
    s=re.sub(r"^f/","",s,flags=re.I)
    s=re.sub(r"\s+forum$","",s,flags=re.I)
    return s

def compile_post(task):
    tid=int(task["intent_template_id"]); inst=task["instantiation_dict"]
    if tid==15:
        forum=forum_slug(inst["forum"])
        title=f'{inst["category"]} recommendations?'
        body=f'Hey, looking for good {inst["category"]} under {inst["price"]}, any suggestions?'
    elif tid==16:
        forum=forum_slug(inst["forum"])
        title=f'{inst["interest"]} Meet up!'
        body=f'virtual meetup for {inst["interest"]} on {inst["date"]}'
    elif tid==19:
        forum=forum_slug(inst["forum"])
        title=str(inst["title"])
        body=None
    else:
        raise SystemExit(f"unsupported explicit-forum submit template {tid}")
    return {"forum":forum,"title":title,"body":body}

async def submit(page,base,spec):
    url=base.rstrip("/")+"/submit/"+spec["forum"]
    r=await page.goto(url,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"submit page failed: {url}")
    form=page.locator('form[action*="/submit"]').first
    if await form.count()==0: form=page.locator("form").first
    title=form.locator('[name="submission[title]"]').first
    forum=form.locator('[name="submission[forum]"]').first
    if await title.count()==0 or await forum.count()==0:
        raise RuntimeError("submit form contract not found")
    await title.fill(spec["title"])
    if spec["body"] is not None:
        body=form.locator('[name="submission[body]"]').first
        if await body.count()==0: raise RuntimeError("submission body field missing")
        await body.fill(spec["body"])
    forum_value=await forum.input_value()
    if not forum_value: raise RuntimeError("forum was not preselected")
    submit_btn=form.locator('button[type="submit"], input[type="submit"]').first
    if await submit_btn.count()==0: raise RuntimeError("submit control missing")
    await submit_btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"submit_url":url,"forum_value":forum_value,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    spec=compile_post(task)
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    har=out/"network.har"
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        evidence=await submit(page,a.base_url,spec)
        await ctx.close()
        await b.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    ev={"task_id":a.task_id,"compiled":spec,**evidence,"har":str(har)}
    (out/"capability_evidence.json").write_text(json.dumps(ev,indent=2)+"\n")
    print(json.dumps(ev,indent=2))

if __name__=="__main__":
    asyncio.run(main())
