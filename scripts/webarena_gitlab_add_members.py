#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE as GITLAB, sign_in

ROLE_LEVEL={"guest":10,"reporter":20,"developer":30,"maintainer":40,"owner":50}

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()
def norm(s): return re.sub(r"[^a-z0-9]+"," ",clean(s).casefold()).strip()
def sim(a,b): return SequenceMatcher(None,norm(a),norm(b)).ratio()

def users(raw):
    quoted=re.findall(r'"([^"]+)"',str(raw))
    if quoted: return [clean(x) for x in quoted]
    return [clean(x) for x in re.split(r"\band\b|,",str(raw),flags=re.I) if clean(x)]

async def api(page,method,url,data=None):
    payload=await page.evaluate("""async ({method,url,data}) => {
      const opt={method,credentials:'same-origin',headers:{}};
      if(data!==null){
        const p=new URLSearchParams();
        for(const [k,v] of Object.entries(data)) p.set(k,String(v));
        opt.body=p.toString();
        opt.headers['Content-Type']='application/x-www-form-urlencoded; charset=UTF-8';
      }
      const r=await fetch(url,opt);
      return {status:r.status,text:await r.text(),url:r.url};
    }""",{"method":method,"url":url,"data":data})
    return payload

async def resolve_project(page,description):
    q=clean(description)
    for query in [q,re.sub(r"^(my|repo)\s+","",q,flags=re.I)]:
        p=await api(page,"GET",f"{GITLAB}/api/v4/projects?search={quote(query)}")
        if p["status"]!=200: continue
        rows=json.loads(p["text"])
        if rows:
            rows.sort(key=lambda x:(-max(sim(q,x.get("name","")),sim(q,x.get("path_with_namespace",""))),x.get("id",0)))
            return rows[0]
    raise RuntimeError(f"project not found: {description}")

async def resolve_user(page,username):
    p=await api(page,"GET",f"{GITLAB}/api/v4/users?username={quote(username)}")
    if p["status"]!=200: raise RuntimeError(f"user lookup failed {username}: {p['status']}")
    rows=json.loads(p["text"])
    exact=[x for x in rows if clean(x.get("username","")).casefold()==username.casefold()]
    if exact: return exact[0]
    if rows: return rows[0]
    p=await api(page,"GET",f"{GITLAB}/api/v4/users?search={quote(username)}")
    rows=json.loads(p["text"]) if p["status"]==200 else []
    if not rows: raise RuntimeError(f"user not found: {username}")
    rows.sort(key=lambda x:-sim(username,x.get("username","")))
    return rows[0]

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=351: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    repo=clean(inst["repo"]); role=clean(inst["role"]).casefold(); names=users(inst["user_list"])
    if role not in ROLE_LEVEL: raise RuntimeError(f"unsupported role {role}")
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page(); await sign_in(page)
        project=await resolve_project(page,repo)
        resolved=[await resolve_user(page,u) for u in names]
        ids=",".join(str(x["id"]) for x in resolved)
        endpoint=f"{GITLAB}/api/v4/projects/{project['id']}/invitations"
        result=await api(page,"POST",endpoint,{"user_id":ids,"access_level":ROLE_LEVEL[role]})
        if result["status"] not in (200,201):
            raise RuntimeError(f"invite failed {result['status']}: {result['text'][:500]}")
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"repo":repo,"project":{"id":project["id"],"path_with_namespace":project.get("path_with_namespace")},"role":role,"users":[{"username":x.get("username"),"id":x.get("id")} for x in resolved],"endpoint":endpoint,"status":result["status"]}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
