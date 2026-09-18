#!/usr/bin/env python3
"""Exact C9 two-replay lift controller.

Every two-replay endpoint lift is
    x(q) = 468713 + 2^20 q
with cofactor
    m(q) = 234357 + 2^19 q.

For C9 defect Delta(m)=(-217)m-467,

    Delta(m(q)) = -2^19 (97 + 217 q).

Hence the exact fuel valuation is
    V(q) = 19 + v2(97+217q),

and the exact replay budget is floor((V-1)/9).

Independent q=0 reachability filter:
    x(q) == q+2 (mod 3),
so q==1 (mod 3) is impossible for any q=0-compatible source.

This script is an exact arithmetic classifier, not a Collatz proof.
"""
from __future__ import annotations
import argparse

BASE_X=468713
STEP_X=1<<20

def v2(n:int)->int:
    assert n
    n=abs(n)
    return (n&-n).bit_length()-1

def endpoint(q:int)->int:
    return BASE_X+STEP_X*q

def fuel(q:int):
    slack=v2(97+217*q)
    V=19+slack
    budget=(V-1)//9
    return slack,V,budget

def classify(q:int)->str:
    if q%3==1:
        return "IMPOSSIBLE_Q0"
    s,V,b=fuel(q)
    if b==2:
        return f"TWO_REPLAY_ONLY_S{s}"
    return f"DEEPER_FUEL_BUDGET_{b}_S{s}"

def main(limit:int):
    observed=[140,146,150,248,356,1149,1230,1839,2094,3894]
    for q in observed:
        print("OBSERVED_Q",q,"X",endpoint(q),"MOD3",q%3,
              "FUEL",fuel(q),"CLASS",classify(q))
        assert q%3!=1
        assert fuel(q)[2]==2

    assert classify(562)=="IMPOSSIBLE_Q0"
    assert fuel(311)[2]>=3
    assert 311%3!=1
    print("Q562",endpoint(562),classify(562))
    print("Q311",endpoint(311),fuel(311),classify(311))

    counts={}
    for q in range(limit):
        c=classify(q)
        counts[c]=counts.get(c,0)+1
    print("CLASS_COUNTS",dict(sorted(counts.items())))
    print("PASS_C9_TWO_REPLAY_LIFT_CONTROLLER")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--q-limit",type=int,default=8192)
    a=ap.parse_args()
    main(a.q_limit)
