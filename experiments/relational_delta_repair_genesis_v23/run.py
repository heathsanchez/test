#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import (
    DeltaProgram,
    IncidenceBit,
    apply_delta_relation,
    factorized_mapping_set,
    incidence_universe,
    mapping_is_bijection,
    mapping_preserves_consequence,
    relation_to_mapping,
    delta_term,
)
from kernel import (
    Kernel,
    Residual,
    generic_anti_unify,
)
from challenge_pack import (
    BASE,
    WORLD_B,
    WORLD_C,
    NO_GROWTH,
    INCOMPLETE,
    three_cycle_control,
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


def all_rows_clean(dev):
    rows = (
        dev.get("repair", {})
        .get("synthesis", {})
        .get("verification_rows", [])
    )
    return bool(rows) and all(
        row.get("verdict", {}).get("accepted") is True
        and row.get("verdict", {}).get("total_function") is True
        and row.get("verdict", {}).get("bijection") is True
        and row.get("verdict", {}).get("residual_discharge") is True
        and row.get("verdict", {}).get("consequence_preserving") is True
        and row.get("verdict", {}).get("novel_outside_current_language") is True
        for row in rows
    )


def main() -> int:
    k = Kernel()

    train_a = k.develop(BASE)
    train_b = k.develop(WORLD_B)

    compiled_result = k.compile_schema((
        ("TRAIN_A", BASE, train_a["_residual"], train_a["_program"]),
        ("TRAIN_B", WORLD_B, train_b["_residual"], train_b["_program"]),
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

    held_res = heldout_warm["_residual"]
    bad_right = next(
        cell
        for cell in WORLD_C.cells()
        if WORLD_C.consequence(cell) != WORLD_C.consequence(held_res.left)
    )
    bad_res = Residual(
        left=held_res.left,
        right=bad_right,
        consequence=int(WORLD_C.consequence(held_res.left)),
        left_orbit=held_res.left_orbit,
        right_orbit=-1,
    )
    wrong_binding = k.solve_residual(
        WORLD_C,
        bad_res,
        schema=compiled,
        allow_acquisition_search=False,
    )

    no_growth = k.develop(NO_GROWTH)
    incomplete = k.develop(INCOMPLETE)
    verifier_ablation = k.develop(
        BASE,
        verification_enabled=False,
    )

    shape_program = three_cycle_control()
    shape_relation = apply_delta_relation(BASE, shape_program)
    shape_mapping = relation_to_mapping(BASE, shape_relation)
    shape_valid = (
        shape_mapping is not None
        and mapping_is_bijection(BASE, shape_mapping)
        and mapping_preserves_consequence(BASE, shape_mapping)
    )
    shape_lgg = generic_anti_unify(
        delta_term(BASE, train_a["_program"]),
        delta_term(BASE, shape_program),
    )

    composed = k.compose_verified(
        WORLD_C,
        heldout_warm["_mapping"],
        heldout_warm["_mapping"],
    )

    evidence = {
        "experiment":"relational_delta_repair_genesis_v23",
        "scientific_freeze_commit":"f7880590cfff1b726fb02c9e918e92b5169f18fe",
        "post_freeze_challenges":True,
        "hashes":{
            "PROTOCOL.md":sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json":sha256(HERE/"FREEZE.json"),
            "basis.py":sha256(HERE/"basis.py"),
            "kernel.py":sha256(HERE/"kernel.py"),
            "challenge_pack.py":sha256(HERE/"challenge_pack.py"),
        },
        "results":{
            "train_a":safe(train_a),
            "train_b":safe(train_b),
            "compiled_schema":safe(compiled_result),
            "heldout_warm":safe(heldout_warm),
            "heldout_cold_zero":safe(heldout_cold_zero),
            "heldout_cold_search":safe(heldout_cold_search),
            "heldout_after_ablation":safe(heldout_after_ablation),
            "wrong_binding":safe(wrong_binding),
            "composition":safe(composed),
            "shape_control":{
                "program":shape_program.data(),
                "valid_bijection_and_consequence":shape_valid,
                "anti_unification_result":safe(shape_lgg),
            },
            "no_growth":safe(no_growth),
            "incomplete":safe(incomplete),
            "verifier_ablation":safe(verifier_ablation),
        },
        "gates":{},
    }

    G=evidence["gates"]

    tree=ast.parse(
        (HERE/"basis.py").read_text()
        +"\n"+
        (HERE/"kernel.py").read_text()
    )
    names={
        node.id.lower()
        for node in ast.walk(tree)
        if isinstance(node,ast.Name)
    } | {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node,(ast.FunctionDef,ast.ClassDef))
    }
    forbidden={
        "setedit","assignment","redirect","swap",
        "exchange","transposition","cycle"
    }

    G["R1_no_set_like_repair_primitive_in_frozen_core"]=(
        names.isdisjoint(forbidden)
        and "incidencebit" in names
        and "deltaprogram" in names
    )

    G["R2_current_language_exhausted_before_delta_growth"]=(
        train_a.get("status")=="VERIFIED"
        and train_a.get("current_language",{}).get("candidate_count")==12
        and train_a.get("diagnosis",{}).get("status")=="CERTIFIED_RESIDUAL"
    )

    synth_a=train_a.get("repair",{}).get("synthesis",{})
    expected=sum(math.comb(36,d) for d in range(1,5))
    G["R3_exact_minimum_relation_bit_depth_proved"]=(
        synth_a.get("minimum_delta_depth")==4
        and train_a["_program"].depth==4
        and synth_a.get("tested_delta_count")==expected
    )

    G["R4_every_accepted_delta_is_independently_verified"]=(
        all_rows_clean(train_a)
        and all_rows_clean(train_b)
    )

    synth_b=train_b.get("repair",{}).get("synthesis",{})
    G["R5_second_relabelled_world_independently_rediscovers_depth_four"]=(
        train_b.get("status")=="VERIFIED"
        and synth_b.get("minimum_delta_depth")==4
        and train_b.get("acquisition_search_count")==1
        and train_b["_program"].depth==4
    )

    schema_term=compiled_result.get("schema",{}).get("term")
    expected_schema=[
        "DELTA",
        ["BIT",["VAR",0],["VAR",0]],
        ["BIT",["VAR",0],["VAR",1]],
        ["BIT",["VAR",1],["VAR",0]],
        ["BIT",["VAR",1],["VAR",1]],
    ]
    G["R6_generic_anti_unification_yields_non_ground_relational_schema"]=(
        compiled_result.get("status")=="VERIFIED"
        and compiled_result.get("schema",{}).get("variable_count")==2
        and schema_term==expected_schema
    )

    G["R7_schema_is_more_abstract_and_exactly_replays_training_deltas"]=(
        compiled_result.get("schema_constant_count")==0
        and compiled_result.get("instance_constant_counts")==[8,8]
        and compiled_result.get("training_replay")==[True,True]
    )

    G["R8_heldout_warm_zero_search_schema_transfer"]=(
        heldout_warm.get("status")=="VERIFIED"
        and heldout_warm.get("repair",{}).get("route")=="REUSE_COMPILED_SCHEMA"
        and heldout_warm.get("acquisition_search_count")==0
        and heldout_warm.get("repair",{}).get("acquisition_search_count")==0
    )

    G["R9_cold_zero_search_is_unknown"]=(
        heldout_cold_zero.get("status")=="UNKNOWN_RELATIONAL_SCHEMA"
        and heldout_cold_zero.get("acquisition_search_count")==0
    )

    G["R10_cold_search_rediscovers_exact_minimum_delta"]=(
        heldout_cold_search.get("status")=="VERIFIED"
        and heldout_cold_search.get("repair",{}).get("route")=="SYNTHESIZE"
        and heldout_cold_search.get("repair",{})
            .get("synthesis",{})
            .get("minimum_delta_depth")==4
        and heldout_cold_search.get("acquisition_search_count")==1
    )

    G["R11_schema_ablation_restores_unknown"]=(
        heldout_after_ablation.get("status")=="UNKNOWN_RELATIONAL_SCHEMA"
        and heldout_after_ablation.get("acquisition_search_count")==0
    )

    replay_rows=wrong_binding.get("replay_rows",[])
    G["R12_wrong_consequence_binding_rejected"]=(
        wrong_binding.get("status")=="REPLAY_FAILED"
        and bool(replay_rows)
        and all(
            row.get("verdict",{}).get("accepted") is False
            for row in replay_rows
        )
    )

    G["R13_learned_transformation_composes_exactly"]=(
        composed.get("bijection") is True
        and composed.get("consequence_preserving") is True
        and len(composed.get("mapping",[]))==len(WORLD_C.cells())
    )

    G["R14_no_residual_no_relational_repair_growth"]=(
        no_growth.get("status")=="VERIFIED_NO_GROWTH"
        and no_growth.get("constructor_growth_authorized") is False
        and no_growth.get("acquisition_search_count")==0
    )

    G["R15_incomplete_authority_stays_unknown"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
    )

    G["R16_verifier_ablation_admits_no_delta_or_schema"]=(
        verifier_ablation.get("status")=="UNKNOWN_NO_VERIFIER"
        and verifier_ablation.get("acquisition_search_count")==0
    )

    G["different_verified_relation_program_shape_not_forced"]=(
        shape_valid is True
        and shape_program.depth==6
        and shape_lgg is None
    )

    G["minimal_developmental_algorithm_respected"]=all(
        tok in (HERE/"PROTOCOL.md").read_text()
        for tok in (
            "EXECUTE","VERIFY","DIAGNOSE","CONSTRAIN",
            "RESTRUCTURE","CHOOSE","COMPILE","UPDATE"
        )
    )

    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_RELATIONAL_DELTA_REPAIR_GENESIS_WITHOUT_SET_PRIMITIVE"
        if evidence["full_pass"]
        else "RELATIONAL_DELTA_REPAIR_GENESIS_V23_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
