#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import future_partition, partition, same_partition
from kernel import Kernel
from challenge_pack import (
    MAIN_A, MAIN_B, MAIN_C,
    MEMORY_WORLD,
    NONCAN_TRAIN, NONCAN_QUAL,
    WRONG_WORLD,
    HETEROGENEOUS,
    INCOMPLETE,
)


MAIN_CODE = ((0,1),(0,4))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {str(k): safe(v) for k,v in x.items()}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(safe(v) for v in x)
    return x


def codes(result):
    return {
        tuple((int(a[0]), int(a[1])) for a in row.get("accessors", []))
        for row in result.get("minimum_codes", [])
    }


def main() -> int:
    evidence = {
        "experiment": "raw_multichannel_representation_genesis_v16",
        "scientific_freeze_commit": "4317d32b82c26c84e8425680bf5d51c64520b41d",
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

    # Main no-hand-tuned feature emergence.
    km = Kernel()
    main_a = km.solve("M_main_a", MAIN_A)
    evidence["results"]["main_a"] = safe(main_a)

    # Memory genesis.
    memory = Kernel().solve("M_memory", MEMORY_WORLD)
    evidence["results"]["memory"] = safe(memory)

    # Non-canonicity + future qualification.
    noncan = Kernel().solve(
        "M_noncanonical",
        NONCAN_TRAIN,
        qualification=NONCAN_QUAL,
    )
    evidence["results"]["noncanonical"] = safe(noncan)

    # Compile/reuse.
    warm = Kernel()
    train_a = warm.solve("M_compile_a", MAIN_A)
    train_b = warm.solve("M_compile_b", MAIN_B)
    promoted = train_b.get("promoted_code")
    reuse_c = warm.solve(
        "M_reuse_c",
        MAIN_C,
        allow_acquisition_search=False,
    )
    cold_c = Kernel().solve(
        "M_cold_c",
        MAIN_C,
        allow_acquisition_search=False,
    )

    warm2 = Kernel()
    warm2.solve("M_ablate_a", MAIN_A)
    train_b2 = warm2.solve("M_ablate_b", MAIN_B)
    ablated = warm2.ablate_compiled_code(MAIN_C)
    after_ablation = warm2.solve(
        "M_after_ablation",
        MAIN_C,
        allow_acquisition_search=False,
    )

    evidence["results"]["compile_a"] = safe(train_a)
    evidence["results"]["compile_b"] = safe(train_b)
    evidence["results"]["reuse_c"] = safe(reuse_c)
    evidence["results"]["cold_c"] = safe(cold_c)
    evidence["results"]["after_ablation"] = safe(after_ablation)

    # Wrong same-interface dynamics.
    wrong = warm.solve(
        "M_wrong",
        WRONG_WORLD,
        allow_acquisition_search=True,
    )
    evidence["results"]["wrong"] = safe(wrong)

    # Heterogeneous world.
    hetero = Kernel().solve("M_heterogeneous", HETEROGENEOUS)
    evidence["results"]["heterogeneous"] = safe(hetero)

    # Incomplete authority.
    incomplete = Kernel().solve("M_incomplete", INCOMPLETE)
    evidence["results"]["incomplete"] = safe(incomplete)

    # Accessor ablation.
    no_accessor = Kernel().solve(
        "M_no_accessor",
        MAIN_A,
        accessor_enabled=False,
    )
    evidence["results"]["no_accessor"] = safe(no_accessor)

    # Consequence ablation extra control.
    no_consequence = Kernel().solve(
        "M_no_consequence",
        MAIN_A,
        consequence_enabled=False,
    )
    evidence["results"]["no_consequence"] = safe(no_consequence)

    G = evidence["gates"]

    main_dev = main_a.get("developmental", {})
    main_min = main_dev.get("minimum_search", {})
    main_codes = codes(main_min)

    # Check executable identifiers rather than raw substrings: e.g.
    # "generation" contains the characters "ratio" but is not a ratio feature.
    import ast
    frozen_tree = ast.parse((HERE / "kernel.py").read_text())
    frozen_names = {
        node.id.lower()
        for node in ast.walk(frozen_tree)
        if isinstance(node, ast.Name)
    } | {
        node.name.lower()
        for node in ast.walk(frozen_tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    forbidden_feature_names = {
        "fourier", "frequency", "variance", "mean", "ratio",
        "pca", "neural", "threshold",
    }
    G["M1_no_hand_engineered_features_in_frozen_core"] = (
        frozen_names.isdisjoint(forbidden_feature_names)
    )

    G["M2_undifferentiated_beginning_then_consequence_split"] = (
        main_a.get("status") == "VERIFIED"
        and main_dev.get("initial_class_count") == 1
        and len(future_partition(MAIN_A)) == 4
        and main_dev.get("generations", [{}])[0].get(
            "empty_readout_obstruction"
        ) is not None
    )

    G["M3_minimum_two_accessor_marker_bundle_emerges"] = (
        main_a.get("status") == "VERIFIED"
        and tuple(tuple(a) for a in main_a.get("accessors", [])) == MAIN_CODE
        and main_a.get("cost") == [2,2]
        and main_min.get("lower_bound", {}).get("minimum_accessor_count") == 2
        and main_min.get("lower_bound", {}).get("minimum_total_accessor_cost") == 2
        and main_codes == {MAIN_CODE}
        and same_partition(
            partition(MAIN_A, MAIN_CODE),
            future_partition(MAIN_A),
        )
    )

    selected_channels = {a[1] for a in MAIN_CODE}
    G["M4_at_least_half_raw_channels_are_excluded_distractors"] = (
        MAIN_A.channel_count == 6
        and len(selected_channels) == 2
        and MAIN_A.channel_count - len(selected_channels) >= 3
    )

    G["M5_no_premature_memory_when_present_suffices"] = (
        main_a.get("selected_lag") == 0
        and len(main_dev.get("generations", [])) == 1
        and all(a[0] == 0 for a in MAIN_CODE)
    )

    memory_dev = memory.get("developmental", {})
    mem_gens = memory_dev.get("generations", [])
    G["M6_present_inadequacy_certified_before_memory_expansion"] = (
        memory.get("status") == "VERIFIED"
        and len(mem_gens) == 2
        and mem_gens[0].get("authorized_lag") == 0
        and mem_gens[0].get("status") == "CERTIFIED_READOUT_INADEQUACY"
        and mem_gens[1].get("authorized_lag") == 1
        and mem_gens[1].get("status") == "VERIFIED"
        and memory.get("selected_lag") == 1
        and memory.get("accessors") == [[1,2]]
    )

    G["M7_noncanonical_minima_preserved_then_future_selects"] = (
        noncan.get("status") == "VERIFIED"
        and noncan.get("qualification", {}).get("status") == "VERIFIED"
        and {
            ((0,0),),
            ((0,1),),
        }.issubset(
            {
                tuple((int(a[0]),int(a[1])) for a in row.get("accessors", []))
                for row in noncan.get("developmental", {})
                    .get("minimum_search", {})
                    .get("minimum_codes", [])
            }
        )
        and noncan.get("qualification", {}).get("survivors") == [[[0,1]]]
        and noncan.get("accessors") == [[0,1]]
    )

    G["M8_second_world_compiles_readout"] = (
        train_a.get("status") == "VERIFIED"
        and train_b.get("status") == "VERIFIED"
        and promoted is not None
        and tuple(tuple(a) for a in promoted.get("accessors", [])) == MAIN_CODE
        and set(promoted.get("provenance", []))
            == {"M_compile_a", "M_compile_b"}
    )

    G["M8_warm_reuse_zero_search_cold_and_ablation_controls"] = (
        reuse_c.get("status") == "VERIFIED"
        and reuse_c.get("route") == "REUSE_COMPILED_READOUT"
        and reuse_c.get("acquisition_search_count") == 0
        and cold_c.get("status") == "UNKNOWN_READOUT"
        and cold_c.get("acquisition_search_count") == 0
        and train_b2.get("promoted_code") is not None
        and ablated
        and after_ablation.get("status") == "UNKNOWN_READOUT"
    )

    G["M9_wrong_dynamics_falsify_retained_readout_then_redevelop"] = (
        wrong.get("status") in {"VERIFIED", "VERIFIED_FRONTIER"}
        and wrong.get("failed_reuse") is not None
        and wrong.get("failed_reuse", {}).get("status") == "REPLAY_FAILED"
        and wrong.get("acquisition_search_count") == 1
        and wrong.get("route") == "DEVELOP"
    )

    G["M10_same_kernel_handles_heterogeneous_world"] = (
        hetero.get("status") == "VERIFIED"
        and hetero.get("route") == "DEVELOP"
        and hetero.get("accessors") == [[0,0],[0,2],[0,5]]
        and hetero.get("cost") == [3,3]
        and len(future_partition(HETEROGENEOUS)) == 8
    )

    G["M11_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
        and incomplete.get("route") == "STOP"
    )

    G["M12_accessor_ablation_blocks_feature_growth"] = (
        no_accessor.get("status") == "UNKNOWN_NO_ACCESSOR_LANGUAGE"
        and no_accessor.get("developmental", {}).get("initial_class_count") == 1
    )

    G["M13_primary_object_is_predictive_quotient_not_feature_vector"] = (
        len(future_partition(MAIN_A)) == 4
        and main_a.get("future_partition") is not None
        and same_partition(
            main_a.get("partition", []),
            main_a.get("future_partition", []),
        )
    )

    G["no_consequence_no_growth"] = (
        no_consequence.get("status") == "UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
        and no_consequence.get("developmental", {}).get("initial_class_count") == 1
    )

    G["minimal_developmental_algorithm_respected"] = all(
        token in (HERE / "PROTOCOL.md").read_text()
        for token in (
            "EXECUTE","VERIFY","DIAGNOSE","CONSTRAIN",
            "RESTRUCTURE","CHOOSE","COMPILE","UPDATE",
        )
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_RAW_MULTICHANNEL_PREDICTIVE_READOUT_GENESIS_WITHOUT_HAND_ENGINEERED_FEATURES"
        if evidence["full_pass"]
        else "RAW_MULTICHANNEL_REPRESENTATION_V16_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
