#!/usr/bin/env python3
"""Exact global cross-valuation affine-state coalescence.

Fix target families
    n_r(z)=2^(K+S) z + 2^K r - 1,  r odd.

For every lower valuation K-g and every odd residue r' mod 2^S, build
    p_{g,r'}(z)=2^(K-g+S) z + 2^(K-g) r' - 1.

While the z coefficient is even, shortcut-Collatz parity is deterministic.
We hash every affine state reached by every lower family. A target residue is
inductively closed if its deterministic affine trajectory hits any state in
that lower-family bank.

This strictly contains same-r, small-shift, and multi-gap coalescence searches.
"""
from __future__ import annotations
import argparse

L=2392312122059207475200
U=3143983941795894239301


def T(n:int)->int:
    return (3*n+1)//2 if n&1 else n//2


def states(A:int,B:int):
    out=[]
    t=0
    while True:
        out.append(((A,B),t))
        if A&1:
            return out
        if B&1:
            A=3*A//2
            B=(3*B+1)//2
        else:
            A//=2
            B//=2
        t+=1


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--k",type=int,default=27)
    ap.add_argument("--s",type=int,default=14)
    ap.add_argument("--max-gap",type=int,default=3)
    A=ap.parse_args()
    assert 4<=A.s<=16
    assert 1<=A.max_gap<A.k

    target_A=1<<(A.k+A.s)
    odd=list(range(1,1<<A.s,2))

    # Universal live z ceiling across all target residues.
    min_B=(1<<A.k)-1
    zmax=max(1,(U-min_B)//target_A)

    bank={}
    by_gap={}
    for g in range(1,A.max_gap+1):
        kp=A.k-g
        pA=1<<(kp+A.s)
        # Every lower family represented here must stay below L on all live z.
        pmax=pA*zmax + (1<<kp)*((1<<A.s)-1)-1
        assert pmax<L,(A.k,A.s,g,pmax,L)

        before=len(bank)
        for rp in odd:
            pB=(1<<kp)*rp-1
            for st,tp in states(pA,pB):
                bank.setdefault(st,(g,rp,tp))
        by_gap[g]=len(bank)-before

    killed={}
    baseline=set()
    for r in odd:
        nB=(1<<A.k)*r-1
        tr=states(target_A,nB)

        # production same-r gap1 baseline
        pA=target_A>>1
        pB=(1<<(A.k-1))*r-1
        p_states={st:tp for st,tp in states(pA,pB)}
        if any(st in p_states for st,_ in tr):
            baseline.add(r)

        for st,tn in tr:
            hit=bank.get(st)
            if hit is None:
                continue
            g,rp,tp=hit
            killed[r]=(g,rp,tn,tp,st)
            break

    # Independent concrete replay for every accepted target class on two z.
    for r,(g,rp,tn,tp,st) in killed.items():
        kp=A.k-g
        for z in (1,17):
            n=target_A*z+(1<<A.k)*r-1
            p=(1<<(kp+A.s))*z+(1<<kp)*rp-1
            assert 0<p<n,(r,g,rp,z,p,n)
            x=n
            for _ in range(tn): x=T(x)
            y=p
            for _ in range(tp): y=T(y)
            assert x==y==st[0]*z+st[1],(r,g,rp,z,tn,tp,x,y,st)

    got=set(killed)
    extra=got-baseline
    hist={}
    for r in extra:
        g=killed[r][0]
        hist[g]=hist.get(g,0)+1

    print("GLOBAL_COALESCENCE",
          f"K={A.k}",f"S={A.s}",f"max_gap={A.max_gap}",
          f"bank_states={len(bank)}",
          f"baseline={len(baseline)}",
          f"killed={len(got)}",
          f"strict_extra={len(extra)}",
          f"odd_classes={len(odd)}")
    for g in sorted(by_gap):
        print("BANK_GAP",f"gap={g}",f"new_states={by_gap[g]}")
    for g in sorted(hist):
        print("EXTRA_BY_GAP",f"gap={g}",f"classes={hist[g]}")
    print("VERIFIED_GLOBAL_CROSS_VALUATION_COALESCENCE")


if __name__=="__main__":
    main()
