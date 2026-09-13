from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

from kernel import Kernel
from challenge_pack import (
    CONSTANT,
    NEIGHBOR,
    NEIGHBOR_RELABELLED,
    AMBIGUOUS,
    FRAME_FAMILY,
    CANONICAL_ONE,
    LOCAL_TWO,
    LOCAL_THREE,
    INCOMPLETE,
    HIDDEN_NEIGHBOR_RELATION,
    HIDDEN_AMBIGUOUS_RELATION,
    EXPECTED_GROUP_12,
    EXPECTED_GROUP_6,
    EXPECTED_GROUP_2,
    EXPECTED_GROUP_1,
)

SCIENTIFIC_FREEZE_COMMIT = "cd45290121ceb0c2d70c22081f7ba899da5c7840"

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def symmetry(result: dict) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(i) for i in p) for p in result.get("symmetry", []))

def relation_frontier(result: dict) -> tuple[tuple[tuple[int, int], ...], ...]:
    rel = result.get("relation", {})
    return tuple(
        tuple(tuple(int(z) for z in edge) for edge in candidate)
        for candidate in rel.get("frontier", [])
    )

def exact_frontier_automorphisms(kernel: Kernel, result: dict) -> bool:
    group = set(symmetry(result))
    n = int(result.get("site_count", 0))
    frontier = relation_frontier(result)
    if result.get("relation", {}).get("status") != "VERIFIED":
        return False
    return all(
        set(kernel.relation_automorphisms(n, relation)) == group
        for relation in frontier
    )

def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    observed = {
        name: git_blob_sha(HERE / name)
        for name in freeze["scientific_core_paths"]
    }
    freeze_ok = observed == freeze["git_blob_sha"]

    kernel = Kernel()

    constant = kernel.synthesize(CONSTANT)
    neighbor = kernel.synthesize(NEIGHBOR)
    neighbor_rel = kernel.synthesize(NEIGHBOR_RELABELLED)
    ambiguous = kernel.synthesize(AMBIGUOUS)

    group_only = {
        name: kernel.synthesize(world, relation_enabled=False)
        for name, world in FRAME_FAMILY.items()
    }

    canonical_one = kernel.synthesize(CANONICAL_ONE, relation_enabled=False)
    local_two = kernel.synthesize(LOCAL_TWO, relation_enabled=False)
    local_three = kernel.synthesize(LOCAL_THREE, relation_enabled=False)

    incomplete = kernel.synthesize(INCOMPLETE)
    no_verifier = kernel.synthesize(NEIGHBOR, verification_enabled=False)

    hidden_neighbor = tuple(sorted(HIDDEN_NEIGHBOR_RELATION))
    hidden_ambiguous = tuple(sorted(HIDDEN_AMBIGUOUS_RELATION))

    expected_groups = {
        "g12": EXPECTED_GROUP_12,
        "g6": EXPECTED_GROUP_6,
        "g2": EXPECTED_GROUP_2,
        "g1": EXPECTED_GROUP_1,
    }

    kernel_text = (HERE / "kernel.py").read_text().lower()
    forbidden = (
        "cycle",
        "path",
        "rotation",
        "reflection",
        "unframed",
        "oriented",
        "anchored",
        "framed",
        "event_window",
        "canonical representative",
    )

    gates = {}
    gates["R1_frozen_scientific_core_byte_identical"] = freeze_ok

    gates["R2_constant_keeps_full_permutation_symmetry_and_empty_relation"] = (
        constant.get("status") == "VERIFIED"
        and int(constant.get("symmetry_size", -1)) == 720
        and constant.get("relation", {}).get("minimum_edge_count") == 0
        and relation_frontier(constant) == ((),)
    )

    gates["R3_hidden_neighborhood_earns_12_element_symmetry"] = (
        neighbor.get("status") == "VERIFIED"
        and symmetry(neighbor) == EXPECTED_GROUP_12
        and int(neighbor.get("symmetry_size", -1)) == 12
    )

    gates["R4_unique_sparsest_exact_relation_recovers_hidden_neighborhood"] = (
        neighbor.get("relation", {}).get("status") == "VERIFIED"
        and neighbor.get("relation", {}).get("minimum_edge_count") == 6
        and neighbor.get("relation", {}).get("frontier_count") == 1
        and relation_frontier(neighbor) == (hidden_neighbor,)
    )

    gates["R5_opaque_consequence_relabelling_preserves_symmetry_and_relation_frontier"] = (
        symmetry(neighbor_rel) == symmetry(neighbor)
        and relation_frontier(neighbor_rel) == relation_frontier(neighbor)
    )

    gates["R6_second_hidden_relation_earns_two_element_symmetry"] = (
        ambiguous.get("status") == "VERIFIED"
        and int(ambiguous.get("symmetry_size", -1)) == 2
    )

    gates["R7_noncanonical_symmetry_preserves_multiple_sparsest_relations"] = (
        ambiguous.get("relation", {}).get("status") == "VERIFIED"
        and ambiguous.get("relation", {}).get("minimum_edge_count") == 5
        and int(ambiguous.get("relation", {}).get("frontier_count", 0)) == 24
        and hidden_ambiguous in relation_frontier(ambiguous)
    )

    gates["R8_no_single_relation_is_silently_selected_on_plural_frontier"] = (
        int(ambiguous.get("relation", {}).get("frontier_count", 0)) > 1
        and "selected_relation" not in ambiguous
        and "selected_relation" not in ambiguous.get("relation", {})
    )

    gates["R9_frame_lattice_not_supplied_four_consequences_earn_12_6_2_1_groups"] = all(
        group_only[name].get("status") == "VERIFIED"
        and symmetry(group_only[name]) == expected_groups[name]
        for name in ("g12", "g6", "g2", "g1")
    )

    gates["R10_largest_earned_frame_family_group_matches_learned_neighborhood_symmetry"] = (
        symmetry(group_only["g12"]) == symmetry(neighbor)
    )

    gates["R11_v35_style_one_symbol_canonical_consequence_has_full_raw_support"] = (
        canonical_one.get("raw_support", {}).get("minimum_support_size") == 6
    )

    gates["R12_genuinely_local_two_site_consequence_has_support_two"] = (
        local_two.get("raw_support", {}).get("minimum_support_size") == 2
    )

    gates["R13_local_support_expands_two_to_three_without_global_canonicalization"] = (
        local_two.get("raw_support", {}).get("minimum_support_size") == 2
        and local_three.get("raw_support", {}).get("minimum_support_size") == 3
    )

    gates["R14_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
    )

    gates["R15_verifier_ablation_authorizes_no_symmetry_or_relation"] = (
        no_verifier.get("status") == "UNKNOWN_NO_VERIFIER"
        and no_verifier.get("symmetry_size") == 0
        and no_verifier.get("relation_frontier") == []
    )

    gates["R16_frozen_kernel_has_no_hidden_topology_or_named_frame_states"] = all(
        re.search(r"\b" + re.escape(token) + r"\b", kernel_text) is None
        for token in forbidden
    )

    gates["R17_every_retained_relation_has_exactly_the_earned_automorphism_group"] = all(
        exact_frontier_automorphisms(kernel, result)
        for result in (constant, neighbor, neighbor_rel, ambiguous)
    )

    gates["R18_all_edge_minimal_exact_relations_are_preserved"] = (
        constant.get("relation", {}).get("frontier_count") == 1
        and neighbor.get("relation", {}).get("frontier_count") == 1
        and ambiguous.get("relation", {}).get("frontier_count") == 24
    )

    evidence = {
        "experiment": "consequence_earned_relation_v37",
        "scientific_freeze_commit": SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest": freeze,
        "observed_core_git_blob_sha": observed,
        "constant": constant,
        "neighbor": neighbor,
        "neighbor_relabelled": neighbor_rel,
        "ambiguous": ambiguous,
        "group_only_family": group_only,
        "canonical_one": canonical_one,
        "local_two": local_two,
        "local_three": local_three,
        "incomplete": incomplete,
        "no_verifier": no_verifier,
        "gates": gates,
    }
    evidence["full_pass"] = all(gates.values())
    evidence["verdict"] = (
        "VERIFIED_RELATION_AND_UNSUPPLIED_SYMMETRY_LATTICE_GENESIS_FROM_CONSEQUENCE"
        if evidence["full_pass"]
        else "CONSEQUENCE_EARNED_RELATION_V37_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
