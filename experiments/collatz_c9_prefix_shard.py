#!/usr/bin/env python3
"""Sharded C9 high-fuel prefix census at scale.

Target two-replay endpoint cylinder for the expanding C9 cycle:
    y == 468713 (mod 2^20).

For hereditary q=0 RIGID births in [lo,hi], follow H boundary steps and record
only matches of at least 17 low bits.  This is the cheap adversarial extension
of the million-source census: either produce the first 18-bit match or push the
observed forbidden-prefix gap to a much larger prospective range.

Bounded census only; not a proof.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base

TARGET=468713
MIN_BITS=17
FULL_BITS=20

def v2abs(x:int)->int:
    if x==0:return 10**9
    x=abs(x)
    return (x&-x).bit_length()-1

def audit(lo:int,hi:int,H:int):
    births=states=0
    counts=Counter()
    hits=[]
    mask=(1<<MIN_BITS)-1
    low=TARGET&mask
    for n in range(max(3,lo)|1,hi+1,2):
        if base.birth_status(n)[0]!='RIGID':
            continue
        ok,_=base.survives_to_q0(n)
        if not ok:
            continue
        births+=1
        k0=n.bit_length()
        _,y=base.forward_state(k0,n)
        for t in range(H+1):
            if t:y=base.T(y)
            states+=1
            if y&mask != low:
                continue
            j=min(FULL_BITS,v2abs(y-TARGET))
            counts[j]+=1
            row=(n,k0+t,y,j,(y-TARGET)>>MIN_BITS,y%(1<<FULL_BITS))
            hits.append(row)
            if j>=18:
                print("C9_18BIT_OR_BETTER_HIT",row)
    print("SOURCE_RANGE",lo,hi)
    print("HORIZON",H)
    print("HEREDITARY_RIGID_BIRTHS",births)
    print("BOUNDARY_STATES",states)
    print("MATCH_EXACT",dict(sorted(counts.items())))
    print("MATCH_GE17",len(hits))
    print("MATCH_GE18",sum(v for j,v in counts.items() if j>=18))
    print("MATCH_GE19",sum(v for j,v in counts.items() if j>=19))
    print("MATCH_GE20",sum(v for j,v in counts.items() if j>=20))
    for row in hits[:20]:print("NEAR_HIT",row)
    if any(j>=18 for j in counts):
        print("SEPARATOR_C9_18BIT_MATCH_FOUND")
    else:
        print("OBSERVED_NO_C9_18BIT_MATCH")
    print("STATUS BOUNDED_SHARDED_PREFIX_CENSUS_ONLY")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,required=True)
    ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args()
    audit(a.lo,a.hi,a.H)
