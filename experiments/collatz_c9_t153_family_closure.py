#!/usr/bin/env python3
"""Exact symbolic closure of the C9 three-replay t=153 reverse family.

Three-replay endpoint lifts are
    x(t) = 326575849 + 2^29 t.

The first discovered q=0-compatible non-direct reverse ancestor used the
35-step parity word

    OOEOEOEOOOOEEOOEEOOOOOOOOEOOOEOEEOE

with 23 odd steps and
    t0 = 153,
    n0 = 30098547115,
    T^35(n0) = x(t0).

For this fixed parity word,
    2^35 x = 3^23 n + B35,
with B35 = 526178937575.

Since 2^64 is invertible modulo 3^23, integrality of n for x(t) forces
    t == 153 (mod 3^23).

Thus every nonnegative lift in this reverse-word family is
    t_s = 153 + 3^23 s,
    n_s = n0 + 2^64 s.

All n_s have the same first five parity symbols OOEOE, and exactly
    T^5(n_s) = (27 n_s + 23)/32 < n_s
for every positive n_s.

Therefore this entire infinite reverse-word family is closed by direct descent
before q=0.  Pure exact arithmetic; this does not prove Collatz globally.
"""
from __future__ import annotations
import argparse

T0=153
N0=30098547115
BASE_X=326575849
X_STEP=1<<29
WORD="OOEOEOEOOOOEEOOEEOOOOOOOOEOOOEOEEOE"
K=35
C=WORD.count("O")
B35=526178937575
MOD3=3**C


def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2


def endpoint(t:int)->int:
    return BASE_X + X_STEP*t


def source_from_t_if_word(t:int):
    num=(1<<K)*endpoint(t)-B35
    den=3**C
    if num%den:
        return None
    return num//den


def family_t(s:int)->int:
    return T0 + MOD3*s


def family_n(s:int)->int:
    return N0 + (1<<64)*s


def main(samples:int):
    assert len(WORD)==K
    assert C==23
    assert source_from_t_if_word(T0)==N0

    # Unique t residue modulo 3^23 for this reverse word.
    for delta in range(-8,9):
        t=T0+delta
        if t<0:
            continue
        n=source_from_t_if_word(t)
        assert (n is not None)==(delta==0)

    print("REVERSE_WORD",WORD)
    print("ODD_COUNT",C)
    print("B35",B35)
    print("T_RESIDUE",T0,"mod",MOD3)
    print("SOURCE_FAMILY",N0,"+",1<<64,"* s")

    for s in range(samples):
        t=family_t(s)
        n=family_n(s)
        x=endpoint(t)
        assert source_from_t_if_word(t)==n

        y=n
        observed=[]
        for _ in range(K):
            observed.append("O" if y&1 else "E")
            y=T(y)
        assert "".join(observed)==WORD
        assert y==x

        y5=n
        for _ in range(5):
            y5=T(y5)
        assert 32*y5==27*n+23
        assert y5<n
        print("SAMPLE",s,"t",t,"n",n,"T5",y5,"endpoint",x)

    print("DIRECT_DESCENT_IDENTITY 32*T5 = 27*n + 23")
    print("DIRECT_DESCENT_GAP_IDENTITY 32*(n-T5) = 5*n - 23")
    print("PASS_T153_REVERSE_FAMILY_DIRECT_DESCENT")
    print("STATUS EXACT_SYMBOLIC_FAMILY_CLOSURE")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--samples",type=int,default=4)
    a=ap.parse_args()
    main(a.samples)
