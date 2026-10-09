#!/usr/bin/env python3
"""Four-site blind wrapper with reusable read-only Shopping capabilities.

The agent receives only the instruction and starting URL. Official evaluator,
template, task identity and instantiation are supplied only to the CI harness.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from webarena_unified_blind_agent import run as run_existing_blind
from webarena_shopping_low_reviews import clean as shop_clean, collect_reviews
from webarena_shopping_admin_monthly_complete import (
    parse_period, month_sequence, magento_filter_url, extract_month_counts,
)
from webarena_shopping_admin_blind_report import parse_report_range, navigate_report

SHOPPING_BASE="http://localhost:7770"
ADMIN_BASE="http://localhost:7780/admin"
ADMIN_AUTH={"X-M2-Admin-Auto-Login":"admin:admin1234"}


def site_from_start(start_url: str) -> str:
    if start_url.startswith("__SHOPPING_ADMIN__"):
        return "shopping_admin"
    if start_url.startswith("__SHOPPING__"):
        return "shopping"
    parsed=urlparse(start_url)
    if parsed.hostname=="localhost" and parsed.port==7780:
        return "shopping_admin"
    if parsed.hostname=="localhost" and parsed.port==7770:
        return "shopping"
    from webarena_unified_blind_agent import site_from_start as existing
    return existing(start_url)


def actual_start(start_url: str) -> str:
    if start_url.startswith("__SHOPPING_ADMIN__"):
        return start_url.replace("__SHOPPING_ADMIN__",ADMIN_BASE,1)
    if start_url.startswith("__SHOPPING__"):
        return start_url.replace("__SHOPPING__",SHOPPING_BASE,1)
    return start_url


def classify_readonly_intent(site: str,intent: str) -> str:
    text=re.sub(r"\s+"," ",intent).strip()
    if site=="shopping" and text.casefold()=="get all review titles with 2 stars or below for the product on the current page.":
        return "shopping_low_reviews"
    if site=="shopping_admin" and text.casefold().startswith("get the monthly count of completed orders "):
        parse_period(text)
        return "admin_monthly_complete_orders"
    if site=="shopping_admin" and text.casefold().startswith("show the "):
        parse_report_range(text)
        return "admin_orders_report_navigation"
    raise ValueError(f"unsupported {site} instruction: {text!r}")


async def execute_readonly(site: str,intent: str,start_url: str,output_dir: Path):
    capability=classify_readonly_intent(site,intent)
    target=actual_start(start_url)
    if site=="shopping" and urlparse(target).path in ("","/"):
        raise ValueError("shopping review retrieval requires the current product URL")
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        context_options={
            "extra_http_headers":ADMIN_AUTH if site=="shopping_admin" else {}
        }
        if capability=="admin_orders_report_navigation":
            context_options["record_har_path"]=str(output_dir/"network.har")
            context_options["record_har_mode"]="full"
        context=await browser.new_context(**context_options)
        page=await context.new_page()
        try:
            if capability=="shopping_low_reviews":
                response=await page.goto(target,wait_until="networkidle",timeout=120000)
                if response is None or response.status!=200:
                    raise RuntimeError("product page failed")
                tab=page.locator("#tab-label-reviews-title")
                if await tab.count():
                    await tab.click()
                    for _ in range(120):
                        if await page.locator(".review-item").count()>0:
                            break
                        count_text=page.locator(".reviews-actions [itemprop='reviewCount']")
                        if await count_text.count() and shop_clean(await count_text.inner_text())=="0":
                            break
                        await page.wait_for_timeout(100)
                reviews=await collect_reviews(page)
                titles=[review["title"] for review in reviews if review["stars"]<=2.0]
                result={
                    "task_type":"RETRIEVE",
                    "status":"SUCCESS" if titles else "NOT_FOUND_ERROR",
                    "retrieved_data":titles if titles else None,
                    "error_details":None,
                }
                evidence={
                    "capability":capability,"observed_url":page.url,
                    "reviews":reviews,
                }
                return result,evidence

            if capability=="admin_orders_report_navigation":
                observed=await navigate_report(page,intent,ADMIN_BASE)
                return {
                    "task_type":"NAVIGATE","status":"SUCCESS",
                    "retrieved_data":None,"error_details":None,
                },observed

            period=parse_period(intent)
            target=magento_filter_url(ADMIN_BASE,period)
            response=await page.goto(target,wait_until="networkidle",timeout=120000)
            if response is None or response.status!=200:
                raise RuntimeError(f"admin monthly report HTTP {getattr(response,'status',None)}")
            expected_months=month_sequence(period)
            data=await extract_month_counts(page,expected_months)
            result={
                "task_type":"RETRIEVE","status":"SUCCESS",
                "retrieved_data":data,"error_details":None,
            }
            evidence={
                "capability":capability,"period_start":period.start.isoformat(),
                "period_end":period.end.isoformat(),
                "observed_url":page.url,"months":len(data),
            }
            return result,evidence
        finally:
            await context.close()
            await browser.close()


async def run(intent: str,start_url: str,output_dir: Path):
    site=site_from_start(start_url)
    if site not in ("shopping","shopping_admin"):
        return await run_existing_blind(intent,start_url,output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    result,evidence=await execute_readonly(site,intent,start_url,output_dir)
    (output_dir/"agent_response.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    )
    (output_dir/"capability_evidence.json").write_text(
        json.dumps({"site":site,"intent":intent,"start_url":start_url,**evidence},
                   indent=2,ensure_ascii=False)+"\n"
    )
    print(json.dumps({"site":site,"response":result,"evidence":evidence},
                     ensure_ascii=False))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--intent",required=True)
    parser.add_argument("--start-url",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    asyncio.run(run(args.intent,args.start_url,Path(args.output_dir)))


if __name__=="__main__":
    main()
