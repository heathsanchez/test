#!/usr/bin/env python3
"""Task-ID-blind GitLab issue navigation using a negated label predicate."""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from urllib.parse import urlencode,urlparse,parse_qs
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import sign_in,BASE

def parse_intent(text):
    text=" ".join(str(text).split())
    m=re.fullmatch(
        r"Navigate to the page showing the list of (?:open|not yet closed) issues "
        r"in the ([^ ]+) repository that have labels related to all except ([^ .]+)",
        text,re.I,
    )
    if not m:
        raise ValueError("unsupported negative-label issue navigation intent")
    repo,label=m.groups()
    parts=repo.split("/")
    if len(parts)!=2 or any(p in ("",".","..") for p in parts) or not all(re.fullmatch(r"[\w.-]+",p) for p in parts):
        raise ValueError("repository path invalid")
    return {"repo":repo,"excluded_label":label}

def filtered_target(spec):
    return BASE+"/"+spec["repo"]+"/-/issues?"+urlencode({
        "state":"opened",
        "not[label_name][]":spec["excluded_label"],
    })

async def navigate(page,intent):
    parsed=parse_intent(intent)
    target=filtered_target(parsed)
    await sign_in(page)
    response=await page.goto(target,wait_until="networkidle",timeout=120000)
    if response is None or response.status!=200:
        raise RuntimeError(f"filtered issues navigation returned {getattr(response,'status',None)}")
    actual=urlparse(page.url)
    params=parse_qs(actual.query)
    if params.get("state")!=["opened"] or params.get("not[label_name][]")!=[parsed["excluded_label"]]:
        raise RuntimeError("observed issue navigation lost exclusion predicate")
    return {"route":"gitlab_issues_excluding_label","target":target,
            "observed_url":page.url,"status":response.status,
            "filter":parsed}

async def run(intent,start_url,out):
    if not start_url.startswith("__GITLAB__"):
        raise ValueError("GitLab start URL required")
    out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context(record_har_path=str(out/"network.har"),record_har_mode="full")
        page=await context.new_page()
        try:
            evidence=await navigate(page,intent)
        finally:
            await context.close()
            await browser.close()
    response={"task_type":"NAVIGATE","status":"SUCCESS",
              "retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--intent",required=True)
    ap.add_argument("--start-url",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    asyncio.run(run(a.intent,a.start_url,Path(a.output_dir)))

if __name__=="__main__":
    main()
