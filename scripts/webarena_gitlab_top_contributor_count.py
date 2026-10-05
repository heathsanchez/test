#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlparse
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE, sign_in

async def api_json(page,url):
    payload=await page.evaluate(
        """async (url) => {
            const r=await fetch(url,{credentials:'same-origin'});
            return {status:r.status,text:await r.text()};
        }""",url)
    if payload["status"]!=200:
        raise RuntimeError(f"GitLab API failed: {payload['status']} {payload['text'][:500]}")
    return json.loads(payload["text"])

async def contributor_counts(page,repo_path,branch_name):
    project_id=quote(repo_path.strip("/"),safe="")
    counts=Counter(); identities={}; seen=set(); pages=0
    for pageno in range(1,100):
        url=f"{BASE}/api/v4/projects/{project_id}/repository/commits?ref_name={quote(branch_name,safe='')}&per_page=100&page={pageno}"
        data=await api_json(page,url); pages+=1
        if not data: break
        for item in data:
            sha=item.get("id")
            if not sha or sha in seen: continue
            seen.add(sha)
            email=str(item.get("author_email","")).strip().casefold()
            name=str(item.get("author_name","")).strip()
            key=email or name.casefold()
            if not key: continue
            counts[key]+=1
            identities[key]={"name":name,"email":str(item.get("author_email","")).strip()}
        if len(data)<100: break
    if not counts: raise RuntimeError("no commits found")
    key,n=counts.most_common(1)[0]
    return n,identities[key],{"pages_scanned":pages,"commits_seen":len(seen),"contributors":len(counts)}

async def resolve_user(page,identity):
    queries=[]
    name=str(identity.get("name","")).strip()
    email=str(identity.get("email","")).strip()
    if name: queries.append(name)
    if "@" in email: queries.append(email.split("@",1)[0])
    candidates={}
    for q in queries:
        data=await api_json(page,BASE+"/api/v4/users?per_page=100&search="+quote(q,safe=""))
        for item in data:
            if item.get("id") is not None:
                candidates[item["id"]]=item
    if not candidates:
        raise RuntimeError(f"no GitLab user candidate for {identity}")
    email_local=email.split("@",1)[0].casefold() if "@" in email else ""
    def score(u):
        uname=str(u.get("username","")).strip().casefold().lstrip("@")
        uname_norm="".join(ch for ch in uname if ch.isalnum())
        local_norm="".join(ch for ch in email_local if ch.isalnum())
        uname_score=3 if email_local and uname==email_local else (2 if local_norm and uname_norm==local_norm else 0)
        name_score=2 if str(u.get("name","")).strip().casefold()==name.casefold() and name else 0
        return uname_score+name_score
    chosen=max(candidates.values(),key=score)
    detail=await api_json(page,BASE+f"/api/v4/users/{chosen['id']}")
    return detail

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    inst=task["instantiation_dict"]
    start=task["start_urls"][0].replace("__GITLAB__",BASE)
    path=urlparse(start).path
    # Strip any tree/blob suffix so project identity is stable.
    path=path.split("/-/")[0]
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await sign_in(page)
        count,identity,evidence=await contributor_counts(page,path,inst["branch_name"])
        attr=str(inst["attribute"]).casefold()
        profile=None
        if "full name" in attr or "username" in attr or "user location" in attr:
            profile=await resolve_user(page,identity)
        await b.close()
    if "number of commits" in attr:
        data=[count]
    elif all(x in attr for x in ("full name","username","user location","email")):
        data=[{
            "full_name":identity["name"],
            "username":str(profile.get("username","")).strip(),
            "user_location":str(profile.get("location","")).strip(),
            "email":identity["email"],
        }]
        if not all(data[0].values()):
            raise RuntimeError(f"incomplete contributor identity projection: {data[0]}")
    else:
        raise RuntimeError("unsupported contributor projection")
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":data,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence.update({"task_id":a.task_id,"repo_path":path,"branch":inst["branch_name"],"winner":identity,"count":count,"profile":profile})
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__": asyncio.run(main())
