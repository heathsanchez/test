#!/usr/bin/env python3
"""
Close ACC Reach V2 without rerunning the timed-out mask6 candidate.

A developmental candidate is inadmissible as soon as any protected replay
obligation fails.  mask6 completed the entire prospective pack with zero hits
and then failed protected replay on ac-08551 and ac-04629 before the job timer
expired on the third replay case.  Those preserved failures are sufficient to
reject mask6; executing the remaining replay obligation cannot restore
admissibility because replay is conjunctive.
"""
import argparse
import glob
import json
import re
from pathlib import Path

EXPECTED = ["current", "depth025"] + [f"mask{i}" for i in range(1, 8)]


def save(p, o):
    Path(p).write_text(json.dumps(o, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dominates(a, b):
    # Developmental objective:
    # maximize strict frozen consequences and verified prospective reach;
    # minimize search nodes and certificate burden.
    dims_ok = (
        a["strict_rows_frozen"] >= b["strict_rows_frozen"]
        and a["verified_prospective"] >= b["verified_prospective"]
        and a["total_nodes"] <= b["total_nodes"]
        and a["total_atomic_length_prospective"] <= b["total_atomic_length_prospective"]
    )
    strict = (
        a["strict_rows_frozen"] > b["strict_rows_frozen"]
        or a["verified_prospective"] > b["verified_prospective"]
        or a["total_nodes"] < b["total_nodes"]
        or a["total_atomic_length_prospective"] < b["total_atomic_length_prospective"]
    )
    return dims_ok and strict


def parse_mask6_log(path):
    rows = []
    for line in Path(path).read_text(errors="replace").splitlines():
        if "REACH_V2_TARGET " not in line:
            continue
        raw = line.split("REACH_V2_TARGET ", 1)[1]
        try:
            rows.append(json.loads(raw))
        except Exception:
            pass
    prospective = [r for r in rows if r.get("role") == "prospective"]
    replay = [r for r in rows if r.get("role") == "protected_replay"]
    if len(prospective) != 8:
        raise RuntimeError(f"mask6 prospective evidence incomplete: {len(prospective)}")
    if any(r.get("quotient") for r in prospective):
        raise RuntimeError("unexpected mask6 prospective quotient hit")
    if not replay:
        raise RuntimeError("mask6 has no preserved replay evidence")
    failed = [r["cid"] for r in replay if not r.get("quotient")]
    if not failed:
        raise RuntimeError("mask6 replay rejection not established")
    return rows, prospective, replay, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports-glob", required=True)
    ap.add_argument("--mask6-log", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    reports = {}
    for p in glob.glob(a.reports_glob, recursive=True):
        try:
            r = json.loads(Path(p).read_text())
        except Exception:
            continue
        pol = r.get("policy")
        if pol in EXPECTED and pol != "mask6":
            reports[pol] = r

    missing_non6 = [p for p in EXPECTED if p != "mask6" and p not in reports]
    if missing_non6:
        raise RuntimeError(f"missing completed policies: {missing_non6}")

    rows, prospective, replay, failed_replay = parse_mask6_log(a.mask6_log)
    reports["mask6"] = {
        "experiment": "ACC_REACH_V2_ANONYMOUS_SUBSET_PRIORITY",
        "policy": "mask6",
        "policy_kind": "reach_v2_anonymous_subset_sum",
        "policy_mask": 6,
        "policy_expression": "long+depth",
        "prospective_targets": 8,
        "protected_controls_attempted": [r["cid"] for r in replay],
        "protected_replay_ok": False,
        "replay_rejection_witnesses": failed_replay,
        "candidate_decision_complete": True,
        "candidate_decision_basis": (
            "Conjunctive protected replay already falsified; remaining replay "
            "obligations cannot restore admissibility."
        ),
        "all_targets_processed": False,
        "quotient_hits_prospective": 0,
        "verified_prospective": 0,
        "strict_ac_frozen": 0,
        "strict_stable_frozen": 0,
        "strict_rows_frozen": 0,
        "total_nodes": sum(int(r.get("nodes", 0)) for r in rows),
        "total_atomic_length_prospective": 0,
    }

    decision_complete = all(
        r.get("all_targets_processed") is True
        or r.get("candidate_decision_complete") is True
        for r in reports.values()
    )
    language_complete = decision_complete and len(reports) == 9

    admissible = [r for r in reports.values() if r.get("protected_replay_ok") is True]
    adequate = [r for r in admissible if int(r.get("strict_rows_frozen", 0)) > 0]
    adequate_masks = [r for r in adequate if str(r["policy"]).startswith("mask")]

    frontier = []
    for x in admissible:
        if not any(dominates(y, x) for y in admissible if y["policy"] != x["policy"]):
            frontier.append(x)
    frontier.sort(key=lambda r: r["policy"])

    if adequate_masks:
        transition = "REACH_V2_ADEQUATE_CONTINUATION_FOUND"
        permission = "ADMIT_MINIMIZE_COMPILE"
    elif adequate:
        transition = "CURRENT_REACH_SETTLES_FROZEN_PACK"
        permission = "NO_NOVEL_DEVELOPMENT_REQUIRED"
    elif language_complete:
        transition = "REACH_V2_OBSTRUCTION_CERTIFIED"
        permission = "RECURSE_ON_REACH_V2_AUTHORIZED"
    else:
        transition = "UNKNOWN_EXPRESSIVITY"
        permission = "NO_RECURSION_LICENSE"

    summary = []
    for pol in EXPECTED:
        r = reports[pol]
        summary.append({
            "policy": pol,
            "expression": r.get("policy_expression"),
            "replay_ok": r.get("protected_replay_ok"),
            "decision_complete": bool(
                r.get("all_targets_processed") is True
                or r.get("candidate_decision_complete") is True
            ),
            "verified_prospective": r.get("verified_prospective"),
            "strict_rows_frozen": r.get("strict_rows_frozen"),
            "total_nodes": r.get("total_nodes"),
            "total_atomic_length_prospective": r.get("total_atomic_length_prospective"),
            "pareto_frontier": any(x["policy"] == pol for x in frontier),
            "replay_rejection_witnesses": r.get("replay_rejection_witnesses", []),
        })

    report = {
        "experiment": "ACC_REACH_V2_FORMAL_CLOSE",
        "declared_language": (
            "All seven non-empty unit-coefficient subset sums of "
            "(shorter_relator_length,longer_relator_length,quotient_depth)."
        ),
        "declared_language_complete": language_complete,
        "candidate_decisions_complete": decision_complete,
        "candidate_count": len(reports),
        "admissible_replay_clean": [r["policy"] for r in admissible],
        "adequate_policies": [r["policy"] for r in adequate],
        "adequate_anonymous_policies": [r["policy"] for r in adequate_masks],
        "pareto_frontier": [r["policy"] for r in frontier],
        "mask6_early_rejection": True,
        "mask6_replay_rejection_witnesses": failed_replay,
        "transition": transition,
        "permission": permission,
        "next_action": (
            "Develop the next causally upstream pre-quotient object: the "
            "proposal-admission guard itself. Exhaust the smallest anonymous "
            "Boolean one-site edit language over the existing boundary-"
            "cancellation predicate before introducing richer structure."
            if transition == "REACH_V2_OBSTRUCTION_CERTIFIED" else
            "Follow the transition-specific warrant."
        ),
        "scope": (
            "This obstruction is only to ACC_REACH_V2_ANONYMOUS_SUBSET_PRIORITY "
            "on the frozen prospective pack. It does not establish unrestricted "
            "search or expressive inadequacy."
        ),
        "unrestricted_search_inadequacy_certified": False,
    }
    save(out / "policy_summary.json", summary)
    save(out / "report.json", report)
    save(out / "mask6_rejection_certificate.json", reports["mask6"])
    print("REACH_V2_FORMAL_CLOSE", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
