#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH

async def submit_form(page,form):
    btn=form.get_by_role("button").last
    if await btn.count()==0:
        raise RuntimeError("form submit button missing")
    await btn.click()
    await page.wait_for_load_state("networkidle",timeout=120000)

async def change_bio(page,base,content):
    url=base.rstrip("/")+"/user/MarvelsGrantMan136/edit_biography"
    r=await page.goto(url,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("biography page failed")
    field=page.locator('[name="user_biography[biography]"]').first
    if await field.count()==0: raise RuntimeError("biography field missing")
    form=field.locator("xpath=ancestor::form[1]")
    await field.fill(content)
    await submit_form(page,form)
    return {"action":"change_bio","content":content,"final_url":page.url}

async def create_forum(page,base,name,description,sidebar):
    url=base.rstrip("/")+"/create_forum"
    r=await page.goto(url,wait_until="networkidle",timeout=120000)
    if r is None or r.status!=200: raise RuntimeError("create forum page failed")
    fields={
      "forum[name]":name,
      "forum[title]":name,
      "forum[description]":description,
      "forum[sidebar]":sidebar,
    }
    first=None
    for key,value in fields.items():
        loc=page.locator(f'[name="{key}"]').first
        if await loc.count()==0: raise RuntimeError(f"forum field missing: {key}")
        if first is None: first=loc
        await loc.fill(value)
    form=first.locator("xpath=ancestor::form[1]")
    await submit_form(page,form)
    return {"action":"create_forum","name":name,"description":description,"sidebar":sidebar,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True); ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999"); ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    tid=int(task["intent_template_id"]); inst=task["instantiation_dict"]
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True); har=out/"network.har"
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        if tid==6:
            evidence=await change_bio(page,a.base_url,str(inst["content"]))
        elif tid==7:
            evidence=await create_forum(page,a.base_url,str(inst["name"]),str(inst["description"]),str(inst["sidebar_list"]))
        else:
            raise SystemExit(f"unsupported template {tid}")
        await ctx.close(); await b.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"task_id":a.task_id,**evidence},indent=2)+"\n")
    print(json.dumps({"task_id":a.task_id,**evidence},indent=2))

if __name__=="__main__": asyncio.run(main())
