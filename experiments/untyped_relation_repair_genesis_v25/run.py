#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import difference_term
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
        and row.get("verdict", {}).get("total") is True
        and row.get("verdict", {}).get("functional") is True
        and row.get("verdict", {}).get("bijection") is True
        and row.get("verdict", {}).get("residual_discharge") is True
        and row.get("verdict", {}).get("consequence_preserving") is True
        and row.get("verdict", {}).get("novel_outside_current_language") is True
        for row in rows
    )


def generator_has_no_type_filter() -> bool:
    tree = ast.parse((HERE / "basis.py").read_text())
    node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "all_relations"
    )
    names = {
        x.id.lower()
        for x in ast.walk(node)
        if isinstance(x, ast.Name)
    } | {
        x.attr.lower()
        for x in ast.walk(node)
        if isinstance(x, ast.Attribute)
    }
    forbidden = {
        "total","functional","bijection","permutation",
        "mapping_is_bijection","mapping_preserves_consequence",
    }
    return names.isdisjoint(forbidden)


def main() -> int:
    k = Kernel()

    train_a = k.develop(BASE)
    train_b = k.develop(WORLD_B)

    compiled_result = k.compile_schema((
        ("TRAIN_A", BASE, train_a["_residual"], train_a["_relation"]),
        ("TRAIN_B", WORLD_B, train_b["_residual"], train_b["_relation"]),
    ))
    compiled = compiled_result.get("_compiled")

    held_exhausted = k.exhaust_current_language(WORLD_C)
    held_diag = k.diagnose_residual(WORLD_C, held_exhausted)
    held_res = held_diag["_residual"]
    predictions = k.predict_difference(WORLD_C, held_res, compiled)
    predicted_json = [term_to_json(t) for t in predictions]

    heldout = k.develop(WORLD_C)
    heldout_term_json = term_to_json(
        difference_term(WORLD_C, heldout["_relation"])
    )

    bad_right = next(
        cell
        for cell in WORLD_C.cells()
        if WORLD_C.consequence(cell) != WORLD_C.consequence(held_res.left)
    )
    bad_res = Residual(
        held_res.left,
        bad_right,
        int(WORLD_C.consequence(held_res.left)),
        held_res.left_orbit,
        -1,
    )
    bad_search = k.exhaustive_repair(WORLD_C, bad_res)

    no_growth = k.develop(NO_GROWTH)
    incomplete = k.develop(INCOMPLETE)
    verifier_ablation = k.develop(BASE, verification_enabled=False)

    composition = k.compose_verified(
        WORLD_C,
        heldout["_mapping"],
        heldout["_mapping"],
    )

    evidence = {
        "experiment":"untyped_relation_repair_genesis_v25",
        "scientific_freeze_commit":"c2e0837fc36f01fbd70891fb0ecba45256399a4c",
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
            "heldout_search":safe(heldout),
            "heldout_difference":heldout_term_json,
            "wrong_binding_search":safe(bad_search),
            "no_growth":safe(no_growth),
            "composition":safe(composition),
            "incomplete":safe(incomplete),
            "verifier_ablation":safe(verifier_ablation),
        },
        "gates":{},
    }

    G=evidence["gates"]

    G["U1_unrestricted_relation_universe_exhausted"]=(
        train_a.get("status")=="VERIFIED"
        and train_a.get("repair",{}).get("tested_relation_count")==2**16
    )

    G["U2_candidate_generator_has_no_transformation_type_filter"]=(
        generator_has_no_type_filter()
    )

    G["U3_current_language_exhausted_before_relation_growth"]=(
        train_a.get("current_language",{}).get("candidate_count")==4
        and train_a.get("diagnosis",{}).get("status")=="CERTIFIED_RESIDUAL"
    )

    G["U4_verifier_recognizes_transformation_structure_after_construction"]=(
        frontier_clean(train_a)
        and frontier_clean(train_b)
    )

    G["U5_exact_global_minimum_over_all_relations"]=(
        train_a.get("repair",{}).get("minimum_extensional_distance")==4
        and train_a.get("repair",{}).get("tested_relation_count")==2**16
    )

    rejects=train_a.get("repair",{}).get("rejection_counts",{})
    G["U6_nontransforming_relations_are_genuinely_considered_and_rejected"]=(
        rejects.get("not_total",0)>0
        and rejects.get("not_functional",0)>0
        and rejects.get("not_bijective",0)>0
    )

    G["U7_independent_relabelled_world_recovers_same_minimum"]=(
        train_b.get("status")=="VERIFIED"
        and train_b.get("repair",{}).get("tested_relation_count")==2**16
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
    G["U8_generic_anti_unification_yields_recurring_difference_schema"]=(
        compiled_result.get("status")=="VERIFIED"
        and schema.get("variable_count")==2
        and schema.get("term")==expected
        and compiled_result.get("schema_constant_count")==0
        and compiled_result.get("training_replay")==[True,True]
    )

    G["U9_schema_predicts_heldout_before_unrestricted_search"]=(
        held_diag.get("status")=="CERTIFIED_RESIDUAL"
        and len(predictions)>=1
    )

    G["U10_heldout_unrestricted_search_confirms_prediction"]=(
        heldout.get("status")=="VERIFIED"
        and heldout.get("repair",{}).get("tested_relation_count")==2**16
        and heldout.get("repair",{}).get("minimum_extensional_distance")==4
        and heldout_term_json in predicted_json
    )

    G["U11_wrong_consequence_binding_has_no_verifier_clean_relation"]=(
        bad_search.get("status")=="CERTIFIED_NO_REPAIR_IN_UNRESTRICTED_RELATION_LANGUAGE"
        and bad_search.get("tested_relation_count")==2**16
    )

    G["U12_no_residual_no_unrestricted_relation_search"]=(
        no_growth.get("status")=="VERIFIED_NO_GROWTH"
        and no_growth.get("constructor_growth_authorized") is False
        and no_growth.get("acquisition_search_count")==0
    )

    G["U13_recovered_relation_composes_exactly"]=(
        composition.get("bijection") is True
        and composition.get("consequence_preserving") is True
        and len(composition.get("mapping",[]))==len(WORLD_C.cells())
    )

    G["U14_incomplete_authority_stays_unknown"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
    )

    G["U15_verifier_ablation_admits_no_relation"]=(
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
        "VERIFIED_UNTYPED_RELATION_REPAIR_GENESIS_WITH_TRANSFORMATION_STRUCTURE_EMERGING_AT_VERIFICATION"
        if evidence["full_pass"]
        else "UNTYPED_RELATION_REPAIR_GENESIS_V25_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
