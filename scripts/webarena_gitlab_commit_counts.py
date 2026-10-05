#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, calendar, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

BASE="http://localhost:8023"

def clean(s): return re.sub(r"\s+"," ",s).strip()

def month_num(token):
    t=token.strip().lower().rstrip(".")
    for i in range(1,13):
        if t in {calendar.month_name[i].lower(),calendar.month_abbr[i].lower()}:
            return i
    raise ValueError(token)

def period_bounds(text):
    s=clean(text)
    m=re.fullmatch(r"during\s+(\d{4})",s,re.I)
    if m:
        y=int(m.group(1)); return datetime(y,1,1,tzinfo=timezone.utc),datetime(y+1,1,1,tzinfo=timezone.utc)
    m=re.fullmatch(r"between start of\s+([A-Za-z]+)\s+(\d{4})\s+and end of\s+([A-Za-z]+)\s+(\d{4})",s,re.I)
    if m:
        sm,sy,em,ey=m.groups(); sy=int(sy); ey=int(ey); sm=month_num(sm); em=month_num(em)
        start=datetime(sy,sm,1,tzinfo=timezone.utc)
        if em==12: end=datetime(ey+1,1,1,tzinfo=timezone.utc)
        else: end=datetime(ey,em+1,1,tzinfo=timezone.utc)
        return start,end
    m=re.fullmatch(r"on\s+([A-Za-z]+)\s+(\d+)(?:st|nd|rd|th)?\s+(\d{4})",s,re.I)
    if m:
        mon,day,y=m.groups(); y=int(y); day=int(day); mon=month_num(mon)
        start=datetime(y,mon,day,tzinfo=timezone.utc)
        from datetime import timedelta
        return start,start+timedelta(days=1)
    raise ValueError(f"unsupported period: {text!r}")

async def sign_in(page):
    await page.goto(BASE+"/users/sign_in",wait_until="networkidle",timeout=180000)
    await page.get_by_test_id("username-field").fill("byteblaze")
    await page.get_by_test_id("password-field").fill("hello1234")
    await page.get_by_test_id("sign-in-button").click()
    await page.wait_for_url("**/",timeout=120000)

async def count_commits(page,repo_path,author,start,end):
    # Use GitLab's own authenticated REST surface rather than guessing the
    # commit-list UI pagination contract.
    project_id=repo_path.strip("/").replace("/","%2F")
    total=0; pages=0; seen=set(); observations=[]
    for pageno in range(1,80):
        api=(
            f"{BASE}/api/v4/projects/{project_id}/repository/commits"
            f"?ref_name=main&since={start.isoformat()}&until={end.isoformat()}&per_page=100&page={pageno}"
        )
        payload=await page.evaluate(
            """async (url) => {
                const r = await fetch(url, {credentials:'same-origin'});
                return {status:r.status, text:await r.text()};
            }""",
            api,
        )
        if payload["status"]!=200:
            raise RuntimeError(f"GitLab commits API failed: {payload['status']} {payload['text'][:500]}")
        data=json.loads(payload["text"])
        pages+=1
        if not data:
            break
        for item in data:
            sha=item.get("id") or item.get("short_id")
            if not sha or sha in seen:
                continue
            seen.add(sha)
            name=clean(str(item.get("author_name","")))
            # Task names may be shortened (e.g. "Kilian" for "Kilian Valkhof").
            wanted=author.casefold()
            observed=name.casefold()
            if observed==wanted or observed.startswith(wanted+" "):
                total+=1
                observations.append({"sha":str(sha)[:8],"author":name,"datetime":item.get("authored_date")})
        if len(data)<100:
            break
    return total,{"pages_scanned":pages,"commits_seen":len(seen),"matches":observations}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    tasks=json.loads(Path(a.task_file).read_text())
    task=next(t for t in tasks if int(t["task_id"])==a.task_id)
    start_url=task["start_urls"][0].replace("__GITLAB__",BASE)
    repo_path=urlparse(start_url).path.rstrip("/")
    inst=task["instantiation_dict"]
    start,end=period_bounds(inst["period"])
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); page=await b.new_page()
        await sign_in(page)
        count,evidence=await count_commits(page,repo_path,inst["user"],start,end)
        await b.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS","retrieved_data":[count],"error_details":None}
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    evidence.update({"task_id":a.task_id,"author":inst["user"],"start":start.isoformat(),"end_exclusive":end.isoformat(),"count":count})
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))

if __name__=="__main__": asyncio.run(main())
