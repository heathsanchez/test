#!/usr/bin/env python3
"""Blind Shopping→Reddit review evidence composition.

Runtime authority: natural-language instruction and starting URL only.
Shopping observations are collected from the rendered product/reviews pages.
Reddit mutation occurs once, using the verified post-submit primitive; the
network HAR and independent postcondition remain the external proof boundary.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import quote,urljoin,urlparse

from playwright.async_api import async_playwright
from webarena_shopping_low_reviews import collect_reviews,clean as normalize_space
from webarena_reddit_forum_resolver import resolve_forum
from webarena_reddit_submit_v3 import AUTH,submit
from webarena_product_name_match import select_observed_product

SHOP="http://localhost:7770"
REDDIT="http://localhost:9999"


def compact(value):
    return re.sub(r"[^a-z0-9]+","",str(value).casefold())


def parse_intent(intent):
    text=normalize_space(str(intent))
    expression=(
        r'Create a post in the (.+?) related discussion forum about (.+?) '
        r'to report customer reviews with ([1-5]) stars? (and less rating|rating) '
        r'from the OneStopShop with the post title "([^"]+)". '
        r'Format the post body as a bullet point list in the same order they appear '
        r'\(md format: - "<review title>"\)\.'
    )
    matched=re.fullmatch(expression,text,re.I)
    if not matched:
        raise ValueError(f"unsupported cross-site review instruction: {text!r}")
    forum,product,stars,mode,title=matched.groups()
    product=normalize_space(product)
    if not compact(product):
        raise ValueError("empty product name")
    if not compact(forum):
        raise ValueError("empty requested forum category")
    # The title must be copied from the authorized instruction, not invented.
    return {
        "forum_description":forum,
        "product":product,
        "stars":int(stars),
        "predicate":"at_most" if mode.casefold().startswith("and less") else "exact",
        "title":title,
    }


def rating_filter(reviews,threshold,predicate):
    if predicate not in ("at_most","exact"):
        raise ValueError(f"unsupported rating operator {predicate!r}")
    if threshold not in range(1,6):
        raise ValueError("rating threshold outside five-star scale")
    seen=set();selected=[]
    for row in reviews:
        stars=float(row["stars"])
        title=normalize_space(str(row["title"]))
        qualifies=stars <= threshold if predicate=="at_most" else abs(stars-threshold)<1e-6
        if qualifies and title and (title,stars) not in seen:
            seen.add((title,stars))
            selected.append({"title":title,"stars":stars})
    return selected


def list_body(selected):
    if not selected:
        raise ValueError("cannot publish an unsupported empty review report")
    return "\n".join(f'- "{row["title"]}"' for row in selected)


async def locate_product(page,product):
    url=SHOP+"/catalogsearch/result/?q="+quote(product)
    reply=await page.goto(url,wait_until="networkidle",timeout=120000)
    if reply is None or reply.status!=200:
        raise RuntimeError("Shopping product search unavailable")
    links=page.locator(".product-item-link")
    observed=[]
    for idx in range(min(await links.count(),120)):
        link=links.nth(idx)
        label=normalize_space(await link.inner_text())
        href=await link.get_attribute("href")
        if not href:
            continue
        destination=urljoin(SHOP,href)
        parsed=urlparse(destination)
        if parsed.hostname!="localhost" or parsed.port!=7770:
            continue
        observed.append({"name":label,"url":destination})
    # A product's displayed title can extend an instruction-derived short
    # name with colour, version or marketing copy. Admit only one uniquely
    # identified ordered-token match; reject competing variants.
    return select_observed_product(product,observed)


async def read_reviews(page,product):
    observed=await locate_product(page,product)
    response=await page.goto(observed["url"],wait_until="networkidle",timeout=120000)
    if response is None or response.status!=200:
        raise RuntimeError("matched product page unavailable")
    review_tab=page.locator("#tab-label-reviews-title")
    if await review_tab.count():
        await review_tab.first.click()
        for _ in range(150):
            if await page.locator(".review-item").count():
                break
            count_label=page.locator(".reviews-actions [itemprop='reviewCount']")
            if await count_label.count():
                if normalize_space(await count_label.first.inner_text())=="0":
                    break
            await page.wait_for_timeout(100)
    reviews=await collect_reviews(page)
    return observed,reviews


async def run(intent,start_url,output_dir):
    if start_url not in ("__SHOPPING__",SHOP):
        raise ValueError("Shopping→Reddit composition needs a Shopping start site")
    parsed=parse_intent(intent)
    output_dir.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        context=await browser.new_context(extra_http_headers=AUTH,
            record_har_path=str(output_dir/"network.har"),record_har_mode="full")
        shopping_page=await context.new_page()
        reddit_page=await context.new_page()
        try:
            product,reviews=await read_reviews(shopping_page,parsed["product"])
            selected=rating_filter(reviews,parsed["stars"],parsed["predicate"])
            body=list_body(selected)
            resolved=await resolve_forum(reddit_page,REDDIT,parsed["forum_description"])
            posted=await submit(reddit_page,REDDIT,{
                "forum":resolved["slug"],"title":parsed["title"],"body":body,
            })
        finally:
            await context.close()
            await browser.close()
    reply={
        "task_type":"MUTATE","status":"SUCCESS",
        "retrieved_data":None,"error_details":None,
    }
    evidence={
        "compiled_from_instruction":parsed,
        "observed_product":product,
        "reviews_seen":len(reviews),
        "qualifying_reviews":selected,
        "observed_forum":resolved,
        "submitted_body":body,
        "postcondition":posted,
    }
    (output_dir/"agent_response.json").write_text(json.dumps(reply,indent=2)+"\n")
    (output_dir/"capability_evidence.json").write_text(
        json.dumps(evidence,indent=2,ensure_ascii=False)+"\n"
    )
    print(json.dumps(evidence,indent=2,ensure_ascii=False))
    return reply


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
