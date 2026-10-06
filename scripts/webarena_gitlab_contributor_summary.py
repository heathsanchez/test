#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from urllib.parse import quote, urlparse
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE, sign_in

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()

def project_path_from_url(url):
    path=urlparse(url).path.rstrip("/")
    return path.split("/-/",1)[0]

async def api_json(page,url):
    payload=await page.evaluate("""async (url) => {
      const r=await fetch(url,{credentials:'same-origin'});
      return {status:r.status,text:await r.text()};
    }""",url)
    if payload["status"]!=200:
        raise RuntimeError(f"GitLab API failed {payload['status']}: {payload['text'][:500]}")
    return json.loads(payload["text"])

async def contributors(page,repo_path,branch):
    pid=quote(repo_path.strip("/"),safe="")
    out=[]
    for pageno in range(1,50):
        data=await api_json(page,f"{BASE}/api/v4/projects/{pid}/repository/contributors?ref={quote(branch,safe='')}&per_page=100&page={pageno}")
        if not data: break
        out.extend(data)
        if len(data)<100: break
    if not out: raise RuntimeError("no repository contributors returned")
    out.sort(key=lambda x:int(x.get("commits",0)),reverse=True)
    return out

async def resolve_user(page,identity):
    qs=[]
    if identity.get("name"): qs.append(str(identity["name"]))
    email=str(identity.get("email",""))
    if "@" in email: qs.append(email.split("@",1)[0])
    candidates={}
    for q in qs:
        for u in await api_json(page,BASE+"/api/v4/users?per_page=100&search="+quote(q,safe="")):
            if u.get("id") is not None: candidates[u["id"]]=u
    if not candidates: raise RuntimeError(f"user profile not found for {identity}")
    name=clean(identity.get("name","")).casefold()
    local=email.split("@",1)[0].casefold() if "@" in email else ""
    def score(u):
        uname=clean(u.get("username","")).casefold().lstrip("@")
        return (4 if uname==local and local else 0)+(2 if clean(u.get("name","")).casefold()==name and name else 0)
    chosen=max(candidates.values(),key=score)
    return await api_json(page,BASE+f"/api/v4/users/{chosen['id']}")

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=316: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]; repo=project_path_from_url(task["start_urls"][0].replace("__GITLAB__",BASE))
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await sign_in(page)
        rows=await contributors(page,repo,inst["branch_name"])
        top=rows[0]; attr=str(inst["attribute"]).casefold(); profile=None
        if "number of commits" in attr:
            data=[int(top["commits"])]
        elif all(x in attr for x in ("full name","username","user location","email")):
            profile=await resolve_user(page,top)
            data=[{
                "full_name":clean(top.get("name","")),
                "username":clean(profile.get("username","")),
                "user_location":clean(profile.get("location","")),
                "email":clean(top.get("email","")),
            }]
        else: raise RuntimeError("unsupported contributor projection")
        await b.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    evidence={"task_id":a.task_id,"repo":repo,"branch":inst["branch_name"],"top":top,"profile":profile,"contributors_seen":len(rows)}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__":
    asyncio.run(main())
