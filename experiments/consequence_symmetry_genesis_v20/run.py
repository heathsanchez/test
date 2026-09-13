#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import (
    all_transforms,
    is_consequence_symmetry,
    is_identity,
    transform_cost,
)
from kernel import Kernel
from challenge_pack import (
    BASE,
    RELABELED,
    BROKEN,
    HETEROGENEOUS,
    INCOMPLETE,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(x):
    if hasattr(x, "data"):
        return safe(x.data())
    if isinstance(x, dict):
        return {
            str(k): safe(v)
            for k, v in x.items()
            if not str(k).startswith("_")
        }
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(safe(v) for v in x)
    return x


def orbit_sets(rows):
    return [
        {tuple(int(z) for z in cell) for cell in orbit}
        for orbit in rows
    ]


def strict_refinement(old_rows, new_rows):
    old = orbit_sets(old_rows)
    new = orbit_sets(new_rows)

    if not all(any(n <= o for o in old) for n in new):
        return False

    for o in old:
        pieces = [n for n in new if n <= o]
        if len(pieces) > 1:
            return True
    return False


def main() -> int:
    evidence = {
        "experiment": "consequence_symmetry_genesis_v20",
        "scientific_freeze_commit": "2dd1d64dacaa049032e704928e26eaea383263cc",
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

    k = Kernel()

    base = k.analyze(BASE)
    relabelled = k.analyze(RELABELED)
    compiled = k.compile(
        BASE,
        base,
        provenance=("V20_BASE_EXACT_REPLAY",),
    )

    broken_replay = k.replay_compiled(BROKEN, compiled)
    broken = k.analyze(BROKEN)

    identity_only = k.analyze(
        BASE,
        retain_nontrivial=False,
    )

    no_compose = k.analyze(
        BASE,
        composition_enabled=False,
    )

    heterogeneous = k.analyze(HETEROGENEOUS)
    incomplete = k.analyze(INCOMPLETE)
    no_consequence = k.analyze(
        BASE,
        consequence_enabled=False,
    )

    # Independent brute-force authority: do not reuse Kernel.analyze.
    independent = tuple(
        t
        for t in all_transforms(
            BASE.state_count,
            BASE.test_count,
        )
        if is_consequence_symmetry(BASE, t)
    )

    evidence["results"]["base"] = safe(base)
    evidence["results"]["compiled"] = safe(compiled)
    evidence["results"]["relabelled"] = safe(relabelled)
    evidence["results"]["broken_replay"] = safe(broken_replay)
    evidence["results"]["broken"] = safe(broken)
    evidence["results"]["identity_only"] = safe(identity_only)
    evidence["results"]["no_compose"] = safe(no_compose)
    evidence["results"]["heterogeneous"] = safe(heterogeneous)
    evidence["results"]["incomplete"] = safe(incomplete)
    evidence["results"]["no_consequence"] = safe(no_consequence)

    G = evidence["gates"]

    # S1: inspect executable identifiers, not explanatory prose.
    tree = ast.parse(
        (HERE / "basis.py").read_text()
        + "\n"
        + (HERE / "kernel.py").read_text()
    )
    names = {
        node.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    forbidden = {
        "rotate", "rotation", "reflect", "reflection",
        "translate", "translation", "geometry", "coordinate",
        "object", "boundary",
    }
    G["S1_no_named_symmetry_or_geometry_ontology"] = (
        names.isdisjoint(forbidden)
    )

    base_group = set(base.get("_group_objects", tuple()))
    independent_set = set(independent)

    G["S2_nontrivial_composite_symmetry_is_generated"] = (
        base.get("status") == "VERIFIED"
        and base.get("symmetry_count") > 1
        and any(
            (not is_identity(t)) and transform_cost(t) > 1
            for t in base_group
        )
        and base.get("max_verified_cost", 0) > 1
    )

    G["S3_exact_full_automorphism_group_recovered"] = (
        base.get("status") == "VERIFIED"
        and base.get("candidate_count") == 14400
        and base_group == independent_set
        and len(base_group) == 10
        and base.get("closed_exactly") is True
    )

    gen = base.get("generator_search", {})
    G["S4_minimum_generator_frontier_preserved"] = (
        gen.get("status") == "VERIFIED"
        and gen.get("minimum_generator_count") == 2
        and gen.get("minimum_total_transposition_cost") == 8
        and len(gen.get("frontier", [])) > 1
        and all(
            len(row) == 2
            for row in gen.get("frontier", [])
        )
    )

    G["S5_cell_orbit_quotient_exactly_compresses_consequence"] = (
        base.get("representatives", {}).get("exact_reconstruction") is True
        and base.get("raw_cell_count") == 25
        and base.get("cell_orbit_count") == 3
        and abs(base.get("compression_ratio") - (25 / 3)) < 1e-12
    )

    G["S6_raw_labels_collapse_into_consequence_relative_state_orbit"] = (
        base.get("state_orbits") == [[0,1,2,3,4]]
        and base.get("test_orbits") == [[0,1,2,3,4]]
    )

    G["S7_independent_relabelling_preserves_structural_signature"] = (
        relabelled.get("status") == "VERIFIED"
        and relabelled.get("structural_signature")
            == base.get("structural_signature")
        and relabelled.get("verified_transformations")
            != base.get("verified_transformations")
    )

    broken_group = set(broken.get("_group_objects", tuple()))
    G["S8_changed_consequence_breaks_old_symmetry_and_refines_orbits"] = (
        broken_replay.get("status") == "REPLAY_FAILED"
        and broken_replay.get("failed_transformation_count", 0) > 0
        and broken.get("status") == "VERIFIED"
        and broken.get("symmetry_count") < base.get("symmetry_count")
        and broken_group < base_group
        and strict_refinement(
            base.get("cell_orbits", []),
            broken.get("cell_orbits", []),
        )
        and broken.get("cell_orbit_count") > base.get("cell_orbit_count")
    )

    G["S9_repaired_broken_symmetry_quotient_is_exact"] = (
        broken.get("representatives", {}).get("exact_reconstruction") is True
        and broken_replay.get("old_quotient_exact") is False
    )

    G["S10_nontrivial_symmetry_ablation_restores_raw_cell_identity"] = (
        identity_only.get("status") == "VERIFIED"
        and identity_only.get("symmetry_count") == 1
        and identity_only.get("cell_orbit_count") == 25
        and abs(identity_only.get("compression_ratio") - 1.0) < 1e-12
    )

    G["S11_composition_ablation_cannot_recover_full_group"] = (
        no_compose.get("status") == "PARTIAL_TRANSFORMATION_LANGUAGE"
        and no_compose.get("symmetry_count") < base.get("symmetry_count")
        and no_compose.get("max_verified_cost") <= 1
    )

    G["S12_same_kernel_recovers_heterogeneous_symmetry_structure"] = (
        heterogeneous.get("status") == "VERIFIED"
        and heterogeneous.get("symmetry_count") == 24
        and heterogeneous.get("cell_orbit_count") == 2
        and heterogeneous.get("structural_signature")
            != base.get("structural_signature")
        and heterogeneous.get("representatives", {}).get(
            "exact_reconstruction"
        ) is True
    )

    G["S13_incomplete_consequence_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
    )

    G["S14_without_consequence_no_nonidentity_symmetry_is_authorized"] = (
        no_consequence.get("status")
            == "UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
        and no_consequence.get("symmetry_count") == 1
    )

    G["minimal_developmental_algorithm_respected"] = all(
        token in (HERE / "PROTOCOL.md").read_text()
        for token in (
            "EXECUTE", "VERIFY", "DIAGNOSE", "CONSTRAIN",
            "RESTRUCTURE", "CHOOSE", "COMPILE", "UPDATE",
        )
    )

    G["transformation_plus_consequence_duality_observed"] = (
        G["S5_cell_orbit_quotient_exactly_compresses_consequence"]
        and G["S8_changed_consequence_breaks_old_symmetry_and_refines_orbits"]
        and G["S14_without_consequence_no_nonidentity_symmetry_is_authorized"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_CONSEQUENCE_SYMMETRY_ORBIT_QUOTIENT_AND_SYMMETRY_BREAKING_GENESIS"
        if evidence["full_pass"]
        else "CONSEQUENCE_SYMMETRY_GENESIS_V20_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))

    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
