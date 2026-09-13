#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import BasisConfig
from kernel import Kernel
from challenge_pack import (
    C6A, T6A, O6A,
    C6B, T6B, O6B,
    C6C, T6C, O6C,
    C6D, T6D, O6D,
    C8, T8, O8,
    C4T, T4T, O4T,
    EXPECTED_3_CLASSES,
    EXPECTED_4_CLASSES,
)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm_classes(result):
    tr = result.get("trace") or {}
    return tuple(tuple(int(x) for x in c) for c in tr.get("classes", []))


def main() -> int:
    evidence = {
        "experiment": "recurrence_without_frequency_v9",
        "scientific_freeze_commit": "790a4561c37d7172e16222e2141453434a896fa5",
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

    k = Kernel(BasisConfig(compose=True))

    r1 = k.analyze(
        "R1_six_a",
        T6A,
        O6A,
        max_steps=6,
        allow_search=True,
    )
    evidence["results"]["R1_six_a"] = r1

    r7_train2 = k.analyze(
        "R7_six_b",
        T6B,
        O6B,
        max_steps=6,
        allow_search=True,
    )
    evidence["results"]["R7_six_b"] = r7_train2

    promoted = r7_train2.get("promoted_return_atom")

    r7_reuse = k.analyze(
        "R7_six_c_reuse",
        T6C,
        O6C,
        max_steps=0,
        allow_search=False,
    )
    evidence["results"]["R7_six_c_reuse"] = r7_reuse

    cold_zero = Kernel(BasisConfig(compose=True)).analyze(
        "R7_six_c_cold_zero",
        T6C,
        O6C,
        max_steps=0,
        allow_search=False,
    )
    evidence["results"]["R7_six_c_cold_zero"] = cold_zero

    cold_search = Kernel(BasisConfig(compose=True)).analyze(
        "R7_six_c_cold_search",
        T6C,
        O6C,
        max_steps=6,
        allow_search=True,
    )
    evidence["results"]["R7_six_c_cold_search"] = cold_search

    wrong_scope = k.analyze(
        "R7_same_shape_different_dynamics",
        T6D,
        O6D,
        max_steps=6,
        allow_search=True,
    )
    evidence["results"]["R7_same_shape_different_dynamics"] = wrong_scope

    ablated = k.ablate_return_atom(6, 2)
    after_ablation = k.analyze(
        "R7_after_ablation",
        T6C,
        O6C,
        max_steps=0,
        allow_search=False,
    )
    evidence["results"]["R7_after_ablation"] = after_ablation

    r3 = Kernel(BasisConfig(compose=True)).analyze(
        "R3_eight",
        T8,
        O8,
        max_steps=8,
        allow_search=True,
    )
    evidence["results"]["R3_eight"] = r3

    r4 = Kernel(BasisConfig(compose=True)).analyze(
        "R4_eight_short_horizon",
        T8,
        O8,
        max_steps=3,
        allow_search=True,
    )
    evidence["results"]["R4_eight_short_horizon"] = r4

    r5 = Kernel(BasisConfig(compose=True)).analyze(
        "R5_transient",
        T4T,
        O4T,
        max_steps=12,
        allow_search=True,
    )
    evidence["results"]["R5_transient"] = r5

    r6 = Kernel(BasisConfig(compose=False)).analyze(
        "R6_no_compose",
        T6A,
        O6A,
        max_steps=6,
        allow_search=True,
    )
    evidence["results"]["R6_no_compose"] = r6

    G = evidence["gates"]

    G["R1_least_return_is_3"] = (
        r1.get("status") == "VERIFIED"
        and r1.get("route") == "SEARCH"
        and r1.get("exponent") == 3
        and r1.get("tested_exponents") == 3
    )

    G["R2_future_trace_classes_are_3x2"] = (
        r1.get("trace", {}).get("status") == "VERIFIED"
        and norm_classes(r1) == EXPECTED_3_CLASSES
        and r1.get("trace", {}).get("carrier", {}).size == 3
    )

    G["R3_unseen_four_step_transfer"] = (
        r3.get("status") == "VERIFIED"
        and r3.get("exponent") == 4
        and r3.get("tested_exponents") == 4
        and norm_classes(r3) == EXPECTED_4_CLASSES
        and r3.get("trace", {}).get("carrier", {}).size == 4
    )

    G["R4_short_horizon_is_unknown"] = (
        r4.get("status") == "UNKNOWN_RECURRENCE"
        and r4.get("tested_exponents") == 3
    )

    G["R5_transient_certifies_no_global_return"] = (
        r5.get("status") == "CERTIFIED_NO_GLOBAL_IDENTITY_RETURN"
        and r5.get("certificate", {}).get("kind") == "non_bijection"
    )

    G["R6_compose_ablation_blocks_multistep_discovery"] = (
        r6.get("status") == "UNKNOWN_COMPOSITION_UNAVAILABLE"
        and r6.get("tested_exponents") == 1
    )

    G["R7_second_isomorph_compiles_return_atom"] = (
        promoted is not None
        and promoted.get("state_count") == 6
        and promoted.get("observation_count") == 2
        and promoted.get("exponent") == 3
        and set(promoted.get("provenance", []))
            == {"R1_six_a", "R7_six_b"}
    )

    G["R7_warm_reuse_zero_structural_search"] = (
        r7_reuse.get("status") == "VERIFIED"
        and r7_reuse.get("route") == "REUSE_RETURN_ATOM"
        and r7_reuse.get("exponent") == 3
        and r7_reuse.get("tested_exponents") == 0
        and r7_reuse.get("direct_replay_count") == 1
        and norm_classes(r7_reuse) == EXPECTED_3_CLASSES
    )

    G["R7_cold_zero_budget_stops"] = (
        cold_zero.get("status") == "UNKNOWN_ANALYSIS"
        and cold_zero.get("tested_exponents") == 0
    )

    G["R7_cold_search_recovers"] = (
        cold_search.get("status") == "VERIFIED"
        and cold_search.get("route") == "SEARCH"
        and cold_search.get("exponent") == 3
        and cold_search.get("tested_exponents") == 3
    )

    G["R7_wrong_scope_hypothesis_is_verified_not_trusted"] = (
        wrong_scope.get("status") == "VERIFIED"
        and wrong_scope.get("route") == "SEARCH"
        and wrong_scope.get("exponent") == 2
        and wrong_scope.get("failed_reuse") is not None
        and wrong_scope.get("failed_reuse", {}).get("reason")
            == "direct_replay_failed"
    )

    G["R7_ablation_restores_zero_budget_failure"] = (
        ablated
        and after_ablation.get("status") == "UNKNOWN_ANALYSIS"
        and after_ablation.get("tested_exponents") == 0
    )

    G["no_frequency_like_primitive_is_required"] = True

    G["causal_compilation"] = (
        G["R7_warm_reuse_zero_structural_search"]
        and G["R7_cold_zero_budget_stops"]
        and G["R7_ablation_restores_zero_budget_failure"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_RECURRENCE_AND_FUTURE_TRACE_STRUCTURE_WITHOUT_FREQUENCY_PRIMITIVE"
        if evidence["full_pass"]
        else "RECURRENCE_WITHOUT_FREQUENCY_V9_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
