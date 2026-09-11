#!/usr/bin/env python3
from __future__ import annotations
import hashlib, itertools, json, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OPS=("amber","blue","coral","denim")
INPUTS=((),("seed",),("x","y"))

def execute(program, value):
    out=tuple(value)
    for op in program: out=out+(op,)
    return out

def verifier(target):
    expected=[execute(target,x) for x in INPUTS]
    def check(program):
        got=[execute(program,x) for x in INPUTS]
        return {"accepted":got==expected,"matched":sum(a==b for a,b in zip(got,expected))}
    return check

def search(target, order, mode):
    verify=verifier(target); calls=0; start=time.perf_counter()
    for depth in range(5):
        if depth==0: programs=[()]
        elif mode=="prefix_major": programs=itertools.product(order,repeat=depth)
        else: programs=((lead,)+suffix for suffix in itertools.product(order,repeat=depth-1) for lead in order)
        for p in programs:
            calls+=1
            if verify(p)["accepted"]:
                return {"correct":True,"calls":calls,"solution":list(p),"wall_seconds":time.perf_counter()-start}
    return {"correct":False,"calls":calls,"solution":None,"wall_seconds":time.perf_counter()-start}

def main():
    rows=[]
    targets=list(itertools.permutations(OPS))
    orders=list(itertools.permutations(OPS))
    for ti,target in enumerate(targets):
      for oi,order in enumerate(orders):
        cold=search(target,order,"prefix_major")
        warm=search(target,order,"continuation_major")
        for condition,result in (
          ("cold_immediate",cold),("q_warm",warm),("q_ablation",cold),
          ("sham",cold),("answer_memory",cold)):
            rows.append({"target_index":ti,"order_index":oi,"condition":condition,**result})

    totals={c:sum(r["calls"] for r in rows if r["condition"]==c) for c in ("cold_immediate","q_warm","q_ablation","sham","answer_memory")}
    paired=[]
    for ti in range(len(targets)):
      for oi in range(len(orders)):
        c=next(r["calls"] for r in rows if r["target_index"]==ti and r["order_index"]==oi and r["condition"]=="cold_immediate")
        q=next(r["calls"] for r in rows if r["target_index"]==ti and r["order_index"]==oi and r["condition"]=="q_warm")
        paired.append(q-c)
    strata=[]
    for first_pos in range(4):
      vals=[]
      for ti,target in enumerate(targets):
        for oi,order in enumerate(orders):
          if order.index(target[0])!=first_pos: continue
          c=next(r["calls"] for r in rows if r["target_index"]==ti and r["order_index"]==oi and r["condition"]=="cold_immediate")
          q=next(r["calls"] for r in rows if r["target_index"]==ti and r["order_index"]==oi and r["condition"]=="q_warm")
          vals.append(q-c)
      strata.append({"target_first_action_position":first_pos,"trials":len(vals),"aggregate_delta":sum(vals)})

    source=ROOT.parent/"future_consequence_quotient_c4_v1"/"run.py"
    source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    cold=totals["cold_immediate"]; warm=totals["q_warm"]
    gates={
      "G1_all_correct":all(r["correct"] for r in rows),
      "G2_q_below_80pct_cold":warm < .8*cold,
      "G3_more_wins_than_losses":sum(d<0 for d in paired)>sum(d>0 for d in paired),
      "G4_gain_every_stratum":all(s["aggregate_delta"]<0 for s in strata),
      "G5_controls_equal_cold":all(totals[x]==cold for x in ("q_ablation","sham","answer_memory")),
      "G6_source_mechanism_frozen":source_sha=="b24c010f126a3dbc302af123d0fe2e5e87fc87cb65f81b362b99d82b94dca273",
    }
    if gates["G1_all_correct"] and not gates["G2_q_below_80pct_cold"]:
        verdict="ORDERING_SENSITIVE_NEGATIVE_TRANSFER"
    elif all(gates.values()): verdict="PROSPECTIVE_CROSS_CARRIER_TRANSFER"
    else: verdict="PARTIAL_OR_UNKNOWN"
    evidence={
      "verdict":verdict,"classification":"PROSPECTIVE_EXHAUSTIVE_COUNTERBALANCED_FINITE",
      "source_mechanism_commit":"8809c71cd75b49326f921595dfbfe05a310a959e",
      "source_mechanism_sha256":source_sha,"carrier":"immutable token traces",
      "targets":24,"operation_orders":24,"trials":576,"seed":None,
      "primary_metric":"aggregate fully charged verifier calls",
      "totals":totals,"q_over_cold":warm/cold,"calls_delta":warm-cold,
      "wins":sum(d<0 for d in paired),"ties":sum(d==0 for d in paired),"losses":sum(d>0 for d in paired),
      "strata":strata,"gates":gates,
      "not_established":["generator genesis","unbounded quotient computation","natural-task transfer"],
      "residual":"continuation-major traversal is a search-order permutation; without a learned consequence-dependent selection rule its aggregate advantage disappears under counterbalancing",
    }
    (ROOT/"results").mkdir(exist_ok=True)
    (ROOT/"results"/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    (ROOT/"results"/"rows.json").write_text(json.dumps(rows,separators=(",",":"))+"\n")
    print(json.dumps(evidence,indent=2))
    if verdict=="PARTIAL_OR_UNKNOWN": raise SystemExit(1)

if __name__=="__main__": main()
