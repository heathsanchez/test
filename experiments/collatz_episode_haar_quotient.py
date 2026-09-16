#!/usr/bin/env python3
"""Exact Haar-measure quotient of complete odd Collatz episodes.

Exact branch cylinders (proved independently in collatz_episode_exact_cylinders.py):

For current exponent r and exact episode schema (s,r'), the odd cofactor m is
one residue modulo 2^(s+r'+1).  Relative to the odd 2-adic cofactors, its Haar
weight is therefore

    w(s,r') = 2^(-(s+r')) = 2^-s * 2^-r'.

Thus for every fixed current r:

    sum_{s>=1,r'>=1} w(s,r') = 1,

and s and r' are independent geometric(1/2) coordinates in the exact
2-adic branch partition.  The residue LOCATION depends on r; the weight does
not.

For a prefix of complete odd episodes, let
    R = total odd shortcut steps = sum r_i
    E = total shortcut steps     = sum (r_i+s_i).

The linear coefficient of the initial odd integer after that prefix is
3^R / 2^E.  A necessary condition for the coefficient not yet to contract is

    3^R >= 2^E.

Transition:
    R' = R+r
    E' = E+r+s
    r_next = r'.

Crucially, the coefficient test is independent of r_next.  This script
computes the exact finite-horizon Haar mass of coefficient-noncontracting
prefixes, merging equal (R,E,r) states.  r' is truncated at R_CAP; the omitted
geometric tail is accumulated as an explicit rigorous upper-error mass, never
silently discarded.

This is an exact measure quotient and diagnostic.  Measure-zero exceptional
paths can still contain ordinary positive integers, so this is NOT a Collatz
proof and does not replace pointwise closure.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path


def survives(R:int,E:int)->bool:
    return 3**R >= 2**E


def branch_weight(s:int,rp:int)->Fraction:
    return Fraction(1,1<<(s+rp))


def one_r_partition_control(r:int,cap:int):
    # Finite rectangle plus exact tails; r is deliberately unused in weights.
    finite=sum(
        (branch_weight(s,rp) for s in range(1,cap+1) for rp in range(1,cap+1)),
        Fraction(0,1),
    )
    s_tail=Fraction(1,1<<cap)       # sum_{s>cap} 2^-s
    rp_tail=Fraction(1,1<<cap)      # sum_{rp>cap} 2^-rp
    # Inclusion-exclusion for the complement of the cap x cap rectangle.
    omitted=s_tail+rp_tail-s_tail*rp_tail
    assert finite+omitted==1,(r,cap,finite,omitted)
    return finite,omitted


def s_max_for_state(R:int,E:int,r:int)->int:
    # Largest s>=1 such that 3^(R+r) >= 2^(E+r+s).
    lhs=3**(R+r)
    base=2**(E+r)
    s=0
    while base*(1<<(s+1)) <= lhs:
        s+=1
    return s


def fixed_r_curve(r0:int,episodes:int,r_cap:int):
    states={(0,0,r0):Fraction(1,1)}
    escaped=Fraction(0,1)
    rows=[]

    for depth in range(1,episodes+1):
        nxt=defaultdict(Fraction)
        step_escape=Fraction(0,1)

        for (R,E,r),mass in states.items():
            sm=s_max_for_state(R,E,r)
            if sm<=0:
                continue

            for s in range(1,sm+1):
                sw=Fraction(1,1<<s)

                # Exact represented r' states.
                for rp in range(1,r_cap+1):
                    R2=R+r
                    E2=E+r+s
                    assert survives(R2,E2)
                    nxt[(R2,E2,rp)] += mass*sw*Fraction(1,1<<rp)

                # Exact omitted r'>r_cap mass.  It is unresolved, not assumed
                # to die; carrying it as escape gives a rigorous upper error.
                step_escape += mass*sw*Fraction(1,1<<r_cap)

        escaped += step_escape
        states=dict(nxt)
        represented=sum(states.values(),Fraction(0,1))
        upper=represented+escaped

        rows.append({
            "depth":depth,
            "states":len(states),
            "represented_mass_num":represented.numerator,
            "represented_mass_den":represented.denominator,
            "represented_mass":float(represented),
            "cumulative_escape_num":escaped.numerator,
            "cumulative_escape_den":escaped.denominator,
            "cumulative_escape":float(escaped),
            "survival_upper_mass":float(upper),
            "max_r_state":max((k[2] for k in states),default=0),
            "max_R":max((k[0] for k in states),default=0),
            "max_E":max((k[1] for k in states),default=0),
        })

    return rows


def mixture_curve(max_initial_r:int,episodes:int,r_cap:int):
    # Initial r itself has exact odd-integer/2-adic relative weight 2^-r.
    curves={r:fixed_r_curve(r,episodes,r_cap) for r in range(1,max_initial_r+1)}
    initial_tail=Fraction(1,1<<max_initial_r)

    rows=[]
    for depth in range(1,episodes+1):
        represented=Fraction(0,1)
        escape=initial_tail
        for r in range(1,max_initial_r+1):
            w=Fraction(1,1<<r)
            z=curves[r][depth-1]
            represented += w*Fraction(z["represented_mass_num"],z["represented_mass_den"])
            escape += w*Fraction(z["cumulative_escape_num"],z["cumulative_escape_den"])
        rows.append({
            "depth":depth,
            "represented_mass":float(represented),
            "rigorous_unresolved_upper_mass":float(represented+escape),
            "explicit_tail_error":float(escape),
        })
    return rows,curves


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--episodes",type=int,default=20)
    ap.add_argument("--r-cap",type=int,default=32)
    ap.add_argument("--max-initial-r",type=int,default=32)
    ap.add_argument("--out")
    a=ap.parse_args()
    assert 1<=a.episodes<=40
    assert 8<=a.r_cap<=64
    assert 8<=a.max_initial_r<=64

    controls=[]
    for r in (1,2,3,5,8,13):
        finite,omitted=one_r_partition_control(r,16)
        controls.append({
            "r":r,
            "finite_rectangle":float(finite),
            "exact_omitted":float(omitted),
        })

    rows,curves=mixture_curve(a.max_initial_r,a.episodes,a.r_cap)

    # Monotonicity: coefficient-noncontracting prefix mass cannot increase
    # with episode depth, apart from the separately carried unresolved tail.
    reps=[z["represented_mass"] for z in rows]
    assert all(b<=a0+1e-18 for a0,b in zip(reps,reps[1:])),reps

    out={
        "kind":"exact_haar_episode_coefficient_quotient",
        "episodes":a.episodes,
        "r_cap":a.r_cap,
        "max_initial_r":a.max_initial_r,
        "branch_relative_weight":"2^(-(s+r_prime))",
        "factorization":"2^-s * 2^-r_prime",
        "state":"(total_odd_steps_R,total_steps_E,current_r)",
        "coefficient_survival":"3^R >= 2^E",
        "partition_controls":controls,
        "mixture_rows":rows,
        "selected_fixed_r":{
            str(r):curves[r] for r in (1,2,3,5,8,13)
            if r in curves
        },
        "scope":[
            "exact_2adic_Haar_measure_quotient",
            "coefficient_noncontraction_not_actual_pointwise_non_descent",
            "measure_zero_exceptional_paths_not_excluded",
            "not_a_Collatz_proof",
        ],
    }

    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

    last=rows[-1]
    print(
        "HAAR_EPISODE_QUOTIENT",
        f"episodes={a.episodes}",
        f"r_cap={a.r_cap}",
        f"max_initial_r={a.max_initial_r}",
        f"represented_mass={last['represented_mass']:.15e}",
        f"upper_mass={last['rigorous_unresolved_upper_mass']:.15e}",
        f"tail_error={last['explicit_tail_error']:.15e}",
    )
    print("EXACT_EPISODE_BRANCH_WEIGHTS_FACTOR_AS_GEOMETRIC_COORDINATES")
    print("VERIFIED_EXACT_HAAR_EPISODE_COEFFICIENT_QUOTIENT")


if __name__=="__main__":
    main()
