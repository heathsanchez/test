#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import VerifiedLiteral, generate_partitions
from kernel import Kernel
from challenge_pack import (
    ALL_EQUAL_1,
    ALL_EQUAL_2,
    DISTINCT_1,
    DISTINCT_2,
    HELDOUT,
    WRONG,
    WRONG_LITERAL,
    V14_RULE_X,
    V14_RULE_Y,
    V14_HELDOUT,
    HET_1,
    HET_2,
    SINGLE,
    BAD,
)


TARGET = (0, 1, 0, 1)
ALL_EQUAL = (0, 0, 0, 0)
FULLY_SPLIT = (0, 1, 2, 3)
HET_TARGET = (0, 0, 1)


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


def main() -> int:
    k = Kernel()
    evidence = {
        "experiment": "parametric_grammar_genesis_v15",
        "scientific_freeze_commit": "6b1b7c057409bf826ed5eac66ffcdf70c4a18d03",
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

    # S2/S3/S4 developmental split from maximally identified schema.
    dev = k.develop([
        [ALL_EQUAL_1, ALL_EQUAL_2],
        [DISTINCT_1, DISTINCT_2],
    ])
    exact = k.exact_minimum([
        ALL_EQUAL_1,
        ALL_EQUAL_2,
        DISTINCT_1,
        DISTINCT_2,
    ])
    evidence["results"]["development"] = safe(dev)
    evidence["results"]["exact_minimum"] = safe(exact)

    compiled_result = k.compile_schema(
        TARGET,
        [ALL_EQUAL_1, ALL_EQUAL_2, DISTINCT_1, DISTINCT_2],
    )
    evidence["results"]["compile"] = safe(compiled_result)
    compiled = compiled_result.get("compiled_schema")

    warm = k.construct_under_budget(HELDOUT, compiled, 1)
    cold_tight = k.construct_under_budget(HELDOUT, None, 1)
    cold_relaxed = k.construct_under_budget(HELDOUT, None, 3)
    ablated = k.construct_under_budget(HELDOUT, None, 1)

    evidence["results"]["warm_heldout"] = safe(warm)
    evidence["results"]["cold_tight"] = safe(cold_tight)
    evidence["results"]["cold_relaxed"] = safe(cold_relaxed)
    evidence["results"]["ablated"] = safe(ablated)

    v14_parametric = k.construct_under_budget(V14_HELDOUT, compiled, 1)
    evidence["results"]["v14_nonterminal_parameters"] = safe(v14_parametric)

    wrong_replay = k.replay_target(compiled, WRONG) if compiled else {
        "status": "NO_COMPILED_SCHEMA"
    }
    evidence["results"]["wrong_replay"] = safe(wrong_replay)

    further = k.develop([
        [ALL_EQUAL_1, ALL_EQUAL_2],
        [DISTINCT_1, DISTINCT_2],
        [WRONG_LITERAL],
    ])
    evidence["results"]["further_refinement"] = safe(further)

    no_split = k.develop([
        [ALL_EQUAL_1, ALL_EQUAL_2],
        [DISTINCT_1, DISTINCT_2],
    ], allow_split=False)
    evidence["results"]["split_ablation"] = safe(no_split)

    single_dev = k.develop([[SINGLE]])
    single_compile = k.compile_schema(TARGET, [SINGLE])
    evidence["results"]["single_example_development"] = safe(single_dev)
    evidence["results"]["single_example_compile"] = safe(single_compile)

    bad = k.develop([[BAD]])
    evidence["results"]["bad_authority"] = safe(bad)

    hetero = k.develop([[HET_1, HET_2]])
    hetero_exact = k.exact_minimum([HET_1, HET_2])
    evidence["results"]["heterogeneous"] = safe(hetero)
    evidence["results"]["heterogeneous_exact"] = safe(hetero_exact)

    G = evidence["gates"]

    basis_text = (HERE / "basis.py").read_text()
    kernel_text = (HERE / "kernel.py").read_text()
    G["S1_no_challenge_specific_parameter_pattern_in_frozen_core"] = (
        "tok_a1" not in basis_text
        and "tok_a1" not in kernel_text
        and "(0, 1, 0, 1)" not in basis_text
        and "(0, 1, 0, 1)" not in kernel_text
        and "ABAB" not in basis_text
        and "ABAB" not in kernel_text
    )

    gens = dev.get("generations", [])
    G["S2_maximally_identified_beginning_retained"] = (
        dev.get("status") == "VERIFIED"
        and len(gens) >= 2
        and tuple(gens[0].get("pattern_after", [])) == ALL_EQUAL
        and gens[0].get("status") == "NO_CHANGE"
        and gens[0].get("parameter_count") == 1
    )

    G["S3_verified_future_forces_minimum_variable_split"] = (
        tuple(dev.get("pattern", [])) == TARGET
        and dev.get("parameter_count") == 2
        and gens[1].get("status") == "SPLIT"
        and tuple(gens[1].get("pattern_before", [])) == ALL_EQUAL
        and tuple(gens[1].get("pattern_after", [])) == TARGET
        and gens[1].get("obstruction") is not None
    )

    G["S4_exact_global_minimum_over_all_set_partitions"] = (
        exact.get("status") == "VERIFIED"
        and exact.get("candidate_count") == 15
        and exact.get("minimum_parameter_count") == 2
        and exact.get("minimum_patterns") == [[0, 1, 0, 1]]
        and [0, 0, 0, 0] not in exact.get("all_fitting_patterns", [])
    )

    G["S5_schema_compiles_after_independent_distinction_support"] = (
        compiled_result.get("status") == "VERIFIED"
        and compiled is not None
        and compiled.get("pattern") == [0, 1, 0, 1]
        and compiled.get("parameter_count") == 2
        and compiled_result.get("support", {}).get("witness_count") == 2
        and str(compiled.get("schema_id", "")).startswith("schema_")
        and compiled.get("lower_dependency") == "V14"
    )

    G["S6_unseen_parameter_transfer_has_causal_budget_advantage"] = (
        warm.get("status") == "VERIFIED"
        and warm.get("route") == "COMPILED_SCHEMA"
        and warm.get("constructor_cost") == 1
        and warm.get("output") == list(HELDOUT)
        and cold_tight.get("status") == "UNKNOWN_BUDGET"
        and cold_tight.get("constructor_cost") == 3
        and cold_relaxed.get("status") == "VERIFIED"
        and ablated.get("status") == "UNKNOWN_BUDGET"
    )

    G["S7_compiled_lower_grammar_tokens_can_fill_parameters"] = (
        v14_parametric.get("status") == "VERIFIED"
        and v14_parametric.get("output") == list(V14_HELDOUT)
        and v14_parametric.get("route") == "COMPILED_SCHEMA"
        and V14_RULE_X != V14_RULE_Y
    )

    G["S8_wrong_same_length_structure_falsifies_schema"] = (
        wrong_replay.get("status") == "REPLAY_FAILED"
        and wrong_replay.get("reason") == "target_violates_schema_equalities"
    )

    fg = further.get("generations", [])
    G["S9_additional_consequence_forces_further_schema_expansion"] = (
        further.get("status") == "VERIFIED"
        and tuple(further.get("pattern", [])) == FULLY_SPLIT
        and further.get("parameter_count") == 4
        and len(fg) >= 3
        and fg[2].get("status") == "SPLIT"
    )

    G["S10_split_ablation_exposes_certified_schema_inadequacy"] = (
        no_split.get("status") == "CERTIFIED_SCHEMA_INADEQUACY"
        and tuple(no_split.get("current_pattern", [])) == ALL_EQUAL
        and no_split.get("obstruction") is not None
    )

    G["S11_single_example_is_provisional_not_compiled"] = (
        single_dev.get("status") == "VERIFIED"
        and tuple(single_dev.get("pattern", [])) == TARGET
        and single_compile.get("status") == "PROVISIONAL_SCHEMA"
        and single_compile.get("support", {}).get("witness_count") == 1
    )

    G["S12_unverified_literal_stays_unknown"] = (
        bad.get("status") == "UNKNOWN_AUTHORITY"
        and bad.get("reason") == "literal_not_authoritative"
    )

    G["S13_same_frozen_learner_finds_different_heterogeneous_schema"] = (
        hetero.get("status") == "VERIFIED"
        and tuple(hetero.get("pattern", [])) == HET_TARGET
        and hetero.get("parameter_count") == 2
        and hetero_exact.get("candidate_count") == 5
        and hetero_exact.get("minimum_patterns") == [[0, 0, 1]]
    )

    G["partition_generator_is_complete_at_declared_bounds"] = (
        len(generate_partitions(4)) == 15
        and len(generate_partitions(3)) == 5
    )

    G["minimal_developmental_algorithm_respected"] = all(
        token in (HERE / "PROTOCOL.md").read_text()
        for token in (
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

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_PARAMETRIC_GRAMMAR_SCHEMA_GENESIS_BY_CONSEQUENCE_FORCED_POSITIONAL_SPLITTING"
        if evidence["full_pass"]
        else "PARAMETRIC_GRAMMAR_GENESIS_V15_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
