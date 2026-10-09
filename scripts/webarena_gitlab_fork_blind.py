#!/usr/bin/env python3
"""Task-ID-blind GitLab forks from observed projects and user namespace."""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE,sign_in

def clean(s):return re.sub(r"\s+"," ",str(s)).strip()
def norm(s):return re.sub(r"[^a-z0-9]+","",clean(s).casefold())

def parse_fork_intent(intent):
    text=clean(intent)
    owner=re.fullmatch(r"Fork all repos from ([A-Za-z0-9][A-Za-z0-9 ._'-]*)\.",text,re.I)
    project=re.fullmatch(r"Fork ([A-Za-z0-9][A-Za-z0-9._ /-]*)\.",text,re.I)
    if owner:kind,value="owner",clean(owner.group(1))
    elif project:kind,value="single",clean(project.group(1))
    else:raise ValueError("unsupported fork instruction")
    if not value or value in (".","..") or ".." in value or (kind=="single" and (value.casefold().startswith(("all repos from ","everything")) or value.count("/")>1)):
        raise ValueError("unsafe or unbounded fork target")
    return kind,value

def select_exact_project(query,candidates):
    target=norm(query);matches=[]
    for project in candidates:
        canonical=str(project.get("path_with_namespace") or "")
        names=(project.get("name"),project.get("path"),canonical,canonical.rsplit("/",1)[-1])
        if target and any(norm(name)==target for name in names if name):matches.append(project)
    if len(matches)!=1:raise ValueError(f"project identity not unique: {query!r}, exact={len(matches)}")
    return matches[0]

def select_user(query,users):
    target=norm(query)
    matches=[u for u in users if target and any(norm(u.get(k))==target for k in ("name","username"))]
    if len(matches)!=1:raise ValueError(f"source user not unique: {query!r}, exact={len(matches)}")
    return matches[0]

def choose_user_namespace(user,namespaces):
    username=norm(user.get("username"));candidates=[]
    for namespace in namespaces:
        if str(namespace.get("kind","")).casefold()!="user" or norm(namespace.get("path"))!=username:continue
        owner=namespace.get("owner_id")
        if owner is not None and str(owner)!=str(user.get("id")):continue
        candidates.append(namespace)
    if len(candidates)!=1:raise RuntimeError("authenticated fork namespace not uniquely observed")
    return int(candidates[0]["id"])

def fork_payload(project,namespace_id):
    return {"id":int(project["id"]),"name":str(project["name"]),
            "namespace_id":int(namespace_id),"path":str(project["path"])}

async def api_get(page,path):
    packet=await page.evaluate("""async (url) => {
      const response=await fetch(url,{credentials:'same-origin'});
      return {status:response.status,body:await response.text()};
    }""",BASE+path)
    if packet["status"]!=200:raise RuntimeError(f"GitLab observed GET failed {packet['status']}: {path}")
    return json.loads(packet["body"])

async def pages(page,path,max_pages=12):
    items=[]
    for number in range(1,max_pages+1):
        glue="&" if "?" in path else "?"
        segment=await api_get(page,f"{path}{glue}per_page=100&page={number}")
        if not isinstance(segment,list):raise RuntimeError("non-list GitLab API page")
        items.extend(segment)
        if len(segment)<100:return items
    raise RuntimeError("project listing exceeded bounded page budget")

async def projects_to_fork(page,kind,requested):
    if kind=="single":
        query=requested.rsplit("/",1)[-1]
        return [select_exact_project(requested,await pages(page,
            "/api/v4/projects?simple=true&search="+quote(query,safe="")))]
    users=await pages(page,"/api/v4/users?search="+quote(requested,safe=""))
    user=select_user(requested,users)
    projects=await pages(page,f"/api/v4/users/{int(user['id'])}/projects")
    owned=[]
    for p in projects:
        ns=p.get("namespace") or {}
        if str(ns.get("kind","")).casefold()=="user" and norm(ns.get("path"))==norm(user.get("username")):
            owned.append(p)
    if not owned:raise RuntimeError("no owned projects observed")
    if len(owned)>25:raise RuntimeError("fork request exceeds bounded 25-project budget")
    if len({p["id"] for p in owned})!=len(owned):raise RuntimeError("duplicate owner projects")
    return sorted(owned,key=lambda p:(norm(p.get("path")),int(p["id"])))

async def submit_fork_once(page,project,namespace_id):
    payload=fork_payload(project,namespace_id)
    url=BASE+f"/api/v4/projects/{payload['id']}/fork"
    packet=await page.evaluate("""async ({url,payload}) => {
      const body=new URLSearchParams();
      for(const [key,value] of Object.entries(payload))body.append(key,String(value));
      const csrf=document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      const headers={'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8',
                     'X-Requested-With':'XMLHttpRequest'};
      if(csrf)headers['X-CSRF-Token']=csrf;
      const response=await fetch(url,{method:'POST',credentials:'same-origin',headers,body:body.toString()});
      return {status:response.status,body:(await response.text()).slice(0,5000)};
    }""",{"url":url,"payload":payload})
    if packet["status"]!=201:
        raise RuntimeError("GitLab fork not confirmed by HTTP 201: "+json.dumps({
            "project":project.get("path_with_namespace"),"status":packet["status"],
            "response":packet["body"][:550]}))
    return {"observed_url":url,"response_status":packet["status"],
            "source_project":project.get("path_with_namespace"),
            "source_project_id":payload["id"],"target_namespace_id":namespace_id}

async def run(intent,start_url,output_dir):
    if start_url not in ("__GITLAB__",BASE):raise ValueError("fork requires GitLab site")
    kind,target=parse_fork_intent(intent)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    evidence={"capability":"gitlab_fork","kind":kind,"requested":target,"posted":[]}
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        context=await browser.new_context(record_har_path=str(out/"network.har"),record_har_mode="full")
        page=await context.new_page()
        try:
            await sign_in(page)
            account=await api_get(page,"/api/v4/user")
            namespace_id=choose_user_namespace(account,await pages(page,"/api/v4/namespaces"))
            projects=await projects_to_fork(page,kind,target)
            evidence["source_project_count"]=len(projects)
            for project in projects:
                receipt=await submit_fork_once(page,project,namespace_id)
                evidence["posted"].append(receipt)
        finally:
            await context.close()
            await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"capability":"gitlab_fork","source_count":len(evidence["posted"])}),flush=True)
    return response

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--intent",required=True);p.add_argument("--start-url",required=True)
    p.add_argument("--output-dir",required=True)
    args=p.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))

if __name__=="__main__":main()
