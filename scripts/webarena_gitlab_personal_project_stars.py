#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DEFAULT="http://localhost:8023"

def clean(s): return re.sub(r"\s+"," ",s).strip()

async def login(page,base):
    await page.goto(base+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/",timeout=120000)

async def list_projects(page,base):
    r=await page.goto(base+"/users/byteblaze/projects",wait_until="networkidle",timeout=180000)
    if r is None or r.status!=200: raise RuntimeError("personal projects page failed")
    links=page.locator('a.project[href^="/byteblaze/"]')
    paths=[]
    for i in range(await links.count()):
        href=await links.nth(i).get_attribute("href")
        if href and href.count("/")==2 and href not in paths:
            paths.append(href)
    out=[]
    for path in paths:
        star=page.locator(f'a[href="{path}/-/starrers"].stars').first
        if await star.count()==0:
            star=page.locator(f'a[href="{path}/-/starrers"]').first
        txt=clean(await star.inner_text()) if await star.count() else ""
        m=re.search(r"\d+",txt.replace(",",""))
        if not m: raise RuntimeError(f"star count missing for {path}")
        out.append({"path":path,"name":path.rsplit("/",1)[-1],"stars":int(m.group())})
    return out

async def project_id(page,base,path):
    r=await page.goto(base+path,wait_until="networkidle",timeout=180000)
    if r is None or r.status!=200: raise RuntimeError(f"project page failed: {path}")
    body=clean(await page.locator("body").inner_text())
    for pat in (r"Project ID:\s*(\d+)",r"project id\s*(\d+)"):
        m=re.search(pat,body,re.I)
        if m: return int(m.group(1))
    html=await page.content()
    for pat in (r'data-project-id=["\'](\d+)',r'"project_id":(\d+)',r'"projectId":(\d+)'):
        m=re.search(pat,html,re.I)
        if m: return int(m.group(1))
    raise RuntimeError(f"project id not visible for {path}")

def select(projects,description):
    d=description.casefold()
    stars=[p["stars"] for p in projects]
    if "more than 100" in d: chosen=[p for p in projects if p["stars"]>100]
    elif "most stars" in d:
        m=max(stars); chosen=[p for p in projects if p["stars"]==m]
    elif "least stars" in d:
        m=min(stars); chosen=[p for p in projects if p["stars"]==m]
    elif "less than 5" in d: chosen=[p for p in projects if p["stars"]<5]
    elif "no stars" in d: chosen=[p for p in projects if p["stars"]==0]
    else: raise ValueError(description)
    return chosen

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default=BASE_DEFAULT); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=289: raise SystemExit("unsupported template")
    base=a.base_url.rstrip("/")
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        await login(page,base)
        projects=await list_projects(page,base)
        for project in projects:
            project["id"]=await project_id(page,base,project["path"])
        await browser.close()
    chosen=select(projects,str(task["instantiation_dict"]["description"]))
    if chosen:
        response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[p["id"] for p in chosen],"error_details":None}
    else:
        response={"task_type":"RETRIEVE","status":"NOT_FOUND_ERROR","retrieved_data":None,"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"projects":projects,"chosen":chosen,"response":response},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,"projects":projects,"chosen":chosen},indent=2))

if __name__=="__main__": asyncio.run(main())
