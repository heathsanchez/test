#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

import sair_probe_program_synthesis_v28 as v28
import sair_residual_constrained_transformer_v32 as v32
from developmental_runtime import DevelopmentalRuntime, Route, SynthesisRegistry, route
from developmental_runtime.intervention import lawful
from domains.sair.runtime_adapter import SAIRRuntimeAdapter
from domains.sair.probe_operator import induce_numeric_literal_shift, expand_numeric_literal_shift

ORDER5 = "MODEL_EXISTS(5,FORWARD)"

def ev(e):
    return None if e is None else {"route": e.route, "intervention_id": e.intervention_id, "detail": e.detail}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--sair-root",required=True); ap.add_argument("--out-dir",required=True)
    a=ap.parse_args(); root=Path(a.sair_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

    rows,_,_,_=v28.load_rows(root,("normal","hard1","hard2"))
    for r in rows: r.pop("y",None)
    old=v28.synth_program_carrier(False); expanded=v28.synth_program_carrier(True)
    old_ids=tuple(p["ast"] for p in old); expanded_ids=tuple(p["ast"] for p in expanded)
    pmap={p["ast"]:dict(p) for p in expanded}; v32.add_raw_programs(pmap)
    # Executable verifier target only; deliberately absent from starting probe language/static generator.
    pmap[ORDER5]={"ast":ORDER5,"order":5,"direction":"FORWARD","cost":4,"kind":"atom"}
    adapter=SAIRRuntimeAdapter(rows,pmap)
    actions=("ACCEPT_COUNTERMODEL_WITNESS","ADVANCE_PROOF_SEARCH_FRONTIER")

    induction=base=None
    for b,cell in sorted(v32.base_groups(rows).items(),key=lambda kv:repr(kv[0])):
        if len(cell)<2: continue
        st=v32.run_stage1(adapter,rows,cell,old_ids,expanded_ids,actions)
        if st is not None and v32.old_carrier_candidate(adapter,expanded_ids,st["after_action"]) is None:
            induction,base=st,b; break
    if induction is None: raise SystemExit("No V37 induction successor")
    successor=induction["after_action"]

    # Reconstruct V36 unique minimum concrete probe (4F).
    audit={"witnesses":0,"bad":0,"unknown":0}
    for order in v32.ORDERS:
        for direction in v32.DIRECTIONS:
            x=v32.ensure_exact_order_values(root,rows,successor.hypotheses,order,direction)
            for k in audit: audit[k]+=int(x[k])
    carrier=v32.exhaustive_raw_carrier(adapter,successor)
    _,ca,_=v32.select_min_resolving_raw_transformer(adapter,successor,carrier)
    resolving=[r for r in ca if r.get("resolves")]
    best=min((r["transformer"]["cost"],r["transformer"]["edit_count"]) for r in resolving)
    minima=[r for r in resolving if (r["transformer"]["cost"],r["transformer"]["edit_count"])==best]
    probes=sorted({r["probe"] for r in minima}); probe4=probes[0] if len(probes)==1 else None
    actual=sorted(successor.hypotheses)[0]

    registry=SynthesisRegistry(); registry.register_probe_operator_inducer(induce_numeric_literal_shift); registry.register_probe_operator_expander(expand_numeric_literal_shift)
    runtime=DevelopmentalRuntime(adapter,registry)
    prepared4=adapter.prepare_probe_extension(successor,probe4)
    pre4=route(adapter,prepared4)
    after_probe4,eprobe4=runtime.execute_probe(prepared4,actual)
    learned=tuple(after_probe4.metadata.get("learned_probe_operators",()))
    post4=route(adapter,after_probe4)
    after_action4=after_probe4; eact4=None
    if post4.route is Route.ACT:
        after_action4,eact4=runtime.execute_common_continuation(after_probe4,actual)
    succ4=route(adapter,after_action4)

    # Exact order-5 verifier values become available only after the V37 successor exists.
    a5=v32.ensure_exact_order_values(root,rows,after_action4.hypotheses,5,"FORWARD")
    static_carrier=set(old_ids)|set(expanded_ids)
    absent_initial=(ORDER5 not in successor.probe_language and ORDER5 not in static_carrier)

    candidate5=registry.synthesize_probe_extension(adapter,after_action4)
    meta=dict(after_action4.metadata); meta.pop("learned_probe_operators",None)
    ablated=after_action4.evolve(metadata=meta,lawbook=())
    ablated_candidate=registry.synthesize_probe_extension(adapter,ablated)

    developed5=after_action4; events5=[]
    if succ4.route is Route.DEVELOP_PROBES:
        developed5,events5=runtime.develop_until_intervention(after_action4)
    probe5=next((e.intervention_id for e in events5 if e.route=="SYNTHESIZE_PROBE"),None)
    eprobe5=None; post5=None; eact5=None; final=None; lawful5=True
    if probe5==ORDER5 and events5 and events5[-1].route=="PROBE":
        after_probe5,eprobe5=runtime.execute_probe(developed5,actual)
        post5=route(adapter,after_probe5)
        state5=after_probe5
        if post5.route is Route.ACT:
            state5,eact5=runtime.execute_common_continuation(after_probe5,actual)
            rec=adapter.execute(after_probe5,actual,adapter.intervention(eact5.intervention_id)); lawful5=lawful(rec)
        final=route(adapter,state5)

    plus1=any(op.get("kind")=="NUMERIC_LITERAL_SHIFT" and int(op.get("delta",0))==1 for op in learned)
    gates={
      "official_natural_sair_corpus_answer_blind":len(rows)==1269 and all("y" not in r for r in rows),
      "v37_order4_continuation_reconstructed":probe4=="MODEL_EXISTS(4,FORWARD)" and pre4.route is Route.PROBE and post4.route is Route.ACT,
      "v37_successor_routes_develop_probes":succ4.route is Route.DEVELOP_PROBES,
      "plus_one_operator_induced_and_retained":plus1 and any("NUMERIC_LITERAL_SHIFT" in x for x in after_probe4.lawbook),
      "order5_absent_from_starting_carrier":absent_initial,
      "retained_operator_selects_order5_forward":candidate5==ORDER5 and probe5==ORDER5,
      "operator_ablation_blocks_order5_extension":ablated_candidate is None,
      "order5_exact_verifier_zero_bad_zero_unknown":int(a5["bad"])==0 and int(a5["unknown"])==0,
      "order5_executes_and_recomputes_route":eprobe5 is not None and post5 is not None,
      "licensed_order5_continuation_is_lawful":lawful5,
      "successor_routed_again":final is not None,
      "no_protected_answer_used":all("y" not in r for r in rows),
    }
    gates["V38_NATURAL_RETAINED_OPERATOR_ORDER5_GATE"]=all(gates.values())
    result={"status":"V38_NATURAL_RETAINED_OPERATOR_ORDER5","induction_base":repr(base),"actual_world":rows[actual]["id"],"probe4":probe4,"probe4_event":ev(eprobe4),"action4_event":ev(eact4),"successor4_route":succ4.route.name,"learned_operators":list(learned),"candidate5":candidate5,"ablated_candidate":ablated_candidate,"order5_verifier_audit":a5,"events5":[ev(e) for e in events5],"probe5_event":ev(eprobe5),"post5_route":post5.route.name if post5 else None,"action5_event":ev(eact5),"final_route":final.route.name if final else None,"final_reason":final.reason if final else None,"gates":gates}
    (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)); print(json.dumps(result,indent=2,sort_keys=True))
    if not gates["V38_NATURAL_RETAINED_OPERATOR_ORDER5_GATE"]: raise SystemExit(2)
if __name__=="__main__": main()
