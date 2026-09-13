#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import block_size_signature, refines
from kernel import Kernel
from challenge_pack import (
    MAIN, DUPLICATE, PERTURBED, BRANCH, RELEVANCE,
    RECORD_INTERVAL, RELABELED, INCOMPLETE,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    return x


def structural_signature(result):
    active = result["_active_by_context"]
    return {
        "active_block_sizes": sorted(
            tuple(block_size_signature(p)) for p in active.values()
        ),
        "global_blocks": result["_global"]["minimum_block_count"],
        "pairwise_incomparability": sorted(
            row["incomparable"] for row in result["pairwise"]
        ),
        "grain_count": result["grain_count"],
    }


def main() -> int:
    k = Kernel()

    main_result = k.build_multigrain(MAIN)
    relabelled = k.build_multigrain(RELABELED)
    duplicate = k.build_multigrain(DUPLICATE)
    update = k.update_one_context(MAIN, PERTURBED, 0)
    branch = k.build_multigrain(BRANCH)
    relevance = k.build_multigrain(RELEVANCE)
    record = k.build_multigrain(RECORD_INTERVAL)
    incomplete = k.build_multigrain(INCOMPLETE)
    no_consequence = k.build_multigrain(MAIN, consequence_enabled=False)

    evidence = {
        "experiment": "contextual_multigrain_genesis_v28",
        "scientific_freeze_commit": "0c97a75798949a56cfaba933fe5cedb3e3f25547",
        "post_freeze_challenges": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json": sha256(HERE/"FREEZE.json"),
            "basis.py": sha256(HERE/"basis.py"),
            "kernel.py": sha256(HERE/"kernel.py"),
            "challenge_pack.py": sha256(HERE/"challenge_pack.py"),
        },
        "results": {
            "main": safe(main_result),
            "relabelled": safe(relabelled),
            "duplicate": safe(duplicate),
            "one_context_update": safe(update),
            "branch": safe(branch),
            "relevance": safe(relevance),
            "record_interval": safe(record),
            "incomplete": safe(incomplete),
            "no_consequence": safe(no_consequence),
        },
        "gates": {},
    }

    G = evidence["gates"]

    G["G1_exhausts_all_partitions"] = (
        main_result.get("status") == "VERIFIED"
        and main_result.get("tested_partition_count_per_context") == 15
        and all(c.get("tested_partition_count") == 15 for c in main_result["contexts"])
        and record.get("contexts", [{}])[0].get("tested_partition_count") == 203
    )

    active = main_result["_active_by_context"]
    G["G2_recovers_contextwise_coarsest_predictive_grains"] = (
        len(active) == 2
        and all(len(p) == 2 for p in active.values())
        and main_result["contexts"][0]["minimum_partitions"]
            == [main_result["contexts"][0]["direct_signature_partition"]]
        and main_result["contexts"][1]["minimum_partitions"]
            == [main_result["contexts"][1]["direct_signature_partition"]]
    )

    G["G3_incompatible_contexts_induce_incomparable_grains"] = (
        len(main_result["pairwise"]) == 1
        and main_result["pairwise"][0]["incomparable"] is True
    )

    # Exhaustive global search proves that two blocks cannot serve both.
    G["G4_no_per_context_minimum_size_grain_serves_both"] = (
        main_result["_global"]["minimum_block_count"] == 4
        and all(len(p) == 2 for p in active.values())
    )

    global_p = main_result["_global"]["_minimum_partitions"][0]
    G["G5_single_fixed_grain_is_strictly_finer_than_each_context_grain"] = (
        all(refines(global_p, p) and global_p != p for p in active.values())
    )

    G["G6_contextual_active_complexity_strictly_beats_fixed_complexity"] = (
        all(
            count < main_result["_global"]["minimum_block_count"]
            for count in main_result["active_block_counts"].values()
        )
    )

    G["G7_relabelling_preserves_multigrain_structure"] = (
        relabelled.get("status") == "VERIFIED"
        and structural_signature(main_result) == structural_signature(relabelled)
    )

    G["G8_duplicate_context_reuses_existing_grain"] = (
        duplicate.get("status") == "VERIFIED"
        and duplicate.get("grain_count") == 1
        and len(duplicate["_grains"][0].contexts) == 2
    )

    changed = update.get("changed", {}).get("0", {})
    G["G9_one_context_change_refines_only_that_grain"] = (
        update.get("status") == "VERIFIED"
        and changed.get("changed") is True
        and changed.get("refined") is True
        and update.get("unrelated_preserved", {}).get("1") is True
    )

    G["G10_branch_and_relevance_labels_use_same_frozen_mechanism"] = (
        branch.get("status") == "VERIFIED"
        and relevance.get("status") == "VERIFIED"
        and structural_signature(branch) == structural_signature(relevance)
        == structural_signature(main_result)
    )

    record_ctx = record["contexts"][0]
    G["G11_nontrivial_prediction_recordability_interval_recovered"] = (
        record.get("status") == "VERIFIED"
        and record_ctx.get("minimum_block_count") == 2
        and len(record_ctx.get("record_partition", [])) == 4
        and record_ctx.get("admissible_interval_count") == 4
    )

    q_record = record["_active_by_context"][0]
    # q_record here is predictive minimum; fetch actual record quotient from context analysis.
    record_analysis = k.analyze_context(RECORD_INTERVAL, 0)
    actual_record = record_analysis["_record_partition"]
    admissible = record_analysis["_admissible"]
    G["G12_no_admitted_grain_is_finer_than_recordability_bound"] = (
        len(admissible) == 4
        and all(refines(actual_record, p) for p in admissible)
    )

    pred = record_analysis["_minimum_partitions"][0]
    G["G13_coarsest_predictive_grain_lies_inside_recordability_interval"] = (
        pred in admissible
        and refines(actual_record, pred)
    )

    G["G14_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
    )

    G["G15_without_consequence_no_predictive_grain_is_certified"] = (
        no_consequence.get("status") == "UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
        and no_consequence.get("grains") == []
    )

    G["G16_forced_single_global_grain_is_causally_more_complex"] = (
        main_result["_global"]["minimum_block_count"] == 4
        and max(main_result["active_block_counts"].values()) == 2
        and min(main_result["active_block_counts"].values()) == 2
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_CONTEXTUAL_MULTIGRAIN_AND_PREDICTION_RECORDABILITY_INTERVAL"
        if evidence["full_pass"]
        else "CONTEXTUAL_MULTIGRAIN_V28_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
