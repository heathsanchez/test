from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import KINDS,WORLDS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="7295e63edbac1d0a550a15e020f81e50fb557724"

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
            "unique_product_coordinates",
            "multiplication_image_spans_full_monoid",
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
    one_class_bound={
        kind:k.synthesize(WORLDS[(kind,0)],allowed_action_classes=1)
        for kind in KINDS
    }
    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("reset_three_class",0)],verification_enabled=False)

    rev1=results["reversible_one_class"]["0"]
    chain=results["collapse_chain_one_class"]["0"]
    rev2=results["reversible_two_class"]["0"]
    rev3=results["reversible_three_class"]["0"]
    resets=results["reset_three_class"]["0"]
    mixed=results["mixed_two_class"]["0"]
    coupled=results["coupled_flip_reset"]["0"]

    G={}
    G["M1_frozen_scientific_core_byte_identical"]=freeze_ok

    p=rev1.get("class_profiles",[{}])[0]
    G["M2_reversible_one_class_is_derived_not_assumed"]=(
        rev1.get("status")=="VERIFIED"
        and rev1.get("classification")=="UNDECOMPOSED_SINGLE_CLASS"
        and p.get("order")==8
        and p.get("unit_count")==8
        and p.get("all_elements_units") is True
        and p.get("rank_spectrum")==[8]
        and p.get("rank_behavior")=="NO_RANK_LOSS"
        and rev1.get("full_profile")==p
    )

    p=chain.get("class_profiles",[{}])[0]
    G["M3_irreversible_chain_derives_rank_loss_and_global_collapse"]=(
        chain.get("status")=="VERIFIED"
        and chain.get("classification")=="UNDECOMPOSED_SINGLE_CLASS"
        and p.get("order")==4
        and p.get("unit_count")==1
        and p.get("all_elements_units") is False
        and p.get("rank_spectrum")==[1,2,4,8]
        and p.get("minimum_rank")==1
        and p.get("nonidentity_idempotent_count")==1
        and p.get("constant_map_count")==1
        and p.get("rank_behavior")=="GLOBAL_COLLAPSE_PRESENT"
    )

    G["M4_two_reversible_classes_are_direct_but_state_underresolved"]=(
        rev2.get("status")=="VERIFIED"
        and rev2.get("classification")=="UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS"
        and [p.get("order") for p in rev2.get("class_profiles",[])]==[2,2]
        and all(p.get("all_elements_units") is True for p in rev2.get("class_profiles",[]))
        and rev2.get("full_profile",{}).get("order")==4
        and rev2.get("full_profile",{}).get("all_elements_units") is True
        and rev2.get("internal_direct_product") is True
        and rev2.get("weak_action_component_count")==2
        and rev2.get("weak_action_component_sizes")==[4,4]
    )

    G["M5_third_reversible_class_closes_direct_complementarity"]=(
        rev3.get("status")=="VERIFIED"
        and rev3.get("classification")=="DERIVED_DIRECT_MONOID_COMPLEMENTARITY"
        and [p.get("order") for p in rev3.get("class_profiles",[])]==[2,2,2]
        and all(p.get("all_elements_units") is True for p in rev3.get("class_profiles",[]))
        and rev3.get("full_profile",{}).get("order")==8
        and rev3.get("full_profile",{}).get("all_elements_units") is True
        and rev3.get("internal_direct_product") is True
        and rev3.get("weak_action_component_count")==1
        and rev3.get("weak_action_component_sizes")==[8]
    )

    reset_profiles=resets.get("class_profiles",[])
    G["M6_three_independent_irreversible_idempotent_classes_form_direct_monoid"]=(
        resets.get("status")=="VERIFIED"
        and resets.get("classification")=="DERIVED_DIRECT_MONOID_COMPLEMENTARITY"
        and len(reset_profiles)==3
        and all(
            p.get("order")==2
            and p.get("unit_count")==1
            and p.get("all_elements_units") is False
            and p.get("rank_spectrum")==[4,8]
            and p.get("minimum_rank")==4
            and p.get("nonidentity_idempotent_count")==1
            and p.get("rank_behavior")=="PARTIAL_RANK_LOSS"
            for p in reset_profiles
        )
        and resets.get("full_profile",{}).get("order")==8
        and resets.get("full_profile",{}).get("rank_spectrum")==[1,2,4,8]
        and resets.get("internal_direct_product") is True
        and resets.get("weak_action_component_count")==1
    )

    mixed_profiles=mixed.get("class_profiles",[])
    G["M7_reversible_and_mixed_irreversible_classes_can_still_be_independent"]=(
        mixed.get("status")=="VERIFIED"
        and mixed.get("classification")=="DERIVED_DIRECT_MONOID_COMPLEMENTARITY"
        and len(mixed_profiles)==2
        and mixed_profiles[0].get("order")==2
        and mixed_profiles[0].get("all_elements_units") is True
        and mixed_profiles[1].get("order")==8
        and mixed_profiles[1].get("unit_count")==4
        and mixed.get("full_profile",{}).get("order")==16
        and mixed.get("internal_direct_product") is True
        and mixed.get("pairwise_commuting") is True
        and mixed.get("weak_action_component_count")==1
    )

    mp=mixed_profiles[1] if len(mixed_profiles)>1 else {}
    G["M8_mixed_class_rank_structure_is_derived_from_closure"]=(
        mp.get("rank_spectrum")==[2,8]
        and mp.get("minimum_rank")==2
        and mp.get("all_elements_units") is False
        and mp.get("nonidentity_idempotent_count")==4
        and mp.get("rank_behavior")=="PARTIAL_RANK_LOSS"
    )

    G["M9_noncommuting_flip_reset_control_blocks_false_decomposition"]=(
        coupled.get("status")=="VERIFIED"
        and coupled.get("classification")=="COUPLED_TRANSFORMATION_MONOID"
        and [p.get("order") for p in coupled.get("class_profiles",[])]==[2,2]
        and coupled.get("full_profile",{}).get("order")==4
        and coupled.get("pairwise_commuting") is False
        and coupled.get("pairwise_identity_intersections") is True
        and coupled.get("class_order_product")==4
        and coupled.get("multiplication_image_size")==4
        and coupled.get("unique_product_coordinates") is True
        and coupled.get("multiplication_image_spans_full_monoid") is True
        and coupled.get("internal_direct_product") is False
    )

    G["M10_opaque_state_relabelling_preserves_algebraic_profiles"]=all(
        summary(results[kind][str(v)])==summary(results[kind]["0"])
        for kind in KINDS for v in range(3)
    )

    G["M11_consequence_label_relabelling_preserves_algebraic_profiles"]=all(
        summary(relabelled[kind])==summary(results[kind]["0"])
        for kind in KINDS
    )

    two_rows={(r.state,r.action,r.after,r.consequence) for r in WORLDS[("reversible_two_class",0)].rows}
    three_prefix={
        (r.state,r.action,r.after,r.consequence)
        for r in WORLDS[("reversible_three_class",0)].rows
        if r.action<2
    }
    G["M12_removing_third_reversible_class_restores_underresolved_algebra"]=(
        two_rows==three_prefix
        and rev2.get("classification")=="UNDERRESOLVED_MULTIPLE_ACTION_COMPONENTS"
        and rev3.get("classification")=="DERIVED_DIRECT_MONOID_COMPLEMENTARITY"
        and rev2.get("full_profile",{}).get("order")==4
        and rev3.get("full_profile",{}).get("order")==8
    )

    multi=(
        "reversible_two_class","reversible_three_class","reset_three_class",
        "mixed_two_class","coupled_flip_reset",
    )
    G["M13_one_class_bound_preserves_controls_and_rejects_multi_class_worlds"]=(
        one_class_bound["reversible_one_class"].get("status")=="VERIFIED"
        and one_class_bound["collapse_chain_one_class"].get("status")=="VERIFIED"
        and all(
            one_class_bound[kind].get("status")=="CERTIFIED_ACTION_CLASS_BOUND_INADEQUACY"
            and one_class_bound[kind].get("algebra_steps")==0
            for kind in multi
        )
    )

    G["M14_unknown_authority_and_verifier_ablation_authorize_no_algebraic_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("algebra_steps")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    G["M15_authority_does_not_require_bijective_actions"]=(
        "invalid_nonbijective" not in source
        and "sorted(images)" not in source
        and chain.get("status")=="VERIFIED"
        and resets.get("status")=="VERIFIED"
        and mixed.get("status")=="VERIFIED"
    )

    forbidden=(
        "reversible_one_class","collapse_chain_one_class",
        "reversible_two_class","reversible_three_class","reset_three_class",
        "mixed_two_class","coupled_flip_reset",
        "hidden","graph","edge","site","channel",
    )
    G["M16_hidden_challenge_and_old_topology_vocabulary_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"finite_transformation_monoid_genesis_v44",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":relabelled,
        "one_class_bound":one_class_bound,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_REVERSIBILITY_AND_IRREVERSIBILITY_GENESIS_FROM_FINITE_TRANSFORMATION_CLOSURE"
        if evidence["full_pass"] else
        "FINITE_TRANSFORMATION_MONOID_V44_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
