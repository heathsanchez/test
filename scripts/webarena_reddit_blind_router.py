#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

from webarena_reddit_submit_v3 import AUTH, submit
from webarena_reddit_profile_forum_mutations import change_bio, create_forum
from webarena_reddit_forum_resolver import resolve_forum
from webarena_reddit_subscribe import ranked_detail, subscribe
from webarena_reddit_reply import reply_to_submission, reply_to_comment
from webarena_reddit_edit_post import candidates as edit_candidates, edit_post
from webarena_reddit_vote import vote_ranked, vote_by_user

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()

def unplaceholder(url: str, base: str) -> str:
    return str(url).replace("__REDDIT__", base.rstrip("/"))

def quoted(s: str):
    return re.findall(r'"([^"]*)"', s)

async def route(page, base: str, intent: str, start_url: str):
    text=clean(intent)
    low=text.casefold()

    # Action -> action composition: create a post and then reply to that created object.
    m=re.fullmatch(r'Post a review of my recent reading, titled "([^"]+)" in f/([^ ]+) and then comment "([^"]+)" on the created post', text, re.I)
    if m:
        title,forum,comment=m.groups()
        created=await submit(page,base,{"forum":forum,"title":title,"body":None})
        replied=await reply_to_submission(page,comment)
        return {"route":"post_then_comment","created":created,"replied":replied}

    m=re.fullmatch(r'Change my bio to "([^"]+)" in the discussion forum',text,re.I)
    if m:
        return {"route":"change_bio","result":await change_bio(page,base,m.group(1))}

    m=re.fullmatch(r'Create a new forum with name and title "([^"]+)", description "([^"]+)", and sidebar "([^"]+)"',text,re.I)
    if m:
        name,description,sidebar=m.groups()
        return {"route":"create_forum","result":await create_forum(page,base,name,description,sidebar)}

    m=re.fullmatch(r'Subscribe to the "([^"]+)" forum from the page of the (.+?) post in that forum\.',text,re.I)
    if m:
        forum,selector=m.groups()
        resolved=await resolve_forum(page,base,forum)
        ranked=await ranked_detail(page,base,resolved["slug"],selector)
        action=await subscribe(page,resolved["slug"])
        return {"route":"subscribe","forum":resolved,"ranked":ranked,"action":action}

    if low.startswith("reply to "):
        target_url=unplaceholder(start_url,base)
        r=await page.goto(target_url,wait_until="networkidle",timeout=120000)
        if r is None or r.status!=200:
            raise RuntimeError(f"reply start page failed: {target_url}")
        q=quoted(text)
        if not q: raise RuntimeError("reply content missing")
        content=q[-1]
        if re.match(r'Reply to the post on this page',text,re.I):
            action=await reply_to_submission(page,content)
            description="the post"
        else:
            m=re.match(r'Reply to (.+?) in this post with ',text,re.I)
            if not m: raise RuntimeError(f"unparsed reply target: {text}")
            description=m.group(1)
            action=await reply_to_comment(page,description,content)
        return {"route":"reply","start_url":target_url,"description":description,"action":action}

    m=re.fullmatch(r'Edit my post on (.+?) by adding a line to the body that says "([^"]+)"',text,re.I)
    if m:
        wanted,content=m.groups()
        target,ranked=await edit_candidates(page,base,wanted)
        action=await edit_post(page,target,content)
        return {"route":"edit_post","wanted":wanted,"target":target,"candidates":ranked,"action":action}

    m=re.fullmatch(r'Upvote the newest post in the (.+?) forum',text,re.I)
    if m:
        resolved=await resolve_forum(page,base,m.group(1))
        selected,events=await vote_ranked(page,base,resolved["slug"],f'/f/{resolved["slug"]}/new',1,1)
        return {"route":"vote_newest","forum":resolved,"selected":selected,"events":events}

    m=re.fullmatch(r'(Like|DisLike) all submissions created by ([^ ]+) in forum (.+)',text,re.I)
    if m:
        verb,user,forum=m.groups()
        direction=-1 if verb.casefold()=="dislike" else 1
        resolved=await resolve_forum(page,base,forum)
        selected,events=await vote_by_user(page,base,resolved["slug"],user,direction)
        return {"route":"vote_by_user","forum":resolved,"user":user,"direction":direction,"selected":selected,"events":events}

    # Explicit-forum post variants.
    m=re.fullmatch(r'Create a post in f/([^\.]+)\. Title it "([^"]+)" and in post details ask "([^"]+)"',text,re.I)
    if m:
        forum,title,body=m.groups()
        return {"route":"post_explicit","action":await submit(page,base,{"forum":forum,"title":title,"body":body})}

    m=re.fullmatch(r'Post a notice in f/([^ ]+) titled "([^"]+)"\. Set post details to "([^"]+)"',text,re.I)
    if m:
        forum,title,body=m.groups()
        return {"route":"post_explicit","action":await submit(page,base,{"forum":forum,"title":title,"body":body})}

    m=re.fullmatch(r'Post in (.+?) forum with title "([^"]+)"',text,re.I)
    if m:
        forum,title=m.groups()
        return {"route":"post_explicit","action":await submit(page,base,{"forum":forum,"title":title,"body":None})}

    m=re.fullmatch(r'Post a notice in (.+?) forum titled "([^"]+)"\. Set post details to "([^"]+)"',text,re.I)
    if m:
        forum,title,body=m.groups()
        resolved=await resolve_forum(page,base,forum)
        return {"route":"post_resolved","forum":resolved,"action":await submit(page,base,{"forum":resolved["slug"],"title":title,"body":body})}

    # Semantic forum selection variants.
    m=re.fullmatch(r'Create a post in the most appropriate forum\. Title it "([^"]+)" and in post details ask "([^"]+)"',text,re.I)
    if m:
        title,body=m.groups()
        resolved=await resolve_forum(page,base,title+" "+body)
        return {"route":"semantic_post","forum":resolved,"action":await submit(page,base,{"forum":resolved["slug"],"title":title,"body":body})}

    m=re.fullmatch(r'Ask for advice in a forum for relations\. Title it "([^"]+)" and in post details ask "([^"]+)"',text,re.I)
    if m:
        title,body=m.groups()
        resolved=await resolve_forum(page,base,"relations relationship advice")
        return {"route":"semantic_post","forum":resolved,"action":await submit(page,base,{"forum":resolved["slug"],"title":title,"body":body})}

    m=re.fullmatch(r'Create a discussion post titled "([^"]+)" in a relevant forum and ask users for their opinions with the simple prompt, "([^"]+)"',text,re.I)
    if m:
        title,body=m.groups()
        resolved=await resolve_forum(page,base,title)
        return {"route":"semantic_post","forum":resolved,"action":await submit(page,base,{"forum":resolved["slug"],"title":title,"body":body})}

    m=re.fullmatch(r'Post my question with the title "([^"]+)", in a forum where I\'m likely to get an answer',text,re.I)
    if m:
        title=m.group(1)
        resolved=await resolve_forum(page,base,title)
        return {"route":"semantic_post","forum":resolved,"action":await submit(page,base,{"forum":resolved["slug"],"title":title,"body":None})}

    raise RuntimeError(f"no blind route for intent: {text}")

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--intent",required=True)
    ap.add_argument("--start-url",required=True)
    ap.add_argument("--base-url",default="http://localhost:9999")
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    har=out/"network.har"
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        ctx=await browser.new_context(extra_http_headers=AUTH,record_har_path=str(har),record_har_mode="full")
        page=await ctx.new_page()
        evidence=await route(page,a.base_url.rstrip("/"),a.intent,a.start_url)
        await ctx.close(); await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS","retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(json.dumps({"intent":a.intent,"start_url":a.start_url,**evidence},indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"intent":a.intent,"start_url":a.start_url,**evidence},indent=2,ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
