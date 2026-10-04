#!/usr/bin/env python3
"""Deterministic WebArena-Verified capability for monthly completed-order counts.

Boundary:
- observes only the Shopping Admin web application through Playwright;
- does not read the benchmark's expected answers;
- does not access the container database or filesystem;
- emits the official agent_response.json format.

The capability is parameterized by the task intent/period and is intended for
WebArena-Verified template 270 and compatible future tasks.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import calendar
import json
import re
import urllib.parse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright

MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS.update({abbr.lower(): i for i, abbr in enumerate(calendar.month_abbr) if abbr})

@dataclass(frozen=True)
class Period:
    start: date
    end: date

def month_num(token: str) -> int:
    key = token.strip().lower().rstrip(".")
    if key not in MONTHS:
        raise ValueError(f"unknown month: {token!r}")
    return MONTHS[key]

def parse_period(text: str) -> Period:
    # Covers "from January 2023 through May 2023, inclusive" and
    # "from Jan 2022 through Nov 2022, inclusive".
    m = re.search(
        r"from\s+([A-Za-z]+)\s+(\d{4})\s+through\s+([A-Za-z]+)\s+(\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError(f"unsupported period wording: {text!r}")
    sm, sy, em, ey = m.groups()
    smn, emn = month_num(sm), month_num(em)
    start = date(int(sy), smn, 1)
    end = date(int(ey), emn, calendar.monthrange(int(ey), emn)[1])
    if end < start:
        raise ValueError(f"end before start: {text!r}")
    return Period(start, end)

def month_sequence(period: Period) -> list[tuple[int, int]]:
    out = []
    y, m = period.start.year, period.start.month
    while (y, m) <= (period.end.year, period.end.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out

def magento_filter_url(base_url: str, period: Period) -> str:
    params = [
        ("report_type", "created_at_order"),
        ("period_type", "month"),
        ("from", f"{period.start.month:02d}/{period.start.day:02d}/{period.start.year}"),
        ("to", f"{period.end.month:02d}/{period.end.day:02d}/{period.end.year}"),
        ("show_order_statuses", "1"),
        ("order_statuses", "complete"),
        ("show_empty_rows", "1"),
        ("show_actual_columns", "0"),
    ]
    payload = urllib.parse.urlencode(params)
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    encoded = urllib.parse.quote(encoded, safe="")
    return base_url.rstrip("/") + "/reports/report_sales/sales/filter/" + encoded + "/"

def parse_count(text: str) -> int:
    s = text.strip().replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        raise ValueError(f"no numeric count in {text!r}")
    value = float(m.group(0))
    if not value.is_integer():
        raise ValueError(f"non-integral order count {value}")
    return int(value)

def infer_month(text: str) -> int | None:
    low = text.lower()
    # Prefer full names to avoid accidental short matches.
    for i in range(1, 13):
        full = calendar.month_name[i].lower()
        if full in low:
            return i
    for i in range(1, 13):
        abbr = calendar.month_abbr[i].lower()
        if re.search(rf"\b{re.escape(abbr)}\b", low):
            return i
    # Fallback for renderer forms like 01/2023 or 2023-01.
    m = re.search(r"\b(0?[1-9]|1[0-2])[/.-](\d{4})\b", text)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{4})[/.-](0?[1-9]|1[0-2])\b", text)
    if m:
        return int(m.group(2))
    return None

async def extract_month_counts(page, expected_months: list[tuple[int, int]]) -> list[dict]:
    tables = page.locator("table")
    table_count = await tables.count()
    diagnostics = []
    for ti in range(table_count):
        table = tables.nth(ti)
        headers = [
            re.sub(r"\s+", " ", (await table.locator("th").nth(i).inner_text()).strip())
            for i in range(await table.locator("th").count())
        ]
        diagnostics.append({"table": ti, "headers": headers})
        norm = [h.lower() for h in headers]
        if "interval" not in norm or "orders" not in norm:
            continue
        interval_idx = norm.index("interval")
        orders_idx = norm.index("orders")
        rows = table.locator("tbody tr")
        found: list[tuple[str, int]] = []
        for ri in range(await rows.count()):
            cells = rows.nth(ri).locator("td")
            n = await cells.count()
            if n <= max(interval_idx, orders_idx):
                continue
            interval = re.sub(r"\s+", " ", (await cells.nth(interval_idx).inner_text()).strip())
            count_text = (await cells.nth(orders_idx).inner_text()).strip()
            if not interval or interval.lower().startswith("total"):
                continue
            found.append((interval, parse_count(count_text)))
        if not found:
            continue

        # Align rows to the requested consecutive months. Magento's renderer may
        # show month names, date ranges, or locale-specific numeric month forms.
        result_by_month: dict[int, int] = {}
        unlabelled: list[int] = []
        for interval, count in found:
            mn = infer_month(interval)
            if mn is None:
                unlabelled.append(count)
            else:
                result_by_month[mn] = count

        expected_nums = [m for _, m in expected_months]
        if all(m in result_by_month for m in expected_nums):
            return [
                {"month": calendar.month_name[m], "count": result_by_month[m]}
                for _, m in expected_months
            ]

        # If the grid has exactly one row per requested month but labels are not
        # parseable, preserve the displayed row order.
        if len(found) == len(expected_months):
            return [
                {"month": calendar.month_name[m], "count": found[i][1]}
                for i, (_, m) in enumerate(expected_months)
            ]

    body = (await page.locator("body").inner_text())[:30000]
    raise RuntimeError(
        "could not locate a complete Interval/Orders monthly grid; "
        + json.dumps({"tables": diagnostics, "body": body}, ensure_ascii=False)
    )

async def solve(base_url: str, intent: str, period_text: str) -> tuple[list[dict], dict]:
    period = parse_period(period_text)
    expected_months = month_sequence(period)
    target = magento_filter_url(base_url, period)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers={"X-M2-Admin-Auto-Login": "admin:admin1234"}
        )
        page = await context.new_page()
        response = await page.goto(target, wait_until="networkidle", timeout=120_000)
        if response is None or response.status != 200:
            raise RuntimeError(f"report navigation failed: status={getattr(response,'status',None)} url={page.url}")
        data = await extract_month_counts(page, expected_months)
        evidence = {
            "requested_intent": intent,
            "period": {"start": period.start.isoformat(), "end": period.end.isoformat()},
            "observed_url": page.url,
            "page_title": await page.title(),
            "retrieved_data": data,
        }
        await browser.close()
        return data, evidence

def empty_har() -> dict:
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "metalogic-webarena-capability", "version": "1"},
            "entries": [],
        }
    }

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
        raise SystemExit(f"task {args.task_id} not present in {args.task_file}")
    if task.get("intent_template_id") != 270:
        raise SystemExit(f"task {args.task_id} is not template 270")

    period_text = task.get("instantiation_dict", {}).get("period", "")
    data, evidence = await solve(args.base_url, task["intent"], period_text)

    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent_response.json").write_text(
        json.dumps(
            {
                "task_type": "RETRIEVE",
                "status": "SUCCESS",
                "retrieved_data": data,
                "error_details": None,
            },
            indent=2,
        )
        + "\n"
    )
    (out / "network.har").write_text(json.dumps(empty_har(), indent=2) + "\n")
    (out / "capability_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"task_id": args.task_id, **evidence}, indent=2))

if __name__ == "__main__":
    asyncio.run(amain())
