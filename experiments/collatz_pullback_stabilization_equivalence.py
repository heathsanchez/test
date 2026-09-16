#!/usr/bin/env python3
"""Exact pullback-stabilization formulation of a Collatz counterexample.

For an initial odd state

    x0 = 2^r0 * m0 - 1,   m0 odd,

a prefix of complete odd episodes has an exact cofactor pullback

    m_j = (A_j m0 + B_j) / 2^D_j,

with A_j odd.  Exact oddness of m_j gives the unique nested cylinder

    m0 == rho_j := (2^D_j - B_j) A_j^(-1)  (mod 2^(D_j+1)).

The exact moduli strictly grow because every complete episode contributes
s+r' >= 2 denominator bits.

If m0 is an ordinary positive integer, then once 2^(D_j+1) > m0 the canonical
residue rho_j in [0,2^(D_j+1)) must equal m0 numerically.  Hence every
ordinary integer trajectory has an eventually constant pullback-residue tail
(as long as the trajectory prefix continues).

Conversely, for any infinite compatible episode path, if rho_j is eventually
the same positive odd integer m*, then m* belongs to every exact prefix
cylinder.  Determinism implies the actual trajectory of
x*=2^r0*m*-1 follows every prefix of that path.  If the path is globally
non-descending below x*, x* is a positive-integer counterexample.

Therefore:

  positive integer counterexample
  <=>
  infinite globally non-descending exact episode path
  with eventually constant positive pullback residue.

This does NOT prove Collatz.  It isolates the remaining pointwise gap after
2-adic/measure compression: rule out an eventually constant pullback tail
(except the trivial base cycle).

The bounded census below independently checks all algebraic identities and
measures how many complete episodes a stabilized pullback can persist before
first descent on finite exact domains.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from collatz_odd_episode_grammar import episode


def compose(A:int,B:int,D:int,r:int,s:int,rp:int):
    d=s+rp
    return (
        (3**r)*A,
        (3**r)*B + ((1<<s)-1)*(1<<D),
        D+d,
    )


def canonical_rho(A:int,B:int,D:int):
    mod=1<<(D+1)
    return ((1<<D)-B)*pow(A,-1,mod)%mod,mod


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-r",type=int,default=16)
    ap.add_argument("--precision",type=int,default=16)
    ap.add_argument("--episode-cap",type=int,default=256)
    ap.add_argument("--out")
    a=ap.parse_args()

    assert 1<=a.max_r<=24
    assert 8<=a.precision<=20
    assert 1<=a.episode_cap<=1024

    M=1<<a.precision
    cases=0
    unresolved=0
    prefix_controls=0
    stabilized_cases=0
    max_stable_episodes=0
    max_stable_case=None
    stable_hist=Counter()
    first_stable_bit_margin=Counter()
    max_delay=0

    for r0 in range(1,a.max_r+1):
        for m0 in range(1,M,2):
            x0=(1<<r0)*m0-1
            if x0==1:
                continue

            cases+=1
            x=x0
            A,B,D=1,0,0
            stable_started=False
            stable_len=0
            descended=False

            for j in range(1,a.episode_cap+1):
                r,m,s,rp,mp,xp=episode(x)
                A,B,D=compose(A,B,D,r,s,rp)
                rho,mod=canonical_rho(A,B,D)

                # Exact pullback controls.
                assert m0%mod==rho,(r0,m0,j,D,rho,m0%mod)
                assert (A*m0+B)==(1<<D)*mp
                assert mp&1
                prefix_controls+=1

                if mod>m0:
                    # Ordinary-integer stabilization theorem.
                    assert rho==m0,(r0,m0,j,D,rho,mod)
                    if not stable_started:
                        stable_started=True
                        stabilized_cases+=1
                        margin=(D+1)-m0.bit_length()
                        first_stable_bit_margin[margin]+=1
                    stable_len+=1
                elif stable_started:
                    raise AssertionError("nested exact pullback unstabilized")

                if xp<x0:
                    descended=True
                    max_delay=max(max_delay,j)
                    break
                x=xp

            if not descended:
                unresolved+=1

            if stable_started:
                stable_hist[stable_len]+=1
                if stable_len>max_stable_episodes:
                    max_stable_episodes=stable_len
                    max_stable_case=(r0,m0,x0,j,D)

    assert unresolved==0,(unresolved,cases)

    out={
        "kind":"counterexample_pullback_stabilization_equivalence",
        "max_r":a.max_r,
        "precision":a.precision,
        "cases":cases,
        "unresolved":unresolved,
        "prefix_controls":prefix_controls,
        "stabilized_cases":stabilized_cases,
        "max_stable_episodes_before_descent":max_stable_episodes,
        "max_stable_case":max_stable_case,
        "max_episode_delay":max_delay,
        "stable_length_hist":dict(sorted(stable_hist.items())),
        "first_stable_bit_margin_hist":dict(sorted(first_stable_bit_margin.items())),
        "equivalence":[
            "ordinary_positive_m0_implies_exact_pullback_residue_eventually_equals_m0",
            "eventually_constant_positive_pullback_on_infinite_compatible_path_realizes_that_integer",
            "counterexample_requires_infinite_globally_non_descending_eventually_constant_pullback_path",
        ],
        "remaining_gap":"exclude_infinite_globally_non_descending_eventually_constant_positive_pullback_tail",
        "proof_status":"general_algebraic_equivalence_plus_bounded_exact_census_not_Collatz_proof",
    }

    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    print(
        "PULLBACK_STABILIZATION_EQUIVALENCE",
        f"max_r={a.max_r}",
        f"precision={a.precision}",
        f"cases={cases}",
        f"unresolved={unresolved}",
        f"prefix_controls={prefix_controls}",
        f"stabilized_cases={stabilized_cases}",
        f"max_stable_episodes={max_stable_episodes}",
        f"max_episode_delay={max_delay}",
    )
    if max_stable_case:
        print("MAX_STABLE_CASE",*max_stable_case)
    print("COUNTEREXAMPLE_REQUIRES_EVENTUALLY_CONSTANT_POSITIVE_PULLBACK_TAIL")
    print("VERIFIED_PULLBACK_STABILIZATION_EQUIVALENCE")


if __name__=="__main__":
    main()
