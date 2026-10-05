#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import BASE, sign_in

def norm(s): return re.sub(r"[^a-z0-9]+","",str(s).casefold())

async def api_json(page,url):
    payload=await page.evaluate(
        """async (url) => {
            const r=await fetch(url,{credentials:'same-origin'});
            return {status:r.status,text:await r.text()};
        }""",url)
    if payload["status"]!=200:
        raise RuntimeError(f"GitLab API failed {payload['status']}: {payload['text'][:500]}")
    return json.loads(payload["text"])

def owner_hint(text):
    m=re.search(r"([A-Za-z0-9_.-]+)[\"']s\s+",text)
    return m.group(1).casefold() if m else None

def choose_project(wanted,projects):
    owner=owner_hint(wanted)
    target=norm(wanted)
    def score(p):
        path=str(p.get("path_with_namespace",""))
        name=str(p.get("name",""))
        ns=str((p.get("namespace") or {}).get("full_path",""))
        s=max(SequenceMatcher(None,target,norm(path)).ratio(),SequenceMatcher(None,target,norm(name)).ratio())
        if owner and (ns.casefold()==owner or path.casefold().startswith(owner+"/")): s+=0.5
        if "react" in wanted.casefold() and "react" in path.casefold(): s+=0.2
        if "app" in wanted.casefold() and "app" in path.casefold(): s+=0.2
        return s
    return max(projects,key=score)

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    wanted=str(task["instantiation_dict"]["repo"])
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await sign_in(page)
        projects=await api_json(page,BASE+"/api/v4/projects?simple=true&per_page=100&search="+quote("react"))
        chosen=choose_project(wanted,projects)
        pid=chosen["id"]
        contributors=await api_json(page,f"{BASE}/api/v4/projects/{pid}/repository/contributors?order_by=commits&sort=desc&per_page=100")
        await b.close()
    ranked=[c for c in contributors if c.get("email")]
    if len(ranked)<3: raise RuntimeError("fewer than three contributors with emails")
    top=ranked[:3]
    emails=[str(c["email"]).strip() for c in top]
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":emails,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    evidence={"wanted":wanted,"project":{"id":pid,"path":chosen.get("path_with_namespace")},"top":[{"name":c.get("name"),"email":c.get("email"),"commits":c.get("commits")} for c in top]}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,**evidence},indent=2))
if __name__=="__main__": asyncio.run(main())
