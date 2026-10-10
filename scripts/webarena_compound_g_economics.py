#!/usr/bin/env python3
"""Prospective two-capability composition economics, official WebArena G.

E: frozen grouped_row_count from artifact 11467591099 / run 37587112851.
F: frozen cancellation filter from artifact 11663621950 / run 38036286320.
G: untouched template-234 task 290 (train; SKU) and 291 (heldout; product spend).

All arms share the same observed order grid, evaluator, hypothesis grammar, and
budget. When a capability is removed, a strong stateless schema interpreter may
reconstruct it; it is NOT prevented from doing so. Correctness is judged only
by the pinned official evaluator. A green workflow is not proof of positive
economic compounding; outcomes are explicitly classified by evidence.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import time
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from webarena_compounding_economics_v1 import verify_retained, read, sha, digest
from webarena_customer_count_representation_synth import (
    clean, status_class, live_table, expose_customer_email, advance,
)

SOURCE = "6473f72db5dcefc97b5725b59e734504edc28a21"
TRAIN = (290,)
HELDOUT = (291,)
BASE = "http://localhost:7780/admin"
GRAMMAR = (("newest_id", 1), ("newest_id", 2), ("newest_id", 3),
           ("newest_date", 1), ("oldest_id", 1), ("newest_id", 4))


async def observe(base: str) -> dict:
    """Observe order-grid fields only, without answer labels or oracle queries."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            extra_http_headers={"X-M2-Admin-Auto-Login": "admin:admin1234"})
        page = await ctx.new_page()
        rsp = await page.goto(base.rstrip("/") + "/sales/order/",
                              wait_until="networkidle", timeout=120000)
        assert rsp is not None and rsp.status == 200
        await expose_customer_email(page)
        out, seen, source_headers = [], set(), []
        for _ in range(60):
            table, headers = await live_table(page)
            source_headers = headers
            lower = [x.casefold() for x in headers]
            ix = {name: lower.index(name) for name in
                  ("id", "customer email", "status")}
            date_col = next((i for i, h in enumerate(lower)
                             if h in ("purchase date", "created at")), None)
            trs = table.locator("tbody tr")
            for j in range(await trs.count()):
                tr = trs.nth(j)
                cells = tr.locator("td")
                if await cells.count() <= max(ix.values()):
                    continue
                item = {k: clean(await cells.nth(i).inner_text())
                        for k, i in ix.items()}
                oid = item["id"]
                if not oid or oid in seen:
                    continue
                seen.add(oid)
                links = await tr.locator('a[href*="/sales/order/view/"]').evaluate_all(
                    "(els) => els.map(e => e.href)")
                fallback = base.rstrip("/") + "/sales/order/view/order_id/" + str(int(re.sub(r"\D", "", oid))) + "/"
                out.append({
                    "id": oid, "customer email": item["customer email"],
                    "status": item["status"], "status_class": status_class(item["status"]),
                    "purchase_date": (clean(await cells.nth(date_col).inner_text())
                                      if date_col is not None and await cells.count() > date_col
                                      else ""),
                    "view_href": links[0] if links else fallback,
                })
            if not await advance(page, table, headers):
                break
        await browser.close()
    assert out and len(out) == len(seen)
    assert {"customer email", "status", "id"}.issubset(set(h.casefold() for h in source_headers))
    return {"row_semantics": "one row per order", "headers": source_headers,
            "rows": out, "source": "live pinned WebArena shopping-admin order grid"}


def check_F(archive: str) -> tuple[str, dict]:
    root = Path(archive)
    r = read(root / "result.json")
    assert r["authority_commit"] == SOURCE
    assert r["train"] == [288] and r["heldout"] == [292]
    assert r["claims"]["reusable_E_to_F_cancellation_grouping"] == "WARRANTED_BOUNDED"
    assert all(r["arms"][k]["state"] == "WARRANTED_BOUNDED_F"
               for k in ("retained_e", "stateless_schema", "stateless_broad"))
    c = r["arms"]["retained_e"]["chosen"]
    assert c == {"group_key": "customer email", "status_filter": "cancelled"}
    return c["status_filter"], {
        "run": 38036286320, "artifact": 11663621950,
        "f_source_exact_commit": "6502a30d6ff45814a01bba5f68d7d093b9d2cb1b",
        "archive_result_sha256": sha(root / "result.json"),
        "F_chosen_filter": c["status_filter"],
    }


def validate(tasks, ob):
    assert all("eval" not in x and "reference_url" not in x for x in tasks), "candidate oracle leak"
    t = {int(x["task_id"]): x for x in tasks}
    assert all(x in t and int(t[x]["intent_template_id"]) == 234 for x in TRAIN + HELDOUT)
    assert "most cancellations" in t[290]["intent"].casefold()
    assert ob["row_semantics"] == "one row per order"
    assert ob["rows"] and len({x["id"] for x in ob["rows"]}) == len(ob["rows"])
    assert any(x["status_class"] == "cancelled" for x in ob["rows"])
    return t


def infer_group(intent, ob):
    """Credible stateless schema-driven reconstruction, not an intentionally weak baseline."""
    assert "customer" in intent.casefold()
    options = [x.casefold() for x in ob["headers"]
               if "customer" in x.casefold() and "email" in x.casefold()]
    assert len(options) == 1 and options[0] in ob["rows"][0], options
    return options[0]


def infer_filter(intent, ob):
    """Extract exact semantics from the instruction when filter memory is removed."""
    m = re.search(r"\bcancell?ed\b|\bcancellations\b", intent.casefold())
    assert m and {"cancelled", "complete", "pending"} & set(
        x["status_class"] for x in ob["rows"])
    return "cancelled"


def date_key(row):
    s = row.get("purchase_date", "")
    for f in ("%b %d, %Y, %I:%M:%S %p", "%B %d, %Y, %I:%M:%S %p",
              "%b %d, %Y, %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, f).timestamp()
        except ValueError:
            pass
    return float(int(re.sub(r"\D", "", row["id"])))


def select_order_rows(ob, key, filt, mode, limit):
    rows = [x for x in ob["rows"] if filt == "any" or x["status_class"] == filt]
    if not rows or key not in rows[0]:
        return []
    counts = Counter(x[key] for x in rows)
    best = max(counts.values())
    winners = sorted(k for k, count in counts.items() if count == best)
    selected = []
    for entity in winners:
        group = [r for r in rows if r[key] == entity]
        if mode == "newest_date":
            group.sort(key=lambda r: (date_key(r), int(re.sub(r"\D","",r["id"]))), reverse=True)
        else:
            group.sort(key=lambda r: int(re.sub(r"\D","",r["id"])),
                       reverse=(mode == "newest_id"))
        selected.extend(group[:limit])
    return selected


def extract_product_receipt(items_text: str, totals_text: str):
    # Exact selectors verified by separate read-only DOM probe, no grader labels.
    sku = re.findall(r"(?im)\bSKU\s*:\s*([A-Za-z0-9_./-]+)", items_text)
    totals = {}
    for line in totals_text.splitlines():
        m = re.match(r"\s*(Grand Total|Subtotal|Shipping\s*&\s*Handling)\s*\t?\s*\$?\s*([0-9,]+\.\d{2})", line, re.I)
        if m:
            totals[m.group(1).casefold().strip()] = Decimal(m.group(2).replace(",", ""))
    if not sku or "subtotal" not in totals:
        raise ValueError({"sku_count": len(sku), "totals": list(totals)})
    return {"sku": sku, "subtotal": str(totals["subtotal"]),
            "shipping": str(totals.get("shipping & handling", "0")),
            "grand_total": str(totals.get("grand total", "0"))}


class DetailReader:
    def __init__(self, page):
        self.page = page
        self.cache = {}
        self.fetch_seconds = 0.0
        self.fetch_count = 0

    async def get(self, row):
        oid = row["id"]
        if oid in self.cache:
            return self.cache[oid]
        start = time.perf_counter()
        rsp = await self.page.goto(row["view_href"], wait_until="networkidle", timeout=120000)
        assert rsp is not None and rsp.status == 200, (oid, rsp.status if rsp else None)
        items = self.page.locator("table.edit-order-table")
        totals = self.page.locator("table.order-subtotal-table")
        assert await items.count() == 1 and await totals.count() == 1, ("order details missing", oid)
        data = extract_product_receipt(await items.inner_text(), await totals.inner_text())
        self.fetch_seconds += time.perf_counter() - start
        self.fetch_count += 1
        self.cache[oid] = data
        return data


async def candidate(task_id, ob, key, filt, mode, limit, reader):
    chosen = select_order_rows(ob, key, filt, mode, limit)
    if not chosen:
        return {"task_type": "RETRIEVE", "status": "NOT_FOUND_ERROR",
                "retrieved_data": None, "error_details": None}
    receipts = [await reader.get(x) for x in chosen]
    if task_id == 290:
        data = [sku for receipt in receipts for sku in receipt["sku"]]
    elif task_id == 291:
        data = [float(sum((Decimal(x["subtotal"]) for x in receipts), Decimal(0)))]
    else:
        raise ValueError("unregistered test task")
    return {"task_type": "RETRIEVE", "status": "SUCCESS",
            "retrieved_data": data, "error_details": None}


def passed(x):
    return x["score"] == 1.0 and x["status"] == "success"


def grade(wa, empty, root, arm, phase, tid, response, label):
    path = root / arm / phase / (str(tid) + "_" + label + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(response, indent=2) + "\n")
    s = time.perf_counter()
    x = wa.evaluate_task(task_id=tid, agent_response=path, network_trace=empty)
    return {"task_id": tid, "score": float(x.score), "status": x.status.value,
            "verifier_seconds": time.perf_counter() - s, "response_path": str(path)}


async def experiment(args):
    from playwright.async_api import async_playwright
    from webarena_verified.api import WebArenaVerified
    from webarena_verified.types.config import WebArenaVerifiedConfig
    from webarena_verified.types.tracing import NetworkTrace

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    begin = time.perf_counter()
    erep, ereceipt = verify_retained(args.archive_e)
    retained_filter, freceipt = check_F(args.archive_f)
    shared_pinning_seconds = time.perf_counter() - begin
    ob = read(args.observation)
    tasks = validate(read(args.tasks), ob)
    assert erep["group_key"] in ob["rows"][0]
    wa = WebArenaVerified(config=WebArenaVerifiedConfig.from_file(Path(args.config)))
    empty = NetworkTrace.model_construct(is_playwright=False, src_file=Path("<none>"), events=())
    root_receipt = {"e": ereceipt, "f": freceipt,
                    "shared_archive_validation_seconds": shared_pinning_seconds,
                    "observation_sha256": sha(args.observation),
                    "source": SOURCE}
    result = {"experiment": "WebArena G two-capability composed acquisition economics",
              "source_exact": SOURCE, "train": list(TRAIN), "heldout": list(HELDOUT),
              "grammar": list(GRAMMAR), "budget": args.budget, "receipts": root_receipt,
              "fixture_order_rows": len(ob["rows"]), "arms": {}, "claims": {}}

    arms = ("stateless_schema", "only_e", "only_f", "retained_ef")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Only source-derived data and code, not verifier answers, enter acquisition.
        for arm in arms:
            have_e = arm in ("only_e", "retained_ef")
            have_f = arm in ("only_f", "retained_ef")
            key = erep["group_key"] if have_e else infer_group(tasks[290]["intent"], ob)
            filt = retained_filter if have_f else infer_filter(tasks[290]["intent"], ob)
            ctx = await browser.new_context(extra_http_headers={
                "X-M2-Admin-Auto-Login": "admin:admin1234"})
            page = await ctx.new_page()
            reader = DetailReader(page)
            start = time.perf_counter()
            search = []
            chosen = None
            for n, (mode, limit) in enumerate(GRAMMAR):
                if n >= args.budget:
                    break
                try:
                    response = await candidate(290, ob, key, filt, mode, limit, reader)
                    g = grade(wa, empty, root, arm, "train", 290, response,
                              str(n) + "_" + mode + "_" + str(limit))
                except Exception as exc:
                    g = {"task_id": 290, "score": 0.0, "status": "candidate_source_error",
                         "error": repr(exc)}
                row = {"mode": mode, "count": limit, "result": g}
                search.append(row)
                if passed(g):
                    chosen = {"group_key": key, "status_filter": filt,
                              "recency_mode": mode, "recent_order_count": limit}
                    break
            freeze = {"arm": arm, "chosen": chosen, "training_task": 290,
                      "search": search, "e_enabled": have_e, "f_enabled": have_f,
                      "prior_E_reconstructed": not have_e,
                      "prior_F_reconstructed": not have_f,
                      "heldout_scored_before_freeze": False}
            freeze["freeze_sha256"] = digest(freeze)
            (root / (arm + "_freeze.json")).write_text(json.dumps(freeze, indent=2) + "\n")
            result["arms"][arm] = {
                "chosen": chosen, "freeze_sha256": freeze["freeze_sha256"],
                "candidate_task_evaluations": len(search),
                "training": search,
                "training_verifier_seconds": sum(z["result"].get("verifier_seconds", 0) for z in search),
                "training_wall_seconds": time.perf_counter() - start,
                "training_detail_fetch_seconds": reader.fetch_seconds,
                "training_detail_pages": reader.fetch_count,
                "retained": {"E": have_e, "F": have_f},
                "state": "FROZEN_BEFORE_HELDOUT"}
            # Hold contexts for exact shared observation consistency and detail reuse.
            result["arms"][arm]["_ctx"] = ctx
            result["arms"][arm]["_reader"] = reader

        # All arms have been source-and-code frozen before any G heldout score.
        assert all((root / (a + "_freeze.json")).exists() for a in arms)
        for arm in arms:
            entry = result["arms"][arm]
            chosen = entry["chosen"]
            held = []
            if chosen is not None:
                try:
                    response = await candidate(291, ob, chosen["group_key"],
                                               chosen["status_filter"], chosen["recency_mode"],
                                               chosen["recent_order_count"], entry["_reader"])
                    held = [grade(wa, empty, root, arm, "heldout", 291, response, "frozen")]
                except Exception as exc:
                    held = [{"task_id": 291, "score": 0.0,
                             "status": "candidate_source_error", "error": repr(exc)}]
            entry["heldout"] = held
            entry["heldout_verifier_seconds"] = sum(v.get("verifier_seconds", 0) for v in held)
            entry["all_detail_fetch_seconds"] = entry["_reader"].fetch_seconds
            entry["all_detail_pages"] = entry["_reader"].fetch_count
            entry["state"] = ("WARRANTED_BOUNDED_G" if held and all(passed(v) for v in held)
                              else "UNKNOWN_OR_REJECTED_G")
            await entry["_ctx"].close()
            del entry["_ctx"]
            del entry["_reader"]
        await browser.close()

    out = result["arms"]
    got = {a: out[a]["state"] == "WARRANTED_BOUNDED_G" for a in arms}
    allgreen = all(got.values())
    costs = {a: out[a]["candidate_task_evaluations"] for a in arms}
    minimum = min(costs[a] for a in ("stateless_schema", "only_e", "only_f"))
    result["claims"] = {
        "source_pinned_two_capability_composition":
            "WARRANTED_BOUNDED" if got["retained_ef"] else "UNKNOWN",
        "retention_is_cheaper_than_strong_stateless":
            ("WARRANTED_BOUNDED_CANDIDATE_EVALUATIONS"
             if allgreen and costs["retained_ef"] < costs["stateless_schema"]
             else ("REJECTED_ON_THIS_FIXTURE" if allgreen else "UNKNOWN")),
        "full_retention_beats_both_single_removal_arms":
            ("WARRANTED_BOUNDED_CANDIDATE_EVALUATIONS"
             if allgreen and costs["retained_ef"] < costs["only_e"]
             and costs["retained_ef"] < costs["only_f"]
             else ("REJECTED_ON_THIS_FIXTURE" if allgreen else "UNKNOWN")),
        "decreasing_total_amortized_acquisition_cost": "UNKNOWN",
        "multi_generation_recursive_acceleration": "UNKNOWN"}
    result["economic_scope"] = (
        "Matched official candidate-evaluator calls and wall-time proxies; "
        "no imputed dollar cost, matched task-difficulty sample, or prior E/F discovery amortization.")
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"claims": result["claims"],
                      "costs": costs,
                      "heldout": {a: out[a]["heldout"] for a in arms},
                      "detail_pages": {a: out[a]["all_detail_pages"] for a in arms}},
                     indent=2))
    assert all(out[a]["candidate_task_evaluations"] <= args.budget for a in arms)
    assert result["claims"]["multi_generation_recursive_acceleration"] == "UNKNOWN"


def selftest():
    ob = {"headers": ["ID", "Customer Email", "Status"],
          "rows": [
            {"id": "00001", "customer email": "a@example", "status_class": "cancelled",
             "purchase_date": "May 20, 2023, 9:00:00 PM"},
            {"id": "00002", "customer email": "a@example", "status_class": "cancelled",
             "purchase_date": "May 21, 2023, 9:00:00 PM"},
            {"id": "00003", "customer email": "b@example", "status_class": "complete",
             "purchase_date": "May 22, 2023, 9:00:00 PM"}]}
    assert infer_group("Get products for customer with the most cancellations", ob) == "customer email"
    assert infer_filter("Get the most recent cancelled orders of a customer", ob) == "cancelled"
    s = select_order_rows(ob, "customer email", "cancelled", "newest_id", 1)
    assert [x["id"] for x in s] == ["00002"]
    s = select_order_rows(ob, "customer email", "cancelled", "newest_date", 1)
    assert [x["id"] for x in s] == ["00002"]
    p = extract_product_receipt(
        "Product\tItem Status\nTest Tee\nSKU: WS09-XS-Blue\n\tOrdered\t$28.00\n",
        "Grand Total\t$48.00\nSubtotal\t$28.00\nShipping & Handling\t$20.00")
    assert p["sku"] == ["WS09-XS-Blue"] and p["subtotal"] == "28.00"
    print("SELFTEST_OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--observe", action="store_true")
    ap.add_argument("--root", default="artifacts/compound_g")
    ap.add_argument("--archive-e", default="artifacts/compound_g/E")
    ap.add_argument("--archive-f", default="artifacts/compound_g/F")
    ap.add_argument("--observation", default="artifacts/compound_g/observation.json")
    ap.add_argument("--tasks", default="artifacts/compound_g/no_eval.json")
    ap.add_argument("--config", default="artifacts/compound_g/config.json")
    ap.add_argument("--base-url", default=BASE)
    ap.add_argument("--budget", type=int, default=6)
    args = ap.parse_args()
    if args.self_test:
        selftest()
    elif args.observe:
        data = asyncio.run(observe(args.base_url))
        path = Path(args.observation)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"rows": len(data["rows"]), "headers": data["headers"],
                          "cancelled": sum(x["status_class"] == "cancelled" for x in data["rows"])},
                         indent=2))
    else:
        asyncio.run(experiment(args))
