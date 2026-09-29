#!/usr/bin/env python3
"""V39 direct-QED falsifier: post-zero-tail K-owner monotonicity.

Test the only remaining scalar direct rank after V38:
once SourceProduct.tail=0, do successive canonical K rewinds strictly lower
their canonical predecessor while the source has not yet hit a simple
OrdinaryExit?

This is a falsifier/discovery gate, not a proof.  A post-zero-tail owner
increase kills the candidate immediately.  Survival does not promote it.
"""
from __future__ import annotations
from collections import Counter
import hashlib,json

import collatz_crystal_k_rewind_v31 as v31
import collatz_crystal_parameter_quotient_v25 as v25
import collatz_crystal_post_p36_adversary_v26 as v26

MOD=v31.MOD

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

def simple_exit(n:int,y:int,k:int):
    if 0<y<n:
        return {"kind":"D","depth":k,"endpoint":str(y)}
    if y%8==5 and y<=4*n:
        return {"kind":"S","depth":k,"endpoint":str(y)}
    if y%3==2:
        p=(2*y-1)//3
        if 0<p<n and T(p)==y:
            return {"kind":"M1","depth":k,"endpoint":str(y),"p":str(p)}
    return None

def source_v26():
    bits=([1,1,0]*((v26.PARITY_LEN+2)//3))[:v26.PARITY_LEN]
    yres,mod=v26.parity_residue(bits)
    t=((yres-v26.A59)*pow(v26.C59,-1,mod))%mod
    return v26.N0+v26.NC*t

def classify_window(states,bits,k):
    # State at depth k, transitions bits[0:k].
    odds=[i for i,b in enumerate(bits[:k]) if b]
    if len(odds)<12:
        return None
    start=odds[-12]
    wb=tuple(bits[start:k])
    assert wb[0]==1 and sum(wb)==12
    S=len(wb)
    x=states[start]
    y=states[k]
    if S>19:
        return {"kind":"B","start":start,"raw_cost":S,"x":x,"y":y}
    w=v31.bits_to_word(wb)
    rawC=v31.cocycle(w)
    assert (pow(2,S)*y-rawC)%MOD==0
    assert (pow(2,S)*y-rawC)//MOD==x
    r=y%MOD
    assert r in v31.best
    bestS,bestC,bestW=v31.best[r]
    p=(pow(2,bestS)*y-bestC)
    assert p%MOD==0
    p//=MOD
    if bestS==S and bestC==rawC:
        return {"kind":"I","start":start,"raw_cost":S,"best_cost":bestS,
                "x":x,"p":p,"y":y,"residue":r}
    assert bestS<S or (bestS==S and bestC>rawC)
    return {"kind":"K","start":start,"raw_cost":S,"best_cost":bestS,
            "drop":S-bestS,"x":x,"p":p,"y":y,"residue":r}

def audit_source(name,n,cap):
    states=[n];bits=[]
    first_exit=None
    K=[]
    zero_depth=n.bit_length()
    for k in range(cap+1):
        y=states[k]
        ex=simple_exit(n,y,k)
        if ex is not None:
            first_exit=ex
            break
        z=classify_window(states,bits,k)
        if z and z["kind"]=="K":
            row={
              "depth":k,"window_start":z["start"],
              "raw_cost":z["raw_cost"],"best_cost":z["best_cost"],
              "drop":z["drop"],"x":str(z["x"]),"p":str(z["p"]),
              "p_ge_source":z["p"]>=n,
              "post_zero_tail":k>=zero_depth,
              "p_minus_source":str(z["p"]-n),
            }
            K.append(row)
        if k==cap: break
        bits.append(y&1)
        states.append(T(y))

    post=[r for r in K if r["post_zero_tail"] and r["p_ge_source"]]
    inc=[];eq=[];dec=[]
    for a,b in zip(post,post[1:]):
        pa=int(a["p"]);pb=int(b["p"])
        item={"from_depth":a["depth"],"to_depth":b["depth"],
              "from_p":a["p"],"to_p":b["p"]}
        if pb>pa: inc.append(item)
        elif pb==pa:eq.append(item)
        else: dec.append(item)
    return {
      "name":name,"source":str(n),"source_bits":zero_depth,
      "first_simple_exit":first_exit,
      "K_events_total":len(K),
      "post_zero_tail_K_ge_source":len(post),
      "post_zero_tail_owner_transitions":{
        "decrease":len(dec),"equal":len(eq),"increase":len(inc),
      },
      "first_increases":inc[:20],
      "post_zero_tail_K":post[:100],
    }

sources=[
 ("V23_MIN",v25.N0,800),
 ("V36_SOURCE",v25.N0+v25.NC*1_018_706,800),
 ("V26_HARD",source_v26(),900),
]
rows=[audit_source(*x) for x in sources]
incs=sum(r["post_zero_tail_owner_transitions"]["increase"] for r in rows)
eqs=sum(r["post_zero_tail_owner_transitions"]["equal"] for r in rows)
result={
 "schema":"COLLATZ_CRYSTAL_ZERO_TAIL_K_RANK_V39",
 "parent":"collatz-crystal-b-transient-v38@b92b6e88a7f55cccd4330a4175d383096a40553b",
 "candidate":"successive source-admitted canonical K predecessors strictly decrease after SourceProduct.tail=0",
 "sources":rows,
 "verdict":(
   "POST_ZERO_TAIL_K_OWNER_RANK_REJECTED"
   if incs or eqs else
   "NO_COUNTEREXAMPLE_ON_FROZEN_EXACT_SOURCES"
 ),
 "claim_boundary":"Exact replay on three frozen adversarial/source-anchor naturals only. Survival is discovery evidence, not universality.",
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
