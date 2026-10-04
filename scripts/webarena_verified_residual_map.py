#!/usr/bin/env python3
"""Compile the pinned WebArena-Verified hard subset into candidate capability families.

No model calls. No benchmark execution. Static analysis only.

Two layers are kept separate:
1. syntactic recurrence by intent_template_id;
2. evaluator-consequence signatures: tasks with the same site set and evaluator
   obligation shape. These are CANDIDATE capability families only, not proved
   behavioral equivalence classes.
"""

from __future__ import annotations

import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

UPSTREAM_SHA = "6473f72db5dcefc97b5725b59e734504edc28a21"
DATASET_URL = (
    "https://raw.githubusercontent.com/ServiceNow/webarena-verified/"
    + UPSTREAM_SHA
    + "/assets/dataset/webarna-verfied-hard.json"
)
EXPECTED_TASKS = 258


def load_tasks() -> list[dict]:
    with urllib.request.urlopen(DATASET_URL, timeout=60) as r:
        tasks = json.load(r)
    if len(tasks) != EXPECTED_TASKS:
        raise RuntimeError(f"expected {EXPECTED_TASKS} tasks, got {len(tasks)}")
    return tasks


def agent_eval(task: dict) -> dict:
    for e in task.get("eval", []):
        if e.get("evaluator") == "AgentResponseEvaluator":
            return e
    raise RuntimeError(f"task {task.get('task_id')} has no AgentResponseEvaluator")


def normalize_url_shape(url):
    if isinstance(url, list):
        return "ALT_URL"
    if not isinstance(url, str):
        return None
    if url.startswith("^"):
        return "REGEX_URL"
    return re.sub(r"__[^_]+__", "__SITE__", url)


def normalize_eval(e: dict) -> dict:
    kind = e.get("evaluator")
    out = {"evaluator": kind}
    if kind == "AgentResponseEvaluator":
        expected = e.get("expected", {})
        out.update(
            task_type=expected.get("task_type"),
            status=expected.get("status"),
            ordered=bool(e.get("ordered", False)),
            schema=e.get("results_schema"),
        )
    elif kind == "NetworkEventEvaluator":
        expected = e.get("expected", {})
        out.update(
            http_method=expected.get("http_method"),
            response_status=expected.get("response_status"),
            url_shape=normalize_url_shape(expected.get("url")),
            has_query=expected.get("query_params") is not None,
            has_post=expected.get("post_data") is not None,
            query_schema=e.get("query_params_schema"),
            post_schema=e.get("post_data_schema"),
            last_event_only=bool(e.get("last_event_only", False)),
            should_not_exist=bool(e.get("should_not_exist", False)),
        )
    else:
        out["keys"] = sorted(k for k in e if k != "expected")
    return out


def consequence_signature(task: dict) -> str:
    """Candidate quotient key.

    This records what the official evaluator can distinguish at the obligation
    *shape* level. It intentionally omits concrete expected values, so equality
    here does NOT prove task equivalence. It only nominates a shared capability
    family for a live separator experiment.
    """
    obj = {
        "sites": sorted(task.get("sites", [])),
        "evals": [normalize_eval(e) for e in task.get("eval", [])],
    }
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def coverage(rows: list[dict], total: int) -> dict:
    out = {}
    running = 0
    for i, row in enumerate(rows, start=1):
        running += row["count"]
        if i in {5, 10, 20, 30, 40, 50}:
            out[str(i)] = {
                "tasks": running,
                "fraction": round(running / total, 6),
                "percent": round(100 * running / total, 1),
            }
    return out


def main() -> None:
    tasks = load_tasks()
    by_type = Counter()
    by_status = Counter()
    by_site = Counter()
    template_groups: dict[str, dict] = {}
    consequence_groups: dict[str, dict] = {}

    for task in tasks:
        ae = agent_eval(task)
        expected = ae.get("expected", {})
        task_type = expected.get("task_type", "UNKNOWN")
        status = expected.get("status", "UNKNOWN")
        by_type[task_type] += 1
        by_status[status] += 1
        by_site.update(task.get("sites", []))

        tid = str(task.get("intent_template_id"))
        g = template_groups.setdefault(
            tid,
            {
                "intent_template_id": task.get("intent_template_id"),
                "intent_template": task.get("intent_template"),
                "count": 0,
                "task_ids": [],
                "sites": set(),
                "types": Counter(),
                "statuses": Counter(),
                "network_evaluators": 0,
            },
        )
        g["count"] += 1
        g["task_ids"].append(task.get("task_id"))
        g["sites"].update(task.get("sites", []))
        g["types"][task_type] += 1
        g["statuses"][status] += 1
        g["network_evaluators"] += sum(
            1 for e in task.get("eval", []) if e.get("evaluator") == "NetworkEventEvaluator"
        )

        sig = consequence_signature(task)
        cg = consequence_groups.setdefault(
            sig,
            {
                "count": 0,
                "task_ids": [],
                "intent_template_ids": set(),
                "sites": sorted(task.get("sites", [])),
                "evals": [normalize_eval(e) for e in task.get("eval", [])],
            },
        )
        cg["count"] += 1
        cg["task_ids"].append(task.get("task_id"))
        cg["intent_template_ids"].add(task.get("intent_template_id"))

    template_rows = []
    for g in template_groups.values():
        avg_net = g["network_evaluators"] / g["count"]
        frontier_score = g["count"] / (1.0 + avg_net)
        template_rows.append(
            {
                "intent_template_id": g["intent_template_id"],
                "intent_template": g["intent_template"],
                "count": g["count"],
                "task_ids": g["task_ids"],
                "sites": sorted(g["sites"]),
                "types": dict(g["types"]),
                "statuses": dict(g["statuses"]),
                "avg_network_evaluators": round(avg_net, 3),
                "frontier_score": round(frontier_score, 3),
            }
        )

    repeated = sorted(
        template_rows, key=lambda x: (-x["count"], str(x["intent_template_id"]))
    )
    frontier = sorted(
        template_rows, key=lambda x: (-x["frontier_score"], -x["count"])
    )

    consequence_rows = []
    for g in consequence_groups.values():
        consequence_rows.append(
            {
                "count": g["count"],
                "task_ids": g["task_ids"],
                "intent_template_ids": sorted(
                    g["intent_template_ids"], key=lambda x: str(x)
                ),
                "sites": g["sites"],
                "evals": g["evals"],
            }
        )
    consequence_rows.sort(key=lambda x: (-x["count"], x["task_ids"]))

    out = {
        "authority": {
            "repo": "ServiceNow/webarena-verified",
            "commit": UPSTREAM_SHA,
            "dataset_url": DATASET_URL,
            "task_count": len(tasks),
        },
        "epistemic_boundary": {
            "template_groups": "syntactic recurrence only",
            "consequence_signatures": (
                "candidate capability families defined by evaluator-obligation "
                "shape; NOT proved future-equivalence and NOT solved-task claims"
            ),
        },
        "summary": {
            "intent_templates": len(template_groups),
            "candidate_consequence_signatures": len(consequence_groups),
            "task_types": dict(by_type),
            "expected_statuses": dict(by_status),
            "sites": dict(by_site),
            "coverage_by_top_templates": coverage(repeated, len(tasks)),
            "coverage_by_top_consequence_signatures": coverage(
                consequence_rows, len(tasks)
            ),
        },
        "template_frontier": frontier,
        "templates_by_recurrence": repeated,
        "candidate_consequence_families": consequence_rows,
    }

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / "webarena_verified_residual_map.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(out["summary"], indent=2, sort_keys=True))
    print("\nLargest candidate consequence families:")
    for row in consequence_rows[:15]:
        print(
            f"count={row['count']} templates={row['intent_template_ids']} "
            f"ids={row['task_ids']}"
        )
    print("\nTop static template frontier:")
    for row in frontier[:15]:
        print(
            f"template={row['intent_template_id']} count={row['count']} "
            f"avg_net={row['avg_network_evaluators']} score={row['frontier_score']} "
            f"ids={row['task_ids']}"
        )
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
