#!/usr/bin/env python3
"""Exact shifted cross-valuation coalescence scout.

For
    n(z) = 2^K (2^S z + r) - 1
compare against the systematically generated smaller families
    p_{g,delta}(z) = 2^(K-g) (2^S z + r + delta) - 1.

The existing production coalescence is exactly (g=1, delta=0).
This scout enumerates symmetric small shifts and valuation gaps, asks whether
the two deterministic affine trajectories reach the same state, and retains
only classes not already killed by the production baseline.

Every accepted family is independently replayed on concrete z values and must
remain below the certified lower boundary L throughout the live interval.
"""
from __future__ import annotations
import argparse

L=2392312122059207475200
U=3143983941795894239301


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


def cert(K:int,S:int,r:int,g:int,delta:int):
    A=1<<(K+S)
    B=(1<<K)*r-1
    PA=A>>g
    PB=(1<<(K-g))*(r+delta)-1

    tn=affine_trajectory(A,B)
    tp=affine_trajectory(PA,PB)
    common=set(tn).intersection(tp)
    if not common:
        return None
    state=min(common,key=lambda q:(tn[q]+tp[q],tn[q],tp[q],q))
    t_n,t_p=tn[state],tp[state]

    # The whole live family must point below L, not merely below n.
    # p=(n+1)/2^g + 2^(K-g) delta - 1 is monotone in n.
    pmax=(U+1)//(1<<g)+(1<<(K-g))*delta-1
    if pmax>=L:
        return None

    for z in (1,17):
        n=A*z+B
        p=PA*z+PB
        assert 0<p<n,(K,S,r,g,delta,z,n,p)
        x=n
        for _ in range(t_n): x=T(x)
        y=p
        for _ in range(t_p): y=T(y)
        assert x==y,(K,S,r,g,delta,z,t_n,t_p,x,y)

    return (t_n,t_p,state)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--k",type=int,default=27)
    ap.add_argument("--s",type=int,default=14)
    ap.add_argument("--max-gap",type=int,default=3)
    ap.add_argument("--shift",type=int,default=16)
    A=ap.parse_args()
    assert 4<=A.s<=18
    assert 1<=A.max_gap<A.k
    assert 0<=A.shift<=64

    odd=range(1,1<<A.s,2)
    baseline=set()
    for r in odd:
        if cert(A.k,A.s,r,1,0):
            baseline.add(r)

    union=set(baseline)
    print("SHIFTED_COALESCENCE_BASELINE",
          f"K={A.k}",f"S={A.s}",
          f"classes={len(baseline)}",f"odd_classes={1<<(A.s-1)}")

    ranked=[]
    for g in range(1,A.max_gap+1):
        for delta in range(-A.shift,A.shift+1):
            if g==1 and delta==0:
                continue
            got=set()
            for r in odd:
                # Ensure positive lower-family constant for replay controls.
                if r+delta<=0:
                    continue
                if cert(A.k,A.s,r,g,delta):
                    got.add(r)
            new=got-union
            if new:
                ranked.append((len(new),g,delta,len(got)))
                union|=got
                print("SHIFT_CENSUS",
                      f"gap={g}",f"delta={delta}",
                      f"raw={len(got)}",f"new={len(new)}",
                      f"union={len(union)}")

    ranked.sort(reverse=True)
    print("TOP_SHIFTS",ranked[:20])
    print("FINAL_UNION",len(union))
    print("STRICT_EXTRA",len(union-baseline))
    print("ODD_CLASSES",1<<(A.s-1))
    print("VERIFIED_SHIFTED_CROSS_VALUATION_COALESCENCE")


if __name__=="__main__":
    main()
