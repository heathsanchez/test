#!/usr/bin/env python3
"""Exact cylinders for complete odd Collatz episodes.

For odd x=2^r m-1 with m odd, one complete odd episode is

    x' = (3^r m - 1) / 2^s
    r' = v2(x'+1)
    m' = (x'+1)/2^r'.

Put D=s+r'.  Exact valuation r' means

    v2(3^r m + 2^s - 1) = D,

not merely divisibility by 2^D.  Therefore

    3^r m + 2^s - 1 == 2^D  (mod 2^(D+1)),

and since 3^r is odd,

    m == (2^D - 2^s + 1) * 3^(-r)  (mod 2^(D+1)).

So one exact episode schema (r,s,r') is a UNIQUE odd cylinder modulo
2^(s+r'+1).  Modulo only 2^(s+r') the two top-bit extensions cannot both
have the same exact valuation; one of them leaves the schema.

For a concrete exact prefix of several episodes with composed map

    m_j = (A m_0 + B) / 2^D,

the fact that m_j is odd similarly gives the exact endpoint cylinder

    m_0 == (2^D - B) * A^(-1)  (mod 2^(D+1)).

This script verifies both statements exhaustively on bounded concrete states
and on full prefixes.  It is an exact cylinder-semantics correction and
foundation for later symbolic work; it is not a Collatz proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from collatz_odd_episode_grammar import episode


def exact_branch_cylinder(r:int,s:int,rp:int):
    D=s+rp
    mod=1<<(D+1)
    rho=((1<<D)-(1<<s)+1)*pow(3**r,-1,mod)%mod
    return D,rho,mod


def compose_step(A:int,B:int,D:int,r:int,s:int,rp:int):
    d=s+rp
    return (
        (3**r)*A,
        (3**r)*B + ((1<<s)-1)*(1<<D),
        D+d,
    )


def replay_schema(r:int,m:int):
    x=(1<<r)*m-1
    rr,mm,s,rp,mp,xp=episode(x)
    assert (rr,mm)==(r,m)
    return s,rp,mp,xp


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=16)
    ap.add_argument("--precision",type=int,default=16)
    ap.add_argument("--prefix-cap",type=int,default=128)
    ap.add_argument("--out")
    a=ap.parse_args()

    assert 1<=a.max_r<=24
    assert 8<=a.precision<=20
    assert 1<=a.prefix_cap<=512

    M=1<<a.precision
    branch_controls=0
    lift_controls=0
    sibling_separations=0
    prefix_controls=0
    max_exact_bits=0
    max_prefix_bits=0

    examples=[]

    for r0 in range(1,a.max_r+1):
        for m0 in range(1,M,2):
            x0=(1<<r0)*m0-1
            if x0==1:
                continue

            # First-episode exact cylinder.
            s,rp,mp,xp=replay_schema(r0,m0)
            D,rho,mod=exact_branch_cylinder(r0,s,rp)
            assert m0%mod==rho,(r0,m0,s,rp,D,rho,m0%mod)
            max_exact_bits=max(max_exact_bits,D+1)

            # Sufficiency on deterministic lifts of the exact cylinder.
            for k in (0,1,3):
                mm=rho+k*mod
                if mm<=0:
                    continue
                ss,rrp,mmp,xxp=replay_schema(r0,mm)
                assert (ss,rrp)==(s,rp),(r0,s,rp,rho,mod,k,ss,rrp)
                lift_controls+=1

            # The sibling sharing only the lower D bits must NOT have the
            # same exact schema.
            sibling=rho^(1<<D)
            if sibling>0:
                ss,rrp,_,_=replay_schema(r0,sibling)
                assert (ss,rrp)!=(s,rp),(r0,s,rp,D,rho,sibling)
                sibling_separations+=1

            branch_controls+=1

            # Full-prefix endpoint cylinder.
            x=x0
            A,B,CD=1,0,0
            for j in range(a.prefix_cap):
                rr,mm,s,rp,mp,xp=episode(x)
                A,B,CD=compose_step(A,B,CD,rr,s,rp)
                cmod=1<<(CD+1)
                crho=((1<<CD)-B)*pow(A,-1,cmod)%cmod
                assert m0%cmod==crho,(r0,m0,j,CD,crho,m0%cmod)
                assert (A*m0+B)%cmod==(1<<CD)
                assert (A*m0+B)//(1<<CD)==mp
                assert mp&1
                max_prefix_bits=max(max_prefix_bits,CD+1)
                prefix_controls+=1

                if len(examples)<64 and j<2:
                    examples.append({
                        "r0":r0,"m0":m0,"episode":j+1,
                        "r":rr,"s":s,"rp":rp,
                        "exact_branch_bits":s+rp+1,
                        "prefix_bits":CD+1,
                        "prefix_residue":crho,
                    })

                if xp<x0:
                    break
                x=xp

    out={
        "kind":"exact_complete_odd_episode_cylinders",
        "max_r":a.max_r,
        "precision":a.precision,
        "branch_controls":branch_controls,
        "lift_controls":lift_controls,
        "sibling_separations":sibling_separations,
        "prefix_controls":prefix_controls,
        "max_exact_branch_bits":max_exact_bits,
        "max_prefix_bits":max_prefix_bits,
        "exact_branch_modulus_rule":"2^(s+r_prime+1)",
        "exact_prefix_modulus_rule":"2^(D_total+1)",
        "examples":examples,
        "proof_status":"exact_general_formula_with_bounded_exhaustive_controls_not_global_proof",
    }

    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print(
        "EXACT_EPISODE_CYLINDERS",
        f"max_r={a.max_r}",
        f"precision={a.precision}",
        f"branch_controls={branch_controls}",
        f"lift_controls={lift_controls}",
        f"sibling_separations={sibling_separations}",
        f"prefix_controls={prefix_controls}",
        f"max_exact_branch_bits={max_exact_bits}",
        f"max_prefix_bits={max_prefix_bits}",
    )
    print("EXACT_BRANCH_REQUIRES_ONE_VALUATION_BIT_BEYOND_DENOMINATOR")
    print("VERIFIED_EXACT_COMPLETE_ODD_EPISODE_CYLINDERS")


if __name__=="__main__":
    main()
