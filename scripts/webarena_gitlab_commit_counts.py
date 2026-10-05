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
    total=0; seen=set(); pages=0; observations=[]
    for pageno in range(1,80):
        url=f"{BASE}{repo_path}/-/commits/main?page={pageno}"
        r=await page.goto(url,wait_until="networkidle",timeout=180000)
        if r is None or r.status!=200: raise RuntimeError(f"commit page failed {url}")
        rows=page.locator(".commit")
        n=await rows.count()
        if n==0: break
        pages+=1
        new=0
        oldest=None
        for i in range(n):
            row=rows.nth(i)
            sha=clean(await row.locator(".label-monospace").first.inner_text()) if await row.locator(".label-monospace").count() else clean(await row.inner_text())[:80]
            if sha in seen: continue
            seen.add(sha); new+=1
            a=clean(await row.locator(".commit-author-link").first.inner_text()) if await row.locator(".commit-author-link").count() else ""
            time=row.locator("time").first
            iso=await time.get_attribute("datetime") if await time.count() else None
            if not iso: continue
            dt=datetime.fromisoformat(iso.replace("Z","+00:00"))
            oldest=dt if oldest is None or dt<oldest else oldest
            if a.casefold()==author.casefold() and start<=dt<end:
                total+=1
                observations.append({"sha":sha,"author":a,"datetime":iso})
        if new==0: break
        # Commit pages are reverse chronological; once the oldest visible commit
        # precedes the requested interval, later pages cannot contribute.
        if oldest is not None and oldest<start: break
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
