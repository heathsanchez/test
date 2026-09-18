#!/usr/bin/env python3
"""Bit-prefix audit for the expanding C9 high-fuel endpoint cylinder.

Target two-replay endpoint:
    x == 468713 (mod 2^20).

For every hereditary q=0 RIGID birth source n <= N, follow H ordinary boundary
steps and measure the largest j<=20 for which an endpoint y satisfies
    y == 468713 (mod 2^j).

This is deliberately cheaper than classifying every post-q0 state.  If a bit
precision is absent even from the raw ordinary boundary orbits of all hard
births, it is certainly absent from the stricter RIGID sublanguage.

Bounded census only; not a proof.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base

TARGET=468713
BITS=20


def v2_abs(x:int)->int:
    if x==0:
        return 10**9
    x=abs(x)
    return (x & -x).bit_length()-1


def audit(N:int,H:int):
    ge=[0]*(BITS+1)
    exact=Counter()
    best=(-1,None)
    sources=0
    states=0
    for n in range(3,N+1,2):
        if base.birth_status(n)[0]!='RIGID':
            continue
        survives,_=base.survives_to_q0(n)
        if not survives:
            continue
        sources+=1
        k0=n.bit_length()
        _,y=base.forward_state(k0,n)
        for t in range(H+1):
            if t:
                y=base.T(y)
            states+=1
            j=min(BITS,v2_abs(y-TARGET))
            exact[j]+=1
            for b in range(1,j+1):
                ge[b]+=1
            if j>best[0]:
                best=(j,(n,k0+t,y,y%(1<<BITS)))
    print("SOURCE_LIMIT",N)
    print("HORIZON",H)
    print("HEREDITARY_Q0_RIGID_BIRTHS",sources)
    print("BOUNDARY_STATES_SCANNED",states)
    print("MAX_MATCH_BITS",best[0])
    print("BEST_MATCH",best[1])
    print("MATCH_COUNTS_GE",[(j,ge[j]) for j in range(1,BITS+1)])
    print("EXACT_MATCH_HIST",sorted(exact.items()))
    missing=[j for j in range(1,BITS+1) if ge[j]==0]
    print("FIRST_ABSENT_PRECISION",missing[0] if missing else None)
    if ge[BITS]:
        print("SEPARATOR_FULL_C9_HIGH_FUEL_RESIDUE_APPEARS",ge[BITS])
    else:
        print("OBSERVED_C9_HIGH_FUEL_RESIDUE_ABSENT")
    print("STATUS BOUNDED_RESIDUE_PREFIX_CENSUS_ONLY")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=(1<<20)-1)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args()
    audit(a.N,a.H)
