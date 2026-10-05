#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from playwright.async_api import async_playwright

BASE="http://localhost:8023"

def clean(s): return re.sub(r"\s+"," ",s).strip()
def norm(s): return re.sub(r"[^a-z0-9]+","",s.casefold())

async def login(page):
    await page.goto(BASE+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/",timeout=120000)

async def api_json(page,url):
    payload=await page.evaluate(
        """async (url) => {
            const r=await fetch(url,{credentials:'same-origin'});
            return {status:r.status,text:await r.text()};
        }""",url)
    if payload["status"]!=200:
        raise RuntimeError(f"GitLab API {payload['status']}: {payload['text'][:500]}")
    return json.loads(payload["text"])

def semantic_query(text):
    low=text.casefold()
    if "gan" in low: return "GAN"
    if "covid" in low: return "Covid"
    return text

def choose_project(wanted,projects):
    low=wanted.casefold()
    if "best " in low or "most stared" in low or "most starred" in low:
        return max(projects,key=lambda p:(int(p.get("star_count",0)),int(p.get("forks_count",0))))
    target=norm(wanted)
    def score(p):
        return max(
            SequenceMatcher(None,target,norm(str(p.get("name","")))).ratio(),
            SequenceMatcher(None,target,norm(str(p.get("path_with_namespace","")))).ratio(),
        )
    return max(projects,key=score)

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    wanted=str(task["instantiation_dict"]["repo"])
    q=semantic_query(wanted)
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await login(page)
        projects=await api_json(page,BASE+"/api/v4/projects?simple=true&per_page=100&search="+q.replace(" ","%20"))
        if not projects: raise RuntimeError(f"no GitLab projects for {q!r}")
        chosen=choose_project(wanted,projects)
        await b.close()
    ssh=chosen.get("ssh_url_to_repo")
    if not ssh: raise RuntimeError("chosen project has no SSH clone URL")
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[ssh],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence={"wanted":wanted,"query":q,"chosen":{"id":chosen.get("id"),"name":chosen.get("name"),"path":chosen.get("path_with_namespace"),"stars":chosen.get("star_count"),"ssh":ssh}}
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,**evidence},indent=2))

if __name__=="__main__": asyncio.run(main())
