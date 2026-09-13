#!/usr/bin/env python3
import argparse
import glob
import json
from pathlib import Path

EXPECTED = ["current", "depth025"] + [f"mask{i}" for i in range(1, 8)]


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dominates(a, b):
    # Higher strict rows and verified reach are better; lower nodes are better.
    no_worse = (
        a["strict_rows_frozen"] >= b["strict_rows_frozen"]
        and a["verified_prospective"] >= b["verified_prospective"]
        and a["total_nodes"] <= b["total_nodes"]
    )
    strictly = (
        a["strict_rows_frozen"] > b["strict_rows_frozen"]
        or a["verified_prospective"] > b["verified_prospective"]
        or a["total_nodes"] < b["total_nodes"]
    )
    return no_worse and strictly


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    reports = {}
    result_rows = {}
    paths = {}
    for rp in sorted(glob.glob(a.glob, recursive=True)):
        p = Path(rp)
        try:
            rep = json.loads(p.read_text())
        except Exception:
            continue
        pol = rep.get("policy")
        if pol not in EXPECTED:
            continue
        reports[pol] = rep
        base = p.parent
        rfile = base / "results.json"
        pfile = base / "paths.json"
        if rfile.exists():
            result_rows[pol] = json.loads(rfile.read_text())
        if pfile.exists():
            paths[pol] = json.loads(pfile.read_text())

    missing = [x for x in EXPECTED if x not in reports]
    if missing:
        raise RuntimeError(f"missing policies: {missing}")

    complete = all(reports[p].get("all_targets_processed") for p in EXPECTED)
    masks_complete = all(f"mask{i}" in reports for i in range(1, 8))
    current = reports["current"]

    admissible = [
        reports[p] for p in EXPECTED
        if reports[p].get("protected_replay_ok") is True
    ]
    frontier = []
    for x in admissible:
        if not any(dominates(y, x) for y in admissible if y["policy"] != x["policy"]):
            frontier.append(x)
    frontier.sort(key=lambda x: (
        -x["strict_rows_frozen"],
        -x["verified_prospective"],
        x["total_nodes"],
        x["policy"],
    ))

    adequate = [x for x in admissible if x["strict_rows_frozen"] > 0]
    adequate_masks = [x for x in adequate if x["policy"].startswith("mask")]

    def strict_cells(policy):
        cells = set()
        for r in result_rows.get(policy, []):
            if r.get("role") != "prospective":
                continue
            if r.get("strict_ac_frozen"):
                cells.add(("ac", r["challenge_id"]))
            if r.get("strict_stable_frozen"):
                cells.add(("stable_ac", r["stable_id"]))
        return cells

    current_cells = strict_cells("current")
    novel = {}
    for i in range(1, 8):
        pol = f"mask{i}"
        cells = strict_cells(pol) - current_cells
        novel[pol] = sorted([{"problem": k, "challenge_id": cid} for k, cid in cells],
                            key=lambda z: (z["problem"], z["challenge_id"]))

    if adequate_masks:
        transition = "REACH_V2_ADEQUATE_CONTINUATION_FOUND"
        permission = "ADMIT_MINIMIZE_COMPILE"
        next_action = (
            "Admit every replay-clean adequate anonymous policy, retain the "
            "Pareto-undominated frontier, publish only fresh verifier-clean "
            "strict consequences, and prospectively reuse the surviving policy."
        )
    elif adequate:
        transition = "CURRENT_REACH_SETTLES_FROZEN_PACK"
        permission = "NO_DEVELOPMENT_REQUIRED_FOR_THIS_PACK"
        next_action = (
            "The frozen encounter is already settled by an existing policy. "
            "Publish fresh strict consequences; do not promote a novel policy "
            "without prospective advantage."
        )
    elif complete and masks_complete:
        transition = "REACH_V2_OBSTRUCTION_CERTIFIED"
        permission = "RECURSE_ON_REACH_V2_AUTHORIZED"
        next_action = (
            "The complete anonymous unit-subset priority language failed to "
            "produce any replay-clean strict record consequence on the frozen "
            "prospective pack. Make this Reach V2 language the next developable "
            "object; do not claim unrestricted search inadequacy."
        )
    else:
        transition = "UNKNOWN_EXPRESSIVITY"
        permission = "NO_RECURSION_LICENSE"
        next_action = "Complete the declared Reach V2 candidate language first."

    # Select the shortest verifier-clean AC certificate for every target that
    # was a strict AC or Stable consequence under at least one admissible policy.
    strict_target_ids = set()
    for x in adequate:
        for r in result_rows.get(x["policy"], []):
            if r.get("role") == "prospective" and (
                r.get("strict_ac_frozen") or r.get("strict_stable_frozen")
            ):
                strict_target_ids.add(r["challenge_id"])

    best = {}
    best_policy = {}
    for x in admissible:
        pol = x["policy"]
        pmap = paths.get(pol, {})
        rmap = {r["challenge_id"]: r for r in result_rows.get(pol, [])
                if r.get("role") == "prospective"}
        for cid in strict_target_ids:
            moves = pmap.get(cid)
            rr = rmap.get(cid)
            if moves is None or rr is None:
                continue
            if (rr.get("ac_verdict") or {}).get("ok") is not True:
                continue
            if cid not in best or len(moves) < len(best[cid]):
                best[cid] = moves
                best_policy[cid] = pol

    submission_text = "".join(
        f"{cid}: {json.dumps(moves,separators=(',',':'))}\n"
        for cid, moves in sorted(best.items())
    )
    (out / "best_strict_ac.txt").write_text(submission_text, encoding="utf-8")

    summary_rows = []
    for p in EXPECTED:
        r = reports[p]
        summary_rows.append({
            "policy": p,
            "policy_kind": r.get("policy_kind"),
            "policy_expression": r.get("policy_expression"),
            "protected_replay_ok": r.get("protected_replay_ok"),
            "quotient_hits_prospective": r.get("quotient_hits_prospective"),
            "verified_prospective": r.get("verified_prospective"),
            "strict_rows_frozen": r.get("strict_rows_frozen"),
            "strict_ac_frozen": r.get("strict_ac_frozen"),
            "strict_stable_frozen": r.get("strict_stable_frozen"),
            "total_nodes": r.get("total_nodes"),
            "novel_strict_vs_current": novel.get(p, []),
            "pareto_frontier": any(z["policy"] == p for z in frontier),
        })

    report = {
        "experiment": "ACC_REACH_V2_ANONYMOUS_SUBSET_PRIORITY_SYNTHESIS",
        "declared_language_complete": bool(complete and masks_complete),
        "candidate_policies": len(reports),
        "anonymous_candidates_exhausted": 7 if masks_complete else sum(
            f"mask{i}" in reports for i in range(1, 8)
        ),
        "admissible_replay_clean": [x["policy"] for x in admissible],
        "adequate_policies": [x["policy"] for x in adequate],
        "adequate_anonymous_policies": [x["policy"] for x in adequate_masks],
        "pareto_frontier": [x["policy"] for x in frontier],
        "current_strict_rows": current.get("strict_rows_frozen"),
        "novel_strict_cells_vs_current": novel,
        "strict_targets_for_fresh_recheck": sorted(strict_target_ids),
        "best_policy_by_strict_target": best_policy,
        "transition": transition,
        "permission": permission,
        "next_action": next_action,
        "scope": (
            "Authority is limited to the frozen prospective target pack and "
            "ACC_REACH_V2_ANONYMOUS_SUBSET_PRIORITY: all seven non-empty "
            "unit-coefficient subset sums of (shorter relator length, longer "
            "relator length, quotient depth), with protected replay."
        ),
        "unrestricted_search_inadequacy_certified": False,
    }

    save(out / "policy_summary.json", summary_rows)
    save(out / "report.json", report)
    print("REACH_V2_SYNTHESIS", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
