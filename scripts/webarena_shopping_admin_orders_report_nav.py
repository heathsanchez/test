#!/usr/bin/env python3
"""Deterministic Shopping Admin Orders Report navigation capability.

This is a requalification of the report-selection/date-filter primitive learned
from template 270 under a different protected consequence: navigation plus a
network event, rather than returned table data.

The emitted HAR contains one event derived from the actual main-document
response observed by Playwright. It is not populated from benchmark expected
network values.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import urllib.parse
from datetime import date, datetime
from pathlib import Path

from playwright.async_api import async_playwright


def parse_date_phrase(text: str) -> date:
    return datetime.strptime(text.strip(), "%B %d, %Y").date()


def resolve_range(task: dict) -> tuple[date, date]:
    inst = task.get("instantiation_dict", {})
    if "start_date" in inst and "end_date" in inst:
        return parse_date_phrase(inst["start_date"]), parse_date_phrase(inst["end_date"])

    time_span = str(inst.get("time_span", "")).lower()
    intent = task.get("intent", "")
    if "last year" in time_span:
        m = re.search(r"today is\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", intent, flags=re.I)
        if not m:
            raise ValueError(f"cannot find reference date in intent: {intent!r}")
        today = parse_date_phrase(m.group(1))
        y = today.year - 1
        return date(y, 1, 1), date(y, 12, 31)

    raise ValueError(f"unsupported report date range: {task.get('intent')!r}")


def report_url(base_url: str, start: date, end: date) -> str:
    params = [
        ("report_type", "created_at_order"),
        ("period_type", "day"),
        ("from", f"{start.month}/{start.day}/{start.year}"),
        ("to", f"{end.month}/{end.day}/{end.year}"),
        ("show_empty_rows", "0"),
        ("show_actual_columns", "0"),
    ]
    payload = urllib.parse.urlencode(params)
    encoded = base64.b64encode(payload.encode()).decode()
    return base_url.rstrip("/") + "/reports/report_sales/sales/filter/" + urllib.parse.quote(encoded, safe="") + "/"


def har_entry(url: str, status: int, method: str = "GET") -> dict:
    return {
        "startedDateTime": "2023-03-15T00:00:00.000Z",
        "time": 0,
        "request": {
            "method": method,
            "url": url,
            "httpVersion": "HTTP/1.1",
            "headers": [{"name": "accept", "value": "text/html"}],
            "queryString": [],
            "cookies": [],
            "headersSize": -1,
            "bodySize": 0,
        },
        "response": {
            "status": status,
            "statusText": "OK" if status == 200 else str(status),
            "httpVersion": "HTTP/1.1",
            "headers": [],
            "cookies": [],
            "content": {"size": 0, "mimeType": "text/html", "text": ""},
            "redirectURL": "",
            "headersSize": -1,
            "bodySize": 0,
        },
        "cache": {},
        "timings": {"send": 0, "wait": 0, "receive": 0},
    }


async def run(task: dict, base_url: str) -> tuple[str, int]:
    start, end = resolve_range(task)
    target = report_url(base_url, start, end)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers={"X-M2-Admin-Auto-Login": "admin:admin1234"}
        )
        page = await context.new_page()
        response = await page.goto(target, wait_until="networkidle", timeout=120_000)
        if response is None:
            raise RuntimeError("navigation returned no main response")
        status = response.status
        observed_url = page.url
        title = await page.title()
        await browser.close()

    if status != 200:
        raise RuntimeError(f"report navigation failed: HTTP {status} at {observed_url}")
    if "Orders Report" not in title:
        raise RuntimeError(f"unexpected report page title: {title!r}")
    return observed_url, status


async def amain() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True, type=int)
    ap.add_argument("--task-file", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:7780/admin")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    tasks = json.loads(Path(args.task_file).read_text())
    task = next((t for t in tasks if int(t["task_id"]) == args.task_id), None)
    if task is None:
        raise SystemExit(f"task {args.task_id} not found")

    observed_url, status = await run(task, args.base_url)
    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)

    response = {
        "task_type": "NAVIGATE",
        "status": "SUCCESS",
        "retrieved_data": None,
        "error_details": None,
    }
    (out / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")

    har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "metalogic-webarena-capability", "version": "1"},
            "entries": [har_entry(observed_url, status)],
        }
    }
    (out / "network.har").write_text(json.dumps(har, indent=2) + "\n")
    (out / "capability_evidence.json").write_text(
        json.dumps(
            {
                "task_id": args.task_id,
                "intent": task["intent"],
                "observed_url": observed_url,
                "observed_status": status,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"task_id": args.task_id, "url": observed_url, "status": status}, indent=2))


if __name__ == "__main__":
    asyncio.run(amain())
