#!/usr/bin/env python3
"""Exact 2-adic cost of an r' jump in the odd-episode Collatz grammar.

For one complete odd episode
    x = 2^r m - 1,  m odd,
    x' = (3^r m - 1)/2^s,
    r' = v2(x'+1),

the requirement that the next odd state have exponent r' is

    2^(s+r') | 3^r m + 2^s - 1.

Since 3^r is odd and invertible modulo every power of two, this fixes a
UNIQUE residue of the current odd cofactor m:

    m == (1-2^s) * 3^(-r)  (mod 2^(s+r')).

Exact valuation r' (not merely >=r') adds the next-bit condition excluding
divisibility by 2^(s+r'+1).

Together with the global non-descent bound on s, this means:
- if r stays bounded, the non-descending schema grammar is finite;
- if r is unbounded, every record r' requires correspondingly unbounded
  exact 2-adic precision in m.

This does not rule out an infinite 2-adic escape path.  It identifies that
path precisely as the remaining alternative to bounded-r recurrence.

The script verifies the congruence and exact-next-bit condition exhaustively
on bounded concrete states.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from collatz_odd_episode_grammar import episode
from collatz_non_descending_s_bound import S


def required_residue(r:int,s:int,rp:int):
    D=s+rp
    mod=1<<D
    rho=((1-(1<<s))*pow(3**r,-1,mod))%mod
    return D,rho


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=16)
    ap.add_argument("--precision",type=int,default=16)
    ap.add_argument("--out")
    a=ap.parse_args()
    assert 2<=a.max_r<=32
    assert 8<=a.precision<=20

    M=1<<a.precision
    controls=0
    nondesc=0
    record_like=0
    max_required_D=0
    max_rp=0
    examples=[]

    for r in range(1,a.max_r+1):
        sr=S(r)
        for m in range(1,M,2):
            x=(1<<r)*m-1
            if x==1:
                continue
            rr,mm,s,rp,mp,xp=episode(x)
            assert (rr,mm)==(r,m)

            D,rho=required_residue(r,s,rp)
            mod=1<<D
            assert m%mod==rho,(r,m,s,rp,D,rho,m%mod)

            # Exact valuation: numerator / 2^(s+rp) is odd, hence the same
            # numerator is NOT divisible by one additional factor two.
            num=3**r*m + (1<<s)-1
            assert num%(1<<D)==0
            assert num%(1<<(D+1)) != 0

            if xp>=x:
                nondesc+=1
                assert s<=sr,(r,m,s,sr)
                max_required_D=max(max_required_D,D)
                max_rp=max(max_rp,rp)
                if rp>r:
                    record_like+=1
                    if len(examples)<200:
                        examples.append({
                            "r":r,"m":m,"s":s,"rp":rp,
                            "required_bits":D,"required_residue":rho,
                            "x":x,"xp":xp,
                        })
            controls+=1

    out={
        "kind":"unbounded_r_escape_congruence",
        "max_r":a.max_r,"precision":a.precision,
        "controls":controls,"non_descending_controls":nondesc,
        "r_increase_controls":record_like,
        "max_required_bits":max_required_D,
        "max_observed_rp":max_rp,
        "examples":examples,
        "remaining_global_alternatives":[
            "bounded_r_infinite_recurrence",
            "unbounded_r_with_unbounded_unique_2adic_congruences",
        ],
        "proof_status":"general_congruence_with_bounded_exhaustive_controls_not_global_proof",
    }
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print("UNBOUNDED_R_ESCAPE_CONGRUENCE",
          f"max_r={a.max_r}",f"precision={a.precision}",
          f"controls={controls}",f"non_descending={nondesc}",
          f"r_increases={record_like}",
          f"max_required_bits={max_required_D}",
          f"max_observed_rp={max_rp}")
    print("VERIFIED_EXACT_UNBOUNDED_R_ESCAPE_CONGRUENCE")


if __name__=="__main__":
    main()
