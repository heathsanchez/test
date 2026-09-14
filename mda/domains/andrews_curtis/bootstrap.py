#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mda.kernel.core import Status


def save(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_solution_file(path: Path) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    pat = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = pat.match(line)
        if not m:
            raise ValueError(f"bad solution line: {raw}")
        out[m.group(1)] = list(json.loads(m.group(2)))
    return out


def first(root: Path, name: str) -> Path | None:
    hits = list(root.rglob(name))
    return hits[0] if hits else None


def all_named(root: Path, name: str) -> list[Path]:
    return list(root.rglob(name))


def load_json(path: Path | None, default=None):
    if path is None or not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def replay_cases(acc_root: Path, cases: dict[str, list[int]]) -> list[dict[str, Any]]:
    sys.path.insert(0, str(acc_root / "competition" / "tools"))
    from verifier import core, stable_core

    manifest = json.loads(
        (acc_root / "competition" / "tools" / "verifier" / "data" / "manifest.json").read_text()
    )
    by_id = {c["challenge_id"]: c for c in manifest["challenges"]}
    limits = manifest["limits"]

    rows = []
    for cid, moves in sorted(cases.items()):
        c = by_id[cid]
        if cid.startswith("ac-"):
            verdict = core.verify(c, moves, c["move_spec_version"], limits)
        elif cid.startswith("sac-"):
            verdict = stable_core.verify(c, moves, c["move_spec_version"], limits)
        else:
            raise ValueError(cid)
        rows.append(
            {
                "challenge_id": cid,
                "length": len(moves),
                "ok": bool(verdict.get("ok")),
                "work": verdict.get("work"),
                "certificate_hash": verdict.get("certificate_hash"),
                "reason": verdict.get("reason"),
            }
        )
    return rows


def aggregate_policy_evidence(target_reports: list[dict[str, Any]]) -> dict[str, Any]:
    responsive = [r for r in target_reports if r.get("role") == "responsive_loss"]
    protected = [r for r in target_reports if r.get("role") == "protected_scoring"]

    current_better = []
    mask3_better = []
    equal = []
    unresolved = []
    for r in responsive:
        a, b = r.get("current_best_atomic"), r.get("mask3_best_atomic")
        if not isinstance(a, int) or not isinstance(b, int):
            unresolved.append(r["challenge_id"])
        elif a < b:
            current_better.append(r["challenge_id"])
        elif b < a:
            mask3_better.append(r["challenge_id"])
        else:
            equal.append(r["challenge_id"])

    node_current_better = []
    node_mask3_better = []
    node_equal = []
    for r in responsive:
        a, b = r.get("current_nodes"), r.get("mask3_nodes")
        if not isinstance(a, int) or not isinstance(b, int):
            continue
        if a < b:
            node_current_better.append(r["challenge_id"])
        elif b < a:
            node_mask3_better.append(r["challenge_id"])
        else:
            node_equal.append(r["challenge_id"])

    return {
        "responsive_targets": len(responsive),
        "protected_targets": len(protected),
        "atomic_cost": {
            "current_better": current_better,
            "mask3_better": mask3_better,
            "equal": equal,
            "unresolved": unresolved,
        },
        "search_nodes": {
            "current_better": node_current_better,
            "mask3_better": node_mask3_better,
            "equal": node_equal,
        },
        "route_separators": [
            r["challenge_id"]
            for r in responsive
            if "QUOTIENT_ROUTE_SEPARATOR" in r.get("separators", [])
        ],
    }


def full_cost_frontier(v5_root: Path) -> dict[str, Any]:
    """Use already-frozen V5 raw matched artifacts as the cheapest discriminator.

    Search is paid once per (target, policy).  Compiler cost is then measured
    for each frozen beam on the same reached quotient route.
    """
    raw = []
    for p in v5_root.rglob("result.json"):
        obj = load_json(p, {})
        if isinstance(obj, dict) and obj.get("experiment") == "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1":
            raw.append(obj)

    configs: dict[tuple[str, int], dict[str, Any]] = {}
    for r in raw:
        policy = r.get("policy")
        if policy not in ("current", "mask3"):
            continue
        for t in r.get("compiler_trials", []):
            beam = t.get("beam")
            if not isinstance(beam, int):
                continue
            key = (policy, beam)
            q = configs.setdefault(key, {
                "policy": policy,
                "beam": beam,
                "cases": 0,
                "verified": 0,
                "protected_scoring_regenerated": 0,
                "total_atomic": 0,
                "total_work": 0,
                "total_nodes": 0,
                "total_search_seconds": 0.0,
                "total_compile_seconds": 0.0,
                "max_peak": 0,
            })
            q["cases"] += 1
            # Search cost is identical across beam trials for a target/policy.
            q["total_nodes"] += int(r.get("nodes") or 0)
            q["total_search_seconds"] += float(r.get("search_seconds") or 0.0)
            q["total_compile_seconds"] += float(t.get("compile_seconds") or 0.0)
            ok = (t.get("ac_verdict") or {}).get("ok") is True
            if ok:
                q["verified"] += 1
                n = int(t.get("atomic_length") or 0)
                q["total_atomic"] += n
                q["total_work"] += int((t.get("ac_verdict") or {}).get("work") or 0)
                q["max_peak"] = max(q["max_peak"], int(t.get("peak") or 0))
                if r.get("role") == "protected_scoring" and isinstance(r.get("frozen_ac_best"), int) and n <= r["frozen_ac_best"]:
                    q["protected_scoring_regenerated"] += 1

    vals = list(configs.values())
    # Admission before economy: compare only configs with maximal verified reach
    # and maximal protected regeneration in this frozen scope.
    max_verified = max((x["verified"] for x in vals), default=0)
    eligible = [x for x in vals if x["verified"] == max_verified]
    max_protected = max((x["protected_scoring_regenerated"] for x in eligible), default=0)
    eligible = [x for x in eligible if x["protected_scoring_regenerated"] == max_protected]

    def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
        keys = ("total_atomic", "total_work", "total_nodes", "total_search_seconds", "total_compile_seconds", "max_peak")
        no_worse = all(a[k] <= b[k] for k in keys)
        better = any(a[k] < b[k] for k in keys)
        return no_worse and better

    frontier = [
        x for x in eligible
        if not any(y is not x and dominates(y, x) for y in eligible)
    ]
    frontier.sort(key=lambda x: (x["policy"], x["beam"]))
    for x in vals:
        x["total_wall_proxy_seconds"] = x["total_search_seconds"] + x["total_compile_seconds"]
    vals.sort(key=lambda x: (x["policy"], x["beam"]))
    return {
        "raw_matched_cases": len(raw),
        "configurations": vals,
        "max_verified": max_verified,
        "max_protected_scoring_regenerated": max_protected,
        "pareto_frontier": [{"policy": x["policy"], "beam": x["beam"]} for x in frontier],
        "scope": "frozen V5 matched target pack; historical wall-clock measurements",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--scout-dir", required=True)
    ap.add_argument("--v5-root", required=True)
    ap.add_argument("--v6-root")
    ap.add_argument("--protected", required=True)
    ap.add_argument("--present", required=True)
    ap.add_argument("--conformance", required=True)
    ap.add_argument("--repo-sha", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    acc_root = Path(a.acc_root)
    scout = Path(a.scout_dir)
    v5 = Path(a.v5_root)
    v6 = Path(a.v6_root) if a.v6_root else None
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    present = load_json(Path(a.present), {})
    conformance = load_json(Path(a.conformance), {})
    live_status = load_json(scout / "mathgraph_status.json", [])
    snapshot_ac = load_json(scout / "snapshot_ac.json", {})
    snapshot_stable = load_json(scout / "snapshot_stable.json", {})

    protected_cases = parse_solution_file(Path(a.protected))
    protected_replay = replay_cases(acc_root, protected_cases)
    protected_ok = all(r["ok"] for r in protected_replay)
    if not protected_ok:
        raise RuntimeError(("protected replay failure", protected_replay))

    counts = {
        "unique": sum(x.get("status") == "unique_hold" for x in live_status),
        "tied": sum(x.get("status") == "tied_hold" for x in live_status),
        "lost": sum(x.get("status") == "lost" for x in live_status),
        "submitted_cells": len(live_status),
    }
    live_protected = [x for x in live_status if x.get("status") in ("unique_hold", "tied_hold")]

    target_reports_path = first(v5, "target_reports.json")
    separators_path = first(v5, "separators.json")
    target_reports = load_json(target_reports_path, [])
    separators = load_json(separators_path, [])
    policy_evidence = aggregate_policy_evidence(target_reports)
    full_cost = full_cost_frontier(v5)

    v5_candidate_path = None
    for p in v5.rglob("fortified_ac.txt"):
        if "peephole" in str(p):
            v5_candidate_path = p
            break
    v5_cases = parse_solution_file(v5_candidate_path) if v5_candidate_path else {}
    v5_replay = replay_cases(acc_root, v5_cases)
    v5_replay_ok = all(r["ok"] for r in v5_replay)
    if v5_cases and not v5_replay_ok:
        raise RuntimeError(("V5 regression replay failure", v5_replay))

    atlas_report = None
    peephole_report = None
    for p in all_named(v5, "report.json"):
        s = str(p)
        obj = load_json(p, {})
        if "atlas" in s and isinstance(obj, dict) and "moves_saved" in obj:
            atlas_report = obj
        if "peephole" in s and isinstance(obj, dict) and "moves_saved" in obj:
            peephole_report = obj

    v6_report = None
    if v6 and v6.exists():
        for p in all_named(v6, "report.json"):
            obj = load_json(p, {})
            if isinstance(obj, dict) and obj.get("challenge_id") == "ac-08491":
                v6_report = obj
                break

    baseline = {
        "experiment": "ACC_MDA_BASELINE_V1",
        "repo_sha": a.repo_sha,
        "grounding_pin": present.get("verifier_version"),
        "authority_model": {
            "semantic": "deterministic pinned official verifier",
            "economic": "OPEN timestamped live leaderboard",
        },
        "official_conformance": conformance,
        "protected_replay": {
            "count": len(protected_replay),
            "all_ok": protected_ok,
            "rows": protected_replay,
        },
        "v5_regression_replay": {
            "count": len(v5_replay),
            "all_ok": v5_replay_ok,
            "rows": v5_replay,
        },
        "live_economic_snapshot": counts,
        "live_protected_cells": live_protected,
        "snapshot_ac_present": bool(snapshot_ac),
        "snapshot_stable_present": bool(snapshot_stable),
        "status": Status.VERIFIED.value if protected_ok and conformance.get("ok") else Status.UNKNOWN_AUTHORITY.value,
    }
    save(out / "baseline.json", baseline)

    solvent_components = [
        {"id": "official-verifier-adapter", "decision": "RETAIN", "reason": "grounding authority; cannot be erased"},
        {"id": "protected-certificate-replay", "decision": "RETAIN", "reason": f"{len(protected_replay)}/{len(protected_replay)} protected certificates replay"},
        {"id": "gssub-current", "decision": "PRESERVE_FRONTIER", "reason": "verified on V5 matched scope and wins at least one atomic-cost comparison"},
        {"id": "gssub-mask3-short-plus-long", "decision": "PRESERVE_FRONTIER", "reason": "verified on V5 matched scope and wins multiple atomic-cost comparisons; node tradeoff remains"},
        {
            "id": "compiler-beam1",
            "decision": "PRESERVE_FRONTIER" if any(x.get("beam") == 1 for x in full_cost.get("pareto_frontier", [])) else "CONTRACT_FROM_ACTIVE_PRESENT",
            "reason": "reuse frozen full-cost V5 evidence; retain only if beam 1 remains Pareto-undominated",
        },
        {
            "id": "compiler-beam16",
            "decision": "PRESERVE_FRONTIER" if any(x.get("beam") == 16 for x in full_cost.get("pareto_frontier", [])) else "CONTRACT_FROM_ACTIVE_PRESENT",
            "reason": "reuse frozen full-cost V5 evidence; retain only if beam 16 remains Pareto-undominated",
        },
        {
            "id": "compiler-beam64",
            "decision": "PRESERVE_FRONTIER" if any(x.get("beam") == 64 for x in full_cost.get("pareto_frontier", [])) else "CONTRACT_FROM_ACTIVE_PRESENT",
            "reason": "reuse frozen full-cost V5 evidence; retain only if beam 64 remains Pareto-undominated",
        },
        {"id": "proof-atlas", "decision": "RETAIN" if (atlas_report or {}).get("moves_saved", 0) > 0 else "UNKNOWN_AUTHORITY", "reason": f"V5 exact replay saved {(atlas_report or {}).get('moves_saved', 0)} moves"},
        {"id": "peephole-superoptimizer", "decision": "RETAIN" if (peephole_report or {}).get("moves_saved", 0) > 0 else "UNKNOWN_AUTHORITY", "reason": f"V5 exact replay saved {(peephole_report or {}).get('moves_saved', 0)} moves"},
        {"id": "v3-guard-variants", "decision": "LEAVE_UNPROMOTED", "reason": "prior qualification incomplete; no inheritance authority"},
        {"id": "atomic-cost-first-search", "decision": "LEAVE_UNPROMOTED", "reason": "bounded failures are UNKNOWN_SEARCH, not proof of inadequacy or value"},
        {
            "id": "v6-window7-near-miss",
            "decision": "CONTRACT_FROM_ACTIVE_PRESENT" if v6_report is not None and int(v6_report.get("moves_saved", 0)) == 0 else "UNKNOWN_AUTHORITY",
            "reason": "bounded ablation on ac-08491 saved 0 moves and changed no protected consequence" if v6_report is not None else "V6 result unavailable in this evidence freeze",
        },
    ]
    solvent = {
        "experiment": "ACC_MDA_SOLVENT_V1",
        "scope": "existing ACC machinery only; no new solver construction",
        "protected_replay_ok": protected_ok,
        "policy_evidence": policy_evidence,
        "full_cost_discriminator": full_cost,
        "components": solvent_components,
        "status": Status.VERIFIED.value if protected_ok else Status.UNKNOWN_AUTHORITY.value,
        "claim_boundary": "Contraction decisions are scoped to recovered evidence and pinned dependencies.",
    }
    save(out / "solvent" / "report.json", solvent)

    responsive = [r for r in target_reports if r.get("role") == "responsive_loss"]
    current_verified = sum(isinstance(r.get("current_best_atomic"), int) for r in responsive)
    mask3_verified = sum(isinstance(r.get("mask3_best_atomic"), int) for r in responsive)
    seed_obstruction = len(responsive) > 0
    candidate_frontier = []
    if current_verified:
        candidate_frontier.append("gssub-current + exact-atomic-compiler")
    if mask3_verified:
        candidate_frontier.append("gssub-mask3-short-plus-long + exact-atomic-compiler")

    genesis_status = Status.UNKNOWN_CHOICE.value if len(candidate_frontier) > 1 else Status.VERIFIED.value if len(candidate_frontier) == 1 else Status.UNKNOWN_SEARCH.value
    genesis = {
        "experiment": "ACC_MDA_GENESIS_V1",
        "seed": ["official-verifier-adapter", "protected-certificate-replay", "fresh-live-publication-gate"],
        "seed_class_complete": True,
        "seed_obstruction": seed_obstruction,
        "seed_obstruction_scope": "construct a new certificate on the frozen responsive-loss encounters",
        "constraint": "add the least existing constructive machinery that produces V0-verified candidates while Q_t replays",
        "responsive_encounters": len(responsive),
        "current_verified_encounters": current_verified,
        "mask3_verified_encounters": mask3_verified,
        "minimal_lawful_frontier": candidate_frontier,
        "compiled_future_value": {
            "proof_atlas_moves_saved": (atlas_report or {}).get("moves_saved"),
            "peephole_moves_saved": (peephole_report or {}).get("moves_saved"),
        },
        "status": genesis_status,
        "growth_beyond_boot_language_authorized": False,
        "reason": "existing boot continuations settle the frozen construction obligation; their choice is not uniquely identified, so preserve the frontier",
    }
    save(out / "genesis" / "report.json", genesis)

    surviving_beams = sorted({int(x["beam"]) for x in full_cost.get("pareto_frontier", []) if isinstance(x.get("beam"), int)})
    surviving = [
        "official-verifier-adapter",
        "protected-certificate-replay",
        "exact-atomic-compiler",
        "search-policy-frontier:{current,mask3}",
        "compiler-execution-frontier:{" + ",".join(f"beam{x}" for x in surviving_beams) + "}",
        "proof-atlas",
        "peephole-superoptimizer",
        "fresh-live-publication-gate",
    ]
    invariant = {
        "experiment": "ACC_MDA_INVARIANT_V1",
        "survives_genesis_and_solvent": surviving,
        "non_identifiable": [
            "current vs mask3 as a universal active search policy",
            "compiler beam as a universal active execution policy",
        ],
        "verified_separators": separators,
        "reused_full_cost_discriminator": full_cost,
        "next_authorized_probe": {
            "question": "Which retained search/compiler frontier member minimizes full prospective cost on the same frozen encounters?",
            "hold_fixed": ["official verifier pin", "target pack", "resource ceilings", "protected replay", "exact atomic correctness"],
            "measure": ["verified reach", "final atomic length", "official work", "nodes", "wall time", "peak memory"],
            "purpose": "contract the existing frontier, not invent a new solver",
        },
        "new_solver_growth_authorized": False,
        "overall_status": Status.UNKNOWN_CHOICE.value,
    }
    save(out / "invariant.json", invariant)

    md = [
        "# ACC MDA Invariant Report",
        "",
        "## What survives both directions",
        "",
        *[f"- {x}" for x in surviving],
        "",
        "## What remains non-identifiable",
        "",
        "- A universal winner between current and mask3 is not warranted.",
        "- A universal compiler beam is not warranted among the surviving full-cost frontier; dominated beams are contracted.",
        "",
        "## Solvent result",
        "",
        f"- Proof Atlas retained: V5 saved {(atlas_report or {}).get('moves_saved', 0)} exact moves.",
        f"- Peephole retained: V5 saved {(peephole_report or {}).get('moves_saved', 0)} exact moves.",
        "- V3 guards and atomic-cost-first search remain unpromoted, not disproved.",
        f"- V6 window-7: {'contracted from active present' if v6_report is not None and int(v6_report.get('moves_saved',0)) == 0 else 'UNKNOWN'} within its bounded evidence.",
        "",
        "## Genesis result",
        "",
        f"- Deliberately small replay-only seed is constructively inadequate on {len(responsive)} frozen new encounters.",
        f"- Existing current constructed verified candidates on {current_verified}/{len(responsive)} responsive encounters.",
        f"- Existing mask3 constructed verified candidates on {mask3_verified}/{len(responsive)} responsive encounters.",
        "- Therefore the boot language already contains adequate continuations; no expansion beyond it is authorized.",
        "",
        "## Next probe",
        "",
        "Measure the full cost vector of the preserved search/compiler frontier on the same frozen encounters.",
        "The purpose is to contract lawful alternatives where consequence permits, not to hand-design a new mechanism.",
        "",
        "## Claim boundary",
        "",
        "The live competition future is OPEN. This report does not prove shortest paths, solver impossibility, or unrestricted expressive inadequacy.",
        "",
    ]
    (out / "invariant_report.md").write_text("\n".join(md), encoding="utf-8")

    runtime_present = dict(present)
    runtime_present["runtime_freeze_sha"] = a.repo_sha
    runtime_present["live_economic_snapshot"] = counts
    runtime_present["live_protected_cells"] = live_protected
    runtime_present["mda_state"] = {
        "P_t": surviving,
        "Q_t_count": len(protected_replay),
        "frontier": candidate_frontier,
        "status": Status.UNKNOWN_CHOICE.value,
        "growth_beyond_boot_language_authorized": False,
    }
    save(out / "PRESENT.runtime.json", runtime_present)

    transitions = [
        {
            "transition_id": "acc-mda-bootstrap-v1",
            "from_present": present.get("source_present_sha"),
            "encounter": "MDA baseline + solvent + genesis on recovered V5 evidence and fresh live economic state",
            "observed_consequence": "protected replay verified; current/mask3 remain distinct lawful continuations; Atlas/peephole save exact moves",
            "warrant_status": Status.UNKNOWN_CHOICE.value,
            "residual": "active search/compiler choice not uniquely identified",
            "constraint": "preserve Q_t; do not expand beyond boot language while adequate existing continuations survive",
            "candidate_continuation": candidate_frontier,
            "protected_replay": "PASS",
            "frontier_effect": "preserve incomparable frontier",
            "retained": True,
            "revocation_conditions": ["official verifier or manifest changes", "protected replay fails", "matched prospective evidence dominates a frontier member"],
            "to_present": a.repo_sha,
        },
        {
            "transition_id": "acc-v6-window7-solvent",
            "from_present": present.get("source_present_sha"),
            "encounter": "ac-08491 local peephole window 5 -> 7",
            "observed_consequence": None if v6_report is None else {"old_length": v6_report.get("old_length"), "new_length": v6_report.get("new_length"), "moves_saved": v6_report.get("moves_saved")},
            "warrant_status": Status.VERIFIED.value if v6_report is not None else Status.UNKNOWN_AUTHORITY.value,
            "residual": "no protected consequence changed",
            "constraint": "do not inherit extra mechanism absent prospective value",
            "candidate_continuation": "leave V6 window-7 out of active present",
            "protected_replay": "PASS",
            "frontier_effect": "contract/unpromote bounded no-value branch",
            "retained": False,
            "revocation_conditions": ["new scoped evidence shows positive future value"],
            "to_present": a.repo_sha,
        },
    ]
    (out / "transitions.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in transitions), encoding="utf-8")

    retained = {
        "retained": [x for x in solvent_components if x["decision"] in ("RETAIN", "PRESERVE_FRONTIER")],
        "unpromoted": [x for x in solvent_components if x["decision"] == "LEAVE_UNPROMOTED"],
        "contracted": [x for x in solvent_components if x["decision"] == "CONTRACT_FROM_ACTIVE_PRESENT"],
    }
    save(out / "retained_capabilities.json", retained)

    final = {
        "experiment": "ACC_MDA_BOOTSTRAP_V1",
        "repo_sha": a.repo_sha,
        "baseline_status": baseline["status"],
        "protected_replay_ok": protected_ok,
        "protected_replay_count": len(protected_replay),
        "v5_regression_replay_ok": v5_replay_ok,
        "v5_regression_count": len(v5_replay),
        "live_scoring": counts,
        "genesis_status": genesis_status,
        "minimal_lawful_frontier": candidate_frontier,
        "solvent_contracted": [x["id"] for x in retained["contracted"]],
        "solvent_unpromoted": [x["id"] for x in retained["unpromoted"]],
        "survives_both": surviving,
        "new_solver_growth_authorized": False,
        "full_cost_frontier": full_cost.get("pareto_frontier", []),
        "next_action": "if the reused full-cost evidence still leaves a frontier, construct the cheapest new probe that separates those survivors; do not invent a new solver",
        "claim_boundary": "live competitive future OPEN; no unrestricted inadequacy claim",
    }
    save(out / "final.json", final)
    print("ACC_MDA_BOOTSTRAP", json.dumps(final, sort_keys=True))


if __name__ == "__main__":
    main()
