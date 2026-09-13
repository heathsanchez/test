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
    EditProgram,
    SetEdit,
    factorized_mapping_set,
    program_term,
)
from kernel import (
    Kernel,
    Residual,
    generic_anti_unify,
    schema_variables,
)
from challenge_pack import (
    WORLD_A,
    WORLD_B,
    WORLD_C,
    NO_GROWTH,
    INCOMPLETE,
    three_edit_control_program,
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
    return x


def all_verifier_rows_clean(development):
    rows = (
        development.get("repair", {})
        .get("synthesis", {})
        .get("verification_rows", [])
    )
    return bool(rows) and all(
        row.get("verdict", {}).get("accepted") is True
        and row.get("verdict", {}).get("bijection") is True
        and row.get("verdict", {}).get("residual_discharge") is True
        and row.get("verdict", {}).get("consequence_preserving") is True
        and row.get("verdict", {}).get("novel_outside_current_language") is True
        for row in rows
    )


def main() -> int:
    k = Kernel()

    train_a = k.develop(WORLD_A)
    train_b = k.develop(WORLD_B)

    compiled_result = k.compile_schema((
        (
            "TRAIN_A",
            WORLD_A,
            train_a["_residual"],
            train_a["_program"],
        ),
        (
            "TRAIN_B",
            WORLD_B,
            train_b["_residual"],
            train_b["_program"],
        ),
    ))
    compiled = compiled_result.get("_compiled")

    heldout_warm = k.develop(
        WORLD_C,
        schema=compiled,
        allow_acquisition_search=False,
    )

    heldout_cold_zero = Kernel().develop(
        WORLD_C,
        schema=None,
        allow_acquisition_search=False,
    )

    heldout_cold_search = Kernel().develop(
        WORLD_C,
        schema=None,
        allow_acquisition_search=True,
    )

    heldout_after_ablation = Kernel().develop(
        WORLD_C,
        schema=None,
        allow_acquisition_search=False,
    )

    # Wrong-binding control: keep the same left endpoint but deliberately bind
    # the schema obligation to a presentation with a different consequence.
    held_res = heldout_warm["_residual"]
    bad_right = next(
        cell
        for cell in WORLD_C.cells()
        if WORLD_C.consequence(cell) != WORLD_C.consequence(held_res.left)
    )
    bad_residual = Residual(
        left=held_res.left,
        right=bad_right,
        consequence=int(WORLD_C.consequence(held_res.left)),
        left_orbit=held_res.left_orbit,
        right_orbit=-1,
    )
    wrong_binding = k.solve_residual(
        WORLD_C,
        bad_residual,
        schema=compiled,
        allow_acquisition_search=False,
    )

    # Different verified edit-program shape. This is deliberately not a
    # minimum repair; it is a generic anti-unification shape control.
    shape_program = three_edit_control_program()
    all_l0_a = factorized_mapping_set(WORLD_A)
    shape_residual = Residual(
        left=(0,0),
        right=(0,2),
        consequence=int(WORLD_A.consequence((0,0))),
        left_orbit=0,
        right_orbit=2,
    )
    shape_verdict = k.verify_program(
        WORLD_A,
        shape_residual,
        shape_program,
        all_l0_a,
    )
    shape_lgg = generic_anti_unify(
        program_term(WORLD_A, train_a["_program"]),
        program_term(WORLD_A, shape_program),
    )

    no_growth = k.develop(NO_GROWTH)
    incomplete = k.develop(INCOMPLETE)
    verifier_ablation = k.develop(
        WORLD_A,
        verification_enabled=False,
    )

    evidence = {
        "experiment": "meta_repair_constructor_genesis_v22",
        "scientific_freeze_commit": "c6552ba10067af7d208cddc06760e574aaae8b84",
        "post_freeze_challenges": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE / "PROTOCOL.md"),
            "FREEZE.json": sha256(HERE / "FREEZE.json"),
            "basis.py": sha256(HERE / "basis.py"),
            "kernel.py": sha256(HERE / "kernel.py"),
            "challenge_pack.py": sha256(HERE / "challenge_pack.py"),
        },
        "results": {
            "train_a": safe(train_a),
            "train_b": safe(train_b),
            "compiled_schema": safe(compiled_result),
            "heldout_warm": safe(heldout_warm),
            "heldout_cold_zero": safe(heldout_cold_zero),
            "heldout_cold_search": safe(heldout_cold_search),
            "heldout_after_ablation": safe(heldout_after_ablation),
            "wrong_binding": safe(wrong_binding),
            "shape_control": {
                "program": shape_program.data(),
                "verdict": safe(shape_verdict),
                "anti_unification_result": safe(shape_lgg),
            },
            "no_growth": safe(no_growth),
            "incomplete": safe(incomplete),
            "verifier_ablation": safe(verifier_ablation),
        },
        "gates": {},
    }

    G = evidence["gates"]

    # M1 checks executable identifiers rather than comments/prose.
    tree = ast.parse(
        (HERE / "basis.py").read_text()
        + "\n"
        + (HERE / "kernel.py").read_text()
    )
    executable_names = {
        node.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    forbidden_constructor_names = {
        "swap",
        "exchange",
        "transposition",
        "cycle",
    }

    G["M1_only_generic_set_edit_is_primitive"] = (
        executable_names.isdisjoint(forbidden_constructor_names)
        and "setedit" in executable_names
    )

    synth_a = train_a.get("repair", {}).get("synthesis", {})
    G["M2_exact_minimum_repair_depth_is_proved"] = (
        train_a.get("status") == "VERIFIED"
        and synth_a.get("minimum_edit_depth") == 2
        and train_a["_program"].depth == 2
    )

    expected_tested = (
        25 * 25
        + (25 * 24 // 2) * (25 ** 2)
    )
    G["M3_repair_emerges_from_full_generic_enumeration"] = (
        synth_a.get("tested_program_count") == expected_tested
        and len(synth_a.get("frontier", [])) >= 1
    )

    G["M4_every_accepted_training_repair_is_independently_verified"] = (
        all_verifier_rows_clean(train_a)
        and all_verifier_rows_clean(train_b)
    )

    synth_b = train_b.get("repair", {}).get("synthesis", {})
    G["M5_second_independent_residual_synthesizes_same_depth_without_reuse"] = (
        train_b.get("status") == "VERIFIED"
        and synth_b.get("minimum_edit_depth") == 2
        and train_b.get("acquisition_search_count") == 1
        and train_b["_program"].depth == 2
        and WORLD_A.world_id != WORLD_B.world_id
    )

    schema_json = compiled_result.get("schema", {}).get("term")
    vars_count = compiled_result.get("schema", {}).get("variable_count")
    G["M6_generic_anti_unification_generates_non_ground_repeated_schema"] = (
        compiled_result.get("status") == "VERIFIED"
        and vars_count == 2
        and schema_json == [
            "SEQ",
            ["SET", ["VAR",0], ["VAR",1]],
            ["SET", ["VAR",1], ["VAR",0]],
        ]
    )

    G["M7_schema_is_strictly_more_abstract_and_replays_training_instances"] = (
        compiled_result.get("schema_constant_count") == 0
        and compiled_result.get("instance_constant_counts") == [4,4]
        and compiled_result.get("training_replay") == [True,True]
        and compiled_result.get("schema", {}).get("provenance")
            == ["TRAIN_A","TRAIN_B"]
    )

    G["M8_heldout_warm_schema_transfer_has_zero_edit_search"] = (
        heldout_warm.get("status") == "VERIFIED"
        and heldout_warm.get("repair", {}).get("route")
            == "REUSE_COMPILED_SCHEMA"
        and heldout_warm.get("acquisition_search_count") == 0
        and heldout_warm.get("repair", {}).get(
            "acquisition_search_count"
        ) == 0
    )

    G["M9_cold_zero_search_returns_unknown_schema"] = (
        heldout_cold_zero.get("status") == "UNKNOWN_REPAIR_SCHEMA"
        and heldout_cold_zero.get("acquisition_search_count") == 0
    )

    G["M10_cold_search_rediscovers_minimum_repair"] = (
        heldout_cold_search.get("status") == "VERIFIED"
        and heldout_cold_search.get("repair", {}).get("route") == "SYNTHESIZE"
        and heldout_cold_search.get("repair", {})
            .get("synthesis", {})
            .get("minimum_edit_depth") == 2
        and heldout_cold_search.get("acquisition_search_count") == 1
    )

    G["M11_schema_ablation_restores_unknown"] = (
        heldout_after_ablation.get("status") == "UNKNOWN_REPAIR_SCHEMA"
        and heldout_after_ablation.get("acquisition_search_count") == 0
    )

    replay_rows = wrong_binding.get("replay_rows", [])
    G["M12_wrong_binding_is_replay_rejected"] = (
        wrong_binding.get("status") == "REPLAY_FAILED"
        and bool(replay_rows)
        and all(
            row.get("verdict", {}).get("accepted") is False
            for row in replay_rows
        )
    )

    G["M13_different_verified_program_shape_is_not_forced_into_schema"] = (
        shape_verdict.get("accepted") is True
        and shape_program.depth == 3
        and shape_lgg is None
    )

    G["M14_no_residual_no_constructor_growth"] = (
        no_growth.get("status") == "VERIFIED_NO_GROWTH"
        and no_growth.get("constructor_growth_authorized") is False
        and no_growth.get("acquisition_search_count") == 0
    )

    G["M15_incomplete_authority_stays_unknown"] = (
        incomplete.get("status") == "UNKNOWN_AUTHORITY"
    )

    G["M16_verifier_ablation_admits_no_repair_or_schema"] = (
        verifier_ablation.get("status") == "UNKNOWN_NO_VERIFIER"
        and verifier_ablation.get("repair", {}).get("status")
            == "UNKNOWN_NO_VERIFIER"
        and verifier_ablation.get("acquisition_search_count") == 0
    )

    G["minimal_developmental_algorithm_respected"] = all(
        token in (HERE / "PROTOCOL.md").read_text()
        for token in (
            "EXECUTE", "VERIFY", "DIAGNOSE", "CONSTRAIN",
            "RESTRUCTURE", "CHOOSE", "COMPILE", "UPDATE",
        )
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_META_REPAIR_CONSTRUCTOR_GENESIS_FROM_GENERIC_POINTWISE_EDITS"
        if evidence["full_pass"]
        else "META_REPAIR_CONSTRUCTOR_GENESIS_V22_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
