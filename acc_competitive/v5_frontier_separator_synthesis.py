#!/usr/bin/env python3
import argparse
import glob
import json
from pathlib import Path

POLICIES = ("current", "mask3")


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verified_lengths(row):
    vals = []
    for t in row.get("compiler_trials", []):
        if (t.get("ac_verdict") or {}).get("ok") is True:
            vals.append((int(t["beam"]), int(t["atomic_length"])))
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--selection", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    selection = json.loads(Path(a.selection).read_text())
    expected_ids = [x["challenge_id"] for x in selection]
    roles = {x["challenge_id"]: x["role"] for x in selection}

    rows = {}
    paths = {}
    for fp in glob.glob(a.glob, recursive=True):
        try:
            r = json.loads(Path(fp).read_text())
        except Exception:
            continue
        if r.get("experiment") != "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1":
            continue
        key = (r["challenge_id"], r["policy"])
        rows[key] = r
        cand = Path(fp).parent / "candidate_ac.txt"
        if cand.exists() and r.get("best_atomic_length") is not None:
            line = cand.read_text().strip()
            old = paths.get(r["challenge_id"])
            n = int(r["best_atomic_length"])
            if old is None or n < old[0]:
                paths[r["challenge_id"]] = (n, line, r["policy"])

    missing = [
        {"challenge_id": cid, "policy": p}
        for cid in expected_ids for p in POLICIES
        if (cid, p) not in rows
    ]

    target_reports = []
    separators = []
    for cid in expected_ids:
        c = rows.get((cid, "current"))
        m = rows.get((cid, "mask3"))
        tr = {
            "challenge_id": cid,
            "role": roles[cid],
            "current_present": c is not None,
            "mask3_present": m is not None,
        }
        if c is None or m is None:
            tr["warrant_class"] = "UNKNOWN_SEARCH"
            tr["reason"] = "matched policy execution incomplete"
            target_reports.append(tr)
            continue

        cq = bool(c.get("quotient_found"))
        mq = bool(m.get("quotient_found"))
        tr.update({
            "current_quotient": cq,
            "mask3_quotient": mq,
            "current_nodes": c.get("nodes"),
            "mask3_nodes": m.get("nodes"),
            "current_qsteps": c.get("quotient_steps"),
            "mask3_qsteps": m.get("quotient_steps"),
            "current_path_hash": c.get("quotient_path_sha256"),
            "mask3_path_hash": m.get("quotient_path_sha256"),
            "current_best_atomic": c.get("best_atomic_length"),
            "mask3_best_atomic": m.get("best_atomic_length"),
            "current_gap_ac": c.get("best_gap_ac_frozen"),
            "mask3_gap_ac": m.get("best_gap_ac_frozen"),
        })

        cls = []
        if cq != mq:
            cls.append("SEARCH_REACHABILITY_SEPARATOR")
        if cq and mq and c.get("quotient_path_sha256") != m.get("quotient_path_sha256"):
            cls.append("QUOTIENT_ROUTE_SEPARATOR")

        for label, r in (("current", c), ("mask3", m)):
            vl = verified_lengths(r)
            if len({n for _, n in vl}) > 1:
                cls.append(f"COMPILER_BEAM_SEPARATOR:{label}")
                tr[f"{label}_beam_lengths"] = dict(vl)

        ca = c.get("best_atomic_length")
        ma = m.get("best_atomic_length")
        if isinstance(ca, int) and isinstance(ma, int) and ca != ma:
            cls.append("FINAL_ATOMIC_COST_SEPARATOR")

        if cq and mq and not isinstance(ca, int) and not isinstance(ma, int):
            cls.append("COMPILER_OR_TERMINAL_BLOCKAGE_COMMON")
        elif (cq and not isinstance(ca, int)) != (mq and not isinstance(ma, int)):
            cls.append("COMPILER_OR_TERMINAL_SEPARATOR")

        tr["separators"] = cls
        if cls:
            tr["warrant_class"] = "VERIFIED_SEPARATOR_WITHIN_FROZEN_SCOPE"
            separators.append({"challenge_id": cid, "separators": cls})
        else:
            tr["warrant_class"] = "BOUNDED_NON_SEPARATION"
            tr["reason"] = "no tested distinction separated the two retained policies on this frozen target"
        target_reports.append(tr)

    # A frozen finite test cannot license unrestricted adequacy/inadequacy.
    complete = len(missing) == 0
    global_class = "MATCHED_SCOPE_CLASSIFIED" if complete else "UNKNOWN_SEARCH"

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "best_verified_ac.txt").write_text(
        "".join(paths[c][1] + "\n" for c in sorted(paths)),
        encoding="utf-8",
    )
    save(out / "target_reports.json", target_reports)
    save(out / "separators.json", separators)

    report = {
        "experiment": "ACC_V5_MATCHED_FRONTIER_SEPARATOR_SYNTHESIS",
        "authority_scope": "frozen official verifier + frozen public leaderboard snapshot",
        "warrant_horizon": "OPEN",
        "expected_targets": len(expected_ids),
        "expected_cases": len(expected_ids) * len(POLICIES),
        "completed_cases": len(rows),
        "missing_cases": missing,
        "search_complete_for_declared_matched_scope": complete,
        "global_warrant_class": global_class,
        "protected_scoring_targets": sum(x["role"] == "protected_scoring" for x in selection),
        "responsive_loss_targets": sum(x["role"] == "responsive_loss" for x in selection),
        "targets_with_verified_separators": len(separators),
        "verified_candidate_targets": len(paths),
        "publication_candidates": sorted(paths),
        "claim_boundary": (
            "Results classify only the frozen matched target/policy/compiler scope. "
            "The live competitive future is OPEN. Bounded non-separation is not "
            "unrestricted equivalence, and failure is not expressive inadequacy."
        ),
        "promotion_authorized": False,
        "recursion_authorized": False,
        "next_decision_rule": (
            "Use the observed separator support to decide which layer deserves "
            "a smaller follow-up experiment; preserve all still-warranted policies."
        ),
    }
    save(out / "report.json", report)
    print("V5_FRONTIER_SYNTHESIS", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
