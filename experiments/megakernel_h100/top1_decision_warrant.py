"""MathGraph decision-level warrant for a pinned megakernel observation.

A reference top-1 margin m and observed uniform logit error e prove stability
through the interval condition m > 2e. This is only an observation-specific
error envelope; it is NOT a bound for future model inputs or GPU runs.
"""
import argparse
import json
import math
from pathlib import Path

PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"


def qualify(report, check_name):
    base = {
        "schema": "mathgraph-top1-decision-warrant-v1",
        "check": check_name,
        "status": "UNKNOWN",
        "scope": "single observed full-depth synthetic model execution",
        "future_input_guarantee": False,
    }
    if report.get("source_pin") != PIN or report.get("sm_count") != 132 or report.get("runpod_status") != "COMPLETED":
        base["status"] = "UNKNOWN_RUN_PROVENANCE"
        return base
    c = report.get("checks", {}).get(check_name)
    if not isinstance(c, dict) or c.get("source_commit") != PIN:
        base["status"] = "UNKNOWN_CHECK_PROVENANCE"
        return base
    if (c.get("fixture_layers"), c.get("executed_layers")) != (16, 16) or c.get("lm_head_exercised") is not True:
        base["status"] = "UNKNOWN_NOT_FULL_LMHEAD_SCOPE"
        return base
    if not isinstance(c.get("pyvm_completed_calls"), int) or c["pyvm_completed_calls"] < 1:
        base["status"] = "UNKNOWN_REFERENCE_UNEXECUTED"
        return base

    choice = c.get("logit_choice")
    metrics = c.get("fields", {}).get("logits")
    if not isinstance(choice, dict) or not isinstance(metrics, dict):
        base["status"] = "UNKNOWN_NO_LOGIT_OBSERVATION"
        return base
    n = metrics.get("elements")
    e = metrics.get("max_abs_diff")
    m = choice.get("reference_top1_margin")
    r = choice.get("reference_top1")
    g = choice.get("native_top1")
    if (not isinstance(n, int) or n < 2
        or not isinstance(r, int) or not isinstance(g, int)
        or not 0 <= r < n or not 0 <= g < n
        or not isinstance(e, (int, float)) or not math.isfinite(e) or e < 0
        or not isinstance(m, (int, float)) or not math.isfinite(m) or m < 0):
        base["status"] = "UNKNOWN_INVALID_NUMERIC_EVIDENCE"
        return base
    if metrics.get("nonfinite") != 0:
        base["status"] = "UNKNOWN_NONFINITE"
        return base

    base.update({
        "reference_top1": r,
        "native_top1": g,
        "reference_margin": float(m),
        "observed_uniform_error": float(e),
        "required_margin_strictly_greater_than": 2 * float(e),
        "observed_action_agreement": r == g,
    })
    if r != g:
        base["status"] = "REJECTED_ACTION_DISAGREEMENT"
    elif m > 2 * e:
        base["status"] = "BOUNDED_ENVELOPE_STABILITY_CERTIFIED"
    else:
        base["status"] = "OBSERVED_MATCH_ENVELOPE_INCONCLUSIVE"
    return base


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--check", action="append")
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    keys = a.check or sorted(report.get("checks", {}))
    results = [qualify(report, key) for key in keys]
    payload = {"schema": "mathgraph-top1-decision-audit-v1", "results": results}
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if all(x["status"] in (
        "BOUNDED_ENVELOPE_STABILITY_CERTIFIED",
        "OBSERVED_MATCH_ENVELOPE_INCONCLUSIVE"
    ) for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
