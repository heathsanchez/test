#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH
from webarena_reddit_recent_comments import resolve_forum

async def ranked_detail(page, base, slug, selector):
    s=selector.casefold()
    if "controversial" in s:
        routes=[f"/f/{slug}/controversial", f"/f/{slug}"]
    elif "commented" in s:
        routes=[f"/f/{slug}/top?sort=comments&t=all", f"/f/{slug}/top?t=all", f"/f/{slug}"]
    else:
        routes=[f"/f/{slug}/top?t=all", f"/f/{slug}/top", f"/f/{slug}"]
    for route in routes:
        r=await page.goto(base+route,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200:
            continue
        post=page.locator(".submission").first
        if await post.count()==0:
            continue
        links=post.locator("a.text-sm")
        for i in range(await links.count()):
            href=await links.nth(i).get_attribute("href")
            if href and f"/f/{slug}/" in href:
                rr=await page.goto(urljoin(base,href),wait_until="networkidle",timeout=120000)
                if rr is not None and rr.status==200:
                    return {"route":route,"detail_url":page.url}
    raise RuntimeError(f"could not reach ranked post for {slug!r} / {selector!r}")

async def subscribe(page, slug):
    form=page.locator(f'form.subscribe-form[data-forum="{slug}"]').first
    if await form.count()==0:
        form=page.locator('form.subscribe-form').first
    if await form.count()==0:
        raise RuntimeError("subscribe form missing")
    btn=form.locator("button.subscribe-button").first
    if await btn.count()==0:
        raise RuntimeError("subscribe button missing")
    label=(await btn.inner_text()).strip()
    if "unsubscribe" in label.casefold():
        return {"already_subscribed":True,"label":label,"final_url":page.url}
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)
    return {"already_subscribed":False,"label":label,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=4:
        raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    forum=str(inst["forum"])
    selector=str(inst["post_selector"])
    base=a.base_url.rstrip("/")
    out=Path(a.output_dir)/str(a.task_id)
    out.mkdir(parents=True,exist_ok=True)
    har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        resolved=await resolve_forum(page,base,forum)
        ranked=await ranked_detail(page,base,resolved["slug"],selector)
        action=await subscribe(page,resolved["slug"])
        await ctx.close()
        await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"forum":forum,"selector":selector,"resolved":resolved,"ranked":ranked,"action":action}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
