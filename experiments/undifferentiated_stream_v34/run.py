from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import AXES,VARIANTS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="2d3c9635cc272425833e967c3825b9a9221b513f"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def safe(x):
    if hasattr(x,"data"): return safe(x.data())
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items() if not str(k).startswith("_")}
    if isinstance(x,(list,tuple)): return [safe(v) for v in x]
    return x

def graph_shape(result):
    states=result["machine"]["states"]
    root=int(result["machine"]["root"])
    memo={}
    def rec(s):
        if s in memo:return memo[s]
        row=states[s]
        if row[0]=="OUT":
            ans=("OUT",)
        else:
            ans=("STEP",rec(int(row[1])),rec(int(row[2])))
        memo[s]=ans
        return ans
    return rec(root)

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    frozen_ok=observed==freeze["git_blob_sha"]

    results={}
    exact={}
    raw={}
    for variant,cases in VARIANTS.items():
        k=Kernel()
        rows={}
        checks={}
        for case in cases:
            r=k.synthesize(case.world)
            rows[case.axis]=safe(r)
            checks[case.axis]=(r.get("status")=="VERIFIED" and r.get("exact_replay") is True)
            raw[(variant,case.axis)]=r
        results[str(variant)]=rows
        exact[str(variant)]=checks

    rel_results={}
    for case in RELABELLED:
        r=Kernel().synthesize(case.world)
        rel_results[case.axis]=safe(r)
        raw[("rel",case.axis)]=r

    incomplete=Kernel().synthesize(INCOMPLETE)
    no_verifier=Kernel().synthesize(VARIANTS[0][6].world,verification_enabled=False)

    evidence={
        "experiment":"undifferentiated_stream_residual_machine_v34",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":rel_results,
        "exact_checks":exact,
        "incomplete":safe(incomplete),
        "no_verifier":safe(no_verifier),
        "gates":{},
    }
    G=evidence["gates"]
    G["S1_frozen_scientific_core_byte_identical"]=frozen_ok
    G["S2_exact_replay_all_worlds_all_stream_permutations"]=all(all(v.values()) for v in exact.values())

    r0=raw[(0,"constant")]
    G["S3_constant_consequence_contracts_to_single_output_state"]=(
        r0["state_count"]==1 and r0["terminal_count"]==1
        and r0["neutral_transition_count"]==0 and r0["branching_transition_count"]==0
    )

    e0=raw[(0,"early_event")]
    G["S4_first_event_reference_is_one_branch_plus_two_terminals"]=(
        e0["state_count"]==3 and e0["terminal_count"]==2
        and e0["branching_transition_count"]==1 and e0["neutral_transition_count"]==0
    )

    e1=raw[(1,"early_event")]
    d0=raw[(0,"delayed_event")]
    d1=raw[(1,"delayed_event")]
    G["S5_reference_moves_are_realized_as_transition_persistence_not_index_instruction"]=(
        e1["neutral_transition_count"]==5
        and e1["branching_transition_count"]==1
        and d0["neutral_transition_count"]==3
        and d1["neutral_transition_count"]==0
    )

    xr=raw[(0,"xor_relation")]
    G["S6_two_event_boolean_relation_requires_internal_residual_memory"]=(
        xr["terminal_count"]==2 and xr["branching_transition_count"]==3
        and xr["state_count"]==5 and xr["exact_replay"] is True
    )

    p4=raw[(0,"pair4_relation")]
    G["S7_four_class_two_event_relation_constructs_four_terminal_machine"]=(
        p4["terminal_count"]==4 and p4["state_count"]==7
        and p4["branching_transition_count"]==3
    )

    t8=raw[(0,"triple8_relation")]
    G["S8_eight_class_three_event_relation_constructs_eight_terminal_machine"]=(
        t8["terminal_count"]==8 and t8["state_count"]==15
        and t8["branching_transition_count"]==7
    )

    c0,c1=raw[(0,"contextual")],raw[(1,"contextual")]
    i0,i2=raw[(0,"interventional")],raw[(2,"interventional")]
    G["S9_conditional_structures_reorganize_when_sources_move_in_stream"]=(
        graph_shape(c0)!=graph_shape(c1)
        and graph_shape(i0)!=graph_shape(i2)
    )

    dist=raw[(0,"distant_pair")]
    G["S10_widely_separated_relation_preserves_distinction_through_intervening_symbols"]=(
        dist["terminal_count"]==4 and dist["branching_transition_count"]==3
        and dist["neutral_transition_count"]>=10 and dist["state_count"]==17
    )

    con=raw[(0,"contraction")]
    G["S11_raw_128_stream_identity_contracts_to_three_state_consequence_machine"]=(
        con["state_count"]==3 and con["terminal_count"]==2 and 128/con["state_count"]>40
    )

    G["S12_consequence_label_relabelling_preserves_machine_graph_shape"]=all(
        graph_shape(raw[(0,axis)])==graph_shape(raw[("rel",axis)])
        for axis in AXES
    )

    G["S13_incomplete_encounter_authority_stays_unknown"]=incomplete.get("status")=="UNKNOWN_AUTHORITY"
    G["S14_verifier_ablation_authorizes_no_machine"]=(
        no_verifier.get("status")=="UNKNOWN_NO_VERIFIER" and no_verifier.get("state_count")==0
    )

    source=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text()).lower()
    forbidden=(
        "atom","read","bank","channel","history","joint","coordinate",
        "position_index","input_index","slot"
    )
    G["S15_no_named_input_variable_or_random_access_constructor_in_frozen_kernel"]=all(
        re.search(r"\b"+re.escape(tok)+r"\b",source) is None for tok in forbidden
    )

    all_state_forms=set()
    all_nonterminal_arity_ok=True
    for key,r in raw.items():
        if r.get("status")!="VERIFIED":continue
        for state in r["_machine"].states:
            all_state_forms.add(state[0])
            if state[0]=="STEP" and len(state)!=3:
                all_nonterminal_arity_ok=False
    G["S16_single_generic_step_is_only_executable_nonterminal_form"]=(
        all_state_forms=={"OUT","STEP"} and all_nonterminal_arity_ok
    )

    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_UNDIFFERENTIATED_STREAM_REFERENCE_PERSISTENCE_AND_RELATIONAL_RESIDUAL_GENESIS"
        if evidence["full_pass"] else
        "UNDIFFERENTIATED_STREAM_V34_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
