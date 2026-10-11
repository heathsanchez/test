"""V177: quantify EXACT candidate-least-bad residue exclusion by 3
source-qualified all-offset lower mergers. These exclude the *position*
of the hypothetical LEAST positive bad source, not all bad integers.

Source families:
   21+72w -> 3+12w, independent clocks (3,2)
   23+384w -> 3+54w, independent clocks (7,1)
   9+1728w -> 7+1296w, independent clocks (6,4)
All are correct TRUE shortcut two-clock meetings and strict smaller
positive companions for EVERY nonnegative w. Each is independently
source-witnessed and has a generic Lean proof in V177.
"""
from __future__ import annotations
from fractions import Fraction
from math import gcd, lcm
import json


def T(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2


def advance(n:int,clock:int)->int:
    for _ in range(clock):
        n=T(n)
    return n


def main():
    rules=[
       {"base":21,"stride":72,"earlier_base":3,"earlier_stride":12,"i":3,"j":2},
       {"base":23,"stride":384,"earlier_base":3,"earlier_stride":54,"i":7,"j":1},
       {"base":9,"stride":1728,"earlier_base":7,"earlier_stride":1296,"i":6,"j":4},
    ]
    mod=lcm(*(r["stride"] for r in rules))
    assert mod==3456
    for r in rules:
        assert 0<r["earlier_base"]<r["base"]<r["stride"]<mod
        assert 0<r["earlier_stride"]<r["stride"]
        for w in tuple(range(300))+(1000,100_000,10**7):
            n=r["base"]+r["stride"]*w
            p=r["earlier_base"]+r["earlier_stride"]*w
            assert 0<p<n
            assert advance(n,r["i"])==advance(p,r["j"])
    for i,r in enumerate(rules):
        for s in rules[i+1:]:
            g=gcd(r["stride"],s["stride"])
            assert (r["base"]-s["base"])%g!=0
    counts_per_period={}
    for r in rules:
        label=f"{r['base']}mod{r['stride']}"
        counts_per_period[label]=mod//r["stride"]
    residue_classes={
        n for n in range(1,mod+1)
        if any(n>=r["base"] and (n-r["base"])%r["stride"]==0 for r in rules)
    }
    assert len(residue_classes)==sum(counts_per_period.values())==59
    assert sum(counts_per_period.values())==48+9+2
    density=Fraction(len(residue_classes),mod)
    assert density==Fraction(59,3456)
    # Double-check the exact finite original source count vs a union
    # of disjoint progressions at several dyadic cutoffs.
    sample_counts=[]
    for k in (10,12,14,16,18,20):
        X=2**k
        formula=sum((X-1-r["base"])//r["stride"]+1
           for r in rules if r["base"]<X)
        observed=sum(1 for n in range(1,X) if
            any(n>=r["base"] and (n-r["base"])%r["stride"]==0
                for r in rules))
        assert observed==formula
        sample_counts.append({"k":k,"cutoff":X,"excluded_least_bad_candidates":formula})
    print(json.dumps({
        "schema":"COLLATZ_V177_THREE_INFINITE_LEAST_BAD_EXCLUSION_CLASSES",
        "rules":rules,
        "exact_common_period":mod,
        "pairwise_disjoint_by_congruence":True,
        "per_period_counts":counts_per_period,
        "all_three_union_numerator":density.numerator,
        "all_three_union_denominator":density.denominator,
        "exact_exclusion_scope":"ONLY_THE_POSSIBLE_LEAST_BAD_ORIGINAL_SOURCE_INDEX",
        "not_terminal_certification_of_entire_progressions":True,
        "not_density_one_and_no_global_Collatz":True,
        "dyadic_audit":sample_counts,
        "global_collatz":"UNKNOWN","qed":False
    },indent=2,sort_keys=True))


if __name__=="__main__":
    main()
