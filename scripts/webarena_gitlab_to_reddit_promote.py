#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from webarena_reddit_submit_v3 import observed_postcondition
from webarena_gitlab_commit_counts import sign_in

GITLAB="http://localhost:8023"
REDDIT="http://localhost:9999"
REDDIT_AUTH={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"}

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

async def api_json(page,url):
    payload=await page.evaluate("""async (url) => {
      const r=await fetch(url,{credentials:'same-origin'});
      return {status:r.status,text:await r.text()};
    }""",url)
    if payload["status"]!=200:
        raise RuntimeError(f"GitLab API failed {payload['status']}: {payload['text'][:500]}")
    return json.loads(payload["text"])

async def fetch_project(page,repo):
    pid=quote(repo.strip("/"),safe="")
    data=await api_json(page,f"{GITLAB}/api/v4/projects/{pid}")
    desc=clean(data.get("description",""))
    if not desc: raise RuntimeError(f"project description missing for {repo}")
    return {"path":clean(data.get("path_with_namespace",repo)),"description":desc}

async def submit_url_post(page,forum,title,url):
    r=await page.goto(REDDIT+"/submit/"+forum,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("Reddit submit page failed")
    form=page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count()==0: raise RuntimeError("submission form missing")
    await form.locator('[name="submission[title]"]').first.fill(title)
    await form.locator('[name="submission[url]"]').first.fill(url)
    forum_el=form.locator('[name="submission[forum]"]').first
    forum_value=await forum_el.input_value()
    if not forum_value: raise RuntimeError("forum not preselected")
    btn=form.get_by_role("button",name="Create submission").first
    if await btn.count()==0: raise RuntimeError("submit control missing")
    # Click may have posted successfully before Playwright times out waiting
    # for navigation. Never replay a potentially committed POST.
    expected={"forum":forum,"title":title}
    try:
        await btn.click()
    except PlaywrightTimeoutError:
        if not await observed_postcondition(page,expected):
            raise
    try:
        await page.wait_for_load_state("networkidle",timeout=120000)
    except PlaywrightTimeoutError:
        if not await observed_postcondition(page,expected):
            raise
    if not await observed_postcondition(page,expected):
        raise RuntimeError("cross-site Reddit post lacks independently observed forum and title")
    return {"forum_value":forum_value,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=117: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; repo=clean(inst["repo"]); forum=clean(inst["forum"])
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    stage="playwright_start"
    diagnostic={"task_id":a.task_id,"repo":repo,"forum":forum,"stage":stage}
    try:
        async with async_playwright() as p:
            stage="browser_launch"; diagnostic["stage"]=stage
            b=await p.chromium.launch(headless=True)
            stage="context_create"; diagnostic["stage"]=stage
            ctx=await b.new_context(extra_http_headers=REDDIT_AUTH,record_har_path=str(har),record_har_mode="full")
            stage="gitlab_sign_in"; diagnostic["stage"]=stage
            git=await ctx.new_page(); await sign_in(git)
            stage="gitlab_fetch_project"; diagnostic["stage"]=stage
            project=await fetch_project(git,repo)
            diagnostic["project"]=project
            stage="reddit_open"; diagnostic["stage"]=stage
            reddit=await ctx.new_page()
            post_url=f"{GITLAB}/{project['path']}"
            diagnostic["post_url"]=post_url
            stage="reddit_submit"; diagnostic["stage"]=stage
            post=await submit_url_post(reddit,forum,project["description"],post_url)
            diagnostic["post"]=post
            stage="close"; diagnostic["stage"]=stage
            await ctx.close(); await b.close()
    except Exception as e:
        diagnostic.update({"stage":stage,"exception_type":type(e).__name__,"exception":str(e)})
        (out/"failure_evidence.json").write_text(json.dumps(diagnostic,indent=2,ensure_ascii=False)+"\n")
        print(json.dumps(diagnostic,indent=2,ensure_ascii=False))
        raise
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"repo":repo,"forum":forum,"project":project,"post_url":post_url,**post}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2,ensure_ascii=False)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
