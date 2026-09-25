#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

def totalR(c): return fk.vpz(c["A"],3)

def analyze(lo,hi,K,out):
    pats=defaultdict(dict); seqs=[]; counts=Counter()
    for n in range(lo|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID" or not fk.completed_rigid_source(n,K):
            continue
        for r,seq in fk.return_sequences(n,K).items():
            if not seq: continue
            seqs.append((r,seq))
            for e in seq:
                c=e["cert"]; pats[r][fk.semantic_id(c)]=c
    bank={r:tuple(pats[r][k] for k in sorted(pats[r])) for r in sorted(pats)}
    nearest_lower=nearest_valid=all_valid=all_lower=source_lower=0
    exact_checks=0; rows=[]
    for r,seq in seqs:
        cs=bank[r]
        for e in seq:
            m=e["m0"]; n=e["source"]
            vals=[fk.vpz(fk.defect(c,m),3) for c in cs]
            mx=max(v for v in vals if v is not None) if all(v is not None for v in vals) else None
            inds=[i for i,v in enumerate(vals) if (v is None if mx is None else v==mx)]
            nearest=cs[inds[0]]
            valid=[]
            for c,v in zip(cs,vals):
                R=totalR(c)
                if v is not None and v>=R:
                    A,B,D=c["A"],c["B"],c["D"]
                    num=(1<<D)*m-B
                    assert num%A==0
                    p=num//A
                    if p>0:
                        all_valid+=1; valid.append((p,c,v))
                        assert ra.admissible(c,p)
                        assert ra.replay(c,p)==m
                        assert p-m==fk.defect(c,m)//A
                        exact_checks+=1
                        if p<m:
                            all_lower+=1
                            if (1<<r)*p-1<n: source_lower+=1
            nv=[z for z in valid if z[1] is nearest]
            if nv:
                nearest_valid+=1
                if nv[0][0]<m: nearest_lower+=1
            if len(rows)<40:
                rows.append({
                    "source":n,"anchor":r,"m":m,
                    "nearest":fk.semantic_tuple(nearest),"nearest_depth":vals[inds[0]],
                    "nearest_R":totalR(nearest),
                    "nearest_reverse_p":nv[0][0] if nv else None,
                    "nearest_reverse_lower":bool(nv and nv[0][0]<m),
                    "valid_reverse_count":len(valid),
                    "lower_reverse_count":sum(p<m for p,c,v in valid),
                    "source_lower_count":sum(((1<<r)*p-1<n) for p,c,v in valid),
                })
    result={
      "range":[lo|1,hi],"K":K,
      "exact_reverse_checks":exact_checks,
      "all_valid_reverse":all_valid,"all_lower_reverse":all_lower,
      "source_lower_reverse":source_lower,
      "nearest_valid_reverse":nearest_valid,"nearest_lower_reverse":nearest_lower,
      "sample":rows,
      "scope":"bounded q0 RIGID same-anchor return bank"
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for k,v in result.items():
        if k!="sample": print(k.upper(),v)
    print("SAMPLE",json.dumps(rows,sort_keys=True))
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--lo",type=int,default=46081); ap.add_argument("--hi",type=int,default=46591); ap.add_argument("--K",type=int,default=128); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); analyze(a.lo,a.hi,a.K,a.output)
