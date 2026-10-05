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
        await b.close()
    if "number of commits" not in str(inst["attribute"]).casefold():
        raise RuntimeError("unsupported contributor projection")
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[count],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence.update({"task_id":a.task_id,"repo_path":path,"branch":inst["branch_name"],"winner":identity,"count":count})
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__": asyncio.run(main())
