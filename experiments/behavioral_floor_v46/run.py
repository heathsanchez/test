from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import (
    KINDS,WORLDS,RELABELLED,INCOMPLETE,
    TOKEN_PERMS,
    EXPECTED_FLOOR_DEPTH,EXPECTED_STATE_COUNT,
    EXPECTED_TOKEN_CLASS_COUNT,EXPECTED_TOKEN_CLASSES,
    HIDDEN_GENERATOR_STATE_COUNT,
    transform_token_classes,
)

SCIENTIFIC_FREEZE_COMMIT="8125a1d1e2d4d0f57f55e636b68405461a936cfb"

def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def history_label_map(result):
    return {
        tuple(h):int(c)
        for h,c in zip(result["prefixes"],result["history_class_labels"])
    }

def same_history_equivalence(base,other,perm=None):
    a=history_label_map(base)
    b=history_label_map(other)
    histories=list(a)
    if perm is None:
        image={h:h for h in histories}
    else:
        image={
            h:tuple(int(perm[t]) for t in h)
            for h in histories
        }
    for i,h in enumerate(histories):
        ih=image[h]
        for g in histories[:i]:
            ig=image[g]
            if (a[h]==a[g])!=(b[ih]==b[ig]):
                return False
    return True

def token_classes(result):
    return tuple(tuple(int(x) for x in row) for row in result["token_classes"])

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

    delayed_horizon={
        str(bound):k.synthesize(
            WORLDS[("delayed_four",0)],
            maximum_future_depth_override=bound,
        )
        for bound in (1,2,3,4)
    }

    state_bound={
        kind:k.synthesize(WORLDS[(kind,0)],maximum_state_count=1)
        for kind in KINDS
    }

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("delayed_four",0)],verification_enabled=False)

    constant=results["constant"]["0"]
    parity=results["parity"]["0"]
    future4=results["future_four"]["0"]
    delayed=results["delayed_four"]["0"]
    nonmin=results["nonminimal_six"]["0"]

    G={}
    G["B1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["B2_constant_consequence_collapses_histories_and_tokens_at_depth_zero"]=(
        constant.get("status")=="VERIFIED"
        and constant.get("classification")=="BOUNDED_BEHAVIORAL_FLOOR"
        and constant.get("floor_future_depth")==0
        and constant.get("state_count")==1
        and constant.get("token_class_count")==1
        and token_classes(constant)==((0,1,2),)
        and constant.get("right_congruence") is True
        and constant.get("stable_to_next_horizon") is True
        and constant.get("pairwise_distinguishing_witness_count")==0
    )

    G["B3_parity_derives_two_states_and_merges_redundant_encounter_tokens"]=(
        parity.get("status")=="VERIFIED"
        and parity.get("floor_future_depth")==0
        and parity.get("state_count")==2
        and parity.get("token_class_count")==2
        and token_classes(parity)==((0,),(1,2))
        and parity.get("pairwise_distinguishability_complete") is True
    )

    G["B4_future_dependent_four_state_world_refines_until_right_congruence"]=(
        future4.get("status")=="VERIFIED"
        and future4.get("floor_future_depth")==1
        and future4.get("state_count")==4
        and future4.get("tested_future_depths")==2
        and future4["tested"][0]["future_depth"]==0
        and future4["tested"][0]["state_count"]==2
        and future4["tested"][0]["right_congruence"] is False
        and future4["tested"][1]["future_depth"]==1
        and future4["tested"][1]["state_count"]==4
        and future4["tested"][1]["right_congruence"] is True
        and future4["tested"][1]["stable_to_next_horizon"] is True
    )

    G["B5_delayed_world_self_selects_two_step_predictive_depth"]=(
        delayed.get("status")=="VERIFIED"
        and delayed.get("floor_future_depth")==2
        and delayed.get("state_count")==4
        and [
            (r["future_depth"],r["state_count"],r["right_congruence"],r["stable_to_next_horizon"])
            for r in delayed["tested"]
        ]==[
            (0,2,False,False),
            (1,3,False,False),
            (2,4,True,True),
        ]
    )

    G["B6_insufficient_future_authority_stays_unknown_until_floor_is_witnessed"]=(
        delayed_horizon["1"].get("status")=="UNKNOWN_FUTURE_HORIZON_INSUFFICIENT"
        and delayed_horizon["2"].get("status")=="UNKNOWN_FUTURE_HORIZON_INSUFFICIENT"
        and delayed_horizon["3"].get("status")=="VERIFIED"
        and delayed_horizon["3"].get("floor_future_depth")==2
        and delayed_horizon["3"].get("state_count")==4
        and delayed_horizon["4"].get("status")=="VERIFIED"
        and delayed_horizon["4"].get("floor_future_depth")==2
    )

    G["B7_every_delayed_floor_state_pair_has_explicit_future_witness"]=(
        delayed.get("pairwise_distinguishability_complete") is True
        and delayed.get("pairwise_distinguishing_witness_count")==6
        and delayed.get("maximum_minimal_distinguishing_depth")==2
        and all(
            len(w["distinguishing_suffix"])==w["suffix_length"]
            and w["consequence_a"]!=w["consequence_b"]
            for w in delayed["pairwise_distinguishing_witnesses"]
        )
    )

    G["B8_six_state_hidden_generator_contracts_to_four_behavioral_states"]=(
        HIDDEN_GENERATOR_STATE_COUNT["nonminimal_six"]==6
        and nonmin.get("status")=="VERIFIED"
        and nonmin.get("floor_future_depth")==1
        and nonmin.get("state_count")==4
        and nonmin.get("state_count")<HIDDEN_GENERATOR_STATE_COUNT["nonminimal_six"]
    )

    G["B9_contracted_four_state_floor_is_right_congruent_and_pairwise_necessary"]=(
        nonmin.get("right_congruence") is True
        and nonmin.get("stable_to_next_horizon") is True
        and nonmin.get("pairwise_distinguishability_complete") is True
        and nonmin.get("pairwise_distinguishing_witness_count")==6
        and nonmin.get("maximum_minimal_distinguishing_depth")==1
    )

    G["B10_encounter_token_distinctions_are_derived_not_assumed"]=all(
        results[kind]["0"].get("token_class_count")==EXPECTED_TOKEN_CLASS_COUNT[kind]
        and token_classes(results[kind]["0"])==EXPECTED_TOKEN_CLASSES[kind]
        for kind in KINDS
    )

    equivariant=True
    for kind in KINDS:
        base=results[kind]["0"]
        for variant,perm in enumerate(TOKEN_PERMS):
            current=results[kind][str(variant)]
            expected_classes=transform_token_classes(
                EXPECTED_TOKEN_CLASSES[kind],perm
            )
            if not (
                current.get("status")=="VERIFIED"
                and current.get("floor_future_depth")==base.get("floor_future_depth")
                and current.get("state_count")==base.get("state_count")
                and current.get("token_class_count")==base.get("token_class_count")
                and token_classes(current)==expected_classes
                and same_history_equivalence(base,current,perm)
            ):
                equivariant=False
                break

    G["B11_opaque_encounter_token_relabelling_is_equivariant"]=equivariant

    G["B12_consequence_label_relabelling_preserves_behavioral_floor"]=all(
        relabelled[kind].get("status")=="VERIFIED"
        and relabelled[kind].get("floor_future_depth")==results[kind]["0"].get("floor_future_depth")
        and relabelled[kind].get("state_count")==results[kind]["0"].get("state_count")
        and token_classes(relabelled[kind])==token_classes(results[kind]["0"])
        and relabelled[kind].get("transition_maps")==results[kind]["0"].get("transition_maps")
        and relabelled[kind].get("history_class_labels")==results[kind]["0"].get("history_class_labels")
        for kind in KINDS
    )

    G["B13_one_state_bound_preserves_constant_and_is_inadequate_for_every_nontrivial_floor"]=(
        state_bound["constant"].get("status")=="VERIFIED"
        and state_bound["constant"].get("state_count")==1
        and all(
            state_bound[kind].get("status")=="CERTIFIED_STATE_BOUND_INADEQUACY"
            and state_bound[kind].get("derived_state_count")==EXPECTED_STATE_COUNT[kind]
            and len(state_bound[kind].get("pairwise_distinguishing_witnesses",[]))
                == EXPECTED_STATE_COUNT[kind]*(EXPECTED_STATE_COUNT[kind]-1)//2
            for kind in KINDS if kind!="constant"
        )
    )

    G["B14_unknown_authority_and_verifier_ablation_authorize_no_floor"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_future_depths")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "constant","parity","future_four","delayed_four","nonminimal_six",
        "hidden","graph","edge","site","channel","cartesian","factorization",
        "set_partitions",
    )
    G["B15_hidden_generator_and_candidate_ontology_catalogues_absent_from_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    G["B16_every_retained_state_distinction_has_verified_future_consequence_witness"]=all(
        result.get("status")=="VERIFIED"
        and result.get("classification")=="BOUNDED_BEHAVIORAL_FLOOR"
        and result.get("state_count")==EXPECTED_STATE_COUNT[kind]
        and result.get("floor_future_depth")==EXPECTED_FLOOR_DEPTH[kind]
        and result.get("pairwise_distinguishability_complete") is True
        for kind,result in ((kind,results[kind]["0"]) for kind in KINDS)
    )

    evidence={
        "experiment":"behavioral_floor_v46",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "hidden_generator_state_count":HIDDEN_GENERATOR_STATE_COUNT,
        "expected_floor_depth":EXPECTED_FLOOR_DEPTH,
        "results":results,
        "relabelled_results":relabelled,
        "delayed_horizon_ablation":delayed_horizon,
        "one_state_bound_ablation":state_bound,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_BEHAVIORAL_FLOOR_FROM_FUTURE_CONSEQUENTIAL_DISTINGUISHABILITY"
        if evidence["full_pass"] else
        "BEHAVIORAL_FLOOR_V46_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
