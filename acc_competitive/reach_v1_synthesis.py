#!/usr/bin/env python3
"""Synthesize the single missing equivalence class of ACC_REACH_V1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text())


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reach", required=True)
    ap.add_argument("--candidate-runs-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    reach = load(args.reach)
    candidates = reach["candidate_targets"]
    root = Path(args.candidate_runs_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    results = []
    missing = []
    quotient_hits = []
    strict = []
    verified_noncompetitive = []
    saturated = []

    for c in candidates:
        cid = c["challenge_id"]
        matches = list(root.rglob(f"{cid}/search_results.json"))
        if len(matches) != 1:
            missing.append({"challenge_id": cid, "matches": [str(x) for x in matches]})
            continue
        rows = load(matches[0])
        if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("challenge_id") != cid:
            raise SystemExit(f"malformed candidate result for {cid}: {matches[0]}")
        r = rows[0]
        q = bool(r.get("quotient_found"))
        ok = bool((r.get("ac_verdict") or {}).get("ok"))
        n = r.get("atomic_length") if ok else None
        frozen = c.get("frozen_best")

        if ok and isinstance(n, int) and isinstance(frozen, int) and n < frozen:
            typ = "STRICT_VERIFIED_WIN"
            strict.append(cid)
        elif ok and isinstance(n, int):
            typ = "VERIFIED_BUT_NONCOMPETITIVE"
            verified_noncompetitive.append(cid)
        elif q:
            typ = "QUOTIENT_HIT_NOT_VERIFIED"
            quotient_hits.append(cid)
        elif (r.get("nodes") or 0) >= (r.get("max_nodes") or 10**30):
            typ = "SATURATED_NO_QUOTIENT"
            saturated.append(cid)
        else:
            typ = "INCOMPLETE_EXECUTION"

        results.append({
            "challenge_id": cid,
            "typed_result": typ,
            "frozen_best": frozen,
            "nodes": r.get("nodes"),
            "max_nodes": r.get("max_nodes"),
            "quotient_found": q,
            "verified": ok,
            "atomic_length": n,
            "effective_quotient_total_cap": r.get("quotient_total_cap"),
            "depth_weight": r.get("depth_weight"),
            "compiler_beam": r.get("compiler_beam"),
            "source": str(matches[0]),
        })
        if q and cid not in quotient_hits:
            quotient_hits.append(cid)

    complete_execution = not missing and len(results) == len(candidates) and not any(
        r["typed_result"] == "INCOMPLETE_EXECUTION" for r in results
    )

    if strict:
        transition = "ADEQUATE_CONTINUATION_FOUND_IN_REACH_V1"
        permission = "RETAIN_VERIFIED_WIN; DO_NOT_EXPAND_REACH"
        next_action = "Verify fresh competitiveness and retain the successful current-Reach continuation."
        reach_obstruction = False
    elif not complete_execution:
        transition = "UNKNOWN_EXPRESSIVITY"
        permission = "NO_REACH_EXPANSION_LICENSE"
        next_action = "Complete the frozen Reach V1 candidate executions."
        reach_obstruction = False
    elif quotient_hits:
        transition = "REACH_V1_REFINED_BY_QUOTIENT_HIT"
        permission = "DOWNSTREAM_CLOSURE_ONLY; NO_NEW_MECHANISM"
        next_action = (
            "For quotient-hit residuals, exhaust only the already-admitted downstream "
            "compiler/reverse value closure before changing Reach V1."
        )
        reach_obstruction = False
    elif len(saturated) == len(candidates):
        transition = "REACH_V1_OBSTRUCTION_CERTIFIED"
        permission = "RECURSE_ON_REACH_V1_AUTHORIZED"
        next_action = (
            "The frozen finite closure of already-admitted pre-quotient parameter values "
            "is exhausted on all certified residuals. Make Reach V1 itself the next "
            "developable object; do not claim unrestricted expressive inadequacy."
        )
        reach_obstruction = True
    else:
        transition = "UNKNOWN_EXPRESSIVITY"
        permission = "NO_REACH_EXPANSION_LICENSE"
        next_action = "Residual outcomes do not yet certify a complete Reach V1 obstruction."
        reach_obstruction = False

    report = {
        "experiment": "ACC_REACH_V1_MISSING_CLASS_SYNTHESIS",
        "reach_id": reach["reach_id"],
        "candidate_count": len(candidates),
        "result_count": len(results),
        "complete_execution": complete_execution,
        "strict_verified_wins": strict,
        "verified_noncompetitive": verified_noncompetitive,
        "quotient_hits": sorted(set(quotient_hits)),
        "saturated_no_quotient": saturated,
        "reach_v1_obstruction_certified": reach_obstruction,
        "unrestricted_expressive_inadequacy_certified": False,
        "transition": transition,
        "permission": permission,
        "next_action": next_action,
        "scope": (
            "Authority is limited to ACC_REACH_V1_EXISTING_VALUE_CLOSURE: the finite "
            "closure of parameter VALUES already admitted by the completed portfolio."
        ),
    }
    dump(out / "typed_results.json", results)
    dump(out / "report.json", report)
    print("REACH_V1_SYNTHESIS", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
