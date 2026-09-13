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


def generator_is_composition_only() -> bool:
    tree = ast.parse((HERE / "basis.py").read_text())
    target_names = {
        "atomic_expressions",
        "expressions_of_width",
        "all_expression_sets",
    }
    nodes = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name in target_names
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
        "tuplefact","pair","relation","edge","source","target",
        "total","functional","bijection","permutation",
    }
    return (
        names.isdisjoint(forbidden)
        and "atom" in names
        and "cat" in names
    )


def main() -> int:
    k = Kernel()

    main_run = k.develop(BASE)
    relabelled = k.develop(WORLD_B)
    growth_ablation = k.develop(
        BASE,
        allow_composition_growth=False,
    )
    no_growth = k.develop(NO_GROWTH)
    incomplete = k.develop(INCOMPLETE)
    verifier_ablation = k.develop(
        BASE,
        verification_enabled=False,
    )

    evidence = {
        "experiment":"compositional_relation_carrier_genesis_v27",
        "scientific_freeze_commit":"f4f0799472ef042c9b9d1fef52e4d133abdb16cb",
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
            "composition_growth_ablation":safe(growth_ablation),
            "no_growth":safe(no_growth),
            "incomplete":safe(incomplete),
            "verifier_ablation":safe(verifier_ablation),
        },
        "gates":{},
    }

    G=evidence["gates"]
    gens=main_run.get("generations",[])
    gen1=gens[0] if len(gens)>0 else {}
    gen2=gens[1] if len(gens)>1 else {}

    G["C1_no_tuple_pair_or_relation_constructor_in_candidate_generator"]=(
        generator_is_composition_only()
    )

    G["C2_l0_residual_precedes_compositional_growth"]=(
        main_run.get("status")=="VERIFIED"
        and len(gens)==2
        and main_run.get("selected_width")==2
    )

    G["C3_width_one_is_exhaustively_inadequate"]=(
        gen1.get("width")==1
        and gen1.get("status")=="CERTIFIED_NO_VERIFIER_CLEAN_STRUCTURE_AT_WIDTH"
        and gen1.get("tested_candidate_count")==2**4
        and gen1.get("rejection_counts",{}).get("no_role_pair")==2**4
    )

    G["C4_cat_growth_occurs_only_after_complete_width_one_failure"]=(
        gen1.get("tested_candidate_count")==16
        and gen1.get("status")=="CERTIFIED_NO_VERIFIER_CLEAN_STRUCTURE_AT_WIDTH"
        and gen2.get("width")==2
    )

    G["C5_width_two_is_exhausted_and_sufficient"]=(
        gen2.get("status")=="VERIFIED"
        and gen2.get("tested_candidate_count")==2**16
        and bool(gen2.get("frontier"))
    )

    G["C6_minimum_sufficient_width_is_two_no_higher_width_searched"]=(
        main_run.get("selected_width")==2
        and len(gens)==2
        and all(g.get("width")<=2 for g in gens)
    )

    G["C7_relational_roles_are_verifier_selected"]=(
        main_run.get("selected_role_pair") in ([0,1],[1,0])
        and bool(gen2.get("frontier",[])[0].get("role_rows"))
    )

    G["C8_exact_minimum_repair_within_minimum_width"]=(
        main_run.get("minimum_extensional_distance")==4
        and gen2.get("minimum_extensional_distance")==4
    )

    rejects=gen2.get("rejection_counts",{})
    G["C9_nonrelational_compositions_are_genuinely_considered"]=(
        rejects.get("no_total_role",0)>0
        and rejects.get("no_functional_role",0)>0
        and rejects.get("no_bijective_role",0)>0
    )

    rgens=relabelled.get("generations",[])
    G["C10_independent_relabelling_recovers_same_width_and_cost"]=(
        relabelled.get("status")=="VERIFIED"
        and relabelled.get("selected_width")==2
        and relabelled.get("minimum_extensional_distance")==4
        and len(rgens)==2
        and rgens[0].get("tested_candidate_count")==16
        and rgens[1].get("tested_candidate_count")==2**16
    )

    G["C11_composition_ablation_stops_at_certified_inadequacy"]=(
        growth_ablation.get("status")=="CERTIFIED_COMPOSITIONAL_INADEQUACY"
        and growth_ablation.get("selected_width")==1
        and len(growth_ablation.get("generations",[]))==1
    )

    G["C12_no_residual_no_composition_growth"]=(
        no_growth.get("status")=="VERIFIED_NO_GROWTH"
        and no_growth.get("composition_growth_authorized") is False
        and no_growth.get("generations")==[]
    )

    G["C13_incomplete_authority_stays_unknown"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
    )

    G["C14_verifier_ablation_admits_no_composed_carrier"]=(
        verifier_ablation.get("status")=="UNKNOWN_NO_VERIFIER"
        and verifier_ablation.get("composition_growth_authorized") is False
        and verifier_ablation.get("generations")==[]
    )

    selected = main_run.get("selected_flattened_leaves",[])
    G["C15_composed_syntax_flattens_to_verified_binary_incidence"]=(
        len(selected)==4
        and all(len(leaves)==2 for leaves in selected)
        and len(main_run.get("mapping",[]))==4
    )

    G["minimal_developmental_algorithm_respected"]=(
        G["C2_l0_residual_precedes_compositional_growth"]
        and G["C3_width_one_is_exhaustively_inadequate"]
        and G["C4_cat_growth_occurs_only_after_complete_width_one_failure"]
        and G["C6_minimum_sufficient_width_is_two_no_higher_width_searched"]
        and G["C11_composition_ablation_stops_at_certified_inadequacy"]
        and G["C12_no_residual_no_composition_growth"]
        and G["C13_incomplete_authority_stays_unknown"]
        and G["C14_verifier_ablation_admits_no_composed_carrier"]
    )

    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_COMPOSITIONAL_RELATION_CARRIER_GENESIS_WITHOUT_TUPLE_PRIMITIVE"
        if evidence["full_pass"]
        else "COMPOSITIONAL_RELATION_CARRIER_V27_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
