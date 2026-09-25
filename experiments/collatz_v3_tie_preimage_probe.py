#!/usr/bin/env python3
"""Probe a sufficient preimage-cover law for 3-adic no-overcancellation.

For an equality tie q_i at transported depth H=h+R under active return c,
let p_i=F_c^{-1}(q_i). Then v3(p_i-q_*)=h. If some legal return centre q_j
satisfies v3(p_i-q_j)>h, any overcancellation v3(m-p_i)>h would imply
v3(m-q_j)>h, contradicting maximality of the current nearest depth h.

This finite probe asks whether every observed equality-tie preimage has such a
strictly deeper return-centre cover.
"""
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path

import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base


def centre(c): return Fraction(int(c["B"]),int(c["C"]))

def apply(c,x): return (int(c["A"])*x+int(c["B"]))/(1<<int(c["D"]))

def inv_apply(c,y): return ((1<<int(c["D"]))*y-int(c["B"]))/int(c["A"])

def v3f(x):
    if x==0:return None
    assert x.denominator%3!=0
    return fk.vpz(x.numerator,3)

def rexp(c):
    a=int(c["A"]);r=0
    while a>1:
        assert a%3==0;a//=3;r+=1
    return r

def nearest(bank,m):
    vals=[fk.vpz(fk.defect(c,m),3) for c in bank]
    h=max(vals);i=next(i for i,v in enumerate(vals) if v==h)
    return i,h,vals

def audit(lo,hi,K,out):
    patterns=defaultdict(dict);seqs=[];incomplete=[];counts=Counter()
    for n in range(max(3,lo)|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID":continue
        counts["hereditary_birth_rigid"]+=1
        if not fk.completed_rigid_source(n,K):
            incomplete.append(n);continue
        counts["completed_sources"]+=1
        for r,seq in fk.return_sequences(n,K).items():
            if not seq:continue
            seqs.append(seq);counts["anchor_sequences"]+=1
            counts["return_occurrences"]+=len(seq)
            for e in seq:
                c=e["cert"];patterns[r][fk.semantic_id(c)]=c
    banks={r:tuple(sorted(patterns[r].values(),key=fk.semantic_tuple)) for r in sorted(patterns)}
    counts["semantic_patterns"]=sum(len(v) for v in banks.values())

    ties=[]; uncovered=[]
    for seq in seqs:
        for pos,e in enumerate(seq[:-1]):
            bank=banks[e["anchor"]];c=e["cert"]
            ni,h,_=nearest(bank,e["m0"]);qstar=centre(bank[ni])
            H=h+rexp(c); z=apply(c,qstar)
            for qi in bank:
                s=v3f(z-centre(qi))
                if s!=H:continue
                p=inv_apply(c,centre(qi))
                assert v3f(p-qstar)==h
                depths=[]
                for j,qj in enumerate(bank):
                    d=v3f(p-centre(qj))
                    depths.append((10**9 if d is None else d,j,d))
                depths.sort(reverse=True)
                best_num,bj,best=depths[0]
                row={
                    "source":e["source"],"anchor":e["anchor"],"position":pos,
                    "h":h,"H":H,"active":fk.semantic_id(c),
                    "nearest":fk.semantic_id(bank[ni]),
                    "tie":fk.semantic_id(qi),
                    "preimage_exact_centre":best is None,
                    "cover":fk.semantic_id(bank[bj]),
                    "cover_depth":None if best is None else best,
                    "strict_cover":best is None or best>h,
                    "active_tuple":fk.semantic_tuple(c),
                    "active_word":c["word"],
                    "nearest_tuple":fk.semantic_tuple(bank[ni]),
                    "nearest_word":bank[ni]["word"],
                    "tie_tuple":fk.semantic_tuple(qi),
                    "tie_word":qi["word"],
                    "cover_tuple":fk.semantic_tuple(bank[bj]),
                    "cover_word":bank[bj]["word"],
                    "preimage":[p.numerator,p.denominator],
                }
                ties.append(row)
                if not row["strict_cover"]:uncovered.append(row)

    result={
      "range":[lo,hi],"K":K,"counts":dict(counts),
      "incomplete_sources":incomplete,
      "tie_preimages":len(ties),
      "strictly_covered":len(ties)-len(uncovered),
      "uncovered":uncovered[:40],
      "examples":ties[:40],
    }
    result["verdict"]=(
      "PASS_BOUNDED_EVERY_3ADIC_TIE_PREIMAGE_STRICTLY_COVERED"
      if not incomplete and not uncovered
      else "SEPARATOR_UNCOVERED_3ADIC_TIE_PREIMAGE")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("COUNTS",json.dumps(dict(counts),sort_keys=True))
    print("INCOMPLETE",len(incomplete))
    print("TIE_PREIMAGES",len(ties),"STRICTLY_COVERED",len(ties)-len(uncovered),
          "UNCOVERED",len(uncovered))
    for z in uncovered[:20]:print("UNCOVERED",json.dumps(z,sort_keys=True))
    for z in ties[:10]:print("TIE",json.dumps(z,sort_keys=True))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--lo",type=int,default=3)
    p.add_argument("--hi",type=int,default=8191)
    p.add_argument("--K",type=int,default=128)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();audit(a.lo,a.hi,a.K,a.out)
