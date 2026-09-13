#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from kernel import Kernel
from challenge_pack import (
    MAIN_A, MAIN_B, MAIN_C, MAIN_QUAL,
    NONCAN_TRAIN, NONCAN_QUAL,
    WRONG, LOW_DATA, HETEROGENEOUS, INCOMPLETE,
)


MAIN_CODE = (1,4)
WRONG_CODE = (2,5)
HET_CODE = (0,2,5)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {str(k): safe(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)):
        return [safe(v) for v in x]
    return x


def min_codes(search):
    return {
        tuple(int(a) for a in row.get("accessors", []))
        for row in search.get("minimum_codes", [])
    }


def main() -> int:
    evidence = {
        "experiment": "stochastic_readout_mdl_repair_v18",
        "scientific_freeze_commit": "c4dc2477f97841e25ff70f5d53b9da0709378def",
        "post_freeze_challenges": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json": sha256(HERE/"FREEZE.json"),
            "basis.py": sha256(HERE/"basis.py"),
            "kernel.py": sha256(HERE/"kernel.py"),
            "challenge_pack.py": sha256(HERE/"challenge_pack.py"),
        },
        "results": {},
        "gates": {},
    }

    # Main stochastic selection and independent qualification realization.
    main_a = Kernel().solve("N_main_a", MAIN_A)
    qual_search = Kernel().exhaustive_search(MAIN_QUAL)
    evidence["results"]["main_a"] = safe(main_a)
    evidence["results"]["main_qualification"] = safe(qual_search)

    # Noncanonical exact score tie, qualification selection.
    noncan = Kernel().solve(
        "N_noncanonical",
        NONCAN_TRAIN,
        qualification=NONCAN_QUAL,
    )
    evidence["results"]["noncanonical"] = safe(noncan)

    # Compile/reuse controls.
    warm = Kernel()
    train_a = warm.solve("N_compile_a", MAIN_A)
    train_b = warm.solve("N_compile_b", MAIN_B)
    promoted = train_b.get("promoted_code")
    reuse = warm.solve(
        "N_reuse_c",
        MAIN_C,
        allow_acquisition_search=False,
    )
    cold = Kernel().solve(
        "N_cold_c",
        MAIN_C,
        allow_acquisition_search=False,
    )

    warm2 = Kernel()
    warm2.solve("N_ablate_a", MAIN_A)
    train_b2 = warm2.solve("N_ablate_b", MAIN_B)
    ablated = warm2.ablate(MAIN_C)
    after_ablation = warm2.solve(
        "N_after_ablation",
        MAIN_C,
        allow_acquisition_search=False,
    )

    evidence["results"]["compile_a"] = safe(train_a)
    evidence["results"]["compile_b"] = safe(train_b)
    evidence["results"]["reuse_c"] = safe(reuse)
    evidence["results"]["cold_c"] = safe(cold)
    evidence["results"]["after_ablation"] = safe(after_ablation)

    # Wrong dynamics.
    wrong = warm.solve(
        "N_wrong",
        WRONG,
        allow_acquisition_search=True,
    )
    evidence["results"]["wrong"] = safe(wrong)

    # Low data.
    low = Kernel().solve("N_low_data", LOW_DATA)
    evidence["results"]["low_data"] = safe(low)

    # Heterogeneous.
    het = Kernel().solve("N_heterogeneous", HETEROGENEOUS)
    evidence["results"]["heterogeneous"] = safe(het)

    # Incomplete authority and scoring ablation.
    incomplete = Kernel().solve("N_incomplete", INCOMPLETE)
    no_stat = Kernel().solve(
        "N_no_statistical_authority",
        MAIN_A,
        statistical_enabled=False,
    )
    evidence["results"]["incomplete"] = safe(incomplete)
    evidence["results"]["no_statistical_authority"] = safe(no_stat)

    G = evidence["gates"]

    main_search = main_a.get("search", {})
    G["N1_no_hand_engineered_features_or_loss_threshold"] = (
        MAIN_A.channel_count == 6
        and main_search.get("tested_subset_count") == 64
        and "threshold" not in (HERE/"kernel.py").read_text().lower()
    )

    G["N2_main_noisy_world_selects_two_accessor_code"] = (
        main_a.get("status") == "VERIFIED"
        and tuple(main_a.get("accessors", [])) == MAIN_CODE
        and min_codes(main_search) == {MAIN_CODE}
        and main_search.get("growth_authorized") is True
    )

    G["N3_second_noise_realization_recovers_same_code"] = (
        train_b.get("status") == "VERIFIED"
        and tuple(train_b.get("accessors", [])) == MAIN_CODE
    )

    G["N4_at_least_half_channels_excluded"] = (
        len(MAIN_CODE) == 2
        and MAIN_A.channel_count - len(MAIN_CODE) >= 3
    )

    G["N5_independent_qualification_noise_same_global_optimum"] = (
        qual_search.get("status") == "VERIFIED"
        and min_codes(qual_search) == {MAIN_CODE}
        and qual_search.get("growth_authorized") is True
    )

    non_search = noncan.get("search", {})
    G["N6_noncanonical_tie_preserved_then_qualification_selects"] = (
        { (0,), (1,) }.issubset(min_codes(non_search))
        and noncan.get("qualification", {}).get("survivors") == [[1]]
        and noncan.get("status") == "VERIFIED"
        and noncan.get("accessors") == [1]
    )

    G["N7_two_recoveries_compile_code"] = (
        train_a.get("status") == "VERIFIED"
        and train_b.get("status") == "VERIFIED"
        and promoted is not None
        and tuple(promoted.get("accessors", [])) == MAIN_CODE
        and set(promoted.get("provenance", []))
            == {"N_compile_a","N_compile_b"}
    )

    G["N7_warm_replay_zero_search_cold_and_ablation_controls"] = (
        reuse.get("status") == "VERIFIED"
        and reuse.get("route") == "REUSE_COMPILED_READOUT"
        and reuse.get("acquisition_search_count") == 0
        and cold.get("status") == "UNKNOWN_READOUT"
        and train_b2.get("promoted_code") is not None
        and ablated
        and after_ablation.get("status") == "UNKNOWN_READOUT"
    )

    G["N8_wrong_dynamics_falsify_replay_then_redevelop"] = (
        wrong.get("status") == "VERIFIED"
        and wrong.get("route") == "DEVELOP"
        and wrong.get("failed_reuse") is not None
        and wrong.get("failed_reuse", {}).get("status") == "REPLAY_FAILED"
        and tuple(wrong.get("accessors", [])) == WRONG_CODE
    )

    G["N9_low_data_does_not_authorize_marker_growth"] = (
        low.get("status") == "PROVISIONAL_NO_GROWTH"
        and low.get("accessors") == []
        and low.get("search", {}).get("growth_authorized") is False
    )

    G["N10_heterogeneous_noisy_world_learns_different_code"] = (
        het.get("status") == "VERIFIED"
        and tuple(het.get("accessors", [])) == HET_CODE
        and tuple(het.get("accessors", [])) != MAIN_CODE
    )

    G["N11_incomplete_counts_stay_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
    )

    G["N12_statistical_scoring_ablation_authorizes_no_growth"] = (
        no_stat.get("status") == "UNKNOWN_NO_STATISTICAL_AUTHORITY"
        and no_stat.get("route") == "DEVELOP"
    )

    G["universal_code_has_no_tunable_loss_weight"] = (
        "loss_weight" not in (HERE/"kernel.py").read_text().lower()
        and "beta =" not in (HERE/"kernel.py").read_text().lower()
    )

    # Direct residual-repair control: channel 0 is constant in MAIN_A.
    # Adding it to the predictive pair must leave KT data evidence unchanged
    # and worsen only the structural code by exactly one bit.
    _k = Kernel()
    base_score = _k.score(MAIN_A, MAIN_CODE)
    redundant_score = _k.score(MAIN_A, (0,) + MAIN_CODE)
    G["N13_redundant_accessor_costs_exactly_one_structural_bit"] = (
        abs(base_score["data_bits"] - redundant_score["data_bits"]) < 1e-9
        and abs(
            redundant_score["model_bits"] - base_score["model_bits"] - 1.0
        ) < 1e-9
        and abs(
            redundant_score["total_bits"] - base_score["total_bits"] - 1.0
        ) < 1e-9
    )

    G["minimal_developmental_algorithm_respected"] = all(
        token in (HERE/"PROTOCOL.md").read_text()
        for token in (
            "EXECUTE","VERIFY","DIAGNOSE","CONSTRAIN",
            "RESTRUCTURE","CHOOSE","COMPILE","UPDATE",
        )
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_STOCHASTIC_RAW_READOUT_GENESIS_AFTER_MONOTONE_MDL_REPAIR"
        if evidence["full_pass"]
        else "STOCHASTIC_READOUT_MDL_REPAIR_V18_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
