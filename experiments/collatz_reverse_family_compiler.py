#!/usr/bin/env python3
"""Compile a fixed reverse-word separator into an infinite-family descent proof.

Input data:
  * endpoint family x(t) = X0 + XSTEP*t;
  * one witnessed compatible pair (t0,n0);
  * a fixed shortcut parity word W of length K taking n0 to x(t0).

For W with c odd steps,
    2^K x = 3^c n + B_W.

Because XSTEP is a power of two in the applications here, it is invertible
modulo 3^c.  Therefore integrality of n forces one exact residue:
    t == t0 (mod 3^c).

Writing t=t0+3^c*s gives an infinite source family
    n_s = n0 + 2^K*XSTEP*s.

For every prefix j of W, derive
    2^j T^j(n) = A_j n + B_j
and search for the earliest prefix with A_j < 2^j and
    A_j*n0 + B_j < 2^j*n0.
Since n_s >= n0 for s>=0, the same strict descent then holds for the entire
family.

Exact symbolic compiler; does not prove Collatz globally.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyCertificate:
    K:int
    odd_count:int
    full_B:int
    t_modulus:int
    source_step:int
    prefix_j:int
    prefix_A:int
    prefix_B:int


def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2


def prefix_affines(word:str):
    A=1
    B=0
    rows=[]
    for j,ch in enumerate(word,1):
        if ch=="O":
            B=3*B+(1<<(j-1))
            A=3*A
        elif ch=="E":
            pass
        else:
            raise ValueError(ch)
        rows.append((j,A,B))
    return rows


def compile_family(X0:int,XSTEP:int,t0:int,n0:int,word:str)->FamilyCertificate:
    K=len(word)
    rows=prefix_affines(word)
    odd=word.count("O")
    full_A=3**odd
    full_B=rows[-1][2] if rows else 0
    x0=X0+XSTEP*t0

    assert (1<<K)*x0 == full_A*n0 + full_B

    # Verify the witnessed parity word concretely.
    y=n0
    obs=[]
    for _ in range(K):
        obs.append("O" if y&1 else "E")
        y=T(y)
    assert "".join(obs)==word
    assert y==x0

    t_mod=3**odd
    # Coefficient of t in the full numerator is 2^K * XSTEP and hence coprime
    # to 3^odd because XSTEP is a power of two.
    assert XSTEP>0 and XSTEP&(XSTEP-1)==0
    assert ((1<<K)*XSTEP)%3 != 0

    source_step=(1<<K)*XSTEP

    # Earliest prefix that contracts the minimum source n0.  Once A<2^j,
    # increasing n only makes the descent inequality stronger.
    chosen=None
    for j,A,B in rows:
        if A >= (1<<j):
            continue
        if A*n0+B < (1<<j)*n0:
            chosen=(j,A,B)
            break
    assert chosen is not None

    return FamilyCertificate(
        K=K,odd_count=odd,full_B=full_B,t_modulus=t_mod,
        source_step=source_step,prefix_j=chosen[0],
        prefix_A=chosen[1],prefix_B=chosen[2],
    )


def verify_samples(cert:FamilyCertificate,X0:int,XSTEP:int,t0:int,n0:int,
                   word:str,samples:int):
    for s in range(samples):
        t=t0+cert.t_modulus*s
        n=n0+cert.source_step*s
        x=X0+XSTEP*t

        # Full word.
        y=n
        obs=[]
        for _ in range(cert.K):
            obs.append("O" if y&1 else "E")
            y=T(y)
        assert "".join(obs)==word
        assert y==x

        # Contracting prefix.
        z=n
        for _ in range(cert.prefix_j):
            z=T(z)
        assert (1<<cert.prefix_j)*z == cert.prefix_A*n+cert.prefix_B
        assert z<n


def main(samples:int):
    # First discovered C9 three-replay non-direct reverse family.
    X0=326575849
    XSTEP=1<<29
    t0=153
    n0=30098547115
    word="OOEOEOEOOOOEEOOEEOOOOOOOOEOOOEOEEOE"

    cert=compile_family(X0,XSTEP,t0,n0,word)
    verify_samples(cert,X0,XSTEP,t0,n0,word,samples)

    print("WORD",word)
    print("FULL_LENGTH",cert.K)
    print("ODD_COUNT",cert.odd_count)
    print("FULL_B",cert.full_B)
    print("T_RESIDUE",t0,"mod",cert.t_modulus)
    print("SOURCE_FAMILY",n0,"+",cert.source_step,"* s")
    print("CONTRACTING_PREFIX",cert.prefix_j)
    print("PREFIX_IDENTITY",
          1<<cert.prefix_j,"* T^j(n) =",
          cert.prefix_A,"* n +",cert.prefix_B)
    print("PREFIX_GAP",
          (1<<cert.prefix_j)-cert.prefix_A,"* n -",cert.prefix_B)
    print("PASS_REVERSE_FAMILY_COMPILER_T153")
    print("STATUS EXACT_REUSABLE_REVERSE_FAMILY_COMPILER")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--samples",type=int,default=4)
    a=ap.parse_args()
    main(a.samples)
