#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from urllib.parse import urlparse
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
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


def postcondition(url,forum,title,visible_text):
    """Confirm actual posted detail location and user-requested title."""
    path=urlparse(str(url)).path.strip("/").split("/")
    if len(path)<4 or path[0]!="f" or path[1].casefold()!=forum_slug(forum).casefold():
        return False
    if not path[2].isdigit() or not path[3]:
        return False
    return clean(title).casefold() in clean(visible_text).casefold()


async def observed_postcondition(page,spec):
    try:
        visible=await page.locator("body").inner_text(timeout=5000)
    except Exception:
        return False
    return postcondition(page.url,spec["forum"],spec["title"],visible)


async def submit(page,base,spec):
    url=base.rstrip("/")+"/submit/"+spec["forum"]
    r=await page.goto(url,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"submit page failed: {url}")
    form=page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count()==0: raise RuntimeError("submission form not found")
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
    submit_btn=form.get_by_role("button",name="Create submission").first
    if await submit_btn.count()==0: raise RuntimeError("submit control missing")
    # Playwright can time out waiting for scheduled navigation after the
    # click was already delivered. Never replay a possibly committed mutation.
    # A timeout is admissible only when the resulting page independently
    # establishes the intended forum and submitted title.
    navigation_timeout=False
    try:
        await submit_btn.click()
    except PlaywrightTimeoutError:
        navigation_timeout=True
        if not await observed_postcondition(page,spec):
            raise
    if not navigation_timeout:
        try:
            await page.wait_for_load_state("networkidle",timeout=120000)
        except PlaywrightTimeoutError:
            if not await observed_postcondition(page,spec):
                raise
    if not await observed_postcondition(page,spec):
        raise RuntimeError("post-submit page does not confirm forum and title")
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
