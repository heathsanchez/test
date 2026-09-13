#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import BasisConfig, FrameTrace, InfluenceRelation
from kernel import Kernel
from challenge_pack import (
    WORLD_A,
    WORLD_B,
    WORLD_C,
    WORLD_DIFFERENT,
    WORLD_PATH,
    WORLD_SHORT,
    WORLD_MISSING_INTERVENTION,
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


def analyze_world(
    kernel,
    request_id,
    world,
    *,
    max_return,
    intervention_complete=True,
    allow_pattern_search=True,
):
    return kernel.analyze(
        request_id,
        world["channel_count"],
        world["interventions"],
        world["trace"],
        max_return=max_return,
        intervention_search_complete=intervention_complete,
        allow_pattern_search=allow_pattern_search,
    )


def inferred_rows(result):
    rel = result.get("inference", {}).get("relation")
    return tuple(rel.rows) if rel is not None else None


def main() -> int:
    evidence = {
        "experiment": "simulated_cymatics_v11",
        "scientific_freeze_commit": "88c90e102e964a2a0d3d06daca5ff1fd3df126be",
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

    # C1 independent primary world.
    c1 = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=True)),
        "C1_grid_vertical",
        WORLD_A,
        max_return=12,
    )
    evidence["results"]["C1_grid_vertical"] = safe(c1)

    # C2 independent relabelled copy.
    c2 = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=True)),
        "C2_grid_vertical_permuted",
        WORLD_B,
        max_return=12,
    )
    evidence["results"]["C2_grid_vertical_permuted"] = safe(c2)

    # C3 compilation trajectory.
    warm = Kernel(BasisConfig(compose=True, temporal_replay=True))
    t1 = analyze_world(
        warm, "C3_train_a", WORLD_A, max_return=12
    )
    t2 = analyze_world(
        warm, "C3_train_b", WORLD_B, max_return=12
    )
    promoted = t2.get("promoted_pattern_atom")

    reuse = analyze_world(
        warm,
        "C3_reuse_c",
        WORLD_C,
        max_return=12,
        allow_pattern_search=False,
    )

    cold_zero = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=True)),
        "C3_cold_zero",
        WORLD_C,
        max_return=12,
        allow_pattern_search=False,
    )

    # Same channel count and spatial world, different temporal-standing pattern.
    different = analyze_world(
        warm,
        "C4_different_pattern",
        WORLD_DIFFERENT,
        max_return=12,
        allow_pattern_search=True,
    )

    ablated = warm.ablate_pattern_atom(9)
    after_ablation = analyze_world(
        warm,
        "C3_after_ablation",
        WORLD_C,
        max_return=12,
        allow_pattern_search=False,
    )

    evidence["results"]["C3_train_a"] = safe(t1)
    evidence["results"]["C3_train_b"] = safe(t2)
    evidence["results"]["C3_reuse_c"] = safe(reuse)
    evidence["results"]["C3_cold_zero"] = safe(cold_zero)
    evidence["results"]["C4_different_pattern"] = safe(different)
    evidence["results"]["C3_after_ablation"] = safe(after_ablation)

    # C5 unseen causal carrier.
    c5 = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=True)),
        "C5_path_world",
        WORLD_PATH,
        max_return=24,
    )
    evidence["results"]["C5_path_world"] = safe(c5)

    # C6 temporal horizon.
    c6 = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=True)),
        "C6_short_trace",
        WORLD_SHORT,
        max_return=12,
    )
    evidence["results"]["C6_short_trace"] = safe(c6)

    # C7 missing intervention.
    c7 = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=True)),
        "C7_missing_intervention",
        WORLD_MISSING_INTERVENTION,
        max_return=12,
        intervention_complete=False,
    )
    evidence["results"]["C7_missing_intervention"] = safe(c7)

    # C8 compose ablation.
    c8 = analyze_world(
        Kernel(BasisConfig(compose=False, temporal_replay=True)),
        "C8_no_compose",
        WORLD_A,
        max_return=12,
    )
    evidence["results"]["C8_no_compose"] = safe(c8)

    # C9 temporal replay ablation.
    c9 = analyze_world(
        Kernel(BasisConfig(compose=True, temporal_replay=False)),
        "C9_no_temporal_replay",
        WORLD_A,
        max_return=12,
    )
    evidence["results"]["C9_no_temporal_replay"] = safe(c9)

    G = evidence["gates"]

    sig1 = c1.get("signature", {})
    sig2 = c2.get("signature", {})
    sig5 = c5.get("signature", {})

    G["C1_exact_hidden_influence_and_return"] = (
        c1.get("status") == "VERIFIED"
        and c1.get("construction", {}).get("temporal", {}).get("return_displacement") == 6
        and sig1.get("channel_count") == 9
        and sig1.get("return_displacement") == 6
        and sig1.get("persistent_count") == 3
        and sig1.get("persistent_component_sizes") == [3]
        and sig1.get("other_component_sizes") == [3, 3]
        and sig1.get("persistent_to_other_incidence_count") == 6
        and sig1.get("full_component_sizes") == [9]
        and sorted(c1.get("construction", {}).get("persistent_channels", []))
            == sorted(WORLD_A["hidden_persistent_channels"])
    )

    G["C2_permutation_invariant_pattern_signature"] = (
        c2.get("status") == "VERIFIED"
        and sig1 == sig2
        and inferred_rows(c1) != inferred_rows(c2)
        and sorted(c1.get("construction", {}).get("persistent_channels", []))
            != sorted(c2.get("construction", {}).get("persistent_channels", []))
    )

    G["C3_second_copy_compiles_anonymous_pattern"] = (
        promoted is not None
        and promoted.get("channel_count") == 9
        and set(promoted.get("provenance", []))
            == {"C3_train_a", "C3_train_b"}
        and str(promoted.get("atom_id", "")).startswith("pat_")
    )

    G["C3_warm_third_copy_reuses_zero_pattern_search"] = (
        reuse.get("status") == "VERIFIED"
        and reuse.get("route") == "REUSE_PATTERN_ATOM"
        and reuse.get("pattern_search_count") == 0
        and reuse.get("signature") == sig1
    )

    G["C3_cold_zero_acquisition_stops"] = (
        cold_zero.get("status") == "UNKNOWN_PATTERN"
        and cold_zero.get("pattern_search_count") == 0
    )

    G["C3_ablation_restores_zero_acquisition_failure"] = (
        ablated
        and after_ablation.get("status") == "UNKNOWN_PATTERN"
        and after_ablation.get("pattern_search_count") == 0
    )

    G["C4_retained_pattern_verified_not_trusted"] = (
        different.get("status") == "VERIFIED"
        and different.get("route") == "SEARCH"
        and different.get("failed_reuse") is not None
        and different.get("failed_reuse", {}).get("reason")
            == "pattern_replay_failed"
        and different.get("signature", {}).get("persistent_count") == 0
        and different.get("signature") != sig1
    )

    G["C5_unseen_geometry_same_language"] = (
        c5.get("status") == "VERIFIED"
        and sig5.get("channel_count") == 9
        and sig5.get("return_displacement") == 18
        and sig5.get("persistent_count") == 1
        and sig5.get("persistent_component_sizes") == [1]
        and sig5.get("other_component_sizes") == [4, 4]
        and sig5.get("persistent_to_other_incidence_count") == 2
        and sorted(c5.get("construction", {}).get("persistent_channels", []))
            == sorted(WORLD_PATH["hidden_persistent_channels"])
    )

    G["C6_incomplete_temporal_horizon_is_unknown"] = (
        c6.get("status") == "UNKNOWN_TEMPORAL_REPLAY"
        and c6.get("construction", {}).get("temporal", {}).get("available_frames") == 10
    )

    G["C7_incomplete_spatial_observation_is_unknown"] = (
        c7.get("status") == "UNKNOWN_INFLUENCE"
        and c7.get("inference", {}).get("missing_source") == 5
    )

    G["C8_compose_ablation_blocks_relational_pattern"] = (
        c8.get("status") == "UNKNOWN_COMPOSITION_UNAVAILABLE"
        and c8.get("inference", {}).get("status") == "VERIFIED"
        and c8.get("construction", {}).get("persistent_channels") is not None
    )

    G["C9_temporal_replay_ablation_blocks_pattern"] = (
        c9.get("status") == "UNKNOWN_TEMPORAL_REPLAY"
        and c9.get("inference", {}).get("status") == "VERIFIED"
        and c9.get("construction", {}).get("temporal", {}).get("reason")
            == "temporal_replay_unavailable"
    )

    G["causal_pattern_compilation"] = (
        G["C3_warm_third_copy_reuses_zero_pattern_search"]
        and G["C3_cold_zero_acquisition_stops"]
        and G["C3_ablation_restores_zero_acquisition_failure"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_FINITE_STANDING_PATTERN_GENESIS_WITHOUT_COORDINATES_OR_SPECTRAL_PRIMITIVES"
        if evidence["full_pass"]
        else "SIMULATED_CYMATICS_V11_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
