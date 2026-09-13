from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import KINDS,WORLDS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="bb03759eb9cd753799df1b08e262c5e07f89a60b"

def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def algebra_summary(r):
    return {
        k:r.get(k)
        for k in (
            "status","action_classes","class_count","class_group_orders",
            "full_group_order","full_state_orbit_count","full_state_orbit_sizes",
            "pairwise_commuting","pairwise_trivial_intersections",
            "class_group_order_product","direct_order_match",
            "regular_transitive_action","carriers","classification",
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
    nover=k.synthesize(WORLDS[("three_class",0)],verification_enabled=False)

    one=results["one_class"]["0"]
    two=results["two_class"]["0"]
    three=results["three_class"]["0"]
    two4=results["two_by_four"]["0"]
    coupled=results["coupled_order8"]["0"]

    G={}
    G["A1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["A2_one_class_stays_undecomposed_without_carriers"]=(
        one.get("status")=="VERIFIED"
        and one.get("classification")=="UNDECOMPOSED_SINGLE_CLASS"
        and one.get("class_count")==1
        and one.get("class_group_orders")==[8]
        and one.get("full_group_order")==8
        and one.get("full_state_orbit_count")==1
        and one.get("carriers")==[]
    )

    G["A3_two_class_system_is_algebraically_underresolved"]=(
        two.get("status")=="VERIFIED"
        and two.get("classification")=="UNDERRESOLVED_MULTIPLE_STATE_ORBITS"
        and two.get("class_group_orders")==[2,2]
        and two.get("full_group_order")==4
        and two.get("full_state_orbit_count")==2
        and two.get("full_state_orbit_sizes")==[4,4]
        and two.get("pairwise_commuting") is True
        and two.get("pairwise_trivial_intersections") is True
        and two.get("direct_order_match") is True
        and two.get("regular_transitive_action") is False
    )

    G["A4_two_class_carriers_preserve_residual_multiplicity"]=(
        len(two.get("carriers",[]))==2
        and all(
            c.get("status")=="DERIVED"
            and c.get("class_group_order")==2
            and c.get("other_group_order")==2
            and c.get("orbit_block_count")==4
            and c.get("orbit_block_sizes")==[2,2,2,2]
            and c.get("induced_group_order")==2
            and c.get("induced_orbit_count")==2
            and c.get("induced_orbit_size")==2
            for c in two.get("carriers",[])
        )
    )

    G["A5_third_class_yields_direct_complementarity_from_group_algebra"]=(
        three.get("status")=="VERIFIED"
        and three.get("classification")=="DERIVED_DIRECT_COMPLEMENTARITY"
        and three.get("class_group_orders")==[2,2,2]
        and three.get("full_group_order")==8
        and three.get("full_state_orbit_count")==1
        and three.get("full_state_orbit_sizes")==[8]
        and three.get("pairwise_commuting") is True
        and three.get("pairwise_trivial_intersections") is True
        and three.get("class_group_order_product")==8
        and three.get("direct_order_match") is True
        and three.get("regular_transitive_action") is True
    )

    G["A6_three_full_carriers_have_derived_binary_degrees"]=(
        len(three.get("carriers",[]))==3
        and all(
            c.get("status")=="DERIVED"
            and c.get("class_group_order")==2
            and c.get("other_group_order")==4
            and c.get("orbit_block_count")==2
            and c.get("orbit_block_sizes")==[4,4]
            and c.get("induced_group_order")==2
            and c.get("induced_orbit_count")==1
            and c.get("induced_orbit_size")==2
            for c in three.get("carriers",[])
        )
    )

    carriers24=two4.get("carriers",[])
    degrees24=sorted(
        (c.get("class_group_order"),c.get("induced_orbit_size"))
        for c in carriers24 if c.get("status")=="DERIVED"
    )
    G["A7_independent_two_by_four_action_algebra_derives_degrees_two_and_four"]=(
        two4.get("status")=="VERIFIED"
        and two4.get("classification")=="DERIVED_DIRECT_COMPLEMENTARITY"
        and two4.get("class_group_orders")==[2,4]
        and two4.get("full_group_order")==8
        and two4.get("full_state_orbit_count")==1
        and two4.get("regular_transitive_action") is True
        and degrees24==[(2,2),(4,4)]
    )

    G["A8_noncommuting_order8_control_is_not_misclassified_as_independent"]=(
        coupled.get("status")=="VERIFIED"
        and coupled.get("classification")=="COUPLED_ACTION_ALGEBRA"
        and coupled.get("class_group_orders")==[4,2]
        and coupled.get("full_group_order")==8
        and coupled.get("full_state_orbit_count")==1
        and coupled.get("pairwise_commuting") is False
        and coupled.get("pairwise_trivial_intersections") is True
        and coupled.get("class_group_order_product")==8
        and coupled.get("direct_order_match") is True
        and coupled.get("regular_transitive_action") is True
    )

    G["A9_coupled_control_exposes_nonnormal_carrier_obstruction"]=any(
        c.get("status")=="COUPLED_NONNORMAL_ACTION"
        for c in coupled.get("carriers",[])
    )

    G["A10_opaque_state_relabelling_preserves_all_algebraic_invariants"]=all(
        algebra_summary(results[kind][str(v)])==algebra_summary(results[kind]["0"])
        for kind in KINDS for v in range(3)
    )

    G["A11_consequence_label_relabelling_preserves_all_algebraic_invariants"]=all(
        algebra_summary(relabelled[kind])==algebra_summary(results[kind]["0"])
        for kind in KINDS
    )

    two_rows={(r.state,r.action,r.after,r.consequence) for r in WORLDS[("two_class",0)].rows}
    three_prefix={
        (r.state,r.action,r.after,r.consequence)
        for r in WORLDS[("three_class",0)].rows
        if r.action<4
    }
    G["A12_removing_third_class_restores_underresolved_two_class_algebra"]=(
        two_rows==three_prefix
        and two.get("classification")=="UNDERRESOLVED_MULTIPLE_STATE_ORBITS"
        and three.get("classification")=="DERIVED_DIRECT_COMPLEMENTARITY"
        and two.get("full_group_order")==4
        and three.get("full_group_order")==8
    )

    G["A13_one_class_bound_preserves_control_and_rejects_multiclass_worlds"]=(
        one_class_bound["one_class"].get("status")=="VERIFIED"
        and all(
            one_class_bound[kind].get("status")=="CERTIFIED_ACTION_CLASS_BOUND_INADEQUACY"
            for kind in ("two_class","three_class","two_by_four","coupled_order8")
        )
    )

    G["A14_unknown_authority_and_verifier_ablation_authorize_no_algebraic_growth"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("algebra_steps")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden_search=(
        "set_partitions","partition","equivalence","quotient",
        "factorization","coordinate","cartesian"
    )
    G["A15_no_partition_quotient_or_coordinate_search_language_in_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden_search
    )

    forbidden_hidden=(
        "one_class","two_class","three_class","two_by_four","coupled_order8",
        "hidden","graph","edge","site","channel","d8"
    )
    G["A16_hidden_generator_and_old_topology_vocabulary_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden_hidden
    )

    evidence={
        "experiment":"transformation_algebra_genesis_v43",
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
        "VERIFIED_TRANSFORMATION_ALGEBRA_DERIVED_COMPONENT_GENESIS"
        if evidence["full_pass"] else
        "TRANSFORMATION_ALGEBRA_V43_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
