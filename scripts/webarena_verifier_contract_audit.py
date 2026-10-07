#!/usr/bin/env python3
"""Audit whether explicit task-output contracts agree with WebArena-Verified evaluator authority.

This is a frozen, benchmark-specific diagnostic used to test a broader claim:
a scalable verifier can drive improvement, but verifier score is not itself
evidence that the optimized behavior preserves the user's declared contract.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def quoted_keys(spec: str) -> list[str]:
    if not re.search(r"\bkeys?\b", spec, flags=re.IGNORECASE):
        return []
    return list(dict.fromkeys(re.findall(r'"([^"]+)"', spec)))


def expected_object_keys(evaluator: dict) -> list[str] | None:
    data = evaluator.get("expected", {}).get("retrieved_data")
    if not isinstance(data, list) or not data:
        return None
    if not all(isinstance(row, dict) for row in data):
        return None
    # Require one stable object shape across the expected rows.
    shapes = {tuple(sorted(row.keys())) for row in data}
    if len(shapes) != 1:
        return None
    return list(next(iter(shapes)))


def audit(tasks: list[dict]) -> dict:
    checked = []
    mismatches = []
    for task in tasks:
        spec = str(task.get("instantiation_dict", {}).get("retrieved_data_format_spec", ""))
        requested = sorted(quoted_keys(spec))
        if not requested:
            continue
        for evaluator in task.get("eval", []):
            if evaluator.get("evaluator") != "AgentResponseEvaluator":
                continue
            expected = expected_object_keys(evaluator)
            if expected is None:
                continue
            expected = sorted(expected)
            row = {
                "task_id": int(task["task_id"]),
                "intent_template_id": int(task["intent_template_id"]),
                "requested_keys": requested,
                "evaluator_expected_keys": expected,
            }
            checked.append(row)
            if requested != expected:
                row = {
                    **row,
                    "intent": task.get("intent"),
                    "retrieved_data_format_spec": spec,
                    "expected_retrieved_data": evaluator.get("expected", {}).get("retrieved_data"),
                }
                mismatches.append(row)

    return {
        "epistemic_state": "WARRANTED_BOUNDED",
        "boundary": "explicit quoted output-key contracts vs AgentResponseEvaluator expected object keys",
        "total_tasks": len(tasks),
        "checked_contracts": len(checked),
        "match_count": len(checked) - len(mismatches),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    tasks = json.loads(Path(args.dataset).read_text())
    result = audit(tasks)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

    # Frozen qualification boundary for upstream 6473f72...
    assert result["total_tasks"] == 812, result
    assert result["checked_contracts"] == 86, result
    assert result["mismatch_count"] == 1, result
    mismatch = result["mismatches"][0]
    assert mismatch["task_id"] == 203, result
    assert mismatch["requested_keys"] == ["order_id", "purchase_date"], result
    assert mismatch["evaluator_expected_keys"] == ["date", "order_id"], result


if __name__ == "__main__":
    main()
