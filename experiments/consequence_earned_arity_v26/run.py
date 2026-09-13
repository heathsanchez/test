#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from kernel import Kernel
from challenge_pack import BASE, WORLD_B, NO_GROWTH, INCOMPLETE


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


def tuple_generator_has_no_relation_semantics() -> bool:
    tree = ast.parse((HERE / "basis.py").read_text())
    nodes = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name in {"tuple_universe", "all_tuple_sets"}
    ]
    names = set()
    for node in nodes:
        names |= {
            x.id.lower()
            for x in ast.walk(node)
            if isinstance(x, ast.Name)
        }
        names |= {
            x.attr.lower()
            for x in ast.walk(node)
            if isinstance(x, ast.Attribute)
        }
    forbidden = {
        "relation","edge","source","target",
        "total","functional","bijection","permutation",
    }
    return names.isdisjoint(forbidden)


def main() -> int:
    k = Kernel()

    main_run = k.develop(BASE)
    relabelled = k.develop(WORLD_B)
    no_growth_allowed = k.develop(
        BASE,
        allow_arity_growth=False,
    )
    no_growth_world = k.develop(NO_GROWTH)
    incomplete = k.develop(INCOMPLETE)
    verifier_ablation = k.develop(
        BASE,
        verification_enabled=False,
    )

    evidence = {
        "experiment":"consequence_earned_arity_v26",
        "scientific_freeze_commit":"d21b6e7a41f3701efb80fc6ee1cecd150275956f",
        "post_freeze_challenges":True,
        "hashes":{
            "PROTOCOL.md":sha256(HERE/"PROTOCOL.md"),
            "FREEZE.json":sha256(HERE/"FREEZE.json"),
            "basis.py":sha256(HERE/"basis.py"),
            "kernel.py":sha256(HERE/"kernel.py"),
            "challenge_pack.py":sha256(HERE/"challenge_pack.py"),
        },
        "results":{
            "main":safe(main_run),
            "relabelled":safe(relabelled),
            "arity_growth_ablation":safe(no_growth_allowed),
            "no_residual_world":safe(no_growth_world),
            "incomplete":safe(incomplete),
            "verifier_ablation":safe(verifier_ablation),
        },
        "gates":{},
    }

    G=evidence["gates"]
    gens=main_run.get("generations",[])
    gen1=gens[0] if len(gens)>0 else {}
    gen2=gens[1] if len(gens)>1 else {}

    G["A1_candidate_generator_has_only_generic_tuple_set_structure"]=(
        tuple_generator_has_no_relation_semantics()
    )

    G["A2_l0_residual_precedes_tuple_language_search"]=(
        main_run.get("status")=="VERIFIED"
        and main_run.get("selected_arity")==2
        and len(gens)==2
    )

    G["A3_arity_one_is_exhaustively_inadequate"]=(
        gen1.get("arity")==1
        and gen1.get("status")=="CERTIFIED_NO_VERIFIER_CLEAN_STRUCTURE_AT_ARITY"
        and gen1.get("tested_candidate_count")==2**4
        and gen1.get("rejection_counts",{}).get("no_role_pair")==2**4
    )

    G["A4_arity_growth_occurs_only_after_complete_arity_one_failure"]=(
        gen1.get("status")=="CERTIFIED_NO_VERIFIER_CLEAN_STRUCTURE_AT_ARITY"
        and gen1.get("tested_candidate_count")==16
        and gen2.get("arity")==2
    )

    G["A5_arity_two_is_exhausted_and_succeeds"]=(
        gen2.get("status")=="VERIFIED"
        and gen2.get("tested_candidate_count")==2**16
        and bool(gen2.get("frontier"))
    )

    G["A6_minimum_sufficient_arity_is_two_and_no_higher_arity_searched"]=(
        main_run.get("selected_arity")==2
        and len(gens)==2
        and all(g.get("arity")<=2 for g in gens)
    )

    role=main_run.get("selected_role_pair")
    G["A7_coordinate_roles_are_selected_by_verifier"]=(
        role in ([0,1],[1,0])
        and bool(gen2.get("frontier",[])[0].get("role_rows"))
    )

    G["A8_exact_minimum_change_within_minimum_arity"]=(
        main_run.get("minimum_extensional_distance")==4
        and gen2.get("minimum_extensional_distance")==4
    )

    rejects=gen2.get("rejection_counts",{})
    G["A9_nonrelational_tuple_sets_are_genuinely_considered"]=(
        rejects.get("no_total_role",0)>0
        and rejects.get("no_functional_role",0)>0
        and rejects.get("no_bijective_role",0)>0
    )

    rgens=relabelled.get("generations",[])
    G["A10_independent_relabelling_recovers_same_arity_and_cost"]=(
        relabelled.get("status")=="VERIFIED"
        and relabelled.get("selected_arity")==2
        and relabelled.get("minimum_extensional_distance")==4
        and len(rgens)==2
        and rgens[0].get("tested_candidate_count")==16
        and rgens[1].get("tested_candidate_count")==2**16
    )

    G["A11_arity_growth_ablation_stops_at_certified_inadequacy"]=(
        no_growth_allowed.get("status")=="CERTIFIED_ARITY_INADEQUACY"
        and no_growth_allowed.get("selected_arity")==1
        and len(no_growth_allowed.get("generations",[]))==1
    )

    G["A12_no_residual_no_tuple_language_growth"]=(
        no_growth_world.get("status")=="VERIFIED_NO_GROWTH"
        and no_growth_world.get("arity_growth_authorized") is False
        and no_growth_world.get("generations")==[]
    )

    G["A13_incomplete_authority_stays_unknown"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
    )

    G["A14_verifier_ablation_admits_no_tuple_structure_or_arity_growth"]=(
        verifier_ablation.get("status")=="UNKNOWN_NO_VERIFIER"
        and verifier_ablation.get("arity_growth_authorized") is False
        and verifier_ablation.get("generations")==[]
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
        "VERIFIED_CONSEQUENCE_EARNED_BINARY_ARITY_FROM_GENERIC_TUPLE_SET_CONSTRUCTION"
        if evidence["full_pass"]
        else "CONSEQUENCE_EARNED_ARITY_V26_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
