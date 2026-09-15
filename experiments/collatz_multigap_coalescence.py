#!/usr/bin/env python3
"""Exact multi-gap cross-valuation coalescence scout.

For fixed n_K(z)=2^(K+S)z + 2^K r - 1, compare against the strictly
smaller same-m families n_(K-g)(z)=2^(K-g+S)z + 2^(K-g)r - 1.

While affine parity is deterministic, both trajectories are exact affine
functions of z.  A common affine state closes the whole r-class by strong
induction.  The existing production sieve is g=1; this scout asks whether
larger valuation gaps add nonredundant classes.
"""
from __future__ import annotations
import argparse

def T(n:int)->int:
    return (3*n+1)//2 if n&1 else n//2

def affine_trajectory(A:int,B:int):
    out={}
    t=0
    while True:
        out[(A,B)]=t
        if A&1:
            return out
        if B&1:
            A=3*A//2
            B=(3*B+1)//2
        else:
            A//=2
            B//=2
        t+=1

def gap_set(K:int,S:int,g:int):
    assert 1<=g<K
    out=set()
    A=1<<(K+S)
    for r in range(1,1<<S,2):
        B=(1<<K)*r-1
        P_A=A>>g
        P_B=(1<<(K-g))*r-1
        tn=affine_trajectory(A,B)
        tp=affine_trajectory(P_A,P_B)
        common=set(tn).intersection(tp)
        if not common:
            continue
        state=min(common,key=lambda q:(tn[q]+tp[q],tn[q],tp[q],q))
        # independent concrete replay on two family members
        for z in (1,17):
            n=A*z+B
            p=P_A*z+P_B
            assert p<n
            x=n
            for _ in range(tn[state]): x=T(x)
            y=p
            for _ in range(tp[state]): y=T(y)
            assert x==y,(K,S,g,r,z,tn[state],tp[state],x,y)
        out.add(r)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--k",type=int,default=28)
    ap.add_argument("--s",type=int,default=16)
    ap.add_argument("--max-gap",type=int,default=5)
    A=ap.parse_args()
    assert 2<=A.s<=20 and 2<=A.max_gap<A.k

    union=set()
    for g in range(1,A.max_gap+1):
        s=gap_set(A.k,A.s,g)
        new=s-union
        union|=s
        print("GAP_CENSUS",
              f"K={A.k}",f"S={A.s}",f"gap={g}",
              f"raw={len(s)}",f"new={len(new)}",f"union={len(union)}",
              f"odd_classes={1<<(A.s-1)}")
    if A.k==28 and A.s==16 and A.max_gap>=5:
        assert len(gap_set(28,16,1))==17917
        assert len(union)==17938
    print("VERIFIED_MULTI_GAP_COALESCENCE_SCOUT")

if __name__=="__main__":
    main()
