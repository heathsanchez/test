#!/usr/bin/env python3
"""Bounded adversarial test: does hereditary q=0 RIGID imply low parity complexity?

External formal work shows an unbounded Collatz orbit cannot have a uniform
factor-complexity envelope of slope <5/3.  A possible finish would therefore
be a theorem that the hereditary RIGID boundary language has such an upper
bound.

This script does NOT assume that theorem. It searches for the smallest exact
bounded separator among q=0 RIGID prefixes.

For each fixed source n that survives to q=0 as RIGID, collect the maximal
consecutive shortcut parity word for which every q=0 boundary state remains
RIGID.  Compute finite factor counts p_L of that word and report violations
of:
  p_L <= L+1        (Sturmian/mechanical-level)
  3 p_L <= 5 L + C for small additive C
The finite prefix count is only a necessary sanity test, not a theorem about
an infinite itinerary.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base


def rigid_word(n:int,H:int):
    k0=n.bit_length()
    if base.birth_status(n)[0]!="RIGID":
        return ""
    y=n
    for _ in range(k0):
        y=base.T(y)
    bits=[]
    for k in range(k0,k0+H):
        if base.cylinder_status(k,n)[0]!="RIGID":
            break
        bits.append("1" if y&1 else "0")
        y=base.T(y)
    return "".join(bits)


def complexity(w:str,L:int)->int:
    if L<=0 or L>len(w): return 0
    return len({w[i:i+L] for i in range(len(w)-L+1)})


def audit(N:int,H:int,maxL:int,C:int):
    sources=0; words=0
    sturm_sep=None; linear_sep=None
    worst=[]
    for n in range(3,N+1,2):
        ok,_=base.survives_to_q0(n)
        if not ok or base.birth_status(n)[0]!="RIGID":
            continue
        sources+=1
        w=rigid_word(n,H)
        if not w: continue
        words+=1
        for L in range(1,min(maxL,len(w))+1):
            p=complexity(w,L)
            excess_sturm=p-(L+1)
            excess_53=3*p-(5*L+C)
            worst.append((excess_53,excess_sturm,n,len(w),L,p,w[:80]))
            if excess_sturm>0 and sturm_sep is None:
                sturm_sep=(n,len(w),L,p,w)
            if excess_53>0 and linear_sep is None:
                linear_sep=(n,len(w),L,p,w)
    worst.sort(reverse=True)
    print("SOURCE_LIMIT",N)
    print("HEREDITARY_RIGID_SOURCES",sources)
    print("NONEMPTY_RIGID_WORDS",words)
    print("ADDITIVE_C",C)
    print("STURMIAN_BOUND_SEPARATOR",sturm_sep)
    print("FIVE_THIRDS_BOUND_SEPARATOR",linear_sep)
    print("WORST",worst[:20])
    if linear_sep is None:
        print("OBSERVED_FINITE_RIGID_PREFIXES_WITHIN_FIVE_THIRDS_ENVELOPE")
    else:
        print("SEPARATOR_RIGID_DOES_NOT_IMPLY_TESTED_LOW_COMPLEXITY")
    print("STATUS BOUNDED_SANITY_ONLY")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=8191)
    ap.add_argument("--H",type=int,default=128)
    ap.add_argument("--max-L",type=int,default=32)
    ap.add_argument("--C",type=int,default=8)
    a=ap.parse_args()
    audit(a.N,a.H,a.max_L,a.C)
