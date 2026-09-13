from __future__ import annotations
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent

from basis import PartialMachine, run_partial
from kernel import Kernel
from challenge_pack import WORLDS, CORRUPT, STAGES, heldout_rows, make_world

SCIENTIFIC_FREEZE_COMMIT = "ee59365d8ab26328edb8b4832bbff05af1b5e692"

def git_blob_sha(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def safe(x):
    if isinstance(x, dict):
        return {str(k): safe(v) for k,v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list,tuple)):
        return [safe(v) for v in x]
    return x

def machine_from_result(r: dict) -> PartialMachine:
    d = r["machine"]
    return PartialMachine(
        int(d["initial"]),
        tuple(int(x) for x in d["outputs"]),
        tuple(tuple(None if z is None else int(z) for z in row) for row in d["transitions"]),
        tuple(tuple(int(x) for x in sig) for sig in d["signatures"]),
    )

def edge_set(r: dict) -> set[tuple]:
    out = set()
    for e in r.get("warranted_edges",[]):
        out.add((
            tuple(int(x) for x in e["source_signature"]),
            int(e["symbol"]),
            tuple(int(x) for x in e["target_signature"]),
        ))
    return out

def exact_heldout(r: dict, rows) -> bool:
    if r.get("status") != "VERIFIED_STABLE":
        return False
    m = machine_from_result(r)
    for row in rows:
        y = run_partial(m, row.history)
        if y is None or int(y) != int(row.consequence):
            return False
    return True

def main() -> int:
    freeze = json.loads((HERE/"FREEZE.json").read_text())
    observed = {
        name: git_blob_sha(HERE/name)
        for name in freeze["scientific_core_paths"]
    }
    freeze_ok = observed == freeze["git_blob_sha"]

    kernel = Kernel()
    results = {}
    canonical = {}

    for world in WORLDS:
        r = kernel.synthesize(world)
        results[world.world_id] = safe(r)
        if r.get("status","").startswith("VERIFIED_"):
            canonical[world.world_id] = Kernel.canonical_structure(
                machine_from_result(r)
            )

    def R(kind: str, flip: int, stage: str) -> dict:
        return results[f"{kind}_flip{flip}_stage{stage}"]

    expected = {
        "triad": {
            "states":3,
            "A":(2,4,0,False,"VERIFIED_LOCAL"),
            "B":(3,3,0,True,"VERIFIED_CYCLE_CLOSED"),
            "C":(4,2,1,True,"VERIFIED_CYCLE_CLOSED"),
            "D":(5,1,2,True,"VERIFIED_CYCLE_CLOSED"),
            "E":(6,0,3,True,"VERIFIED_STABLE"),
        },
        "quartet": {
            "states":4,
            "A":(3,5,0,False,"VERIFIED_LOCAL"),
            "B":(4,4,0,True,"VERIFIED_CYCLE_CLOSED"),
            "C":(5,3,1,True,"VERIFIED_CYCLE_CLOSED"),
            "D":(6,2,2,True,"VERIFIED_CYCLE_CLOSED"),
            "E":(7,1,3,True,"VERIFIED_CYCLE_CLOSED"),
            "F":(8,0,4,True,"VERIFIED_STABLE"),
        },
    }

    shape_exact = {}
    for kind in expected:
        for flip in (0,1):
            for stage in STAGES[kind]:
                r = R(kind,flip,stage)
                w,u,ls,cyc,status = expected[kind][stage]
                shape_exact[f"{kind}_{flip}_{stage}"] = (
                    r.get("state_count") == expected[kind]["states"] and
                    r.get("distinguishing_horizon") == 1 and
                    r.get("warranted_transition_count") == w and
                    r.get("unresolved_transition_count") == u and
                    r.get("locally_stable_state_count") == ls and
                    r.get("spanning_warranted_cycle") is cyc and
                    r.get("status") == status
                )

    monotone = {}
    for kind in STAGES:
        for flip in (0,1):
            seq = STAGES[kind]
            ok = True
            for a,b in zip(seq,seq[1:]):
                if not edge_set(R(kind,flip,a)).issubset(edge_set(R(kind,flip,b))):
                    ok = False
                    break
            monotone[f"{kind}_{flip}"] = ok

    complement = {}
    for kind in STAGES:
        for stage in STAGES[kind]:
            a=R(kind,0,stage); b=R(kind,1,stage)
            complement[f"{kind}_{stage}"] = (
                a.get("status")==b.get("status") and
                a.get("state_count")==b.get("state_count") and
                a.get("warranted_transition_count")==b.get("warranted_transition_count") and
                a.get("unresolved_transition_count")==b.get("unresolved_transition_count") and
                a.get("locally_stable_state_count")==b.get("locally_stable_state_count") and
                a.get("spanning_warranted_cycle")==b.get("spanning_warranted_cycle") and
                canonical.get(f"{kind}_flip0_stage{stage}") ==
                canonical.get(f"{kind}_flip1_stage{stage}")
            )

    triad_transfer = {
        f: exact_heldout(R("triad",f,"E"), heldout_rows("triad",flip=f,max_depth=9))
        for f in (0,1)
    }
    quartet_transfer = {
        f: exact_heldout(R("quartet",f,"F"), heldout_rows("quartet",flip=f,max_depth=9))
        for f in (0,1)
    }

    unresolved_not_executable = {}
    for kind in STAGES:
        for flip in (0,1):
            for stage in STAGES[kind][:-1]:
                r=R(kind,flip,stage)
                m=machine_from_result(r)
                unresolved_not_executable[f"{kind}_{flip}_{stage}"] = (
                    r.get("stable_executable") is False and
                    any(z is None for row in m.transitions for z in row)
                )

    corrupt = kernel.synthesize(CORRUPT)
    nover = kernel.synthesize(make_world("triad","B",flip=0), verification_enabled=False)
    kernel_text = (HERE/"kernel.py").read_text().lower()
    forbidden = (
        "triad","quartet","ring3","ring4",
        "stagea","stageb","stagec","staged","stagef",
        "q0","q1","q2","q3",
        "1000","1010",
    )

    gates = {}
    gates["L1_frozen_scientific_core_byte_identical"] = freeze_ok
    gates["L2_minimum_residual_horizon_discovered_without_state_labels"] = all(
        R(kind,f,stage).get("distinguishing_horizon")==1
        for kind in STAGES for f in (0,1) for stage in STAGES[kind]
    )
    gates["L3_first_stage_has_multiple_warranted_and_unresolved_transitions"] = all(
        R(kind,f,"A").get("warranted_transition_count",0) >= 2 and
        R(kind,f,"A").get("unresolved_transition_count",0) >= 2
        for kind in STAGES for f in (0,1)
    )
    gates["L4_first_stage_does_not_claim_spanning_cycle"] = all(
        R(kind,f,"A").get("spanning_warranted_cycle") is False
        for kind in STAGES for f in (0,1)
    )
    gates["L5_one_local_authority_region_closes_cycle_before_whole_stability"] = all(
        R(kind,f,"B").get("spanning_warranted_cycle") is True and
        R(kind,f,"B").get("whole_machine_stable") is False
        for kind in STAGES for f in (0,1)
    )
    gates["L6_preclosure_edges_are_retained_after_cycle_closure"] = all(
        edge_set(R(kind,f,"A")).issubset(edge_set(R(kind,f,"B")))
        for kind in STAGES for f in (0,1)
    )
    gates["L7_cycle_closure_leaves_locally_unstable_states"] = all(
        R(kind,f,"B").get("locally_stable_state_count") <
        R(kind,f,"B").get("state_count")
        for kind in STAGES for f in (0,1)
    )
    gates["L8_later_authority_stabilizes_states_without_revising_closed_cycle"] = all(monotone.values()) and all(
        R(kind,f,"C").get("locally_stable_state_count")==1
        for kind in STAGES for f in (0,1)
    )
    gates["L9_whole_stability_only_when_all_outgoing_transitions_warranted"] = all(
        R("triad",f,"E").get("status")=="VERIFIED_STABLE" and
        R("triad",f,"E").get("unresolved_transition_count")==0 and
        R("quartet",f,"F").get("status")=="VERIFIED_STABLE" and
        R("quartet",f,"F").get("unresolved_transition_count")==0
        for f in (0,1)
    ) and all(
        R(kind,f,stage).get("status")!="VERIFIED_STABLE"
        for kind in STAGES for f in (0,1) for stage in STAGES[kind][:-1]
    )
    gates["L10_final_stable_machine_replays_deeper_heldout_histories"] = all(triad_transfer.values()) and all(quartet_transfer.values())
    gates["L11_second_hidden_family_repeats_chain_cycle_local_whole_ordering"] = all(
        shape_exact[f"quartet_{f}_{stage}"]
        for f in (0,1) for stage in STAGES["quartet"]
    )
    gates["L12_second_family_has_different_residual_state_count"] = all(
        R("triad",f,"A").get("state_count")==3 and
        R("quartet",f,"A").get("state_count")==4
        for f in (0,1)
    )
    gates["L13_binary_relabelling_preserves_status_counts_closure_and_canonical_structure"] = all(complement.values())
    gates["L14_warranted_edges_are_monotone_under_all_authority_expansions"] = all(monotone.values())
    gates["L15_unresolved_edges_are_never_reported_executable"] = all(unresolved_not_executable.values())
    gates["L16_non_prefix_closed_authority_remains_unknown"] = corrupt.get("status")=="UNKNOWN_AUTHORITY"
    gates["L17_verifier_ablation_authorizes_no_transition_construction"] = (
        nover.get("status")=="UNKNOWN_NO_VERIFIER" and
        nover.get("state_count")==0 and
        nover.get("warranted_transition_count")==0
    )
    gates["L18_frozen_kernel_has_no_hidden_family_cycle_state_or_schedule_names"] = all(x not in kernel_text for x in forbidden)
    gates["L19_cycle_closure_precedes_whole_stability_in_two_families"] = all(
        R(kind,f,"B").get("status")=="VERIFIED_CYCLE_CLOSED" and
        R(kind,f,STAGES[kind][-1]).get("status")=="VERIFIED_STABLE"
        for kind in STAGES for f in (0,1)
    )
    gates["L20_local_stabilization_occurs_between_cycle_and_whole_stability"] = all(
        R(kind,f,"C").get("locally_stable_state_count")==1 and
        R(kind,f,"C").get("status")=="VERIFIED_CYCLE_CLOSED"
        for kind in STAGES for f in (0,1)
    )
    gates["L21_all_independently_expected_stage_shapes_recovered"] = all(shape_exact.values())

    evidence = {
        "experiment":"local_transition_closure_v38",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_core_git_blob_sha":observed,
        "results":results,
        "expected_stage_shapes":shape_exact,
        "monotone_edge_retention":monotone,
        "complement_invariance":complement,
        "triad_transfer_to_depth9":triad_transfer,
        "quartet_transfer_to_depth9":quartet_transfer,
        "gates":gates,
    }
    evidence["full_pass"]=all(gates.values())
    evidence["verdict"]=(
        "VERIFIED_LOCAL_TRANSITION_WARRANT_CYCLE_CLOSURE_AND_COMPOSITIONAL_STABILIZATION"
        if evidence["full_pass"] else
        "LOCAL_TRANSITION_CLOSURE_V38_GAPS_EXPOSED"
    )

    (HERE/"evidence.json").write_text(
        json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
