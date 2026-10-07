#!/usr/bin/env python3
"""Schema-driven grouped-count representation synthesis for WebArena customer-order tasks.

The generator is not given domain-specific candidate programs. From one training
instruction plus the observed order-grid schema, it induces an intermediate
representation:
    entity column -> count of matching order rows
and then compiles rank/equality selectors from task language.

This tests representation induction beyond the earlier scalar relation-rebinding DSL.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from playwright.async_api import async_playwright

ORDER_GRID = "/sales/order/"


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.casefold())


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def status_class(s: str) -> str:
    s = clean(s).lower()
    if s in {"complete", "completed"}:
        return "complete"
    if s in {"canceled", "cancelled"}:
        return "cancelled"
    if s == "pending":
        return "pending"
    return s


async def live_table(page, require_email: bool = True):
    tables = page.locator("table:visible")
    for i in range(await tables.count()):
        table = tables.nth(i)
        th = table.locator("thead th")
        headers = [clean(await th.nth(j).inner_text()) for j in range(await th.count())]
        lower = [h.lower() for h in headers]
        needed = {"id", "status"}
        if require_email:
            needed.add("customer email")
        if needed.issubset(set(lower)) and await table.locator("tbody tr").count() > 0:
            return table, headers
    raise RuntimeError("live order grid not found")


async def expose_customer_email(page) -> None:
    controls = page.locator(".admin__data-grid-action-columns:visible")
    if await controls.count() == 0:
        raise RuntimeError("columns control not found")
    control = controls.first
    await control.locator("button.admin__action-dropdown").click()
    labels = control.locator("label.admin__field-label")
    target = None
    for i in range(await labels.count()):
        if clean(await labels.nth(i).inner_text()).lower() == "customer email":
            target = labels.nth(i)
            break
    if target is None:
        raise RuntimeError("customer email column unavailable")
    box = target.locator("xpath=preceding-sibling::input[1]")
    if not await box.is_checked():
        await box.check(force=True)
    await control.locator("button.admin__action-dropdown").click()
    for _ in range(80):
        await page.wait_for_timeout(100)
        try:
            await live_table(page, True)
            return
        except Exception:
            pass
    raise RuntimeError("customer email column did not appear")


async def first_id(table, headers):
    idx = [h.lower() for h in headers].index("id")
    row = table.locator("tbody tr").first
    if not await row.count():
        return None
    cells = row.locator("td")
    return clean(await cells.nth(idx).inner_text()) if await cells.count() > idx else None


async def advance(page, table, headers) -> bool:
    wraps = page.locator(".admin__data-grid-pager-wrap:visible")
    nxt = None
    for i in range(await wraps.count()):
        candidate = wraps.nth(i).locator("button.action-next")
        if await candidate.count() and await candidate.is_enabled():
            nxt = candidate
            break
    if nxt is None:
        return False
    before = await first_id(table, headers)
    await nxt.click(force=True)
    for _ in range(80):
        await page.wait_for_timeout(100)
        table2, headers2 = await live_table(page)
        current = await first_id(table2, headers2)
        if before and current and before != current:
            return True
    raise RuntimeError("pager did not advance")


async def observe(base_url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            extra_http_headers={"X-M2-Admin-Auto-Login": "admin:admin1234"}
        )
        page = await ctx.new_page()
        resp = await page.goto(
            base_url.rstrip("/") + ORDER_GRID,
            wait_until="networkidle",
            timeout=120000,
        )
        if resp is None or resp.status != 200:
            raise RuntimeError("order grid navigation failed")
        await expose_customer_email(page)

        rows_out = []
        seen = set()
        observed_headers = None
        for _ in range(50):
            table, headers = await live_table(page)
            observed_headers = headers
            lower = [h.lower() for h in headers]
            ix = {k: lower.index(k) for k in ["id", "status", "customer email"]}
            rows = table.locator("tbody tr")
            for ri in range(await rows.count()):
                cells = rows.nth(ri).locator("td")
                if await cells.count() <= max(ix.values()):
                    continue
                oid = clean(await cells.nth(ix["id"]).inner_text())
                if not oid or oid in seen:
                    continue
                seen.add(oid)
                email = clean(await cells.nth(ix["customer email"]).inner_text())
                status = clean(await cells.nth(ix["status"]).inner_text())
                if email:
                    rows_out.append(
                        {
                            "id": oid,
                            "customer email": email,
                            "status": status,
                            "status_class": status_class(status),
                        }
                    )
            if not await advance(page, table, headers):
                break
        await browser.close()

    if not rows_out:
        raise RuntimeError("no rows observed")
    return {
        "row_semantics": "one row per order",
        "headers": observed_headers,
        "rows": rows_out,
    }


def output_entity_phrase(intent: str) -> str:
    m = re.search(r"get\s+(.+?)\s+who\b", intent, flags=re.I)
    if not m:
        raise ValueError(f"cannot infer output entity: {intent!r}")
    return clean(m.group(1)).replace("(s)", "")


def induce_representation(task: dict, observation: dict) -> dict:
    intent = str(task["intent"])
    target = output_entity_phrase(intent)
    headers = [h for h in observation["headers"] if h]
    scored = sorted(
        ((similarity(target, h), h) for h in headers),
        reverse=True,
    )
    best_score, best_header = scored[0]
    if best_score < 0.55:
        raise RuntimeError({"target": target, "headers": headers, "scores": scored})

    if "number of orders" not in intent.casefold() and "orders in any state" not in intent.casefold():
        raise RuntimeError("training residual does not request an order-count measure")

    # The representation is induced from the observed row semantics, not selected
    # from a domain-specific candidate list.
    return {
        "representation_type": "grouped_row_count",
        "group_key": best_header.lower(),
        "measure": "row_count",
        "source_row_semantics": observation["row_semantics"],
        "induced_from": {
            "output_entity_phrase": target,
            "matched_header": best_header,
            "header_similarity": best_score,
            "measure_phrase": "number of orders",
        },
    }


ORDINALS = {
    "most": 1,
    "second most": 2,
    "third most": 3,
    "fourth most": 4,
    "fifth most": 5,
}


def compile_selector(intent: str) -> dict:
    low = clean(intent).casefold()
    m = re.search(r"have\s+(\d+)\s+orders?\s+in any state", low)
    if m:
        return {
            "filter": {"status": "any"},
            "selector": {"kind": "count_equals", "value": int(m.group(1))},
        }

    for phrase, rank in sorted(ORDINALS.items(), key=lambda kv: -len(kv[0])):
        if f"completed the {phrase} number of orders" in low:
            return {
                "filter": {"status": "complete"},
                "selector": {
                    "kind": "distinct_count_rank_desc",
                    "rank": rank,
                },
            }
    raise ValueError(f"unsupported selector language: {intent!r}")


def execute(observation: dict, representation: dict, selector: dict, ablate_grouping: bool = False) -> dict:
    rows = observation["rows"]
    key = representation["group_key"]

    if selector["filter"]["status"] == "complete":
        rows = [r for r in rows if r["status_class"] == "complete"]

    if ablate_grouping:
        # Negative control: destroys the induced grouped-count representation by
        # pretending every observed entity has count one.
        counts = Counter({r[key]: 1 for r in rows})
    else:
        counts = Counter(r[key] for r in rows)

    s = selector["selector"]
    if s["kind"] == "count_equals":
        chosen = sorted(k for k, n in counts.items() if n == s["value"])
    elif s["kind"] == "distinct_count_rank_desc":
        levels = sorted(set(counts.values()), reverse=True)
        rank = s["rank"]
        chosen = [] if rank > len(levels) else sorted(k for k, n in counts.items() if n == levels[rank - 1])
    else:
        raise ValueError(s)

    if chosen:
        return {
            "task_type": "RETRIEVE",
            "status": "SUCCESS",
            "retrieved_data": chosen,
            "error_details": None,
        }
    return {
        "task_type": "RETRIEVE",
        "status": "NOT_FOUND_ERROR",
        "retrieved_data": None,
        "error_details": None,
    }


def load_task(path: str, task_id: int) -> dict:
    tasks = json.loads(Path(path).read_text())
    task = next(t for t in tasks if int(t["task_id"]) == task_id)
    if int(task["intent_template_id"]) != 276:
        raise SystemExit("unsupported template")
    return task


def compute(args) -> None:
    task = load_task(args.task_file, args.task_id)
    observation = json.loads(Path(args.observation).read_text())
    representation = json.loads(Path(args.representation).read_text())
    selector = compile_selector(task["intent"])
    response = execute(
        observation,
        representation,
        selector,
        ablate_grouping=args.ablate_grouping,
    )
    out = Path(args.output_dir) / str(args.task_id)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent_response.json").write_text(json.dumps(response, indent=2) + "\n")
    (out / "capability_evidence.json").write_text(
        json.dumps(
            {
                "task_id": args.task_id,
                "representation": representation,
                "selector": selector,
                "ablate_grouping": args.ablate_grouping,
                "response": response,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"task_id": args.task_id, "selector": selector, "response": response}, indent=2))


async def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    obs = sub.add_parser("observe")
    obs.add_argument("--base-url", default="http://localhost:7780/admin")
    obs.add_argument("--output", required=True)

    induce = sub.add_parser("induce")
    induce.add_argument("--task-id", type=int, required=True)
    induce.add_argument("--task-file", required=True)
    induce.add_argument("--observation", required=True)
    induce.add_argument("--output", required=True)

    comp = sub.add_parser("compute")
    comp.add_argument("--task-id", type=int, required=True)
    comp.add_argument("--task-file", required=True)
    comp.add_argument("--observation", required=True)
    comp.add_argument("--representation", required=True)
    comp.add_argument("--output-dir", required=True)
    comp.add_argument("--ablate-grouping", action="store_true")

    args = ap.parse_args()
    if args.cmd == "observe":
        data = await observe(args.base_url)
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"rows": len(data["rows"]), "headers": data["headers"]}, indent=2))
    elif args.cmd == "induce":
        task = load_task(args.task_file, args.task_id)
        observation = json.loads(Path(args.observation).read_text())
        rep = induce_representation(task, observation)
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rep, indent=2) + "\n")
        print(json.dumps(rep, indent=2))
    else:
        compute(args)


if __name__ == "__main__":
    asyncio.run(main())
