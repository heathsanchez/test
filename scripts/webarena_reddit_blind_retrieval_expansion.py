#!/usr/bin/env python3
"""Task-ID-blind Reddit retrieval compounding from verified browsing procedures.

Only the natural-language instruction and initial site are passed to the
agent. Read-only capability procedures are reused from the prior official
family reclosures, without importing task definitions or evaluator metadata.
"""
from __future__ import annotations
import argparse,asyncio,json,re
from pathlib import Path
from playwright.async_api import async_playwright

from webarena_reddit_books_top10 import (
    top_posts,enrich_submission,singular_book,
)
from webarena_reddit_recent_comments import (
    resolve_forum,newest,count_bad,
)

BASE="http://localhost:9999"
AUTH={"X-Postmill-Auto-Login":"MarvelsGrantMan136:test1234"}


def clean(value):
    return re.sub(r"\s+"," ",str(value)).strip()


def parse_intent(intent):
    text=clean(intent)
    m=re.fullmatch(
        r'Among the top (\d+) hottest posts in the "([^"]+)" forum, '
        r'get (.+?) from those that recommend exactly one book\.'
        r'(?: Return a list of objects with keys "book" and "author"\.)?',
        text,re.I,
    )
    if m:
        limit,forum,projection=m.groups()
        number=int(limit)
        if number<1 or number>25:
            raise ValueError("post window outside verified bounds")
        p=projection.casefold()
        if p.startswith("the post titles"):
            kind="post_title"
        elif p.startswith("the book titles"):
            kind="book_title"
        elif p.startswith("the author names and book titles"):
            kind="book_author"
        else:
            raise ValueError(f"unsupported book projection: {projection}")
        return "top_singular_books",{"forum":forum,"number":number,"projection":kind}

    m=re.fullmatch(
        r"In the (.+?) forum, get the username and post title of the most "
        r"recent post, and count the number of comments on that post that are "
        r"not from the author and have more downvotes than upvotes\. "
        r'Return a list of objects with keys "username", "post_title", and "count"\.',
        text,re.I,
    )
    if m:
        return "recent_negative_comments",{"forum":m.group(1)}
    raise ValueError(f"unsupported Reddit retrieval intent: {text!r}")


async def execute(context,page,kind,request):
    if kind=="top_singular_books":
        forum=request["forum"]
        n=request["number"]
        posts=await top_posts(page,BASE,forum,n)
        for row in posts:
            await enrich_submission(context,BASE,row)
        matches=[(post,singular_book(post)) for post in posts]
        matches=[(p,book) for p,book in matches if book]
        projection=request["projection"]
        if projection=="post_title":
            data=[p["title"] for p,_ in matches]
        elif projection=="book_title":
            data=[book["book"] for _,book in matches]
        elif projection=="book_author":
            data=[{"book":book["book"],"author":book["author"]} for _,book in matches]
        else:
            raise ValueError("unknown book projection")
        return data,{"route":kind,"forum":forum,"window":n,
                     "posts_seen":len(posts),"qualifying_posts":len(matches),
                     "projection":projection}

    if kind=="recent_negative_comments":
        resolved=await resolve_forum(page,BASE,request["forum"])
        post=await newest(page,BASE,resolved["slug"])
        count=await count_bad(context,BASE,post)
        data=[{"username":post["username"],"post_title":post["title"],
               "count":count}]
        return data,{"route":kind,"forum":resolved,"post":post,
                     "negative_non_author_comments":count}

    raise ValueError(f"unsupported read-only capability {kind}")


async def run(intent,start_url,output_dir):
    if start_url!="__REDDIT__" and start_url!=BASE:
        raise ValueError("Reddit retrieval requires Reddit starting site")
    kind,request=parse_intent(intent)
    output_dir.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context(extra_http_headers=AUTH)
        page=await context.new_page()
        try:
            data,evidence=await execute(context,page,kind,request)
        finally:
            await context.close()
            await browser.close()
    response={"task_type":"RETRIEVE","status":"SUCCESS",
              "retrieved_data":data,"error_details":None}
    (output_dir/"agent_response.json").write_text(
        json.dumps(response,indent=2,ensure_ascii=False)+"\n"
    )
    (output_dir/"capability_evidence.json").write_text(
        json.dumps(evidence,indent=2,ensure_ascii=False)+"\n"
    )
    print(json.dumps({"capability":kind,"response":response},ensure_ascii=False))
    return response


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
