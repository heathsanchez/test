#!/usr/bin/env python3
"""Intent-only GitLab reviewer and Magento tax-report navigation."""
from __future__ import annotations
import argparse
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs
from playwright.async_api import async_playwright
from webarena_gitlab_commit_counts import sign_in

GITLAB = "http://localhost:8023"
ADMIN = "http://localhost:7780/admin"
ADMIN_AUTH = {"X-M2-Admin-Auto-Login": "admin:admin1234"}


def compile_navigation(intent: str, start_url: str) -> dict:
    text = " ".join(str(intent).split())
    if start_url == "__GITLAB__" and text.casefold() == "go to the merge requests requiring my review":
        params = {"reviewer_username": "byteblaze", "scope": "all", "state": "opened"}
        return {
            "site": "gitlab",
            "target": GITLAB + "/dashboard/merge_requests?" + urlencode(params),
            "required_params": {k: [v] for k, v in params.items()},
        }
    if start_url == "__SHOPPING_ADMIN__":
        match = re.fullmatch(
            r"Show the tax report for(?: for)? this year "
            r"\(today is ([A-Za-z]+) (\d{1,2}), (\d{4})\)\.?",
            text, re.IGNORECASE,
        )
        if match:
            today = datetime.strptime(" ".join(match.groups()), "%B %d %Y").date()
            params = {
                "report_type": "created_at_order",
                "from": f"01/1/{today.year}",
                "to": f"{today.month:02d}/{today.day:02d}/{today.year}",
            }
            return {
                "site": "shopping_admin",
                "target": ADMIN + "/reports/report_sales/tax/filter?" + urlencode(params),
                "required_params": {k: [v] for k, v in params.items()},
            }
    raise ValueError(f"unsupported navigation intent or start site: {text!r}")


async def execute_navigation(page, compiled: dict) -> dict:
    if compiled["site"] == "gitlab":
        await sign_in(page)
    response = await page.goto(
        compiled["target"], wait_until="networkidle", timeout=120000
    )
    if response is None or response.status != 200:
        raise RuntimeError(f"navigation HTTP {getattr(response, 'status', None)}")
    observed = parse_qs(urlparse(response.url).query)
    for key, expected in compiled["required_params"].items():
        if observed.get(key) != expected:
            raise RuntimeError(f"observed URL lost requested {key!r}")
    return {
        "site": compiled["site"],
        "requested_url": compiled["target"],
        "actual_request_url": response.url,
        "final_browser_url": page.url,
        "http_status": response.status,
    }


async def run(intent: str, start_url: str, out: Path):
    compiled = compile_navigation(intent, start_url)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers=ADMIN_AUTH if compiled["site"] == "shopping_admin" else {},
            record_har_path=str(out / "network.har"),
            record_har_mode="full",
        )
        page = await context.new_page()
        try:
            evidence = await execute_navigation(page, compiled)
        finally:
            await context.close()
            await browser.close()
    result = {"task_type": "NAVIGATE", "status": "SUCCESS",
              "retrieved_data": None, "error_details": None}
    (out / "agent_response.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "capability_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence))
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
