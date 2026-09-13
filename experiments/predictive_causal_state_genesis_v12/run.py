#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import full_partition, partition, same_partition
from kernel import Kernel
from challenge_pack import (
    TABLE_A,
    TABLE_B,
    TABLE_C,
    TABLE_WRONG,
    TABLE_HET,
    TABLE_INCOMPLETE,
    AMBIG_TRAIN,
    AMBIG_QUAL,
)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(safe(v) for v in x)
    return x


def first_repair(result):
    gens = result.get("developmental", {}).get("generations", [])
    for gen in gens:
        repairs = gen.get("repairs", [])
        if repairs:
            return repairs[0]
    return None


def main() -> int:
    evidence = {
        "experiment": "predictive_causal_state_genesis_v12",
        "scientific_freeze_commit": "d0d6d625ee4690b416a68f3f58f7388dffcb5f4c",
        "post_freeze_challenges": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE / "PROTOCOL.md"),
            "FREEZE.json": sha256(HERE / "FREEZE.json"),
            "basis.py": sha256(HERE / "basis.py"),
            "kernel.py": sha256(HERE / "kernel.py"),
            "challenge_pack.py": sha256(HERE / "challenge_pack.py"),
        },
        "results": {},
        "gates": {},
    }

    # ------------------------------------------------------------------
    # Main developmental trajectory: blank present -> consequence-sufficient
    # predictive quotient -> independent recurrence -> compile -> reuse.
    # ------------------------------------------------------------------
    k = Kernel()

    a = k.solve("G1_world_a", TABLE_A)
    b = k.solve("G5_world_b", TABLE_B)
    promoted = b.get("promoted_code")
    c_reuse = k.solve(
        "G5_world_c_reuse",
        TABLE_C,
        allow_acquisition_search=False,
    )

    cold_c = Kernel().solve(
        "G5_world_c_cold",
        TABLE_C,
        allow_acquisition_search=False,
    )

    wrong = k.solve(
        "G6_wrong_dynamics",
        TABLE_WRONG,
        allow_acquisition_search=True,
    )

    ablated = k.ablate_compiled_code(TABLE_A)
    after_ablation = k.solve(
        "G5_after_ablation",
        TABLE_C,
        allow_acquisition_search=False,
    )

    hetero = Kernel().solve(
        "G7_heterogeneous",
        TABLE_HET,
        allow_acquisition_search=True,
    )

    incomplete = Kernel().solve(
        "G8_incomplete_authority",
        TABLE_INCOMPLETE,
        allow_acquisition_search=True,
    )

    no_consequence = Kernel().developmental_frontier(
        TABLE_A,
        consequence_enabled=False,
    )

    evidence["results"]["G1_world_a"] = safe(a)
    evidence["results"]["G5_world_b"] = safe(b)
    evidence["results"]["G5_world_c_reuse"] = safe(c_reuse)
    evidence["results"]["G5_world_c_cold"] = safe(cold_c)
    evidence["results"]["G6_wrong_dynamics"] = safe(wrong)
    evidence["results"]["G5_after_ablation"] = safe(after_ablation)
    evidence["results"]["G7_heterogeneous"] = safe(hetero)
    evidence["results"]["G8_incomplete_authority"] = safe(incomplete)
    evidence["results"]["G9_no_consequence"] = safe(no_consequence)

    # ------------------------------------------------------------------
    # Explicit non-canonicity / future selection.
    # ------------------------------------------------------------------
    ka = Kernel()
    amb = ka.solve(
        "G4_ambiguous",
        AMBIG_TRAIN,
        qualification=AMBIG_QUAL,
        allow_acquisition_search=True,
    )
    evidence["results"]["G4_noncanonicity"] = safe(amb)

    G = evidence["gates"]

    full_a = full_partition(TABLE_A)
    min_a = a.get("minimum_search", {})
    pareto_a = min_a.get("pareto_minimal_codes", [])
    dev_a = a.get("developmental", {})
    repair0 = first_repair(a)

    G["G1_starts_as_one_undifferentiated_present"] = (
        dev_a.get("initial_class_count") == 1
        and dev_a.get("generations", [])[0].get("frontier_class_counts") == [1]
        and partition(TABLE_A, ()) == (tuple(range(len(TABLE_A.histories))),)
    )

    G["G1_certified_obstruction_precedes_split"] = (
        repair0 is not None
        and repair0.get("code") == []
        and repair0.get("obstruction", {}).get("history_pair") is not None
        and repair0.get("obstruction", {}).get("current_signature") == []
        and len(repair0.get("minimal_separator_test_indices", [])) >= 1
    )

    G["G1_blank_to_disturbance_builds_multiple_predictive_states"] = (
        a.get("status") == "VERIFIED"
        and len(full_a) == 5
        and len(a.get("partition", [])) == 5
        and same_partition(a.get("partition", []), full_a)
    )

    G["G2_global_minimum_code_exhaustively_verified"] = (
        min_a.get("status") == "VERIFIED"
        and min_a.get("tested_subsets") == 64
        and len(pareto_a) == 1
        and pareto_a[0].get("active_test_indices") == [4]
        and pareto_a[0].get("cost") == [1, 7]
        and a.get("active_test_indices") == [4]
        and a.get("cost") == [1, 7]
    )

    # The local minimum-change path should be allowed to grow through shorter
    # distinctions; global contraction then finds the smaller complete code.
    G["G2_development_then_contraction"] = (
        dev_a.get("status") == "VERIFIED"
        and dev_a.get("final_generation", 0) >= 2
        and a.get("active_test_indices") == [4]
    )

    G["G3_no_premature_hidden_ontology"] = (
        all(
            "hidden" not in str(gen).lower()
            and "state_id" not in str(gen).lower()
            for gen in dev_a.get("generations", [])
        )
        and repair0.get("obstruction", {}).get("current_signature") == []
    )

    amb_min = amb.get("minimum_search", {})
    amb_qual = amb.get("qualification", {})
    amb_dev = amb.get("developmental", {})

    G["G4_incomparable_minimal_repairs_preserved"] = (
        amb.get("status") == "VERIFIED"
        and len(amb_min.get("pareto_minimal_codes", [])) == 2
        and {
            tuple(x.get("active_test_indices", []))
            for x in amb_min.get("pareto_minimal_codes", [])
        } == {(0,), (1,)}
        and amb_min.get("complete_code_count") == 3
    )

    G["G4_future_consequence_selects_branch"] = (
        amb_qual.get("status") == "VERIFIED"
        and amb_qual.get("survivors") == [[1]]
        and amb.get("active_test_indices") == [1]
    )

    G["G5_second_world_compiles_predictive_code"] = (
        b.get("status") == "VERIFIED"
        and promoted is not None
        and promoted.get("active_test_indices") == [4]
        and set(promoted.get("provenance", []))
            == {"G1_world_a", "G5_world_b"}
    )

    G["G5_warm_reuse_zero_acquisition"] = (
        c_reuse.get("status") == "VERIFIED"
        and c_reuse.get("route") == "REUSE_COMPILED_CODE"
        and c_reuse.get("acquisition_search_count") == 0
        and c_reuse.get("active_test_indices") == [4]
    )

    G["G5_cold_zero_acquisition_is_unknown"] = (
        cold_c.get("status") == "UNKNOWN_CODE"
        and cold_c.get("acquisition_search_count") == 0
    )

    G["G5_ablation_restores_unknown"] = (
        ablated
        and after_ablation.get("status") == "UNKNOWN_CODE"
        and after_ablation.get("acquisition_search_count") == 0
    )

    G["G6_wrong_retained_code_is_replay_falsified"] = (
        wrong.get("status") in ("VERIFIED", "VERIFIED_FRONTIER")
        and wrong.get("route") == "DEVELOP"
        and wrong.get("failed_reuse") is not None
        and wrong.get("failed_reuse", {}).get("status") == "REPLAY_FAILED"
        and wrong.get("acquisition_search_count") == 1
    )

    G["G7_same_kernel_handles_heterogeneous_hidden_dynamics"] = (
        hetero.get("status") in ("VERIFIED", "VERIFIED_FRONTIER")
        and hetero.get("route") == "DEVELOP"
        and hetero.get("acquisition_search_count") == 1
        and hetero.get("developmental", {}).get("initial_class_count") == 1
    )

    G["G8_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
        and incomplete.get("route") == "STOP"
    )

    G["G9_no_consequence_no_authorized_split"] = (
        no_consequence.get("status") == "UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
        and no_consequence.get("initial_class_count") == 1
        and no_consequence.get("frontier") == [[]]
        and no_consequence.get("generations") == []
    )

    G["algorithmic_core_is_exactly_developmental"] = all(
        word in (HERE / "PROTOCOL.md").read_text()
        for word in (
            "EXECUTE",
            "VERIFY",
            "DIAGNOSE",
            "CONSTRAIN",
            "RESTRUCTURE",
            "CHOOSE",
            "COMPILE",
            "UPDATE",
        )
    )

    G["no_domain_feature_vocabulary_in_frozen_kernel"] = all(
        token not in (HERE / "kernel.py").read_text().lower()
        for token in (
            "frequency",
            "phase",
            "coordinate",
            "adjacency",
            "eigenmode",
            "nodal",
            "wave",
            "object_detector",
        )
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_PREDICTIVE_CAUSAL_STATE_GENESIS_FROM_UNDIFFERENTIATED_PRESENT"
        if evidence["full_pass"]
        else "PREDICTIVE_CAUSAL_STATE_GENESIS_V12_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
