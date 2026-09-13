from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent

from kernel import Kernel
from challenge_pack import (
    KINDS,WORLDS,RELABELLED,INCOMPLETE,
    TOKEN_PERMS,UNIVERSE,constant_single_open,
)

SCIENTIFIC_FREEZE_COMMIT="9156211c3da2bb120aab513eef83ae303fa83556"

def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def prefix_words():
    return Kernel.words(2,3)

def history_equivalence(result):
    return {
        tuple(h):int(c)
        for h,c in zip(prefix_words(),result["history_class_labels"])
    }

def same_equivalence_under_token_perm(base,other,perm):
    a=history_equivalence(base)
    b=history_equivalence(other)
    hs=list(a)
    image={h:tuple(int(perm[t]) for t in h) for h in hs}
    for i,h in enumerate(hs):
        for g in hs[:i]:
            if (a[h]==a[g])!=(b[image[h]]==b[image[g]]):
                return False
    return True

def token_classes(result):
    return tuple(tuple(int(x) for x in row) for row in result.get("token_classes",[]))

def transform_token_classes(classes,perm):
    return tuple(sorted(
        (
            tuple(sorted(int(perm[t]) for t in cls))
            for cls in classes
        ),
        key=lambda cls:cls[0],
    ))

def witness_signature(result):
    rows=[]
    for key in ("witness_a","witness_b"):
        if key not in result:
            continue
        w=result[key]
        rows.append((
            w.get("law_kind"),
            w.get("floor_status"),
            w.get("floor_future_depth"),
            w.get("state_count"),
            tuple(tuple(int(x) for x in c) for c in w.get("token_classes",[])),
        ))
    return tuple(sorted(rows))

def all_history_samples_present(world):
    observed={tuple(s.tokens) for s in world.samples}
    return observed==set(UNIVERSE)

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed_sha={
        name:git_blob_sha(HERE/name)
        for name in freeze["scientific_core_paths"]
    }
    freeze_ok=observed_sha==freeze["git_blob_sha"]

    k=Kernel()
    results={
        kind:{str(v):k.synthesize(WORLDS[(kind,v)]) for v in range(2)}
        for kind in KINDS
    }
    relabelled={kind:k.synthesize(RELABELLED[kind]) for kind in KINDS}

    closure_ablations=[]
    for i,h in enumerate(UNIVERSE):
        r=k.synthesize(constant_single_open(i))
        closure_ablations.append({
            "index":i,
            "history":list(h),
            "length":len(h),
            "result":r,
        })

    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS[("parity_closed",0)],verification_enabled=False)

    parity_open=results["parity_open"]["0"]
    parity_repeat=results["parity_repeated_open"]["0"]
    parity_closed=results["parity_closed"]["0"]
    future_open=results["future_open"]["0"]
    future_closed=results["future_closed"]["0"]
    branching=results["branching_open"]["0"]
    constant=results["constant_closed"]["0"]

    G={}

    G["F1_frozen_scientific_core_byte_identical"]=freeze_ok

    G["F2_positive_only_parity_has_explicit_two_state_vs_one_state_completion_witnesses"]=(
        parity_open.get("status")=="UNKNOWN_IDENTIFIABILITY"
        and parity_open.get("reason")=="COMPATIBLE_COMPLETIONS_DISAGREE"
        and parity_open.get("completion_count")==2**63
        and parity_open.get("tested_completions")==2
        and witness_signature(parity_open)==(
            ("BRANCHING_SUPPORT","FLOOR",0,1,((0,1),)),
            ("DETERMINISTIC_SUPPORT","FLOOR",0,2,((0,),(1,))),
        )
    )

    G["F3_repetition_does_not_turn_non_observation_into_negative_evidence"]=(
        parity_repeat.get("status")=="UNKNOWN_IDENTIFIABILITY"
        and parity_repeat.get("completion_count")==parity_open.get("completion_count")
        and parity_repeat.get("tested_completions")==2
        and witness_signature(parity_repeat)==witness_signature(parity_open)
        and len(WORLDS[("parity_repeated_open",0)].samples)
            > len(WORLDS[("parity_open",0)].samples)
    )

    G["F4_closing_same_parity_evidence_identifies_two_state_deterministic_floor"]=(
        parity_closed.get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR"
        and parity_closed.get("completion_count")==1
        and parity_closed.get("tested_completions")==1
        and parity_closed.get("floor_future_depth")==0
        and parity_closed.get("state_count")==2
        and token_classes(parity_closed)==((0,),(1,))
        and parity_closed.get("determinism_identifiable") is True
        and parity_closed.get("law_kinds_consistent_with_evidence")==["DETERMINISTIC_SUPPORT"]
    )

    G["F5_closed_future_dependent_evidence_identifies_four_state_depth_one_floor"]=(
        future_closed.get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR"
        and future_closed.get("completion_count")==1
        and future_closed.get("floor_future_depth")==1
        and future_closed.get("state_count")==4
        and token_classes(future_closed)==((0,),(1,))
        and future_closed.get("determinism_identifiable") is True
    )

    G["F6_same_future_dependent_positive_outcomes_open_are_nonidentifiable"]=(
        future_open.get("status")=="UNKNOWN_IDENTIFIABILITY"
        and future_open.get("completion_count")==2**63
        and witness_signature(future_open)==(
            ("BRANCHING_SUPPORT","FLOOR",0,1,((0,1),)),
            ("DETERMINISTIC_SUPPORT","FLOOR",1,4,((0,),(1,))),
        )
    )

    G["F7_observed_conflict_forces_local_branching_but_not_global_floor"]=(
        branching.get("status")=="UNKNOWN_IDENTIFIABILITY"
        and branching.get("forced_branching_histories")==[[]]
        and branching.get("completion_count")==2**62
        and all(
            branching[w].get("law_kind")=="BRANCHING_SUPPORT"
            for w in ("witness_a","witness_b")
        )
        and branching["witness_a"].get("state_count")!=branching["witness_b"].get("state_count")
    )

    G["F8_closed_constant_evidence_identifies_one_state_one_token_class"]=(
        constant.get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR"
        and constant.get("completion_count")==1
        and constant.get("floor_future_depth")==0
        and constant.get("state_count")==1
        and token_classes(constant)==((0,1),)
        and constant.get("determinism_identifiable") is True
    )

    critical=[
        row for row in closure_ablations
        if row["result"].get("status")=="UNKNOWN_IDENTIFIABILITY"
    ]
    noncritical=[
        row for row in closure_ablations
        if row["result"].get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR"
    ]
    G["F9_closure_criticality_matches_exact_predictive_horizon"]=(
        len(critical)==31
        and {row["length"] for row in critical}=={0,1,2,3,4}
        and all(row["length"]<=4 for row in critical)
        and len(noncritical)==32
        and {row["length"] for row in noncritical}=={5}
        and all(
            row["result"].get("state_count")==1
            and row["result"].get("floor_future_depth")==0
            and row["result"].get("determinism_identifiable") is False
            and set(row["result"].get("law_kinds_consistent_with_evidence",[]))
                =={"DETERMINISTIC_SUPPORT","BRANCHING_SUPPORT"}
            for row in noncritical
        )
    )

    token_equivariant=True
    for kind in KINDS:
        base=results[kind]["0"]
        other=results[kind]["1"]
        perm=TOKEN_PERMS[1]
        if base.get("status")!=other.get("status"):
            token_equivariant=False
            break
        if base.get("completion_count")!=other.get("completion_count"):
            token_equivariant=False
            break

        if base.get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR":
            if not (
                base.get("floor_future_depth")==other.get("floor_future_depth")
                and base.get("state_count")==other.get("state_count")
                and same_equivalence_under_token_perm(base,other,perm)
                and token_classes(other)==transform_token_classes(token_classes(base),perm)
            ):
                token_equivariant=False
                break
        elif base.get("status")=="UNKNOWN_IDENTIFIABILITY":
            # Compare witness law/floor sizes; token names may permute.
            sb=sorted(
                (base[w]["law_kind"],base[w]["floor_status"],base[w].get("floor_future_depth"),base[w].get("state_count"))
                for w in ("witness_a","witness_b")
            )
            so=sorted(
                (other[w]["law_kind"],other[w]["floor_status"],other[w].get("floor_future_depth"),other[w].get("state_count"))
                for w in ("witness_a","witness_b")
            )
            if sb!=so:
                token_equivariant=False
                break

    G["F10_opaque_encounter_token_relabelling_is_epistemically_equivariant"]=token_equivariant

    consequence_relabel_ok=True
    for kind in KINDS:
        base=results[kind]["0"]
        rel=relabelled[kind]
        if base.get("status")!=rel.get("status") or base.get("completion_count")!=rel.get("completion_count"):
            consequence_relabel_ok=False
            break
        if base.get("status")=="VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR":
            if not (
                base.get("floor_future_depth")==rel.get("floor_future_depth")
                and base.get("state_count")==rel.get("state_count")
                and base.get("history_class_labels")==rel.get("history_class_labels")
                and base.get("transition_maps")==rel.get("transition_maps")
                and base.get("token_classes")==rel.get("token_classes")
                and base.get("determinism_identifiable")==rel.get("determinism_identifiable")
            ):
                consequence_relabel_ok=False
                break
        elif base.get("status")=="UNKNOWN_IDENTIFIABILITY":
            sb=sorted(
                (base[w]["law_kind"],base[w]["floor_status"],base[w].get("floor_future_depth"),base[w].get("state_count"))
                for w in ("witness_a","witness_b")
            )
            sr=sorted(
                (rel[w]["law_kind"],rel[w]["floor_status"],rel[w].get("floor_future_depth"),rel[w].get("state_count"))
                for w in ("witness_a","witness_b")
            )
            if sb!=sr:
                consequence_relabel_ok=False
                break

    G["F11_consequence_token_relabelling_preserves_epistemic_structure"]=consequence_relabel_ok

    G["F12_every_bounded_history_can_be_observed_and_ontology_still_be_unknown"]=(
        all_history_samples_present(WORLDS[("parity_open",0)])
        and all_history_samples_present(WORLDS[("future_open",0)])
        and parity_open.get("status")=="UNKNOWN_IDENTIFIABILITY"
        and future_open.get("status")=="UNKNOWN_IDENTIFIABILITY"
    )

    G["F13_closed_singleton_support_identifies_determinism_open_repetition_does_not"]=(
        parity_closed.get("determinism_identifiable") is True
        and parity_repeat.get("status")=="UNKNOWN_IDENTIFIABILITY"
        and {parity_repeat[w]["law_kind"] for w in ("witness_a","witness_b")}
            =={"DETERMINISTIC_SUPPORT","BRANCHING_SUPPORT"}
    )

    G["F14_positive_conflict_can_force_branching_but_positive_agreement_cannot_force_no_branch"]=(
        branching.get("forced_branching_histories")==[[]]
        and all(
            branching[w]["law_kind"]=="BRANCHING_SUPPORT"
            for w in ("witness_a","witness_b")
        )
        and parity_open.get("forced_branching_histories")==[]
        and {parity_open[w]["law_kind"] for w in ("witness_a","witness_b")}
            =={"DETERMINISTIC_SUPPORT","BRANCHING_SUPPORT"}
    )

    G["F15_unknown_authority_and_verifier_ablation_authorize_no_epistemic_claim"]=(
        incomplete.get("status")=="UNKNOWN_AUTHORITY"
        and nover.get("status")=="UNKNOWN_NO_VERIFIER"
        and nover.get("tested_completions")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "parity_open","future_open","constant_closed","branching_open",
        "hidden","probability","prior","confidence","p_value","p-value",
        "graph","edge","site","channel","cartesian","factorization","set_partitions",
    )
    G["F16_no_hidden_generator_statistical_prior_or_candidate_ontology_catalogue_in_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None
        for tok in forbidden
    )

    evidence={
        "experiment":"epistemic_floor_v47b",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed_sha,
        "results":results,
        "consequence_relabelled_results":relabelled,
        "constant_single_closure_ablations":closure_ablations,
        "closure_critical_count":len(critical),
        "closure_noncritical_count":len(noncritical),
        "closure_critical_lengths":sorted({row["length"] for row in critical}),
        "closure_noncritical_lengths":sorted({row["length"] for row in noncritical}),
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_EPISTEMIC_FLOOR_AND_IRREDUCIBLE_UNKNOWN_FROM_FINITE_POSITIVE_EVIDENCE"
        if evidence["full_pass"] else
        "EPISTEMIC_FLOOR_V47B_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
