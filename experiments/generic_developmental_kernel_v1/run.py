#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kernel import DevelopmentalKernel
from challenge_pack import ACTION_LEGEND, CHALLENGES, EXPECTED, KERNEL_SHA256

FREEZE_COMMIT = "f3ee5e65cd0592fa41e4cc9476e3d2d8a5613bae"
KERNEL_PATH = ROOT / "kernel.py"
OUT = ROOT / "results"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT.parents[1], text=True).strip()


def main() -> int:
    OUT.mkdir(exist_ok=True)

    current_sha = git("rev-parse", "HEAD")
    kernel_hash = sha256(KERNEL_PATH)

    ancestor_ok = subprocess.run(
        ["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, current_sha],
        cwd=ROOT.parents[1],
    ).returncode == 0
    kernel_diff = git(
        "diff", "--name-only", f"{FREEZE_COMMIT}..{current_sha}", "--",
        str(KERNEL_PATH.relative_to(ROOT.parents[1]))
    )

    engine = DevelopmentalKernel()
    evidence = engine.run_sequence(CHALLENGES)

    by_id = {x["challenge_id"]: x for x in evidence["results"]}
    for x in evidence["results"]:
        x["program_semantics"] = [ACTION_LEGEND.get(a, a) for a in x.get("program", [])]

    gates = {}

    gates["G1_kernel_hash_frozen"] = kernel_hash == KERNEL_SHA256
    gates["G2_freeze_commit_is_ancestor"] = ancestor_ok
    gates["G3_kernel_unchanged_after_challenges"] = kernel_diff == ""

    gates["G4_expected_routes_and_statuses"] = all(
        by_id[cid]["status"] == exp["status"] and by_id[cid]["route"] == exp["route"]
        for cid, exp in EXPECTED.items()
    )

    c1 = by_id["C1_COMPOSITIONAL_IDENTITY_REPAIR"]
    gates["G5_compositional_repair_minimal_and_heldout"] = (
        c1["baseline"]["loss"] == 36
        and c1["program_length"] == 3
        and c1["final_evaluation"]["loss"] == 0
        and c1["final_state"] == {"roles": 3, "couplings": [[0, 2], [1, 2]]}
        and c1["holdout"]["accepted"]
        and [(z["depth"], z["accepted_current_count"]) for z in c1["search_levels"]]
            == [(1, 0), (2, 0), (3, 1)]
    )

    c2 = by_id["C2_TERNARY_COHERENCE_GROWTH"]
    gates["G6_ternary_coherence_exact_v16_world_and_heldout"] = (
        c2["baseline"]["loss"] == 288
        and c2["baseline"]["world"]["objects"] == 17550
        and c2["baseline"]["world"]["ordered_pairs"] == 308002500
        and c2["program_length"] == 4
        and c2["final_evaluation"]["loss"] == 0
        and c2["final_state"] == {"mode": "occurrence", "links": [0, 1, 2]}
        and c2["holdout"]["accepted"]
        and [(z["depth"], z["accepted_current_count"]) for z in c2["search_levels"]]
            == [(1, 0), (2, 0), (3, 0), (4, 1)]
    )

    c3 = by_id["C3_FUTURE_CONSEQUENCE_SELECTION"]
    gates["G7_future_consequence_resolves_noncanonicity"] = (
        c3["route"] == "FUTURE_SELECTED"
        and c3["search_levels"][-1]["future_survivor_counts"] == [4, 2, 1]
        and c3["final_state"] == {"selector": "ALL"}
        and c3["holdout"]["accepted"]
        and c3["holdout"]["relation_count"] == 4
    )

    c4 = by_id["C4_SCOPE_KEY_GROWTH"]
    c5 = by_id["C5_SCOPE_BATCH_GROWTH"]
    c6 = by_id["C6_SCOPE_POST_GROWTH_NOOP"]
    gates["G8_stateful_scope_growth_preserves_and_then_stops"] = (
        c4["final_state"] == {"active": ["B"]}
        and c5["start_source"] == "context"
        and c5["final_state"] == {"active": []}
        and c6["start_source"] == "context"
        and c6["route"] == "NO_CHANGE"
        and c6["final_state"] == {"active": []}
        and evidence["contexts"]["scope_context"] == {"active": []}
    )

    c7 = by_id["C7_REUSE_KEY_REPAIR_ON_RESET"]
    c8 = by_id["C8_REUSE_BATCH_REPAIR_ON_RESET"]
    gates["G9_retained_programs_reused_without_rediscovery"] = (
        c7["route"] == "REUSE"
        and c7["retained_origin"] == "C4_SCOPE_KEY_GROWTH"
        and c7["search_levels"] == []
        and c8["route"] == "REUSE"
        and c8["retained_origin"] == "C5_SCOPE_BATCH_GROWTH"
        and c8["search_levels"] == []
    )

    c9 = by_id["C9_UNCERTIFIED_SEARCH_STOPS_UNKNOWN"]
    c10 = by_id["C10_CERTIFIED_CLASS_OBSTRUCTION"]
    gates["G10_conservative_epistemic_stopping"] = (
        c9["status"] == "UNKNOWN_SEARCH"
        and c10["status"] == "CERTIFIED_NO_REPAIR_IN_CLASS"
    )

    gates["G11_retained_library_only_verified_repairs"] = (
        len(evidence["retained_programs"]) == 5
        and all(x["origin"] in {
            "C1_COMPOSITIONAL_IDENTITY_REPAIR",
            "C2_TERNARY_COHERENCE_GROWTH",
            "C3_FUTURE_CONSEQUENCE_SELECTION",
            "C4_SCOPE_KEY_GROWTH",
            "C5_SCOPE_BATCH_GROWTH",
        } for x in evidence["retained_programs"])
    )

    heldouts = [
        x.get("holdout") for x in evidence["results"]
        if x.get("holdout") is not None
    ]
    gates["G12_all_postselection_holdouts_pass"] = all(
        h.get("accepted") for h in heldouts
    )

    final_verdict = (
        "VERIFIED_FROZEN_GENERIC_DEVELOPMENTAL_KERNEL_HETEROGENEOUS_TRANSFER"
        if all(gates.values())
        else "NEGATIVE_OR_PARTIAL_GENERIC_DEVELOPMENTAL_KERNEL"
    )

    report = {
        "classification": "FINITE_HETEROGENEOUS_CHALLENGE_BLIND_DEVELOPMENTAL_KERNEL",
        "final_verdict": final_verdict,
        "kernel_freeze_commit": FREEZE_COMMIT,
        "kernel_sha256": kernel_hash,
        "challenge_commit": current_sha,
        "kernel_diff_after_freeze": kernel_diff,
        "gates": gates,
        "action_legend": ACTION_LEGEND,
        "evidence": evidence,
        "claim_boundary": [
            "kernel frozen before challenge pack",
            "one unchanged kernel across heterogeneous finite challenges",
            "opaque supplied action substrates",
            "external finite verifiers supplied",
            "no unrestricted action invention",
            "no unrestricted completeness",
            "challenge pack itself is experimenter-designed"
        ]
    }

    (OUT / "evidence.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    print(json.dumps({
        "final_verdict": final_verdict,
        "kernel_sha256": kernel_hash,
        "challenge_commit": current_sha,
        "gates": gates,
        "routes": {
            x["challenge_id"]: {
                "status": x["status"],
                "route": x["route"],
                "program_semantics": x.get("program_semantics", []),
                "retained_origin": x.get("retained_origin")
            }
            for x in evidence["results"]
        }
    }, indent=2, sort_keys=True))

    return 0 if final_verdict.startswith("VERIFIED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
