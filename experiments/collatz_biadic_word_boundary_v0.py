#!/usr/bin/env python3
"""Test whether p-adic centre separation reads return words from opposite ends."""
from __future__ import annotations
import argparse, json
from collections import defaultdict, Counter
from pathlib import Path

import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base


def det(a,b):
    return a["C"]*b["B"]-b["C"]*a["B"]


def cpref(a,b):
    n=0
    for x,y in zip(a,b):
        if x!=y: break
        n+=1
    return n


def csuf(a,b):
    n=0
    for x,y in zip(reversed(a),reversed(b)):
        if x!=y: break
        n+=1
    return n


def sums(word,n,prefix=True):
    seg=word[:n] if prefix else (word[len(word)-n:] if n else ())
    R=sum(x[0] for x in seg)
    D=sum(x[1]+x[2] for x in seg)
    return R,D


def collect(lo,hi,K):
    patterns=defaultdict(dict)
    for n in range(lo|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID":
            continue
        if not fk.completed_rigid_source(n,K):
            continue
        for r,seq in fk.return_sequences(n,K).items():
            for e in seq:
                c=e["cert"]
                patterns[r][fk.semantic_id(c)]=c
    return {r:tuple(patterns[r][k] for k in sorted(patterns[r])) for r in sorted(patterns)}


def analyze(lo,hi,K,out):
    bank=collect(lo,hi,K)
    rows=[]
    stats=Counter()
    for anchor,cs in bank.items():
        for i,a in enumerate(cs):
            for b in cs[i+1:]:
                J=det(a,b)
                if J==0: continue
                w1,w2=a["word"],b["word"]
                p=cpref(w1,w2); s=csuf(w1,w2)
                pR,pD=sums(w1,p,True)
                sR,sD=sums(w1,s,False)
                v2=fk.v2z(J); v3=fk.vpz(J,3)
                row={
                    "anchor":anchor,
                    "a":fk.semantic_tuple(a),"b":fk.semantic_tuple(b),
                    "len_a":len(w1),"len_b":len(w2),
                    "common_prefix":p,"prefix_R":pR,"prefix_D":pD,
                    "common_suffix":s,"suffix_R":sR,"suffix_D":sD,
                    "v2J":v2,"v3J":v3,
                    "v2_minus_prefixD":v2-pD,
                    "v3_minus_suffixR":v3-sR,
                }
                rows.append(row)
                stats["pairs"]+=1
                stats["v2_eq_prefixD"]+=v2==pD
                stats["v2_ge_prefixD"]+=v2>=pD
                stats["v3_eq_suffixR"]+=v3==sR
                stats["v3_ge_suffixR"]+=v3>=sR
                stats[f"v2off:{v2-pD}"]+=1
                stats[f"v3off:{v3-sR}"]+=1
    out.parent.mkdir(parents=True,exist_ok=True)
    payload={"range":[lo|1,hi],"K":K,"stats":dict(stats),"sample":rows[:100]}
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print("STATS",json.dumps(dict(stats),sort_keys=True))
    # emit strongest exact relation candidates
    print("V2_EQ_PREFIXD",stats["v2_eq_prefixD"],"/",stats["pairs"])
    print("V2_GE_PREFIXD",stats["v2_ge_prefixD"],"/",stats["pairs"])
    print("V3_EQ_SUFFIXR",stats["v3_eq_suffixR"],"/",stats["pairs"])
    print("V3_GE_SUFFIXR",stats["v3_ge_suffixR"],"/",stats["pairs"])
    bad2=[r for r in rows if r["v2J"]<r["prefix_D"]]
    bad3=[r for r in rows if r["v3J"]<r["suffix_R"]]
    print("BAD_PREFIX_LOWER",json.dumps(bad2[:5],sort_keys=True))
    print("BAD_SUFFIX_LOWER",json.dumps(bad3[:5],sort_keys=True))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=46081)
    ap.add_argument("--hi",type=int,default=46591)
    ap.add_argument("--K",type=int,default=128)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    analyze(a.lo,a.hi,a.K,a.output)
