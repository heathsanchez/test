#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE as GITLAB, sign_in
from webarena_shopping_to_reddit_reviews import REDDIT, REDDIT_AUTH, choose_forum

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()
def toks(s): return [x for x in re.findall(r"[a-z0-9]+",clean(s).casefold()) if len(x)>1]

def project_score(topic,p):
    hay=" ".join([
        str(p.get("path_with_namespace","")),
        str(p.get("name_with_namespace","")),
        str(p.get("description","")),
    ]).casefold()
    score=0
    for t in toks(topic):
        if t in hay: score+=3
        if t in str(p.get("path_with_namespace","")).casefold(): score+=2
    path=str(p.get("path_with_namespace","")).casefold()
    if clean(topic).casefold() in path: score+=10
    return score

async def api(page,url):
    payload=await page.evaluate(
        """async (url) => { const r=await fetch(url,{credentials:'same-origin'}); return {status:r.status,text:await r.text()}; }""",
        url,
    )
    if payload["status"]!=200: raise RuntimeError(f"GitLab API failed {payload['status']}: {payload['text'][:500]}")
    return json.loads(payload["text"])

async def select_project(page,topic):
    queries=[clean(topic),*toks(topic)]
    rows=[]; seen=set()
    for q in queries:
        url=f"{GITLAB}/api/v4/projects?search={quote(q)}&simple=true&per_page=100"
        batch=await api(page,url)
        if not isinstance(batch,list): continue
        for p in batch:
            path=clean(p.get("path_with_namespace",""))
            if not path or path in seen: continue
            seen.add(path); rows.append(p)
    if not rows: raise RuntimeError(f"no GitLab projects for {topic!r}")
    ranked=sorted(((project_score(topic,p),i,p) for i,p in enumerate(rows)),key=lambda x:(-x[0],x[1]))
    score,_,p=ranked[0]
    if score<=0: raise RuntimeError(f"no relevant GitLab project for {topic!r}")
    return p,[{"score":sc,"path":x.get("path_with_namespace"),"description":x.get("description")} for sc,_,x in ranked[:10]]

async def commit_count(page,p):
    project_id=quote(str(p["path_with_namespace"]),safe="")
    branch=p.get("default_branch") or "main"
    total=0
    for n in range(1,100):
        rows=await api(page,f"{GITLAB}/api/v4/projects/{project_id}/repository/commits?ref_name={quote(branch)}&per_page=100&page={n}")
        if not rows: break
        total+=len(rows)
        if len(rows)<100: break
    return total,branch

async def submit_url(page,forum,path,url,body):
    target=REDDIT+"/submit/"+forum["slug"]
    r=await page.goto(target,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError(f"submit page failed: {target}")
    form=page.locator("form").filter(has=page.locator('[name="submission[title]"]')).first
    if await form.count()==0: raise RuntimeError("submission form missing")
    media=form.locator('[name="submission[mediaType]"][value="url"]').first
    if await media.count()==0: raise RuntimeError("URL media type missing")
    await media.check()
    await form.locator('[name="submission[url]"]').first.fill(url)
    await form.locator('[name="submission[title]"]').first.fill(path)
    await form.locator('[name="submission[body]"]').first.fill(body)
    forum_value=await form.locator('[name="submission[forum]"]').first.input_value()
    btn=form.get_by_role("button",name="Create submission").first
    if await btn.count()==0: raise RuntimeError("submit control missing")
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"submit_url":target,"forum_value":forum_value,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=116: raise SystemExit("unsupported template")
    topic=clean(task["instantiation_dict"]["topic"])
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    stage="playwright_start"; diagnostic={"task_id":a.task_id,"topic":topic,"stage":stage}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            stage="context_create"; diagnostic["stage"]=stage
            ctx=await browser.new_context(extra_http_headers=REDDIT_AUTH,record_har_path=str(har),record_har_mode="full")
            stage="gitlab_sign_in"; diagnostic["stage"]=stage
            git=await ctx.new_page(); await sign_in(git)
            stage="gitlab_select_project"; diagnostic["stage"]=stage
            project,candidates=await select_project(git,topic); diagnostic["candidates"]=candidates
            stage="gitlab_commit_count"; diagnostic["stage"]=stage
            count,branch=await commit_count(git,project)
            path=clean(project["path_with_namespace"]); url=f"{GITLAB}/{path}"
            body=f"{count} commit{'s' if count!=1 else ''} already!"
            stage="reddit_choose_forum"; diagnostic["stage"]=stage
            reddit=await ctx.new_page()
            forum=await choose_forum(reddit,topic+" technology programming machine learning artificial intelligence")
            stage="reddit_submit"; diagnostic["stage"]=stage
            post=await submit_url(reddit,forum,path,url,body)
            await ctx.close(); await browser.close()
    except Exception as e:
        diagnostic.update({"exception_type":type(e).__name__,"exception":str(e)})
        (out/"failure_evidence.json").write_text(json.dumps(diagnostic,indent=2,ensure_ascii=False)+"\n")
        print(json.dumps(diagnostic,indent=2,ensure_ascii=False))
        raise
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"task_id":a.task_id,"topic":topic,"project":path,"branch":branch,"commit_count":count,"candidates":candidates,"forum":forum,"body":body,**post}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__": asyncio.run(main())
