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
    PATH7_A_ROWS, PATH7_B_ROWS, PATH7_C_ROWS,
    RING8_ROWS, BLOCKS7_ROWS,
    PATH7_A_OBS, PATH7_B_OBS, PATH7_C_OBS,
    RING8_OBS, BLOCKS7_OBS,
    PATH7_INCOMPLETE_OBS,
)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def relation_rows(result):
    inf = result.get("inference", {})
    rel = inf.get("relation")
    return tuple(rel.rows) if rel is not None else None


def main() -> int:
    evidence = {
        "experiment": "spatial_structure_without_coordinates_v10",
        "scientific_freeze_commit": "f470fcd693f710cc838e3aa3330bc5f4bf10eabd",
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

    # Independent worlds.
    s1 = Kernel(BasisConfig(compose=True)).analyze(
        "S1_path_a", 7, PATH7_A_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )
    s2 = Kernel(BasisConfig(compose=True)).analyze(
        "S2_ring", 8, RING8_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )
    s3 = Kernel(BasisConfig(compose=True)).analyze(
        "S3_blocks", 7, BLOCKS7_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )
    s4 = Kernel(BasisConfig(compose=True)).analyze(
        "S4_incomplete", 7, PATH7_INCOMPLETE_OBS,
        observation_search_complete=False,
        allow_structure_search=True,
    )
    s5 = Kernel(BasisConfig(compose=False)).analyze(
        "S5_no_compose", 7, PATH7_A_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )

    evidence["results"]["S1_path_a"] = s1
    evidence["results"]["S2_ring"] = s2
    evidence["results"]["S3_blocks"] = s3
    evidence["results"]["S4_incomplete"] = s4
    evidence["results"]["S5_no_compose"] = s5

    # S6/S7 trajectory over three relabelled path worlds.
    k = Kernel(BasisConfig(compose=True))
    train1 = k.analyze(
        "S6_path_train1", 7, PATH7_A_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )
    train2 = k.analyze(
        "S6_path_train2", 7, PATH7_B_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )
    promoted = train2.get("promoted_structure_atom")

    reuse = k.analyze(
        "S7_path_reuse", 7, PATH7_C_OBS,
        observation_search_complete=True,
        allow_structure_search=False,
    )

    cold_zero = Kernel(BasisConfig(compose=True)).analyze(
        "S7_cold_zero", 7, PATH7_C_OBS,
        observation_search_complete=True,
        allow_structure_search=False,
    )

    wrong_same_n = k.analyze(
        "S7_wrong_same_n", 7, BLOCKS7_OBS,
        observation_search_complete=True,
        allow_structure_search=True,
    )

    ablated = k.ablate_structure_atom(7)
    after_ablation = k.analyze(
        "S7_after_ablation", 7, PATH7_C_OBS,
        observation_search_complete=True,
        allow_structure_search=False,
    )

    evidence["results"]["S6_path_train1"] = train1
    evidence["results"]["S6_path_train2"] = train2
    evidence["results"]["S7_path_reuse"] = reuse
    evidence["results"]["S7_cold_zero"] = cold_zero
    evidence["results"]["S7_wrong_same_n"] = wrong_same_n
    evidence["results"]["S7_after_ablation"] = after_ablation

    G = evidence["gates"]

    G["S1_hidden_path_relation_recovered"] = (
        s1.get("status") == "VERIFIED"
        and relation_rows(s1) == PATH7_A_ROWS
        and s1.get("signature", {}).get("component_sizes") == [7]
        and s1.get("signature", {}).get("edge_count") == 12
        and s1.get("signature", {}).get("degree_pairs")
            == [[1,1],[1,1],[2,2],[2,2],[2,2],[2,2],[2,2]]
    )

    G["S2_hidden_ring_relation_recovered"] = (
        s2.get("status") == "VERIFIED"
        and relation_rows(s2) == RING8_ROWS
        and s2.get("signature", {}).get("component_sizes") == [8]
        and s2.get("signature", {}).get("edge_count") == 16
        and s2.get("signature", {}).get("degree_pairs")
            == [[2,2]] * 8
    )

    component_classes = sorted(
        [sorted(c) for c in s3.get("components", [])],
        key=lambda c: (len(c), c),
    )
    G["S3_disconnected_blocks_reified"] = (
        s3.get("status") == "VERIFIED"
        and relation_rows(s3) == BLOCKS7_ROWS
        and s3.get("signature", {}).get("component_sizes") == [3,4]
        and s3.get("component_carrier", {}).get("size") == 2
        and [len(c) for c in component_classes] == [3,4]
    )

    G["S4_incomplete_observation_is_unknown"] = (
        s4.get("status") == "UNKNOWN_INFLUENCE"
        and s4.get("inference", {}).get("missing_source") == 4
    )

    G["S5_compose_ablation_preserves_local_but_blocks_structure"] = (
        s5.get("status") == "UNKNOWN_COMPOSITION_UNAVAILABLE"
        and s5.get("inference", {}).get("status") == "VERIFIED"
        and relation_rows(s5) == PATH7_A_ROWS
    )

    G["S6_permutation_invariant_signature"] = (
        train1.get("status") == "VERIFIED"
        and train2.get("status") == "VERIFIED"
        and train1.get("signature") == train2.get("signature")
        and relation_rows(train1) != relation_rows(train2)
    )

    G["S7_second_copy_compiles_anonymous_structure_atom"] = (
        promoted is not None
        and promoted.get("channel_count") == 7
        and set(promoted.get("provenance", []))
            == {"S6_path_train1", "S6_path_train2"}
    )

    G["S7_warm_third_copy_reuses_zero_signature_search"] = (
        reuse.get("status") == "VERIFIED"
        and reuse.get("route") == "REUSE_STRUCTURE_ATOM"
        and reuse.get("signature_search_count") == 0
        and reuse.get("signature") == train1.get("signature")
    )

    G["S7_cold_zero_acquisition_stops"] = (
        cold_zero.get("status") == "UNKNOWN_STRUCTURE"
        and cold_zero.get("signature_search_count") == 0
    )

    G["S7_wrong_same_size_atom_is_verified_not_trusted"] = (
        wrong_same_n.get("status") == "VERIFIED"
        and wrong_same_n.get("route") == "SEARCH"
        and wrong_same_n.get("failed_reuse") is not None
        and wrong_same_n.get("failed_reuse", {}).get("reason")
            == "signature_replay_failed"
        and wrong_same_n.get("signature", {}).get("component_sizes") == [3,4]
    )

    G["S7_ablation_restores_zero_acquisition_failure"] = (
        ablated
        and after_ablation.get("status") == "UNKNOWN_STRUCTURE"
        and after_ablation.get("signature_search_count") == 0
    )

    G["causal_structural_compilation"] = (
        G["S7_warm_third_copy_reuses_zero_signature_search"]
        and G["S7_cold_zero_acquisition_stops"]
        and G["S7_ablation_restores_zero_acquisition_failure"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_COORDINATE_FREE_CAUSAL_SPATIAL_STRUCTURE_AND_COMPONENT_REIFICATION"
        if evidence["full_pass"]
        else "SPATIAL_STRUCTURE_WITHOUT_COORDINATES_V10_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
