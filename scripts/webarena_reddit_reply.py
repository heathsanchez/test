#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright
from webarena_reddit_submit_v3 import AUTH

def clean(s): return re.sub(r"\s+"," ",str(s)).strip()
def terms(s):
    stop={"the","a","an","of","in","on","this","reply","post","comment","website"}
    return [x for x in re.findall(r"[a-z0-9]+",clean(s).casefold()) if x not in stop]

def start_url(task,base):
    raw=str(task["start_urls"][0])
    return raw.replace("__REDDIT__",base.rstrip("/"))

async def visible_first(locator):
    for i in range(await locator.count()):
        item=locator.nth(i)
        try:
            if await item.is_visible(): return item
        except Exception:
            pass
    return None

async def submit_form(field,content):
    await field.fill(content)
    form=field.locator("xpath=ancestor::form[1]")
    if await form.count()==0: raise RuntimeError("reply form missing")
    buttons=form.get_by_role("button")
    btn=None
    for i in range(await buttons.count()):
        b=buttons.nth(i)
        try:
            if await b.is_visible():
                txt=clean(await b.inner_text()).casefold()
                if any(k in txt for k in ("comment","reply","submit","save")):
                    btn=b; break
        except Exception:
            pass
    if btn is None:
        btn=await visible_first(form.locator('button[type="submit"], input[type="submit"]'))
    if btn is None: raise RuntimeError("reply submit control missing")
    await btn.click()
    await field.page.wait_for_load_state("networkidle",timeout=120000)

async def reply_to_submission(page,content):
    field=await visible_first(page.locator('textarea[name^="reply_to_submission_"], input[name^="reply_to_submission_"]'))
    if field is None:
        raise RuntimeError("submission reply field missing")
    name=await field.get_attribute("name")
    await submit_form(field,content)
    return {"target":"submission","field":name,"final_url":page.url}

async def comment_rows(page):
    rows=[]
    comments=page.locator(".comment")
    for i in range(await comments.count()):
        c=comments.nth(i)
        text=clean(await c.inner_text())
        user=c.locator('a[href^="/user/"]').first
        username=clean(await user.inner_text()) if await user.count() else ""
        rows.append({"index":i,"node":c,"text":text,"username":username})
    return rows

def semantic_score(description,row):
    q=terms(description)
    hay=(row["text"]+" "+row["username"]).casefold()
    score=sum(3 for t in q if t in hay)
    if "manager" in description.casefold() and "manager" in hay: score+=8
    if "website" in description.casefold() and any(x in hay for x in ("website","site","bookshop")): score+=4
    return score

async def expose_comment_reply(page,node):
    field=await visible_first(node.locator('textarea[name^="reply_to_comment_"], input[name^="reply_to_comment_"]'))
    if field is not None: return field
    candidates=node.locator('a,button')
    for i in range(await candidates.count()):
        el=candidates.nth(i)
        try:
            if not await el.is_visible(): continue
            txt=clean(await el.inner_text()).casefold()
            if txt=="reply" or txt.startswith("reply "):
                await el.click()
                await page.wait_for_timeout(150)
                field=await visible_first(node.locator('textarea[name^="reply_to_comment_"], input[name^="reply_to_comment_"]'))
                if field is None:
                    field=await visible_first(page.locator('textarea[name^="reply_to_comment_"], input[name^="reply_to_comment_"]'))
                if field is not None: return field
        except Exception:
            continue
    raise RuntimeError("comment reply field missing")

async def reply_to_comment(page,description,content):
    rows=await comment_rows(page)
    if not rows: raise RuntimeError("no comments found")
    d=description.casefold()
    if "first reply" in d:
        target=rows[0]
    else:
        ranked=sorted(((semantic_score(description,r),r) for r in rows),key=lambda z:(-z[0],z[1]["index"]))
        if not ranked or ranked[0][0]<=0:
            raise RuntimeError(f"no semantic comment target for {description!r}")
        target=ranked[0][1]
    field=await expose_comment_reply(page,target["node"])
    name=await field.get_attribute("name")
    await submit_form(field,content)
    return {"target":"comment","comment_index":target["index"],"username":target["username"],"field":name,"final_url":page.url}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task-id",type=int,required=True)
    ap.add_argument("--task-file",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    task=next(t for t in json.loads(Path(a.task_file).read_text()) if int(t["task_id"])==a.task_id)
    if int(task["intent_template_id"])!=23: raise SystemExit("unsupported template")
    inst=task["instantiation_dict"]
    description=str(inst["position_description"])
    content=str(inst["content_description"])
    base=a.base_url.rstrip("/")
    out=Path(a.output_dir)/str(a.task_id); out.mkdir(parents=True,exist_ok=True)
    har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        url=start_url(task,base)
        r=await page.goto(url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200: raise RuntimeError(f"start page failed: {url}")
        if description.strip().casefold()=="the post":
            action=await reply_to_submission(page,content)
        else:
            action=await reply_to_comment(page,description,content)
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    evidence={"task_id":a.task_id,"start_url":url,"description":description,"content":content,"action":action}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
