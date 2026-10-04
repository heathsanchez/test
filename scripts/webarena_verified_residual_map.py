#!/usr/bin/env python3
"""Compile the pinned WebArena-Verified hard subset into capability families.

No model calls. No benchmark execution. This is a static residual map only.
"""

from __future__ import annotations

import json
import urllib.request
from collections import Counter, defaultdict
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


def main() -> None:
    tasks = load_tasks()
    by_type = Counter()
    by_status = Counter()
    by_site = Counter()
    groups: dict[str, dict] = {}

    for task in tasks:
        ae = agent_eval(task)
        expected = ae.get("expected", {})
        task_type = expected.get("task_type", "UNKNOWN")
        status = expected.get("status", "UNKNOWN")
        by_type[task_type] += 1
        by_status[status] += 1
        by_site.update(task.get("sites", []))

        tid = str(task.get("intent_template_id"))
        g = groups.setdefault(
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

    rows = []
    for g in groups.values():
        avg_net = g["network_evaluators"] / g["count"]
        # Static triage heuristic only: reward recurrence, penalize multi-event execution.
        frontier_score = g["count"] / (1.0 + avg_net)
        rows.append(
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

    repeated = sorted(rows, key=lambda x: (-x["count"], x["intent_template_id"]))
    frontier = sorted(rows, key=lambda x: (-x["frontier_score"], -x["count"]))

    coverage = {}
    running = 0
    for i, row in enumerate(repeated, start=1):
        running += row["count"]
        if i in {5, 10, 20, 30, 40, 50}:
            coverage[str(i)] = {
                "tasks": running,
                "fraction": round(running / len(tasks), 6),
                "percent": round(100 * running / len(tasks), 1),
            }

    out = {
        "authority": {
            "repo": "ServiceNow/webarena-verified",
            "commit": UPSTREAM_SHA,
            "dataset_url": DATASET_URL,
            "task_count": len(tasks),
        },
        "summary": {
            "intent_templates": len(groups),
            "task_types": dict(by_type),
            "expected_statuses": dict(by_status),
            "sites": dict(by_site),
            "coverage_by_top_templates": coverage,
        },
        "frontier": frontier,
        "templates_by_recurrence": repeated,
    }

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / "webarena_verified_residual_map.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(out["summary"], indent=2, sort_keys=True))
    print("\nTop static frontier:")
    for row in frontier[:15]:
        print(
            f"template={row['intent_template_id']} count={row['count']} "
            f"avg_net={row['avg_network_evaluators']} score={row['frontier_score']} "
            f"ids={row['task_ids']}"
        )
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
