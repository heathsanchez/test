"""V144 finite replay of exact source-coupled one-odd-period arithmetic.

Warrant for ALL natural k is supplied solely by separately checked Lean.
"""
from __future__ import annotations
import json


def shortcut(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def affine(n: int, k: int):
    x=n
    alpha=0
    bias=0
    for j in range(k):
        if x%2:
            bias=3*bias+2**j
            alpha+=1
        x=shortcut(x)
    assert 2**k*x == 3**alpha*n+bias
    return x,alpha,bias


def test_single_odd_bias():
    cases=0
    for n in range(1,401):
        for k in range(1,61):
            _,a,b=affine(n,k)
            if a==0:
                assert b==0
            if a==1:
                assert b>0 and b&(b-1)==0
            cases+=1
    return cases


def scan_unique_odd_period_arithmetic():
    # For k>0 and alpha=1, every genuine period must solve
    # (2^k-3)*n = 2^s with 0<=s<k and n>0.
    solutions=[]
    for k in range(1,65):
        denom=2**k-3
        if denom<=0:
            continue
        for s in range(k):
            numerator=1<<s
            if numerator%denom==0:
                n=numerator//denom
                y,alpha,bias=affine(n,k)
                assert y==n and alpha==1 and bias==numerator
                solutions.append({"n":n,"k":k,"odd_clock":s})
    assert solutions==[{"n":1,"k":2,"odd_clock":0},
                       {"n":2,"k":2,"odd_clock":1}]
    return solutions


def main():
    cases=test_single_odd_bias()
    sol=scan_unique_odd_period_arithmetic()
    x=5
    minus_cycle=[5]
    for _ in range(3):
        x=x//2 if x%2==0 else (3*x-1)//2
        minus_cycle.append(x)
    assert minus_cycle==[5,7,10,5]
    return {
      "schema":"COLLATZ_V144_EXACT_ONE_ODD_POSITIVE_PERIOD",
      "finite_affine_prefixes_checked":cases,
      "finite_integer_period_word_horizon":64,
      "only_one_odd_periodic_examples":sol,
      "real_shortcut_cycle_1_2_preserved":True,
      "different_minus_variant_nonterminal_example":minus_cycle,
      "no_new_positive_3n_plus_1_cycle_found_in_finite_audit":True,
      "arbitrary_clock_cycle_exclusion_requires_lean":True,
      "cycles_with_two_or_more_odds_excluded":False,
      "unbounded_no_merge_orbits_excluded":False,
      "global_collatz":"UNKNOWN",
      "qed":False
    }


if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))
