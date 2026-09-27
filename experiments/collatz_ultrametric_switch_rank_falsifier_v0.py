#!/usr/bin/env python3
"""Crystal falsifier for proposed ultrametric return-switch rank.

Tests actual completed q0-RIGID return occurrences on frozen and prospective
bands. This is theorem discovery only: passing finite bands does not promote
the all-depth rank.
"""
from collections import defaultdict
import json
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base

B=20

def collect(lo,hi,K=128):
    patterns=defaultdict(dict); seqs=[]
    for n in range(lo|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID" or not fk.completed_rigid_source(n,K): continue
        for r,seq in fk.return_sequences(n,K).items():
            if not seq: continue
            seqs.append((r,seq))
            for e in seq: patterns[r][fk.semantic_id(e["cert"])]=e["cert"]
    bank={r:tuple(patterns[r][k] for k in sorted(patterns[r])) for r in sorted(patterns)}
    return seqs,bank

def v3_state(e,bank):
    vals=[fk.vpz(fk.defect(c,e["m0"]),3) for c in bank[e["anchor"]]]
    if any(v is None for v in vals): return (B, "ZERO")
    r=max(vals,default=0)
    ids=tuple(fk.semantic_id(bank[e["anchor"]][i]) for i,v in enumerate(vals) if v==r)
    return (min(B,r),ids)

def fuel(e):
    d=fk.defect(e["cert"],e["m0"]); v=fk.v2z(d)
    return -1 if v is None else v-(e["cert"]["D"]+1)

def rank(e,bank):
    r,ids=v3_state(e,bank)
    # Proposed lexicographic rank: deeper 3-adic radius is better (smaller first
    # coordinate); same-centre v2 fuel is second coordinate.
    return (B-r, fuel(e))

def audit(lo,hi):
    seqs,bank=collect(lo,hi)
    bad=[]; same=sw=dec=0
    for _,seq in seqs:
        for a,b in zip(seq,seq[1:]):
            ra,rb=rank(a,bank),rank(b,bank)
            if fk.semantic_id(a["cert"])==fk.semantic_id(b["cert"]): same+=1
            else: sw+=1
            if rb < ra: dec+=1
            else:
                bad.append({"source":a["source"],"anchor":a["anchor"],
                  "a":{"m":a["m0"],"cert":fk.semantic_id(a["cert"]),"rank":ra,"v3":v3_state(a,bank)},
                  "b":{"m":b["m0"],"cert":fk.semantic_id(b["cert"]),"rank":rb,"v3":v3_state(b,bank)}})
    return {"range":[lo,hi],"edges":same+sw,"same":same,"switch":sw,"strict_decrease":dec,
            "violations":len(bad),"first":bad[:5]}

def main():
    rows=[audit(3,8191),audit(8193,32767)]
    print(json.dumps({"schema":"COLLATZ_ULTRAMETRIC_SWITCH_RANK_FALSIFIER_V0",
      "rank":"(20-min(20,nearest_v3_radius), active_v2_excess)",
      "rows":rows,
      "verdict":"FINITE_PASS" if all(x["violations"]==0 for x in rows) else "RANK_FALSIFIED",
      "global_collatz":"UNKNOWN"},indent=2,default=list))
if __name__=="__main__":main()

# trigger
