#!/usr/bin/env python3
"""Test well-founded complexity candidates only on nearest-centre changes."""
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base

def centre(c):
    from fractions import Fraction
    return Fraction(c["B"],c["C"])

def nearest(e,cs):
    m=e["m0"]
    vals=[fk.vpz(fk.defect(c,m),3) for c in cs]
    if any(v is None for v in vals):
        r=None; inds=[i for i,v in enumerate(vals) if v is None]
    else:
        r=max(vals,default=0); inds=[i for i,v in enumerate(vals) if v==r]
    i=min(inds,key=lambda j:(centre(cs[j]).numerator,centre(cs[j]).denominator,fk.semantic_tuple(cs[j])))
    return cs[i],r

def metrics(c):
    q=centre(c)
    return {
      "word_len":len(c["word"]),
      "D":c["D"],
      "R":fk.vpz(c["A"],3),
      "height":max(abs(q.numerator),abs(q.denominator)),
      "height_sum":abs(q.numerator)+abs(q.denominator),
      "absC":abs(c["C"]),
      "absB":abs(c["B"]),
    }

def analyze(lo,hi,K,out):
    pats=defaultdict(dict); seqs=[]
    for n in range(lo|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID" or not fk.completed_rigid_source(n,K): continue
        for r,seq in fk.return_sequences(n,K).items():
            if not seq: continue
            seqs.append((r,seq))
            for e in seq:
                c=e["cert"]; pats[r][fk.semantic_id(c)]=c
    bank={r:tuple(pats[r][k] for k in sorted(pats[r])) for r in sorted(pats)}
    stats=defaultdict(Counter); rows=[]
    for r,seq in seqs:
        cs=bank[r]
        ns=[nearest(e,cs) for e in seq]
        for (a,ra),(b,rb),e0,e1 in zip(ns,ns[1:],seq,seq[1:]):
            qa,qb=centre(a),centre(b)
            if qa==qb:
                stats["radius"]["same_centre"]+=1
                if ra is not None and rb is not None:
                    if rb<ra: stats["radius"]["down"]+=1
                    elif rb==ra: stats["radius"]["equal"]+=1
                    else: stats["radius"]["up"]+=1
                continue
            ma,mb=metrics(a),metrics(b)
            row={"source":e0["source"],"anchor":r,
                 "qa":[qa.numerator,qa.denominator],"qb":[qb.numerator,qb.denominator],
                 "ra":ra,"rb":rb,"a":ma,"b":mb}
            rows.append(row)
            for k in ma:
                if mb[k]<ma[k]: stats[k]["down"]+=1
                elif mb[k]==ma[k]: stats[k]["equal"]+=1
                else: stats[k]["up"]+=1
    result={"range":[lo|1,hi],"K":K,"centre_switches":len(rows),
            "stats":{k:dict(v) for k,v in stats.items()},
            "rows":rows[:100],
            "scope":"nearest-centre changes only; bounded q0 RIGID corpus"}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("CENTRE_SWITCHES",len(rows))
    for k,v in sorted(result["stats"].items()): print("ORDER",k,json.dumps(v,sort_keys=True))
    print("ROWS",json.dumps(rows[:40],sort_keys=True))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,required=True); ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--K",type=int,default=128); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); analyze(a.lo,a.hi,a.K,a.output)
