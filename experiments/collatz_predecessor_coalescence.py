#!/usr/bin/env python3
"""Exact cross-valuation predecessor-coalescence sieve for shortcut Collatz.

Fix a valuation slice
    n = 2^K m - 1,   m odd,
and refine
    m = 2^S z + r,   r odd.

Then
    n(z) = 2^(K+S) z + (2^K r - 1)
and the already-lower predecessor is
    p(z) = (n(z)-1)/2.

Because U < 2L+1, every such p for a live n lies below L.

While the affine z-coefficient is even, shortcut-Collatz parity is independent
of z, so T acts exactly on affine pairs (A,B).  If the n-family and p-family
reach the same affine pair before either loses deterministic parity, the whole
residue family coalesces into the already-lower trajectory and is inductively
closed.

This strictly generalizes the m mod 4 half-sieve.
"""
from __future__ import annotations
import argparse

L = 2392312122059207475200
U = 3143983941795894239301


def T(n: int) -> int:
    return (3*n+1)//2 if n & 1 else n//2


def affine_trajectory(A: int, B: int):
    """Exact deterministic affine states until parity begins to depend on z."""
    out = {}
    t = 0
    while True:
        out[(A,B)] = t
        if A & 1:
            return out
        if B & 1:
            A = 3*A//2
            B = (3*B+1)//2
        else:
            A //= 2
            B //= 2
        t += 1


def merge_certificate(K: int, S: int, r: int):
    assert K >= 1 and S >= 1 and r & 1 and 0 < r < (1<<S)
    A = 1 << (K+S)
    B = (1<<K)*r - 1
    assert B & 1

    Ap = A//2
    Bp = (B-1)//2

    tn = affine_trajectory(A,B)
    tp = affine_trajectory(Ap,Bp)
    common = set(tn).intersection(tp)
    if not common:
        return None

    state = min(common, key=lambda q: (tn[q]+tp[q], tn[q], tp[q], q))
    t_n, t_p = tn[state], tp[state]

    # Independent concrete replays on two members of the affine family.
    for z in (1,17):
        n = A*z+B
        p = (n-1)//2
        x=n
        for _ in range(t_n):
            x=T(x)
        y=p
        for _ in range(t_p):
            y=T(y)
        assert x==y, (K,S,r,z,t_n,t_p,x,y)
        assert p<n

    return {
        "r":r,
        "t_n":t_n,
        "t_p":t_p,
        "A_common":state[0],
        "B_common":state[1],
    }


def census(K: int, S: int):
    rows=[]
    for r in range(1,1<<S,2):
        c=merge_certificate(K,S,r)
        if c is not None:
            rows.append(c)
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--k",type=int,default=10)
    ap.add_argument("--s",type=int,default=16)
    A=ap.parse_args()
    assert 1 <= A.k <= 40
    assert 2 <= A.s <= 20

    assert U < 2*L+1
    assert (U-1)//2 < L

    rows=census(A.k,A.s)
    total=1<<(A.s-1)
    print("COALESCENCE_CENSUS",
          f"K={A.k}",f"S={A.s}",
          f"killed={len(rows)}",f"odd_classes={total}",
          f"fraction={len(rows)/total:.12f}")

    # The old theorem must be contained exactly.
    old_residue=3 if A.k&1 else 1
    old={r for r in range(1,1<<A.s,2) if r%4==old_residue}
    got={r["r"] for r in rows}
    assert old <= got
    print("OLD_HALF_SIEVE_CLASSES",len(old))
    print("STRICT_EXTRA_CLASSES",len(got-old))

    if A.s==16:
        assert len(rows)==17917, len(rows)

    # Count merge-time geometry; this is useful for future quotienting.
    hist={}
    for r in rows:
        key=(r["t_n"],r["t_p"])
        hist[key]=hist.get(key,0)+1
    for key,count in sorted(hist.items()):
        print("MERGE_TIME",f"tn={key[0]}",f"tp={key[1]}",f"classes={count}")

    print("VERIFIED_CROSS_VALUATION_PREDECESSOR_COALESCENCE")


if __name__=="__main__":
    main()
