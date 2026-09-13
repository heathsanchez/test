from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import KINDS,WORLDS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="d62f99158435afa75ab53278848b3c5a1c41feb7"

def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def summary(r):
    return {
        k:r.get(k)
        for k in (
            "status","action_classes","class_count","class_profiles","full_profile",
            "pairwise_commuting","pairwise_identity_intersections",
            "class_order_product","multiplication_image_size",
            "unique_product_coordinates","multiplication_image_spans_full_monoid",
            "internal_direct_product",
            "weak_action_component_count","weak_action_component_sizes",
            "classification",
        )
        if k in r
    }

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    results={
        kind:{str(v):k.synthesize(WORLDS[(kind,v)]) for v in range(3)}
        for kind in KINDS
    }
    relabelled={kind:k.synthesize(RELABELLED[kind]) for kind in KINDS}

    max1={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_successors_per_state=1)
        for kind in KINDS
    }
    min1={
        kind:k.synthesize(WORLDS[(kind,0)],minimum_successors_per_state=1)
        for kind in KINDS
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(
        WORLDS[("nondeterministic_three_class",0)],
        verification_enabled=False,
    )

    det=results["deterministic_one_class"]["0"]
    partial=results["partial_one_class"]["0"]
    nondet=results["nondeterministic_one_class"]["0"]
    two=results["nondeterministic_two_class"]["0"]
    three=results["nondeterministic_three_class"]["0"]
    mixed=results["mixed_three_class"]["0"]
    coupled=results["coupled_flip_blur"]["0"]

    G={}
    G["R1_frozen_scientific_core_byte_identical"]=freeze_ok

    dp=det.get("class_profiles",[{}])[0]
    G["R2_deterministic_control_derives_only_total_functions"]=(
        det.get("status")=="VERIFIED"
        and det.get("classification")=="UNDECOMPOSED_SINGLE_CLASS"
        and dp.get("order")==8
        and dp.get("relation_kinds")==["TOTAL_FUNCTION"]
        and dp.get("total_function_count")==8
        and dp.get("partial_function_count")==0
        and dp.get("nondeterministic_relation_count")==0
        and dp.get("max_branching_spectrum")==[1]
    )

    pp=partial.get("class_profiles",[{}])[0]
    G["R3_partial_control_derives_partial_function_without_branching"]=(
        partial.get("status")=="VERIFIED"
        and partial.get("classification")=="UNDECOMPOSED_SINGLE_CLASS"
        and pp.get("order")==2
        and pp.get("total_function_count")==1
        and pp.get("partial_function_count")==1
        and pp.get("nondeterministic_relation_count")==0
        and pp.get("relation_kinds")==["PARTIAL_FUNCTION","TOTAL_FUNCTION"]
        and pp.get("domain_size_spectrum")==[4,8]
        and pp.get("max_branching_spectrum")==[1]
        and pp.get("nonidentity_idempotent_count")==1
    )

    np=nondet.get("class_profiles",[{}])[0]
    G["R4_branching_control_derives_genuine_nondeterminism"]=(
        nondet.get("status")=="VERIFIED"
        and nondet.get("classification")=="UNDECOMPOSED_SINGLE_CLASS"
        and np.get("order")==2
        and np.get("total_function_count")==1
        and np.get("partial_function_count")==0
        and np.get("nondeterministic_relation_count")==1
        and np.get("relation_kinds")==["NONDETERMINISTIC_RELATION","TOTAL_FUNCTION"]
        and np.get("max_branching_spectrum")==[1,2]
        and np.get("nonidentity_idempotent_count")==1
    )

    G["R5_two_branching_classes_are_direct_but_state_underresolved"]=(
        two.get("status")=="VERIFIED"
        and two.get("classification")=="UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS"
        and [p.get("order") for p in two.get("class_profiles",[])]==[2,2]
        and all(p.get("nondeterministic_relation_count")==1 for p in two.get("class_profiles",[]))
        and two.get("full_profile",{}).get("order")==4
        and two.get("pairwise_commuting") is True
        and two.get("pairwise_identity_intersections") is True
        and two.get("unique_product_coordinates") is True
        and two.get("multiplication_image_spans_full_monoid") is True
        and two.get("internal_direct_product") is True
        and two.get("weak_action_component_count")==2
        and two.get("weak_action_component_sizes")==[4,4]
    )

    G["R6_third_branching_class_closes_direct_relation_complementarity"]=(
        three.get("status")=="VERIFIED"
        and three.get("classification")=="DERIVED_DIRECT_RELATION_COMPLEMENTARITY"
        and [p.get("order") for p in three.get("class_profiles",[])]==[2,2,2]
        and all(p.get("nondeterministic_relation_count")==1 for p in three.get("class_profiles",[]))
        and three.get("full_profile",{}).get("order")==8
        and three.get("pairwise_commuting") is True
        and three.get("pairwise_identity_intersections") is True
        and three.get("class_order_product")==8
        and three.get("multiplication_image_size")==8
        and three.get("unique_product_coordinates") is True
        and three.get("multiplication_image_spans_full_monoid") is True
        and three.get("internal_direct_product") is True
        and three.get("weak_action_component_count")==1
        and three.get("weak_action_component_sizes")==[8]
    )

    mp=mixed.get("class_profiles",[])
    G["R7_deterministic_and_branching_classes_can_be_independent_together"]=(
        mixed.get("status")=="VERIFIED"
        and mixed.get("classification")=="DERIVED_DIRECT_RELATION_COMPLEMENTARITY"
        and [p.get("order") for p in mp]==[2,2,2]
        and mixed.get("full_profile",{}).get("order")==8
        and mixed.get("internal_direct_product") is True
        and mixed.get("weak_action_component_count")==1
    )

    G["R8_mixed_world_derives_one_deterministic_and_two_branching_class_algebras"]=(
        len(mp)==3
        and mp[0].get("relation_kinds")==["TOTAL_FUNCTION"]
        and mp[0].get("total_function_count")==2
        and mp[0].get("nondeterministic_relation_count")==0
        and all(
            p.get("total_function_count")==1
            and p.get("partial_function_count")==0
            and p.get("nondeterministic_relation_count")==1
            and p.get("max_branching_spectrum")==[1,2]
            for p in mp[1:]
        )
    )

    G["R9_flip_blur_same_degree_is_coupled_despite_commutation_and_cardinality"]=(
        coupled.get("status")=="VERIFIED"
        and coupled.get("classification")=="COUPLED_TRANSITION_RELATIONS"
        and [p.get("order") for p in coupled.get("class_profiles",[])]==[2,2]
        and coupled.get("full_profile",{}).get("order")==3
        and coupled.get("pairwise_commuting") is True
        and coupled.get("pairwise_identity_intersections") is True
        and coupled.get("class_order_product")==4
        and coupled.get("multiplication_image_size")==3
        and coupled.get("unique_product_coordinates") is False
        and coupled.get("multiplication_image_spans_full_monoid") is True
        and coupled.get("internal_direct_product") is False
    )

    G["R10_opaque_state_relabelling_preserves_relation_algebra"]=all(
        summary(results[kind][str(v)])==summary(results[kind]["0"])
        for kind in KINDS for v in range(3)
    )

    G["R11_consequence_label_relabelling_preserves_relation_algebra"]=all(
        summary(relabelled[kind])==summary(results[kind]["0"])
        for kind in KINDS
    )

    two_rows={
        (r.state,r.action,r.afters,r.consequence)
        for r in WORLDS[("nondeterministic_two_class",0)].rows
    }
    three_prefix={
        (r.state,r.action,r.afters,r.consequence)
        for r in WORLDS[("nondeterministic_three_class",0)].rows
        if r.action<2
    }
    G["R12_removing_third_branching_class_restores_underresolved_algebra"]=(
        two_rows==three_prefix
        and two.get("classification")=="UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS"
        and three.get("classification")=="DERIVED_DIRECT_RELATION_COMPLEMENTARITY"
        and two.get("full_profile",{}).get("order")==4
        and three.get("full_profile",{}).get("order")==8
    )

    branching_worlds=(
        "nondeterministic_one_class",
        "nondeterministic_two_class",
        "nondeterministic_three_class",
        "mixed_three_class",
        "coupled_flip_blur",
    )
    G["R13_max_successor_one_preserves_nonbranching_and_blocks_branching_worlds"]=(
        max1["deterministic_one_class"].get("status")=="VERIFIED"
        and max1["partial_one_class"].get("status")=="VERIFIED"
        and all(
            max1[kind].get("status")=="CERTIFIED_SUCCESSOR_MULTIPLICITY_BOUND_INADEQUACY"
            and max1[kind].get("algebra_steps")==0
            for kind in branching_worlds
        )
    )

    G["R14_min_successor_one_preserves_total_relations_and_blocks_partial_world"]=(
        min1["partial_one_class"].get("status")=="CERTIFIED_SUCCESSOR_MULTIPLICITY_BOUND_INADEQUACY"
        and min1["partial_one_class"].get("algebra_steps")==0
        and all(
            min1[kind].get("status")=="VERIFIED"
            for kind in KINDS
            if kind!="partial_one_class"
        )
    )

    G["R15_unknown_authority_and_verifier_ablation_authorize_no_relation_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("algebra_steps")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden_hidden=(
        "deterministic_one_class","partial_one_class",
        "nondeterministic_one_class","nondeterministic_two_class",
        "nondeterministic_three_class","mixed_three_class","coupled_flip_blur",
        "hidden","graph","edge","site","channel",
    )
    G["R16_generic_authority_accepts_empty_and_branching_rows_without_hidden_vocab"]=(
        partial.get("status")=="VERIFIED"
        and nondet.get("status")=="VERIFIED"
        and "invalid_nonbijective" not in source
        and "invalid_nondeterministic" not in source
        and "invalid_partial" not in source
        and all(
            re.search(r"\b"+re.escape(tok)+r"\b",source) is None
            for tok in forbidden_hidden
        )
    )

    evidence={
        "experiment":"finite_transition_relation_genesis_v45",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":relabelled,
        "maximum_successor_one_ablation":max1,
        "minimum_successor_one_ablation":min1,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_DETERMINISM_PARTIALITY_AND_BRANCHING_GENESIS_FROM_FINITE_RELATION_CLOSURE"
        if evidence["full_pass"] else
        "FINITE_TRANSITION_RELATION_V45_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
