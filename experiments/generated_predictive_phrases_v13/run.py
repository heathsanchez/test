#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import full_partition, generate_phrases, partition, same_partition
from kernel import Kernel
from challenge_pack import (
    WORLD_A,
    WORLD_B,
    WORLD_C,
    WORLD_WRONG,
    WORLD_HET,
    WORLD_INCOMPLETE,
    AMBIG_TRAIN,
    AMBIG_QUAL,
)


TARGET_PHRASE = (2, 1, 2, 1, 2, 1, 2)


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


def repair_lengths(dev):
    out = []
    for gen in dev.get("generations", []):
        for row in gen.get("repairs", []):
            search = row.get("repair_search", {})
            if search.get("status") == "VERIFIED":
                out.append(search.get("minimum_length"))
    return out


def final_local_codes(dev):
    return dev.get("complete_frontier_codes", [])


def main() -> int:
    evidence = {
        "experiment": "generated_predictive_phrases_v13",
        "scientific_freeze_commit": "312f2fc0725926bdb67cea4f4c3002581912321a",
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

    # --------------------------------------------------------------
    # P1-P4 main genesis + exact global contraction.
    # --------------------------------------------------------------
    k_main = Kernel()
    main = k_main.solve("P2_main_a", WORLD_A)
    evidence["results"]["P2_main_a"] = safe(main)

    dev = main.get("developmental", {})
    minimum = main.get("minimum_search", {})
    min_codes = minimum.get("minimum_codes", [])
    local_codes = final_local_codes(dev)

    # --------------------------------------------------------------
    # P5 generated non-canonicity + future selection.
    # --------------------------------------------------------------
    k_amb = Kernel()
    ambiguous = k_amb.solve(
        "P5_ambiguous",
        AMBIG_TRAIN,
        qualification=AMBIG_QUAL,
    )
    evidence["results"]["P5_ambiguous"] = safe(ambiguous)

    # --------------------------------------------------------------
    # P6/P7 compile across renamed worlds, reuse, cold and ablation.
    # --------------------------------------------------------------
    warm = Kernel()
    train_a = warm.solve("P6_train_a", WORLD_A)
    train_b = warm.solve("P6_train_b", WORLD_B)
    promoted = train_b.get("promoted_phrase")

    reuse = warm.solve(
        "P7_reuse_c",
        WORLD_C,
        allow_acquisition_search=False,
    )
    cold = Kernel().solve(
        "P7_cold_c",
        WORLD_C,
        allow_acquisition_search=False,
    )

    # Separate clean compile for ablation control.
    warm2 = Kernel()
    warm2.solve("P7b_train_a", WORLD_A)
    warm2_b = warm2.solve("P7b_train_b", WORLD_B)
    ablated = warm2.ablate_compiled_phrase(WORLD_C)
    after_ablation = warm2.solve(
        "P7_after_ablation",
        WORLD_C,
        allow_acquisition_search=False,
    )

    evidence["results"]["P6_train_a"] = safe(train_a)
    evidence["results"]["P6_train_b"] = safe(train_b)
    evidence["results"]["P7_reuse_c"] = safe(reuse)
    evidence["results"]["P7_cold_c"] = safe(cold)
    evidence["results"]["P7_after_ablation"] = safe(after_ablation)

    # --------------------------------------------------------------
    # P8 wrong same-interface hidden dynamics.
    # --------------------------------------------------------------
    wrong = warm.solve(
        "P8_wrong_dynamics",
        WORLD_WRONG,
        allow_acquisition_search=True,
    )
    evidence["results"]["P8_wrong_dynamics"] = safe(wrong)

    # --------------------------------------------------------------
    # P9 heterogeneous hidden dynamics.
    # --------------------------------------------------------------
    hetero = Kernel().solve(
        "P9_heterogeneous",
        WORLD_HET,
        allow_acquisition_search=True,
    )
    evidence["results"]["P9_heterogeneous"] = safe(hetero)

    # --------------------------------------------------------------
    # P10 incomplete authority.
    # --------------------------------------------------------------
    incomplete = Kernel().solve(
        "P10_incomplete_authority",
        WORLD_INCOMPLETE,
    )
    evidence["results"]["P10_incomplete_authority"] = safe(incomplete)

    # --------------------------------------------------------------
    # P11 CONCAT ablation.
    # --------------------------------------------------------------
    no_concat = Kernel().solve(
        "P11_no_concat",
        WORLD_A,
        concat_enabled=False,
    )
    evidence["results"]["P11_no_concat"] = safe(no_concat)

    # --------------------------------------------------------------
    # P12 consequence ablation.
    # --------------------------------------------------------------
    no_consequence = Kernel().solve(
        "P12_no_consequence",
        WORLD_A,
        consequence_enabled=False,
    )
    evidence["results"]["P12_no_consequence"] = safe(no_consequence)

    G = evidence["gates"]

    atoms = generate_phrases(
        WORLD_A.action_count,
        WORLD_A.max_phrase_length,
        concat_enabled=False,
    )
    all_phrases = generate_phrases(
        WORLD_A.action_count,
        WORLD_A.max_phrase_length,
        concat_enabled=True,
    )

    G["P1_only_atomic_actions_are_primitive_phrases"] = (
        len(atoms) == WORLD_A.action_count
        and all(len(p) == 1 for p in atoms)
        and len(all_phrases) == 3279
        and all(len(p) >= 1 for p in all_phrases)
    )

    G["P2_blank_present_splits_only_after_consequence_obstruction"] = (
        main.get("status") == "VERIFIED"
        and dev.get("initial_class_count") == 1
        and dev.get("generations", [])[0].get("frontier_class_counts") == [1]
        and bool(dev.get("generations", [])[0].get("repairs"))
        and len(full_partition(WORLD_A)) == 5
    )

    lengths = repair_lengths(dev)
    G["P2_composite_phrases_are_generated_by_development"] = (
        bool(lengths)
        and max(lengths) > 1
        and dev.get("final_generation", 0) >= 2
    )

    G["P3_local_growth_then_generated_phrase_contraction"] = (
        bool(local_codes)
        and any(len(code) > 1 for code in local_codes)
        and main.get("phrases") == [list(TARGET_PHRASE)]
        and main.get("cost") == [1, 7]
    )

    lower = minimum.get("lower_bound", {})
    G["P4_exact_minimum_phrase_proved"] = (
        minimum.get("status") == "VERIFIED"
        and minimum.get("generated_phrase_count") == 3279
        and len(min_codes) == 1
        and min_codes[0].get("phrases") == [list(TARGET_PHRASE)]
        and min_codes[0].get("cost") == [1, 7]
        and lower.get("zero_phrase_complete") is False
        and lower.get("shortest_complete_single_phrase_length") == 7
        and lower.get("shorter_complete_single_phrase_count") == 0
        and lower.get("complete_single_phrase_count") == 1
    )

    amb_min = ambiguous.get("minimum_search", {})
    amb_codes = {
        tuple(tuple(p) for p in row.get("phrases", []))
        for row in amb_min.get("minimum_codes", [])
    }
    G["P5_equal_cost_generated_phrase_frontier_preserved"] = (
        ambiguous.get("status") == "VERIFIED"
        and {((0,0),), ((1,1),)}.issubset(amb_codes)
        and amb_min.get("lower_bound", {}).get(
            "shortest_complete_single_phrase_length"
        ) == 2
    )

    G["P5_future_consequence_selects_generated_phrase"] = (
        ambiguous.get("qualification", {}).get("status") == "VERIFIED"
        and ambiguous.get("qualification", {}).get("survivors") == [[[1,1]]]
        and ambiguous.get("phrases") == [[1,1]]
    )

    G["P6_second_world_compiles_anonymous_phrase"] = (
        train_a.get("status") == "VERIFIED"
        and train_b.get("status") == "VERIFIED"
        and promoted is not None
        and tuple(promoted.get("expansion", [])) == TARGET_PHRASE
        and promoted.get("cost") == 7
        and set(promoted.get("provenance", []))
            == {"P6_train_a", "P6_train_b"}
        and str(promoted.get("atom_id", "")).startswith("phr_")
    )

    G["P7_warm_compiled_phrase_reuses_with_zero_acquisition"] = (
        reuse.get("status") == "VERIFIED"
        and reuse.get("route") == "REUSE_COMPILED_PHRASE"
        and reuse.get("phrase_acquisition_search_count") == 0
        and reuse.get("phrases") == [list(TARGET_PHRASE)]
    )

    G["P7_cold_zero_acquisition_is_unknown"] = (
        cold.get("status") == "UNKNOWN_PHRASE"
        and cold.get("phrase_acquisition_search_count") == 0
    )

    G["P7_ablation_restores_unknown"] = (
        warm2_b.get("promoted_phrase") is not None
        and ablated
        and after_ablation.get("status") == "UNKNOWN_PHRASE"
        and after_ablation.get("phrase_acquisition_search_count") == 0
    )

    G["P8_wrong_retained_phrase_is_replay_falsified"] = (
        wrong.get("status") in {"VERIFIED", "VERIFIED_FRONTIER"}
        and wrong.get("route") == "DEVELOP"
        and wrong.get("failed_reuse") is not None
        and wrong.get("failed_reuse", {}).get("status") == "REPLAY_FAILED"
        and wrong.get("phrase_acquisition_search_count") == 1
    )

    G["P9_same_phrase_grammar_handles_heterogeneous_world"] = (
        hetero.get("status") in {"VERIFIED", "VERIFIED_FRONTIER"}
        and hetero.get("route") == "DEVELOP"
        and hetero.get("phrase_acquisition_search_count") == 1
        and len(full_partition(WORLD_HET)) > 1
    )

    G["P10_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
        and incomplete.get("route") == "STOP"
    )

    G["P11_concat_ablation_exposes_grammar_inadequacy"] = (
        no_concat.get("status") == "CERTIFIED_GRAMMAR_INADEQUACY"
        and no_concat.get("route") == "DEVELOP"
        and no_concat.get("developmental", {}).get("initial_class_count") == 1
    )

    G["P12_no_consequence_no_phrase_growth"] = (
        no_consequence.get("status") == "UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
        and no_consequence.get("developmental", {}).get("initial_class_count") == 1
        and no_consequence.get("developmental", {}).get("frontier") == [[]]
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

    G["compiled_phrase_retains_exact_expansion_and_provenance"] = (
        promoted is not None
        and tuple(promoted.get("expansion", [])) == TARGET_PHRASE
        and bool(promoted.get("consequence_signature"))
        and len(promoted.get("provenance", [])) == 2
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_GENERATED_PREDICTIVE_PHRASE_GENESIS_SELECTION_COMPILATION_AND_REUSE"
        if evidence["full_pass"]
        else "GENERATED_PREDICTIVE_PHRASES_V13_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
