#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


def save(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_results(pattern: str) -> list[dict[str, Any]]:
    rows = []
    for fp in glob.glob(pattern, recursive=True):
        try:
            obj = json.loads(Path(fp).read_text())
        except Exception:
            continue
        if obj.get("experiment") == "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1":
            rows.append(obj)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--selection", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    selection = json.loads(Path(a.selection).read_text())
    expected = [x["challenge_id"] for x in selection]
    rows = load_results(a.glob)
    by = {(r["challenge_id"], r["policy"]): r for r in rows}
    missing = [
        {"challenge_id": cid, "policy": pol}
        for cid in expected
        for pol in ("current", "mask3")
        if (cid, pol) not in by
    ]

    configs: dict[tuple[str, int], dict[str, Any]] = {}
    best_paths: dict[str, tuple[int, str, str, int]] = {}
    target_table = []

    for cid in expected:
        per_target = {"challenge_id": cid}
        for policy in ("current", "mask3"):
            r = by.get((cid, policy))
            if r is None:
                per_target[policy] = {"status": "UNKNOWN_SEARCH"}
                continue
            per_target[policy] = {
                "nodes": r.get("nodes"),
                "search_seconds": r.get("search_seconds"),
                "quotient_found": r.get("quotient_found"),
                "quotient_steps": r.get("quotient_steps"),
                "path_hash": r.get("quotient_path_sha256"),
                "trials": [],
            }
            cand_file = None
            # candidate_ac is the shortest verified beam path for this policy.
            # Individual beam paths are not emitted separately, so publication
            # uses each policy's best exact certificate while developmental
            # comparison retains per-beam metrics below.
            for t in r.get("compiler_trials", []):
                beam = t.get("beam")
                if beam not in (16, 64):
                    continue
                ok = (t.get("ac_verdict") or {}).get("ok") is True and (t.get("stable_verdict") or {}).get("ok") is True
                gap_ac = t.get("gap_ac_frozen")
                gap_st = t.get("gap_stable_frozen")
                rec = {
                    "beam": beam,
                    "ok": ok,
                    "atomic_length": t.get("atomic_length"),
                    "stable_length": t.get("stable_length"),
                    "gap_ac": gap_ac,
                    "gap_stable": gap_st,
                    "work_ac": (t.get("ac_verdict") or {}).get("work"),
                    "work_stable": (t.get("stable_verdict") or {}).get("work"),
                    "compile_seconds": t.get("compile_seconds"),
                    "peak": t.get("peak"),
                }
                per_target[policy]["trials"].append(rec)

                key = (policy, int(beam))
                q = configs.setdefault(key, {
                    "policy": policy,
                    "beam": int(beam),
                    "targets": 0,
                    "verified_targets": 0,
                    "scoring_rows_frozen": 0,
                    "strict_rows_frozen": 0,
                    "total_atomic": 0,
                    "total_stable": 0,
                    "total_work": 0,
                    "total_nodes": 0,
                    "total_search_seconds": 0.0,
                    "total_compile_seconds": 0.0,
                    "max_peak": 0,
                })
                q["targets"] += 1
                q["total_nodes"] += int(r.get("nodes") or 0)
                q["total_search_seconds"] += float(r.get("search_seconds") or 0.0)
                q["total_compile_seconds"] += float(t.get("compile_seconds") or 0.0)
                if ok:
                    q["verified_targets"] += 1
                    q["total_atomic"] += int(t.get("atomic_length") or 0)
                    q["total_stable"] += int(t.get("stable_length") or 0)
                    q["total_work"] += int((t.get("ac_verdict") or {}).get("work") or 0)
                    q["total_work"] += int((t.get("stable_verdict") or {}).get("work") or 0)
                    q["max_peak"] = max(q["max_peak"], int(t.get("peak") or 0))
                    if isinstance(gap_ac, int) and gap_ac <= 0:
                        q["scoring_rows_frozen"] += 1
                        if gap_ac < 0:
                            q["strict_rows_frozen"] += 1
                    if isinstance(gap_st, int) and gap_st <= 0:
                        q["scoring_rows_frozen"] += 1
                        if gap_st < 0:
                            q["strict_rows_frozen"] += 1
            # locate this result's candidate file from source artifact directory
            source = Path(r.get("_source_file", "")) if r.get("_source_file") else None
            per_target[policy]["best_atomic_length"] = r.get("best_atomic_length")
            per_target[policy]["best_gap_ac"] = r.get("best_gap_ac_frozen")
        target_table.append(per_target)

    config_rows = list(configs.values())
    # Correctness/reach first, then scoring consequence, then economy.
    max_verified = max((x["verified_targets"] for x in config_rows), default=0)
    admissible = [x for x in config_rows if x["verified_targets"] == max_verified]
    max_scoring = max((x["scoring_rows_frozen"] for x in admissible), default=0)
    admissible = [x for x in admissible if x["scoring_rows_frozen"] == max_scoring]
    max_strict = max((x["strict_rows_frozen"] for x in admissible), default=0)
    admissible = [x for x in admissible if x["strict_rows_frozen"] == max_strict]

    def dominates(x: dict[str, Any], y: dict[str, Any]) -> bool:
        keys = (
            "total_atomic", "total_stable", "total_work", "total_nodes",
            "total_search_seconds", "total_compile_seconds", "max_peak",
        )
        return all(x[k] <= y[k] for k in keys) and any(x[k] < y[k] for k in keys)

    frontier = [
        x for x in admissible
        if not any(y is not x and dominates(y, x) for y in admissible)
    ]
    frontier.sort(key=lambda x: (x["policy"], x["beam"]))
    config_rows.sort(key=lambda x: (x["policy"], x["beam"]))

    # Recover one shortest verified exact certificate per target across policy
    # artifacts.  The shell workflow separately stages the candidate files into
    # candidate_pool/ with names carrying policy/target provenance.
    out = Path(a.out_dir)
    pool = out / "candidate_pool"
    if pool.exists():
        for fp in pool.glob("*.txt"):
            for raw in fp.read_text().splitlines():
                if ":" not in raw:
                    continue
                cid, rhs = raw.split(":", 1)
                cid = cid.strip()
                moves = json.loads(rhs.strip())
                old = best_paths.get(cid)
                if old is None or len(moves) < old[0]:
                    best_paths[cid] = (len(moves), raw.strip(), fp.name, 0)

    (out / "best_ac.txt").parent.mkdir(parents=True, exist_ok=True)
    (out / "best_ac.txt").write_text(
        "".join(best_paths[c][1] + "\n" for c in sorted(best_paths)),
        encoding="utf-8",
    )


    # Causal retention by ablation over the frozen consequences.
    #
    # Full-cost rule: a component earns retention iff removing it either
    # (a) destroys verified reach on a frozen encounter, or
    # (b) removes an attainable non-dominated consequence vector.  This
    # treats lower compile time / work / nodes / peak as real future value,
    # rather than collapsing everything to atomic length.
    target_options: dict[str, list[dict[str, Any]]] = {cid: [] for cid in expected}
    cost_keys = (
        "atomic_length",
        "stable_length",
        "work",
        "nodes",
        "search_seconds",
        "compile_seconds",
        "peak",
    )

    for cid in expected:
        for policy in ("current", "mask3"):
            r = by.get((cid, policy))
            if not r:
                continue
            for t in r.get("compiler_trials", []):
                beam = t.get("beam")
                if beam not in (16, 64):
                    continue
                if (t.get("ac_verdict") or {}).get("ok") is not True:
                    continue
                if (t.get("stable_verdict") or {}).get("ok") is not True:
                    continue
                if not isinstance(t.get("atomic_length"), int):
                    continue
                target_options[cid].append({
                    "policy": policy,
                    "beam": int(beam),
                    "atomic_length": int(t["atomic_length"]),
                    "stable_length": int(t.get("stable_length") or (int(t["atomic_length"]) + 2)),
                    "work": int((t.get("ac_verdict") or {}).get("work") or 0)
                            + int((t.get("stable_verdict") or {}).get("work") or 0),
                    "nodes": int(r.get("nodes") or 0),
                    "search_seconds": float(r.get("search_seconds") or 0.0),
                    "compile_seconds": float(t.get("compile_seconds") or 0.0),
                    "peak": int(t.get("peak") or 0),
                })

    def vec_dominates_or_equals(a: dict[str, Any], b: dict[str, Any]) -> bool:
        return all(a[k] <= b[k] for k in cost_keys)

    def vec_strictly_dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
        return vec_dominates_or_equals(a, b) and any(a[k] < b[k] for k in cost_keys)

    def target_frontier(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            x for x in options
            if not any(y is not x and vec_strictly_dominates(y, x) for y in options)
        ]

    base_frontiers = {cid: target_frontier(opts) for cid, opts in target_options.items()}

    def option_uses(component: str, x: dict[str, Any]) -> bool:
        if component in ("current", "mask3"):
            return x["policy"] == component
        if component == "beam16":
            return x["beam"] == 16
        if component == "beam64":
            return x["beam"] == 64
        raise ValueError(component)

    def ablate_component(component: str) -> dict[str, Any]:
        reach_loss: list[str] = []
        lost_frontier_points: list[dict[str, Any]] = []
        best_atomic_penalty = 0

        for cid in expected:
            before_all = target_options[cid]
            after_all = [x for x in before_all if not option_uses(component, x)]

            if before_all and not after_all:
                reach_loss.append(cid)
                continue
            if not before_all:
                continue

            before_frontier = base_frontiers[cid]
            after_frontier = target_frontier(after_all)

            # Any before-frontier point unsupported by an equal-or-better
            # survivor is genuine lost capability under the declared full-cost
            # economy.
            for p in before_frontier:
                if option_uses(component, p) and not any(
                    vec_dominates_or_equals(q, p) for q in after_frontier
                ):
                    lost_frontier_points.append({
                        "challenge_id": cid,
                        "policy": p["policy"],
                        "beam": p["beam"],
                        "cost_vector": {k: p[k] for k in cost_keys},
                    })

            before_best = min(x["atomic_length"] for x in before_all)
            after_best = min(x["atomic_length"] for x in after_all) if after_all else None
            if after_best is not None and after_best > before_best:
                best_atomic_penalty += after_best - before_best

        earns = bool(reach_loss or lost_frontier_points)
        return {
            "component": component,
            "reach_loss_targets": reach_loss,
            "lost_pareto_capabilities": lost_frontier_points,
            "lost_pareto_capability_count": len(lost_frontier_points),
            "best_atomic_penalty_if_removed": best_atomic_penalty,
            "earns_retention": earns,
        }

    causal_ablations = [
        ablate_component("current"),
        ablate_component("mask3"),
        ablate_component("beam16"),
        ablate_component("beam64"),
    ]
    causally_retained = [x["component"] for x in causal_ablations if x["earns_retention"]]
    causally_contractable = [x["component"] for x in causal_ablations if not x["earns_retention"]]

    status = "UNKNOWN_SEARCH" if missing else "VERIFIED" if len(frontier) == 1 else "UNKNOWN_CHOICE"
    report = {
        "experiment": "ACC_MDA_PROSPECTIVE_DISCRIMINATOR_V1",
        "expected_targets": len(expected),
        "completed_policy_cases": len(rows),
        "missing_cases": missing,
        "status": status,
        "warrant_horizon": "OPEN",
        "max_verified_targets": max_verified,
        "max_scoring_rows_frozen": max_scoring,
        "max_strict_rows_frozen": max_strict,
        "configurations": config_rows,
        "pareto_frontier": [
            {"policy": x["policy"], "beam": x["beam"]}
            for x in frontier
        ],
        "candidate_targets": sorted(best_paths),
        "causal_ablations": causal_ablations,
        "causally_retained_components": causally_retained,
        "causally_contractable_components": causally_contractable,
        "ablation_cost_coordinates": list(cost_keys),
        "growth_beyond_boot_language_authorized": False,
        "claim_boundary": (
            "This is a prospective frozen probe over a selected responsive-loss pack. "
            "It may select/contract execution policy within that scope; it does not "
            "prove unrestricted solver adequacy or shortest paths."
        ),
    }
    save(out / "target_table.json", target_table)
    save(out / "report.json", report)
    print("ACC_MDA_PROSPECTIVE_DISCRIMINATOR", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
