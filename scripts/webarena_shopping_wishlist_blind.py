#!/usr/bin/env python3
"""Task-ID-blind, fail-closed Shopping wishlist mutation experiment."""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from webarena_shopping_order_history_probe import AUTH_HEADER

BASE="http://localhost:7770"


def normalize(s):
    return re.sub(r"\s+"," ",str(s)).strip().casefold()


def authorize_intent(intent):
    if normalize(intent)!="add the product on the current page to my wishlist":
        raise ValueError(f"unsupported wishlist intent: {intent!r}")


def verify_start_url(start_url):
    if not start_url.startswith("__SHOPPING__"):
        raise ValueError("wishlist requires a Shopping start URL")
    path=start_url.replace("__SHOPPING__","",1)
    if not path.startswith("/") or not path.endswith(".html"):
        raise ValueError("wishlist requires the current product page")
    return BASE+path


async def add_current_product(page, start_url):
    target=verify_start_url(start_url)
    result=await page.goto(target,wait_until="networkidle",timeout=120000)
    if result is None or result.status!=200:
        raise RuntimeError("product detail page unavailable")
    title=page.locator("h1.page-title, h1.product-name").first
    if await title.count()==0:
        raise RuntimeError("product heading missing")
    product=normalize(await title.inner_text())
    if not product:
        raise RuntimeError("product name missing")
    controls=page.locator(
        'a.action.towishlist, button.action.towishlist, '
        'a[data-action="add-to-wishlist"], [data-post*="wishlist/index/add"]'
    )
    usable=None
    for idx in range(await controls.count()):
        candidate=controls.nth(idx)
        if await candidate.is_visible():
            usable=candidate
            break
    if usable is None:
        raise RuntimeError("product wishlist action not visible")
    action_href=await usable.get_attribute("href")
    post_data=await usable.get_attribute("data-post")
    # One action only, with no automatic retry on ambiguous navigation.
    await usable.click(timeout=40000,no_wait_after=True)
    await page.wait_for_load_state("domcontentloaded",timeout=120000)
    target_wishlist=BASE+"/wishlist/index/index/"
    confirmation=await page.goto(target_wishlist,wait_until="networkidle",timeout=120000)
    if confirmation is None or confirmation.status!=200:
        raise RuntimeError("wishlist confirmation page unavailable")
    body=normalize(await page.locator("body").inner_text())
    if product not in body:
        raise RuntimeError(f"product absent from wishlist readback: {product[:120]!r}")
    return {
        "capability":"wishlist_add_current_product",
        "product_name":product,
        "observed_product_url":target,
        "observed_action_href":action_href,
        "observed_data_post":post_data,
        "wishlist_readback_url":page.url,
        "readback_match":True,
    }


async def run(intent,start_url,out):
    authorize_intent(intent)
    out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        context=await browser.new_context(
            extra_http_headers=AUTH_HEADER,
            record_har_path=str(out/"network.har"),
            record_har_mode="full",
        )
        page=await context.new_page()
        try:
            evidence=await add_current_product(page,start_url)
        finally:
            await context.close()
            await browser.close()
    response={"task_type":"MUTATE","status":"SUCCESS",
              "retrieved_data":None,"error_details":None}
    (out/"agent_response.json").write_text(json.dumps(response,indent=2)+"\n")
    (out/"capability_evidence.json").write_text(
        json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence,ensure_ascii=False))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--intent",required=True)
    ap.add_argument("--start-url",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
