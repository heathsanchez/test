#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE as GITLAB, sign_in

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

def repo_from_start(task):
    raw=str(task["start_urls"][0])
    path=raw.split("__GITLAB__",1)[-1].strip("/")
    if not path or "/" not in path: raise ValueError("GitLab repo start URL required")
    return path

def branch_name(target,default_branch,title):
    s=clean(target)
    if "default branch" in s.casefold(): return default_branch
    m=re.search(r"called\s+([A-Za-z0-9._/-]+)",s,re.I)
    if m: return m.group(1)
    slug=re.sub(r"[^a-z0-9]+","-",title.casefold()).strip("-")[:32] or "update"
    return f"title-{slug}"

async def fetch_json(page,url):
    p=await page.evaluate("""async (url)=>{const r=await fetch(url,{credentials:'same-origin'});return {status:r.status,text:await r.text()}}""",url)
    if p["status"]!=200: raise RuntimeError(f"GET failed {p['status']}: {url}")
    return json.loads(p["text"])

async def fetch_text(page,url):
    p=await page.evaluate("""async (url)=>{const r=await fetch(url,{credentials:'same-origin'});return {status:r.status,text:await r.text()}}""",url)
    if p["status"]!=200: raise RuntimeError(f"GET failed {p['status']}: {url}")
    return p["text"]

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=308: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; repo=repo_from_start(task); title=clean(inst["title"])
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page(); await sign_in(page)
        project=await fetch_json(page,f"{GITLAB}/api/v4/projects/{quote(repo,safe='')}")
        default=project.get("default_branch") or "main"
        branch=branch_name(inst["target_branch"],default,title)
        raw_url=f"{GITLAB}/api/v4/projects/{quote(repo,safe='')}/repository/files/{quote('index.html',safe='')}/raw?ref={quote(default)}"
        content=await fetch_text(page,raw_url)
        updated,n=re.subn(r"(?is)<title>.*?</title>",f"<title>{title}</title>",content,count=1)
        if n!=1: raise RuntimeError("exactly one HTML title element required")
        edit_url=f"{GITLAB}/{repo}/-/edit/{default}/index.html"
        r=await page.goto(edit_url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"edit page failed: {edit_url}")
        token=await page.locator('meta[name="csrf-token"]').get_attribute("content")
        if not token: raise RuntimeError("CSRF token missing")
        endpoint=f"{GITLAB}/{repo}/-/update/{default}/index.html"
        result=await page.evaluate("""async ({endpoint,token,data})=>{
          const p=new URLSearchParams();
          for(const [k,v] of Object.entries(data)) p.set(k,String(v));
          const r=await fetch(endpoint,{
            method:'POST',credentials:'same-origin',redirect:'follow',
            headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-CSRF-Token':token},
            body:p.toString()
          });
          return {status:r.status,url:r.url,text:(await r.text()).slice(0,500)};
        }""",{"endpoint":endpoint,"token":token,"data":{
          "_method":"put",
          "file_path":"index.html",
          "branch_name":branch,
          "original_branch":default,
          "content":updated,
          "commit_message":f"Update page title to {title}",
        }})
        if result["status"] not in (200,201):
            raise RuntimeError(f"file update failed: {result}")
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"repo":repo,"default_branch":default,"branch_name":branch,"title":title,"endpoint":endpoint,"result_status":result["status"],"result_url":result["url"]}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
