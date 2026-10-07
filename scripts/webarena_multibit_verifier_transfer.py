#!/usr/bin/env python3
"""Prospective multi-bit verifier-selection experiment for WebArena-Verified template 367.

A single browser observation is frozen. Eight semantic policies vary three bits:
1. recency: newest vs oldest
2. status binding: semantic vs coarse_non_cancelled
3. aggregation: sum vs mean

No candidate reads evaluator expected answers. The workflow scores all eight policies on
one training task, freezes the unique verifier-selected policy, then evaluates untouched
siblings only after the freeze.
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


async def observe(base_url: str) -> dict:
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

        snapshot = {
            "observed_url": page.url,
            "page_title": await page.title(),
            "headers": headers,
            "rows": rows_out,
        }
        await browser.close()
        return snapshot


def orient(rows: list[dict], recency: str) -> list[dict]:
    if recency == "newest":
        return rows
    if recency == "oldest":
        return list(reversed(rows))
    raise ValueError(recency)


def choose(xs: list[dict], predicate: str, n: int) -> list[dict]:
    if predicate in {"completed", "pending", "cancelled"}:
        out = [r for r in xs if r["status_class"] == predicate][:n]
    elif predicate == "non_cancelled":
        out = [r for r in xs if r["status_class"] != "cancelled"][:n]
    else:
        raise ValueError(predicate)
    if len(out) != n:
        raise RuntimeError(f"needed {n} {predicate}, found {len(out)}")
    return out


def aggregate(rows: list[dict], aggregation: str) -> Decimal:
    values = [Decimal(r["payment"]) for r in rows]
    total = sum(values, Decimal("0"))
    if aggregation == "sum":
        return cents(total)
    if aggregation == "mean":
        return cents(total / Decimal(len(values)))
    raise ValueError(aggregation)


def compute(query: dict, rows: list[dict], policy: dict) -> tuple[Decimal, dict]:
    xs = orient(rows, policy["recency"])
    scope = policy["status_binding"]
    aggregation = policy["aggregation"]

    if query["mode"] == "sum":
        predicate = query["predicate"] if scope == "semantic" else "non_cancelled"
        selected = choose(xs, predicate, query["n"])
        value = aggregate(selected, aggregation)
        return value, {
            "operation": aggregation,
            "requested_predicate": query["predicate"],
            "effective_predicate": predicate,
            "selected": selected,
        }

    if query["mode"] == "difference":
        if scope == "semantic":
            left_predicate, right_predicate = "cancelled", "completed"
        else:
            left_predicate = right_predicate = "non_cancelled"
        left = choose(xs, left_predicate, query["cancelled_n"])
        right = choose(xs, right_predicate, query["completed_n"])
        a = aggregate(left, aggregation)
        b = aggregate(right, aggregation)
        value = cents(abs(a - b))
        return value, {
            "operation": f"absolute_difference_of_{aggregation}",
            "left_predicate": left_predicate,
            "right_predicate": right_predicate,
            "left_value": str(a),
            "right_value": str(b),
            "left": left,
            "right": right,
        }

    raise ValueError(query)


def load_task(path: str, task_id: int) -> dict:
    tasks = json.loads(Path(path).read_text())
    task = next((t for t in tasks if int(t["task_id"]) == task_id), None)
    if task is None:
        raise SystemExit(f"task {task_id} not found")
    if int(task.get("intent_template_id")) != 367:
        raise SystemExit(f"task {task_id} is not template 367")
    return task


def response_shape_contract(task: dict, response: dict) -> dict:
    spec = str(task.get("instantiation_dict", {}).get("retrieved_data_format_spec", ""))
    data = response.get("retrieved_data")
    passes = (
        "return the value as a number" in spec.lower()
        and isinstance(data, list)
        and len(data) == 1
        and isinstance(data[0], (int, float))
        and not isinstance(data[0], bool)
        and response.get("task_type") == "RETRIEVE"
        and response.get("status") == "SUCCESS"
        and response.get("error_details") is None
    )
    return {
        "spec": spec,
        "passes": passes,
        "retrieved_data_type": type(data[0]).__name__ if isinstance(data, list) and data else None,
    }


def run_compute(args) -> None:
    task = load_task(args.task_file, args.task_id)
    snapshot = json.loads(Path(args.snapshot).read_text())
    policy = {
        "recency": args.recency,
        "status_binding": args.status_binding,
        "aggregation": args.aggregation,
    }
    query = parse_query(task["intent"])
    value, evidence = compute(query, snapshot["rows"], policy)
    response = {
        "task_type": "RETRIEVE",
        "status": "SUCCESS",
        "retrieved_data": [float(value)],
        "error_details": None,
    }
    contract = response_shape_contract(task, response)
    if not contract["passes"]:
        raise RuntimeError({"contract": contract, "response": response})

    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")
    (out / "candidate_evidence.json").write_text(
        json.dumps(
            {
                "task_id": args.task_id,
                "intent": task["intent"],
                "policy": policy,
                "query": query,
                "computed_value": str(value),
                "protected_response_shape_contract": contract,
                "rows_observed": len(snapshot["rows"]),
                **evidence,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    print(json.dumps({"task_id": args.task_id, "policy": policy, "computed_value": str(value)}, indent=2))


async def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    obs = sub.add_parser("observe")
    obs.add_argument("--base-url", default="http://localhost:7780/admin")
    obs.add_argument("--output", required=True)

    comp = sub.add_parser("compute")
    comp.add_argument("--snapshot", required=True)
    comp.add_argument("--task-id", required=True, type=int)
    comp.add_argument("--task-file", required=True)
    comp.add_argument("--recency", required=True, choices=("newest", "oldest"))
    comp.add_argument("--status-binding", required=True, choices=("semantic", "coarse_non_cancelled"))
    comp.add_argument("--aggregation", required=True, choices=("sum", "mean"))
    comp.add_argument("--output-dir", required=True)

    args = ap.parse_args()
    if args.cmd == "observe":
        snapshot = await observe(args.base_url)
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(json.dumps({"rows_observed": len(snapshot["rows"]), "observed_url": snapshot["observed_url"]}, indent=2))
    else:
        run_compute(args)


if __name__ == "__main__":
    asyncio.run(main())
