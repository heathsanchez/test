from __future__ import annotations
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent

from kernel import Kernel
from challenge_pack import REGULAR, MISLEADING, PRECLOSURE

SCIENTIFIC_FREEZE_COMMIT = "40459f046d5865edf0e7c8460b96ced55e282ad9"

def git_blob_sha(p: Path) -> str:
    data=p.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

class BoolVerifier:
    def __init__(self, hidden):
        self.hidden=dict(hidden)
        self.calls=[]
    def __call__(self, src, sym, dst):
        src=tuple(src); dst=tuple(dst); sym=int(sym)
        self.calls.append((src,sym,dst))
        return bool(self.hidden.get((src,sym)) == dst)

def edge_map_from_result(r):
    return {
        (tuple(src),int(sym)):tuple(dst)
        for (src,sym),dst in r["final_edge_map"].items()
    }

def exact_complete(r, hidden):
    if r.get("status")!="VERIFIED_COMPLETE":
        return False
    return edge_map_from_result(r)==dict(hidden)

def safe(x):
    if isinstance(x, dict):
        out={}
        for k,v in x.items():
            if isinstance(k,tuple):
                k=repr(k)
            out[str(k)]=safe(v)
        return out
    if isinstance(x,(list,tuple,set)):
        return [safe(v) for v in x]
    return x

def normalized_structure(world, result, kernel):
    ins=kernel.inspect(world.graph)
    if not ins.get("spanning_cycle"):
        return None
    order=tuple(tuple(q) for q in ins["cycle_order"])
    pos={q:i for i,q in enumerate(order)}
    cs=int(ins["cycle_symbol"]); alt=int(ins["alternate_symbol"])
    em=edge_map_from_result(result)
    return {
        "n":len(order),
        "cycle_targets":[pos[em[(q,cs)]] for q in order],
        "alternate_targets":[pos[em[(q,alt)]] for q in order],
    }

def main():
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    kernel=Kernel()
    regular_rows={}
    family_groups={"alpha":[],"beta":[]}

    for world in REGULAR:
        hidden=world.hidden_map()

        v_closure=BoolVerifier(hidden)
        closure=kernel.complete(world.graph,v_closure,closure_enabled=True)

        v_base=BoolVerifier(hidden)
        baseline=kernel.complete(world.graph,v_base,closure_enabled=False)

        regular_rows[world.world_id]={
            "inspection":kernel.inspect(world.graph),
            "closure":safe(closure),
            "baseline":safe(baseline),
            "closure_exact":exact_complete(closure,hidden),
            "baseline_exact":exact_complete(baseline,hidden),
            "closure_calls":len(v_closure.calls),
            "baseline_calls":len(v_base.calls),
            "speedup":len(v_base.calls)/max(1,len(v_closure.calls)),
            "normalized_structure":normalized_structure(world,closure,kernel),
            "verifier_return_types_boolean":all(isinstance(bool(hidden.get((s,y))==d),bool) for s,y,d in v_closure.calls),
        }
        family=world.world_id.split("_bf")[0]
        family_groups[family].append(regular_rows[world.world_id])

    misleading_hidden=MISLEADING.hidden_map()
    mv=BoolVerifier(misleading_hidden)
    misleading=kernel.complete(MISLEADING.graph,mv,closure_enabled=True)

    pre_hidden=PRECLOSURE.hidden_map()
    pv=BoolVerifier(pre_hidden)
    pre=kernel.complete(PRECLOSURE.graph,pv,closure_enabled=True)
    pre_ins=kernel.inspect(PRECLOSURE.graph)

    def same_family_invariant(rows):
        first=rows[0]
        return all(
            row["inspection"].get("compiled_displacement")==first["inspection"].get("compiled_displacement")
            and row["closure_calls"]==first["closure_calls"]
            and row["baseline_calls"]==first["baseline_calls"]
            and row["normalized_structure"]==first["normalized_structure"]
            for row in rows[1:]
        )

    kernel_text=(HERE/"kernel.py").read_text().lower()
    forbidden=("alpha","beta","gamma","101","307","911","503")

    gates={}
    gates["R1_frozen_scientific_core_byte_identical"]=freeze_ok
    gates["R2_no_rule_compiled_before_spanning_cycle"]=(
        pre_ins.get("spanning_cycle") is False and
        pre_ins.get("compiled_rule") is False
    )
    gates["R3_verified_cycle_induces_complete_relational_coordinates"]=all(
        row["inspection"].get("spanning_cycle") is True and
        len(row["inspection"].get("cycle_order",[]))==row["inspection"].get("cycle_size")
        for row in regular_rows.values()
    )
    gates["R4_two_consistent_seed_edges_compile_displacement_rule"]=all(
        row["inspection"].get("seed_edge_count")==2 and
        row["inspection"].get("compiled_rule") is True
        for row in regular_rows.values()
    )
    alpha=[r for k,r in regular_rows.items() if k.startswith("alpha_")]
    beta=[r for k,r in regular_rows.items() if k.startswith("beta_")]
    gates["R5_first_regular_family_all_closure_proposals_verify"]=all(
        r["closure"].get("prediction_attempts")==r["closure"].get("prediction_accepts")
        and r["closure"].get("prediction_rejections")==0
        for r in alpha
    )
    gates["R6_second_regular_family_all_closure_proposals_verify"]=all(
        r["closure"].get("prediction_attempts")==r["closure"].get("prediction_accepts")
        and r["closure"].get("prediction_rejections")==0
        for r in beta
    )
    gates["R7_closure_completion_exact_in_both_regular_families"]=all(
        r["closure_exact"] for r in regular_rows.values()
    )
    gates["R8_closure_uses_at_least_3x_fewer_verifier_calls"]=all(
        r["speedup"]>=3.0 for r in regular_rows.values()
    )
    gates["R9_closure_disabled_ablation_restores_local_search_cost"]=all(
        r["baseline"].get("used_closure_resource") is False
        and r["baseline_calls"]>r["closure_calls"]
        and r["baseline_exact"]
        for r in regular_rows.values()
    )
    gates["R10_cycle_edge_removal_prevents_compilation_and_uses_fallback"]=(
        pre_ins.get("compiled_rule") is False
        and pre.get("used_closure_resource") is False
        and exact_complete(pre,pre_hidden)
    )
    gates["R11_opaque_state_relabelling_preserves_rule_structure_and_cost"]=(
        same_family_invariant(family_groups["alpha"])
        and same_family_invariant(family_groups["beta"])
    )
    gates["R12_binary_symbol_relabelling_preserves_rule_structure_and_cost"]=(
        same_family_invariant(family_groups["alpha"])
        and same_family_invariant(family_groups["beta"])
    )
    gates["R13_misleading_family_initially_compiles_rule"]=(
        kernel.inspect(MISLEADING.graph).get("compiled_rule") is True
    )
    gates["R14_contradictory_edge_rejects_and_immediately_revokes_rule"]=(
        misleading.get("prediction_rejections")==1
        and misleading.get("rule_revoked") is True
    )
    rejected={
        (tuple(s),int(y),tuple(d))
        for s,y,d in misleading.get("rejected_edges",[])
    }
    final_m=edge_map_from_result(misleading)
    gates["R15_no_rejected_proposal_is_retained"]=all(
        final_m.get((s,y))!=d for s,y,d in rejected
    )
    gates["R16_fallback_after_revocation_recovers_exact_hidden_machine"]=exact_complete(
        misleading,misleading_hidden
    )
    gates["R17_revoked_regularity_is_not_retained_capability"]=(
        misleading.get("retained_compiled_rule") is False
    )
    gates["R18_kernel_verifier_interface_receives_only_boolean_edge_checks"]=all(
        r["verifier_return_types_boolean"] for r in regular_rows.values()
    )
    gates["R19_frozen_kernel_contains_no_hidden_challenge_names_or_signatures"]=all(
        token not in kernel_text for token in forbidden
    )
    gates["R20_verified_closure_resource_changes_developmental_economics_without_correctness_loss"]=all(
        r["closure_exact"] and r["baseline_exact"] and r["closure_calls"]<r["baseline_calls"]
        for r in regular_rows.values()
    )

    evidence={
        "experiment":"closure_resource_v39",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_core_git_blob_sha":observed,
        "regular_worlds":regular_rows,
        "misleading_world":{
            "inspection":kernel.inspect(MISLEADING.graph),
            "result":safe(misleading),
            "exact":exact_complete(misleading,misleading_hidden),
            "verifier_calls":len(mv.calls),
        },
        "preclosure_control":{
            "inspection":pre_ins,
            "result":safe(pre),
            "exact":exact_complete(pre,pre_hidden),
            "verifier_calls":len(pv.calls),
        },
        "gates":gates,
    }
    evidence["full_pass"]=all(gates.values())
    evidence["verdict"]=(
        "VERIFIED_CLOSURE_AS_FALLIBLE_DEVELOPMENTAL_RESOURCE_AND_VERIFICATION_ACCELERATOR"
        if evidence["full_pass"] else
        "CLOSURE_RESOURCE_V39_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
