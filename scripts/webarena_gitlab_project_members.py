#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright

def clean(s): return re.sub(r"\s+"," ",s).strip()
def norm(s): return re.sub(r"[^a-z0-9]+","",s.casefold())

async def login(page,base):
    await page.goto(base+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/",timeout=120000)

async def resolve_project(page,base,wanted):
    await page.goto(f"{base}/search?search={quote(wanted)}&scope=projects",wait_until="networkidle",timeout=180000)
    links=page.locator('a[href*="/"]')
    best=None
    for i in range(await links.count()):
        a=links.nth(i); href=await a.get_attribute("href"); txt=clean(await a.inner_text())
        if not href or href.startswith(("http","/search","/users","/help","/dashboard")): continue
        path=href.split("?")[0].rstrip("/")
        parts=[p for p in path.split("/") if p]
        if len(parts)!=2: continue
        name=parts[-1]
        sc=max(SequenceMatcher(None,norm(wanted),norm(name)).ratio(),SequenceMatcher(None,norm(wanted),norm(txt)).ratio() if txt else 0)
        if best is None or sc>best["score"]: best={"path":"/"+"/".join(parts),"name":name,"score":sc}
    if not best or best["score"]<0.60: raise RuntimeError(f"project not resolved: {wanted}")
    return best

async def members(page,base,path):
    u=path+"/-/project_members"
    r=await page.goto(base+u,wait_until="networkidle",timeout=180000)
    if r is None or r.status!=200:
        raise RuntimeError("project member page unavailable")
    body=clean(await page.locator("body").inner_text())
    rows=page.locator('[data-testid^="members-table-row-"]')
    found=[]
    for i in range(await rows.count()):
        txt=clean(await rows.nth(i).inner_text())
        m=re.search(r"@([A-Za-z0-9_.-]+)",txt)
        if not m:
            continue
        user=m.group(1)
        if user.casefold()=="byteblaze":
            continue
        if user not in found:
            found.append(user)
    if not found:
        raise RuntimeError("no other project members found")
    return found,body[:12000],u

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:8023"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=298: raise SystemExit("unsupported template")
    wanted=str(task["instantiation_dict"]["repo"]); base=a.base_url.rstrip("/")
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True); page=await browser.new_page()
        await login(page,base); project=await resolve_project(page,base,wanted)
        users,excerpt,members_url=await members(page,base,project["path"]); await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":users,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"requested":wanted,"project":project,"members_url":members_url,"users":users,"excerpt":excerpt},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"project":project,"users":users},indent=2))
if __name__=="__main__": asyncio.run(main())
