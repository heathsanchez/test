#!/usr/bin/env python3
"""Single-feedback semantic transfer experiment for WebArena-Verified template 367.

The candidate policy is deliberately restricted to one unresolved semantic bit:
whether "last N orders" means newest-first or oldest-first in the observed order grid.

The candidate never reads evaluator expected answers. A workflow evaluates two candidate
orientations on exactly one training task (193), freezes the unique verifier-selected
orientation, and only then executes untouched sibling tasks 194-197.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from playwright.async_api import async_playwright


ORDER_GRID = "/sales/order/"


def parse_currency(text: str) -> Decimal:
    m = re.search(r"-?[0-9][0-9,]*(?:\.[0-9]+)?", text.replace("\u00a0", " "))
    if not m:
        raise ValueError(f"no currency value found in {text!r}")
    return Decimal(m.group(0).replace(",", ""))


def cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def status_class(text: str) -> str:
    s = re.sub(r"\s+", " ", text).strip().lower()
    if s in {"canceled", "cancelled"}:
        return "cancelled"
    if s in {"complete", "completed"}:
        return "completed"
    if s == "pending":
        return "pending"
    return "other"


def parse_query(intent: str) -> dict:
    low = intent.lower()

    m = re.search(r"total payment amount of the last\s+(\d+)\s+completed orders", low)
    if m:
        return {"mode": "sum", "n": int(m.group(1)), "predicate": "completed"}

    m = re.search(r"total payment amount of the last\s+(\d+)\s+pending orders", low)
    if m:
        return {"mode": "sum", "n": int(m.group(1)), "predicate": "pending"}

    m = re.search(r"total payment amount of the last\s+(\d+)\s+non[- ]cancelled orders", low)
    if m:
        return {"mode": "sum", "n": int(m.group(1)), "predicate": "non_cancelled"}

    m = re.search(
        r"payment difference between the last\s+(\d+)\s+cancelled orders and the last\s+(\d+)\s+completed orders",
        low,
    )
    if m:
        return {
            "mode": "difference",
            "cancelled_n": int(m.group(1)),
            "completed_n": int(m.group(2)),
        }

    raise ValueError(f"unsupported payment query: {intent!r}")


async def find_order_grid(page):
    tables = page.locator("table:visible")
    for i in range(await tables.count()):
        table = tables.nth(i)
        headers = []
        th = table.locator("thead th")
        for j in range(await th.count()):
            headers.append(re.sub(r"\s+", " ", (await th.nth(j).inner_text()).strip()))
        lower = [x.lower() for x in headers]
        if (
            "purchase date" in lower
            and "grand total (purchased)" in lower
            and "status" in lower
            and await table.locator("tbody tr").count() > 0
        ):
            return table, headers
    raise RuntimeError("visible Magento order grid not found")


async def observe_rows(base_url: str) -> tuple[list[dict], dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers={"X-M2-Admin-Auto-Login": "admin:admin1234"}
        )
        page = await context.new_page()
        response = await page.goto(
            base_url.rstrip("/") + ORDER_GRID,
            wait_until="networkidle",
            timeout=120_000,
        )
        if response is None or response.status != 200:
            raise RuntimeError(f"order grid navigation failed: {getattr(response, 'status', None)}")

        table, headers = await find_order_grid(page)
        lower = [h.lower() for h in headers]
        id_idx = lower.index("id") if "id" in lower else None
        total_idx = lower.index("grand total (purchased)")
        status_idx = lower.index("status")
        date_idx = lower.index("purchase date")

        rows_out = []
        rows = table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells = rows.nth(ri).locator("td")
            n = await cells.count()
            if n <= max(total_idx, status_idx, date_idx):
                continue
            order_id = (
                re.sub(r"\s+", " ", (await cells.nth(id_idx).inner_text()).strip())
                if id_idx is not None and id_idx < n
                else f"row-{ri}"
            )
            status_txt = re.sub(r"\s+", " ", (await cells.nth(status_idx).inner_text()).strip())
            total_txt = re.sub(r"\s+", " ", (await cells.nth(total_idx).inner_text()).strip())
            date_txt = re.sub(r"\s+", " ", (await cells.nth(date_idx).inner_text()).strip())
            rows_out.append(
                {
                    "id": order_id,
                    "purchase_date": date_txt,
                    "status_text": status_txt,
                    "status_class": status_class(status_txt),
                    "payment": str(parse_currency(total_txt)),
                }
            )

        evidence = {
            "observed_url": page.url,
            "page_title": await page.title(),
            "rows_observed": len(rows_out),
            "declared_ui_order_assumption": "row order is the order-grid presentation order",
        }
        await browser.close()
        return rows_out, evidence


def ordered(rows: list[dict], orientation: str) -> list[dict]:
    if orientation == "newest":
        return rows
    if orientation == "oldest":
        return list(reversed(rows))
    raise ValueError(f"unknown orientation: {orientation}")


def compute(query: dict, rows: list[dict], orientation: str) -> tuple[Decimal, dict]:
    xs = ordered(rows, orientation)

    def payment(row: dict) -> Decimal:
        return Decimal(row["payment"])

    if query["mode"] == "sum":
        pred = query["predicate"]
        n = query["n"]
        if pred in {"completed", "pending"}:
            chosen = [r for r in xs if r["status_class"] == pred][:n]
        elif pred == "non_cancelled":
            chosen = [r for r in xs if r["status_class"] != "cancelled"][:n]
        else:
            raise ValueError(pred)
        if len(chosen) != n:
            raise RuntimeError(f"needed {n} {pred} rows, found {len(chosen)}")
        value = cents(sum((payment(r) for r in chosen), Decimal("0")))
        return value, {"selected": chosen, "operation": "sum"}

    if query["mode"] == "difference":
        cn = query["cancelled_n"]
        xn = query["completed_n"]
        cancelled = [r for r in xs if r["status_class"] == "cancelled"][:cn]
        completed = [r for r in xs if r["status_class"] == "completed"][:xn]
        if len(cancelled) != cn or len(completed) != xn:
            raise RuntimeError(
                f"needed {cn} cancelled/{xn} completed rows, got {len(cancelled)}/{len(completed)}"
            )
        a = sum((payment(r) for r in cancelled), Decimal("0"))
        b = sum((payment(r) for r in completed), Decimal("0"))
        value = cents(abs(a - b))
        return value, {
            "cancelled": cancelled,
            "completed": completed,
            "cancelled_total": str(cents(a)),
            "completed_total": str(cents(b)),
            "operation": "absolute_difference",
        }

    raise ValueError(query)


async def amain() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True, type=int)
    ap.add_argument("--task-file", required=True)
    ap.add_argument("--base-url", default="http://localhost:7780/admin")
    ap.add_argument("--orientation", required=True, choices=("newest", "oldest"))
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    tasks = json.loads(Path(args.task_file).read_text())
    task = next((t for t in tasks if int(t["task_id"]) == args.task_id), None)
    if task is None:
        raise SystemExit(f"task {args.task_id} not found")
    if int(task.get("intent_template_id")) != 367:
        raise SystemExit(f"task {args.task_id} is not template 367")

    rows, observed = await observe_rows(args.base_url)
    query = parse_query(task["intent"])
    value, evidence = compute(query, rows, args.orientation)

    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    response = {
        "task_type": "RETRIEVE",
        "status": "SUCCESS",
        "retrieved_data": [float(value)],
        "error_details": None,
    }
    (out / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")
    (out / "candidate_evidence.json").write_text(
        json.dumps(
            {
                "task_id": args.task_id,
                "intent": task["intent"],
                "orientation": args.orientation,
                "query": query,
                "computed_value": str(value),
                **observed,
                **evidence,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "task_id": args.task_id,
                "orientation": args.orientation,
                "computed_value": str(value),
                "rows_observed": observed["rows_observed"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(amain())
