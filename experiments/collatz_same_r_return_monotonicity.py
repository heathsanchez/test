#!/usr/bin/env python3
"""Test exact monotonicity at repeated r-states on stabilized Collatz tails.

For odd episode states x_j = 2^r m_j - 1, a return to the same
r=v2(x+1) lets us compare ordinary integers at the same scale directly.

Candidate bounded-r rank:
    for each r, remember the previous odd state seen at r.
If every later return to that r is strictly smaller, then an infinite
trajectory with bounded r is impossible: finitely many r-slots cannot each
support infinitely many strict descents in positive integers.

This script tests that candidate exactly on bounded domains and on the known
H512 boundary core.  A single increasing/equal return falsifies the candidate;
the script reports the first witness rather than hiding it.
"""

from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from collatz_odd_episode_grammar import episode

BOUNDARY_CORE=26130934783


def v2(n:int)->int:
    return (n & -n).bit_length()-1


def decomp(x:int):
    r=v2(x+1);m=(x+1)>>r
    return r,m


def trace_case(x0:int,cap:int=1024):
    x=x0
    last={}
    counts=Counter()
    first_bad=None
    max_ratio_num=0;max_ratio_den=1
    returns=[]

    for j in range(cap):
        r,m,s,rp,mp,xp=episode(x)
        if r in last:
            prev_j,prev_x,prev_m=last[r]
            if x<prev_x: kind="decrease"
            elif x==prev_x: kind="equal"
            else: kind="increase"
            counts[kind]+=1
            if x*max_ratio_den > max_ratio_num*prev_x:
                max_ratio_num=x;max_ratio_den=prev_x
            item={
                "episode":j+1,"r":r,
                "previous_episode":prev_j,
                "previous_x":prev_x,"current_x":x,
                "previous_m":prev_m,"current_m":m,
                "kind":kind,
            }
            returns.append(item)
            if kind!="decrease" and first_bad is None:
                first_bad=item
        last[r]=(j+1,x,m)
        if xp<x0:
            return {
                "descended":True,"episodes":j+1,"counts":dict(counts),
                "first_bad":first_bad,
                "max_return_ratio_num":max_ratio_num,
                "max_return_ratio_den":max_ratio_den,
                "returns":returns,
            }
        x=xp
    return {
        "descended":False,"episodes":cap,"counts":dict(counts),
        "first_bad":first_bad,
        "max_return_ratio_num":max_ratio_num,
        "max_return_ratio_den":max_ratio_den,
        "returns":returns,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=12)
    ap.add_argument("--precision",type=int,default=14)
    ap.add_argument("--cap",type=int,default=256)
    ap.add_argument("--out")
    a=ap.parse_args()
    M=1<<a.precision

    total=0; returns=0; dec=eq=inc=0; unresolved=0
    first_bad=None
    bad_seed=None
    max_return_ratio_num=0;max_return_ratio_den=1

    for r0 in range(1,a.max_r+1):
        for m0 in range(1,M,2):
            x0=(1<<r0)*m0-1
            if x0==1:continue
            total+=1
            z=trace_case(x0,a.cap)
            if not z["descended"]:unresolved+=1
            c=z["counts"]
            dec+=c.get("decrease",0);eq+=c.get("equal",0);inc+=c.get("increase",0)
            returns+=sum(c.values())
            if z["first_bad"] is not None and first_bad is None:
                first_bad=z["first_bad"];bad_seed=x0
            rn=z["max_return_ratio_num"];rd=z["max_return_ratio_den"]
            if rd and rn*max_return_ratio_den>max_return_ratio_num*rd:
                max_return_ratio_num=rn;max_return_ratio_den=rd

    core=trace_case(BOUNDARY_CORE,2048)
    cc=core["counts"]

    out={
        "kind":"same_r_return_monotonicity_test",
        "max_r":a.max_r,"precision":a.precision,"cases":total,
        "unresolved":unresolved,
        "returns":returns,"decrease":dec,"equal":eq,"increase":inc,
        "candidate_strict_decrease_holds_bounded":eq==0 and inc==0,
        "first_bad_seed":bad_seed,"first_bad_return":first_bad,
        "max_return_ratio_num":max_return_ratio_num,
        "max_return_ratio_den":max_return_ratio_den,
        "boundary_core":{
            "seed":BOUNDARY_CORE,
            "episodes":core["episodes"],
            "descended":core["descended"],
            "counts":cc,
            "first_bad":core["first_bad"],
        },
        "proof_status":"bounded exact test of candidate rank; universal claim only if separately proved",
    }
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("SAME_R_RETURN_MONOTONICITY",
          f"max_r={a.max_r}",f"precision={a.precision}",
          f"cases={total}",f"returns={returns}",
          f"decrease={dec}",f"equal={eq}",f"increase={inc}",
          f"unresolved={unresolved}")
    if first_bad:
        print("SAME_R_RETURN_COUNTEREXAMPLE",
              f"seed={bad_seed}",
              json.dumps(first_bad,separators=(",",":")))
    print("BOUNDARY_CORE_SAME_R_RETURNS",
          f"episodes={core['episodes']}",
          f"decrease={cc.get('decrease',0)}",
          f"equal={cc.get('equal',0)}",
          f"increase={cc.get('increase',0)}")
    if eq==0 and inc==0:
        print("BOUNDED_TEST_SUPPORTS_STRICT_SAME_R_DESCENT")
    else:
        print("STRICT_SAME_R_DESCENT_CANDIDATE_FALSIFIED")
    print("VERIFIED_SAME_R_RETURN_MONOTONICITY_CENSUS")


if __name__=="__main__":
    main()
