#!/usr/bin/env python3
"""Deterministic Shopping Admin payment-fold capability for WebArena-Verified.

Boundary:
- observes only the Magento Admin order grid through Playwright;
- relies on the grid's declared default Purchase Date descending sort;
- reads Status and Grand Total (Purchased);
- does not use benchmark expected answers or container DB/filesystem;
- parameterizes behavior from the task's natural-language payment query.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from webarena_shopping_admin_visible_order_selector import rewind_first

ORDER_GRID = "/sales/order/"


def parse_currency(text: str) -> Decimal:
    # Magento may render currency symbols and grouping separators.
    m = re.search(r"-?[0-9][0-9,]*(?:\.[0-9]+)?", text.replace("\u00a0", " "))
    if not m:
        raise ValueError(f"no currency value found in {text!r}")
    return Decimal(m.group(0).replace(",", ""))


def cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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


def status_class(text: str) -> str:
    s = re.sub(r"\s+", " ", text).strip().lower()
    # Magento renders this state as "Canceled" even when task wording says cancelled.
    if s in {"canceled", "cancelled"}:
        return "cancelled"
    if s in {"complete", "completed"}:
        return "completed"
    if s == "pending":
        return "pending"
    return "other"


async def table_headers(page) -> tuple[object, list[str]]:
    tables = page.locator("table:visible")
    for i in range(await tables.count()):
        table = tables.nth(i)
        hs = []
        th = table.locator("thead th")
        for j in range(await th.count()):
            hs.append(re.sub(r"\s+", " ", (await th.nth(j).inner_text()).strip()))
        lower = [x.lower() for x in hs]
        if (
            "purchase date" in lower
            and "grand total (purchased)" in lower
            and "status" in lower
            and await table.locator("tbody tr").count() > 0
        ):
            return table, hs
    raise RuntimeError("could not find Magento order grid with Purchase Date / Grand Total (Purchased) / Status")


async def collect_rows(page, need: dict, max_pages: int = 20) -> list[dict]:
    rows_out: list[dict] = []
    seen_ids: set[str] = set()

    for page_no in range(max_pages):
        table, headers = await table_headers(page)
        lower = [h.lower() for h in headers]
        id_idx = lower.index("id") if "id" in lower else None
        total_idx = lower.index("grand total (purchased)")
        status_idx = lower.index("status")
        date_idx = lower.index("purchase date")

        rows = table.locator("tbody tr")
        for ri in range(await rows.count()):
            cells = rows.nth(ri).locator("td")
            n = await cells.count()
            if n <= max(total_idx, status_idx, date_idx):
                continue

            order_id = (
                re.sub(r"\s+", " ", (await cells.nth(id_idx).inner_text()).strip())
                if id_idx is not None and id_idx < n
                else f"page{page_no}-row{ri}"
            )
            if order_id in seen_ids:
                continue
            seen_ids.add(order_id)

            status_txt = re.sub(r"\s+", " ", (await cells.nth(status_idx).inner_text()).strip())
            total_txt = re.sub(r"\s+", " ", (await cells.nth(total_idx).inner_text()).strip())
            date_txt = re.sub(r"\s+", " ", (await cells.nth(date_idx).inner_text()).strip())
            rows_out.append(
                {
                    "id": order_id,
                    "purchase_date": date_txt,
                    "status_text": status_txt,
                    "status_class": status_class(status_txt),
                    "payment": parse_currency(total_txt),
                }
            )

        # "Last N" requires global chronology, not the first N matches
        # encountered on a mutable order-grid page. Exhaust pagination.

        # Use the visible Magento order-grid pager only. Hidden UI-component
        # pager instances are not valid continuations of the visible grid.
        pager_wraps = page.locator(".admin__data-grid-pager-wrap:visible")
        next_button = None
        for pi in range(await pager_wraps.count()):
            candidate = pager_wraps.nth(pi).locator("button.action-next")
            if await candidate.count() and await candidate.is_enabled():
                next_button = candidate
                break
        if next_button is None:
            break

        before_first = None
        first_row = table.locator("tbody tr").first
        if id_idx is not None and await first_row.count():
            cells = first_row.locator("td")
            if await cells.count() > id_idx:
                before_first = re.sub(r"\\s+", " ", (await cells.nth(id_idx).inner_text()).strip())

        await next_button.click(force=True)

        changed = False
        for _ in range(80):
            await page.wait_for_timeout(100)
            table2, headers2 = await table_headers(page)
            lower2 = [h.lower() for h in headers2]
            if "id" not in lower2 or before_first is None:
                continue
            first_row2 = table2.locator("tbody tr").first
            if not await first_row2.count():
                continue
            cells2 = first_row2.locator("td")
            idx2 = lower2.index("id")
            if await cells2.count() <= idx2:
                continue
            current = re.sub(r"\\s+", " ", (await cells2.nth(idx2).inner_text()).strip())
            if current and current != before_first:
                changed = True
                break
        if not changed:
            break

    return rows_out


def purchase_timestamp(row: dict) -> datetime:
    raw = re.sub(r"\s+", " ", str(row["purchase_date"])).strip()
    for fmt in ("%b %d, %Y %I:%M:%S %p", "%B %d, %Y %I:%M:%S %p"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognized Magento purchase date: {raw!r}")


def compute(query: dict, rows: list[dict]) -> tuple[Decimal, dict]:
    rows = sorted(rows, key=purchase_timestamp, reverse=True)
    if query["mode"] == "sum":
        pred = query["predicate"]
        n = query["n"]
        if pred in {"completed", "pending"}:
            chosen = [r for r in rows if r["status_class"] == pred][:n]
        elif pred == "non_cancelled":
            chosen = [r for r in rows if r["status_class"] != "cancelled"][:n]
        else:
            raise ValueError(pred)

        if len(chosen) != n:
            raise RuntimeError(f"needed {n} {pred} rows, found {len(chosen)}")
        value = cents(sum((r["payment"] for r in chosen), Decimal("0")))
        return value, {"selected": chosen, "operation": "sum"}

    if query["mode"] == "difference":
        cn = query["cancelled_n"]
        xn = query["completed_n"]
        cancelled = [r for r in rows if r["status_class"] == "cancelled"][:cn]
        completed = [r for r in rows if r["status_class"] == "completed"][:xn]
        if len(cancelled) != cn or len(completed) != xn:
            raise RuntimeError(
                f"needed {cn} cancelled/{xn} completed rows, got {len(cancelled)}/{len(completed)}"
            )
        cancelled_total = sum((r["payment"] for r in cancelled), Decimal("0"))
        completed_total = sum((r["payment"] for r in completed), Decimal("0"))
        # "difference between A and B" is represented as magnitude, independent of phrase order.
        value = cents(abs(cancelled_total - completed_total))
        return value, {
            "cancelled": cancelled,
            "completed": completed,
            "cancelled_total": str(cents(cancelled_total)),
            "completed_total": str(cents(completed_total)),
            "operation": "absolute_difference",
        }

    raise ValueError(query)


async def solve(base_url: str, intent: str) -> tuple[Decimal, dict]:
    query = parse_query(intent)
    need = {}
    if query["mode"] == "sum":
        need[query["predicate"]] = query["n"]
    else:
        need["cancelled"] = query["cancelled_n"]
        need["completed"] = query["completed_n"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers={"X-M2-Admin-Auto-Login": "admin:admin1234"}
        )
        page = await context.new_page()
        response = await page.goto(base_url.rstrip("/") + ORDER_GRID, wait_until="networkidle", timeout=120_000)
        if response is None or response.status != 200:
            raise RuntimeError(f"order grid navigation failed: {getattr(response, 'status', None)}")
        # Magento saves the current grid page across separate browser runs.
        # Restore page 1 before completing a chronologically ordered scan.
        await rewind_first(page)
        rows = await collect_rows(page, need)
        value, evidence = compute(query, rows)
        evidence.update(
            {
                "query": query,
                "observed_url": page.url,
                "page_title": await page.title(),
                "rows_scanned": len(rows),
            }
        )
        await browser.close()
        return value, evidence


async def amain() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True, type=int)
    ap.add_argument("--task-file", required=True)
    ap.add_argument("--base-url", default="http://localhost:7780/admin")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    tasks = json.loads(Path(args.task_file).read_text())
    task = next((t for t in tasks if int(t["task_id"]) == args.task_id), None)
    if task is None:
        raise SystemExit(f"task {args.task_id} not found")
    if int(task.get("intent_template_id")) != 367:
        raise SystemExit(f"task {args.task_id} is not template 367")

    value, evidence = await solve(args.base_url, task["intent"])

    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    result_number = float(value)
    (out / "agent_response.json").write_text(
        json.dumps(
            {
                "task_type": "RETRIEVE",
                "status": "SUCCESS",
                "retrieved_data": [result_number],
                "error_details": None,
            },
            indent=2,
        )
        + "\n"
    )
    (out / "capability_evidence.json").write_text(
        json.dumps(
            {
                "task_id": args.task_id,
                "intent": task["intent"],
                "computed_value": str(value),
                **evidence,
            },
            default=str,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"task_id": args.task_id, "computed_value": str(value), **evidence}, default=str, indent=2))


if __name__ == "__main__":
    asyncio.run(amain())
