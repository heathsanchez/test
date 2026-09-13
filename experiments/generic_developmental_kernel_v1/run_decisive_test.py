#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kernel import DevelopmentalKernel
from challenge_pack import ACTION_LEGEND, CHALLENGES, EXPECTED

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_program(program):
    return [ACTION_LEGEND.get(x, x) for x in program]


def main():
    kernel = DevelopmentalKernel()
    evidence = kernel.run_sequence(CHALLENGES)
    results = evidence["results"]
    by_id = {r["challenge_id"]: r for r in results}

    gates = {}

    # Generic expected routing, fixed in the post-freeze challenge pack.
    gates["G01_all_challenges_present"] = set(by_id) == set(EXPECTED)
    gates["G02_all_expected_status_routes"] = all(
        by_id[cid]["status"] == exp["status"]
        and by_id[cid]["route"] == exp["route"]
        for cid, exp in EXPECTED.items()
    )

    # No-change case.
    c0 = by_id["C0_ALREADY_SUFFICIENT"]
    gates["G03_no_change_means_zero_edit"] = (
        c0["route"] == "NO_CHANGE" and c0["program_length"] == 0
        and c0["final_state"] == {"stable": 1}
    )

    # Compositional representation repair: exact state, no expected program exposed to kernel.
    c1 = by_id["C1_COMPOSITIONAL_IDENTITY_REPAIR"]
    gates["G04_compositional_repair"] = (
        c1["status"] == "RESOLVED"
        and c1["program_length"] == 3
        and c1["final_state"].get("roles") == 3
        and sorted(c1["final_state"].get("couplings", [])) == [[0, 2], [1, 2]]
        and c1["final_evaluation"]["loss"] == 0
        and c1["holdout"]["accepted"]
    )

    # Higher-order binding repair: create occurrence object, bind all active argument positions.
    c2 = by_id["C2_TERNARY_COHERENCE_GROWTH"]
    gates["G05_ternary_growth"] = (
        c2["status"] == "RESOLVED"
        and c2["program_length"] == 4
        and c2["final_state"] == {"links": [0, 1, 2], "mode": "occurrence"}
        and c2["final_evaluation"]["loss"] == 0
        and c2["holdout"]["accepted"]
    )

    # Non-canonicity: current consequence admits multiple minima; future consequence selects one.
    c3 = by_id["C3_FUTURE_CONSEQUENCE_SELECTION"]
    counts = c3["search_levels"][0].get("future_survivor_counts", [])
    gates["G06_future_consequence_selection"] = (
        c3["route"] == "FUTURE_SELECTED"
        and c3["final_state"] == {"selector": "ALL"}
        and len(counts) >= 3
        and counts[0] > 1
        and counts[-1] == 1
        and c3["holdout"]["accepted"]
    )

    # Stateful scope growth across two different residuals.
    c4 = by_id["C4_SCOPE_KEY_GROWTH"]
    c5 = by_id["C5_SCOPE_BATCH_GROWTH"]
    c6 = by_id["C6_SCOPE_POST_GROWTH_NOOP"]
    gates["G07_scope_growth_is_residual_specific"] = (
        c4["final_state"] == {"active": ["B"]}
        and c5["start_source"] == "context"
        and c5["start_state"] == {"active": ["B"]}
        and c5["final_state"] == {"active": []}
        and c6["start_source"] == "context"
        and c6["final_state"] == {"active": []}
        and c6["route"] == "NO_CHANGE"
    )

    # Retained mechanisms must solve reset contexts without rediscovery.
    c7 = by_id["C7_REUSE_KEY_REPAIR_ON_RESET"]
    c8 = by_id["C8_REUSE_BATCH_REPAIR_ON_RESET"]
    gates["G08_retained_repairs_reused"] = (
        c7["route"] == "REUSE"
        and c8["route"] == "REUSE"
        and c7.get("retained_origin") == "C4_SCOPE_KEY_GROWTH"
        and c8.get("retained_origin") == "C5_SCOPE_BATCH_GROWTH"
    )

    # Epistemic restraint: same kind of unresolved present, different completeness authority.
    c9 = by_id["C9_UNCERTIFIED_SEARCH_STOPS_UNKNOWN"]
    c10 = by_id["C10_CERTIFIED_CLASS_OBSTRUCTION"]
    gates["G09_unknown_vs_certified_obstruction"] = (
        c9["status"] == "UNKNOWN_SEARCH"
        and c10["status"] == "CERTIFIED_NO_REPAIR_IN_CLASS"
    )

    # All resolved held-outs that exist must remain verifier-clean.
    heldouts = [
        r["holdout"]
        for r in results
        if r.get("status") == "RESOLVED" and r.get("holdout") is not None
    ]
    gates["G10_all_postselection_holdouts_pass"] = (
        len(heldouts) >= 4 and all(h.get("accepted") for h in heldouts)
    )

    # No resolved candidate may violate protected consequences.
    gates["G11_all_resolved_preserve_protected"] = all(
        r.get("final_evaluation", {}).get("protected_ok", True)
        for r in results if r.get("status") == "RESOLVED"
    )

    # Make the evidence readable without giving the kernel semantic action names.
    for r in results:
        if "program" in r:
            r["program_semantic_labels_posthoc"] = decode_program(r["program"])

    evidence["gates"] = gates
    evidence["kernel_sha256_runtime"] = sha256_file(ROOT / "kernel.py")
    evidence["challenge_pack_sha256"] = sha256_file(ROOT / "challenge_pack.py")
    evidence["runner_sha256"] = sha256_file(ROOT / "run_decisive_test.py")
    evidence["classification"] = (
        "BOUNDED_FROZEN_GENERIC_DEVELOPMENTAL_KERNEL"
    )
    evidence["final_verdict"] = (
        "VERIFIED_FROZEN_GENERIC_DEVELOPMENTAL_KERNEL_HETEROGENEOUS_TRANSFER"
        if all(gates.values())
        else "NEGATIVE_OR_PARTIAL_GENERIC_DEVELOPMENTAL_KERNEL"
    )

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )

    print(json.dumps({
        "final_verdict": evidence["final_verdict"],
        "kernel_sha256_runtime": evidence["kernel_sha256_runtime"],
        "gates": gates,
        "routes": {
            r["challenge_id"]: {
                "status": r["status"],
                "route": r["route"],
                "program": r.get("program_semantic_labels_posthoc", []),
            }
            for r in results
        },
    }, indent=2, sort_keys=True))

    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
