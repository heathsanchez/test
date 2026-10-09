#!/usr/bin/env python3
"""Navigation to observed Magento storefront search results sorted by intent.

Only the user's instruction and starting site enter this agent. It never
inspects benchmark scoring metadata. Evaluation lives in a separate harness.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

from playwright.async_api import async_playwright

BASE = "http://localhost:7770"


def parse_intent(intent: str) -> dict[str, str]:
    text = re.sub(r"\s+", " ", str(intent)).strip()
    match = re.fullmatch(
        r'Pull up the page with all "([^"]+)" listings sorted by '
        r'(descending price|ascending price|name alphabetically|price)\.',
        text,
        re.IGNORECASE,
    )
    if match is None:
        raise ValueError(f"unsupported catalog search sort intent: {text!r}")
    query, sorting = match.groups()
    query = query.strip()
    if not query:
        raise ValueError("empty product query")
    mode = sorting.casefold()
    return {
        "query": query,
        "field": "name" if mode == "name alphabetically" else "price",
        "direction": "desc" if mode == "descending price" else "asc",
    }


def validate_start(start_url: str):
    if start_url not in ("__SHOPPING__", BASE, BASE + "/"):
        raise ValueError("catalog search sort requires Shopping site as initial location")


def build_url(spec: dict[str, str]) -> str:
    params = {"q": spec["query"], "product_list_order": spec["field"]}
    # The observed Magento price-sort default is descending. Omitting
    # product_list_dir preserves the canonical URL and sort-desc UI state.
    if not (spec["field"] == "price" and spec["direction"] == "desc"):
        params["product_list_dir"] = spec["direction"]
    return BASE + "/catalogsearch/result/index?" + urlencode(params)


async def navigate(page, spec: dict[str, str]) -> dict:
    target = build_url(spec)
    reply = await page.goto(target, wait_until="networkidle", timeout=120000)
    if reply is None or reply.status != 200:
        raise RuntimeError(f"sorted catalog search HTTP {getattr(reply,'status',None)}")
    observed = parse_qs(urlparse(page.url).query)
    expected = {
        "q": [spec["query"]],
        "product_list_order": [spec["field"]],
    }
    if spec["field"] == "price" and spec["direction"] == "desc":
        # The live document, not the URL alone, proves descending order.
        direction = page.locator('a.sorter-action.sort-desc[data-role="direction-switcher"]')
        if await direction.count() == 0:
            raise RuntimeError("Magento did not establish descending price order")
    else:
        expected["product_list_dir"] = [spec["direction"]]
    if any(observed.get(key) != value for key, value in expected.items()):
        raise RuntimeError("sorted search URL did not preserve instruction-derived query and order")
    if any(key not in expected for key in observed):
        raise RuntimeError("sorted search URL unexpectedly changed the query")
    return {
        "capability": "catalog_search_sorted",
        "requested_query": spec["query"],
        "sort_field": spec["field"],
        "sort_direction": spec["direction"],
        "requested_url": target,
        "observed_url": page.url,
        "observed_title": await page.title(),
    }


async def run(intent: str, start_url: str, out: Path):
    validate_start(start_url)
    spec = parse_intent(intent)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            record_har_path=str(out / "network.har"),
            record_har_mode="full",
        )
        page = await context.new_page()
        try:
            evidence = await navigate(page, spec)
        finally:
            await context.close()
            await browser.close()
    result = {"task_type": "NAVIGATE", "status": "SUCCESS",
              "retrieved_data": None, "error_details": None}
    (out / "agent_response.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "capability_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, ensure_ascii=False), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True)
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.intent, args.start_url, Path(args.output_dir)))


if __name__ == "__main__":
    main()
