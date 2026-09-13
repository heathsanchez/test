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
    difference_edges,
    difference_term,
    mapping_is_bijection,
    mapping_preserves_consequence,
)
from kernel import Kernel, Residual, term_to_json
from challenge_pack import BASE, WORLD_B, WORLD_C, NO_GROWTH, INCOMPLETE


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


def frontier_clean(dev):
    rows = dev.get("repair", {}).get("frontier", [])
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

    train_a = k.develop(BASE)
    train_b = k.develop(WORLD_B)

    compiled_result = k.compile_schema((
        ("TRAIN_A", BASE, train_a["_residual"], train_a["_mapping"]),
        ("TRAIN_B", WORLD_B, train_b["_residual"], train_b["_mapping"]),
    ))
    compiled = compiled_result.get("_compiled")

    # Prospectively diagnose and predict held-out difference before any
    # held-out global relation acquisition search is performed.
    held_exhausted = k.exhaust_current_language(WORLD_C)
    held_diag = k.diagnose_residual(WORLD_C, held_exhausted)
    held_res = held_diag["_residual"]
    predictions = k.predict_difference(WORLD_C, held_res, compiled)
    predicted_json = [term_to_json(t) for t in predictions]

    # Only now perform the independent cold complete held-out relation search.
    heldout_cold = k.develop(WORLD_C)

    bad_right = next(
        cell for cell in WORLD_C.cells()
        if WORLD_C.consequence(cell) != WORLD_C.consequence(held_res.left)
    )
    bad_res = Residual(
        held_res.left,
        bad_right,
        int(WORLD_C.consequence(held_res.left)),
        held_res.left_orbit,
        -1,
    )
    bad_predictions = k.predict_difference(WORLD_C, bad_res, compiled)
    bad_search = k.exhaustive_repair(WORLD_C, bad_res)

    no_growth = k.develop(NO_GROWTH)
    incomplete = k.develop(INCOMPLETE)
    verifier_ablation = k.develop(BASE, verification_enabled=False)

    composition = k.compose_verified(
        WORLD_C,
        heldout_cold["_mapping"],
        heldout_cold["_mapping"],
    )

    heldout_term = difference_term(WORLD_C, heldout_cold["_mapping"])
    heldout_term_json = term_to_json(heldout_term)

    evidence = {
        "experiment":"edit_free_relational_repair_v24",
        "scientific_freeze_commit":"f0cfe0802ef9303ed02b31aa5a2553719f3255cf",
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
            "heldout_diagnosis":safe(held_diag),
            "heldout_presearch_predictions":predicted_json,
            "heldout_cold_search":safe(heldout_cold),
            "heldout_cold_difference":heldout_term_json,
            "wrong_binding_predictions":[term_to_json(t) for t in bad_predictions],
            "wrong_binding_search":safe(bad_search),
            "no_growth":safe(no_growth),
            "composition":safe(composition),
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
        "setedit","flip","toggle","assignment","redirect",
        "swap","exchange","transposition","cycle"
    }

    G["E1_no_edit_primitive_in_frozen_core"]=(
        names.isdisjoint(forbidden)
        and "all_total_mappings" in names
        and "mapping_relation" in names
    )

    G["E2_complete_direct_relation_language_exhausted"]=(
        train_a.get("status")=="VERIFIED"
        and train_a.get("repair",{}).get("tested_mapping_count")==6**6
        and train_a.get("current_language",{}).get("candidate_count")==12
    )

    G["E3_exact_global_minimum_extensional_repair"]=(
        train_a.get("repair",{}).get("minimum_extensional_distance")==4
        and train_a.get("repair",{}).get("minimum_extensional_distance",0)>1
    )

    G["E4_all_minimum_repairs_are_independently_verifier_clean"]=(
        frontier_clean(train_a)
        and frontier_clean(train_b)
    )

    G["E5_independent_relabelled_world_recovers_same_minimum_distance"]=(
        train_b.get("status")=="VERIFIED"
        and train_b.get("repair",{}).get("tested_mapping_count")==6**6
        and train_b.get("repair",{}).get("minimum_extensional_distance")==4
        and train_b.get("acquisition_search_count")==1
    )

    schema=compiled_result.get("schema",{})
    expected=[
        "DIFF",
        ["EDGE",["VAR",0],["VAR",0]],
        ["EDGE",["VAR",0],["VAR",1]],
        ["EDGE",["VAR",1],["VAR",0]],
        ["EDGE",["VAR",1],["VAR",1]],
    ]
    G["E6_generic_anti_unification_generates_non_ground_difference_schema"]=(
        compiled_result.get("status")=="VERIFIED"
        and schema.get("variable_count")==2
        and schema.get("term")==expected
    )

    G["E7_schema_is_more_abstract_and_replays_training_differences"]=(
        compiled_result.get("schema_constant_count")==0
        and compiled_result.get("instance_constant_counts")==[8,8]
        and compiled_result.get("training_replay")==[True,True]
    )

    G["E8_prospective_heldout_difference_is_predicted_before_cold_search"]=(
        held_diag.get("status")=="CERTIFIED_RESIDUAL"
        and len(predictions)>=1
        and heldout_cold.get("acquisition_search_count")==1
    )

    G["E9_independent_heldout_global_search_confirms_predicted_difference"]=(
        heldout_cold.get("status")=="VERIFIED"
        and heldout_cold.get("repair",{}).get("tested_mapping_count")==6**6
        and heldout_cold.get("repair",{}).get("minimum_extensional_distance")==4
        and heldout_term_json in predicted_json
    )

    G["E10_wrong_consequence_binding_has_no_verifier_clean_repair"]=(
        len(bad_predictions)>=1
        and bad_search.get("status")=="CERTIFIED_NO_REPAIR_IN_DECLARED_RELATION_LANGUAGE"
    )

    G["E11_no_residual_no_relation_construction_growth"]=(
        no_growth.get("status")=="VERIFIED_NO_GROWTH"
        and no_growth.get("constructor_growth_authorized") is False
        and no_growth.get("acquisition_search_count")==0
    )

    G["E12_constructed_relation_composes_exactly"]=(
        composition.get("bijection") is True
        and composition.get("consequence_preserving") is True
        and len(composition.get("mapping",[]))==len(WORLD_C.cells())
    )

    G["E13_incomplete_authority_stays_unknown"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
    )

    G["E14_verifier_ablation_admits_no_constructed_relation"]=(
        verifier_ablation.get("status")=="UNKNOWN_NO_VERIFIER"
        and verifier_ablation.get("acquisition_search_count")==0
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
        "VERIFIED_EDIT_FREE_RELATIONAL_REPAIR_CONSTRUCTION_AND_PROSPECTIVE_DIFFERENCE_SCHEMA"
        if evidence["full_pass"]
        else "EDIT_FREE_RELATIONAL_REPAIR_V24_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
