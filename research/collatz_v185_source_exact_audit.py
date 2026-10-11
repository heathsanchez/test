"""V185 exact source-specific protected-future multiplier audit.

Source-attached TRUE +1 invariant:
if no real clock <=k has T^t(n)<n, then
    2^k * n^a <= (3*n+1)^a, a=oddCount(n,k).

If the source-specific inequality fails, a real strictly smaller
positive endpoint MUST have occurred no later than clock k, giving
an authentic two-clock LowerMerge witness (k'<=k, 0).

Do not confuse a low-odd prefix of an arbitrary source (which may
have ALREADY descended) with a violation by a hypothetical least bad.

G5's positive 187 27-cycle passes the previous coarse 25/8
prefix-bound but FAILS the exact +1 source factor. This exact
adversarial split is not a Collatz QED.
"""
from __future__ import annotations
from math import comb
from pathlib import Path
import json
import random


def T(n:int,c:int=1)->int:
    assert n>0 and c>0 and c%2==1
    return n//2 if n%2==0 else (3*n+c)//2


def replay_prefix(n:int,H:int)->tuple[int,int,int,int|None]:
    current=n
    a=0
    first_descent=None
    tested=0
    product_checked=0
    excess_events=0
    for k in range(H+1):
        if current<n and first_descent is None:
            first_descent=k
        prod_lhs=(1<<k)*n**a*current
        prod_rhs=n*(3*n+1)**a
        gap=(1<<k)*n**a>(3*n+1)**a
        if first_descent is None:
            assert prod_lhs<=prod_rhs,(n,k,a,current,prod_lhs,prod_rhs)
            assert not gap,(n,k,a)
            product_checked+=1
        if gap:
            excess_events+=1
            assert first_descent is not None and first_descent<=k,(n,k,a,first_descent)
        if k<H:
            a+=current%2
            current=T(current)
        tested+=1
    return tested,product_checked,excess_events,first_descent


def adversarial_g5_cycle()->dict:
    src=187
    x=src
    odds=0
    arr=[]
    for clock in range(27):
        assert x>=src
        arr.append(x)
        odds+=x%2
        x=T(x,5)
    assert x==src and odds==17 and len(set(arr))==27
    exact_true_source_condition=(2**27)*src**odds <= (3*src+1)**odds
    coarse_v184_condition=(2**27)*8**odds <=25**odds
    assert not exact_true_source_condition and coarse_v184_condition
    assert (2**27)*(src**odds) > (3*src+1)**odds
    assert (2**27)*(src**odds) <= (3*src+5)**odds
    # Correct true-3n+1 step at the same source does not preserve
    # the synthetic G5 cycle.
    assert T(src,5)==283 and T(src,1)==281
    # The synthetic does not satisfy the source-exact +1 law,
    # so source187 is no counterexample to the TRUE theorem.
    return {
       "cycle_start":src,"cycle_length":27,
       "cycle_minimum":min(arr),"cycle_odds":odds,
       "coarse_V184_25_over_8_condition_passes":coarse_v184_condition,
       "exact_TRUE_source_3n_plus_1_condition_fails":not exact_true_source_condition,
       "G5_specific_growth_requirement_holds":True,
       "synthetic_3n_plus5_not_original_3n_plus1":True,
    }


def main()->None:
    H=130
    count=0
    prefix_checked=0
    exact_gap_constructed=0
    sample=[]
    rng=random.Random(185)
    cases=list(range(1,22001))
    cases += [rng.randrange(1,2500000) for _ in range(3000)]
    cases += [27,111,127,187,255,703,35655,60975,171007,206847]
    cases += [(1<<p)-1 for p in (8,16,32,64,96,128)]
    for n in cases:
        tested,prefix_count,gaps,first_descent = replay_prefix(n,H)
        count+=tested
        prefix_checked+=prefix_count
        exact_gap_constructed+=gaps
        if n in (27,111,127,187,255,703,35655,60975,171007,206847):
            sample.append({"source":str(n),
                           "first_real_source_decrease_clock":first_descent,
                           "true_nondecreasing_protected_prefix_clocks":prefix_count,
                           "source_exact_coefficient_excess_events":gaps})
    assert count>2000000
    assert prefix_checked>100000
    assert exact_gap_constructed>0
    g5=adversarial_g5_cycle()
    # On arbitrary positive source m, n-specific coefficient upper
    # is valid only while every original-source clock is >=m;
    # it is NOT a necessary restriction on already-descent orbits.
    true27=next(z for z in sample if z["source"]=="27")
    assert true27["first_real_source_decrease_clock"] is not None
    out={
      "schema":"COLLATZ_V185_SOURCE_EXACT_FUTURE_COEFFICIENT_GUARD",
      "map":"T(2n)=n, T(2n+1)=3n+2",
      "tested_positive_source_count":len(cases),
      "source_clock_pairs_checked":count,
      "protected_prefix_source_multiplier_cases":prefix_checked,
      "coefficient_excess_to_true_prior_descent_replays":exact_gap_constructed,
      "source_examples":sample,
      "synthetic_G5_187_separator":g5,
      "all_clock_true_source_theorem_submitted_to_Lean":True,
      "all_source_true_terminal_convergence_proved":False,
      "excess_must_be_produced_on_some_clock_for_global_QED":True,
      "global_collatz":"UNKNOWN","qed":False
    }
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/v185-source-exact.json").write_text(
       json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "schema":out["schema"],
        "sources":len(cases),
        "checked":count,
        "protected":prefix_checked,
        "genuine_descent_excess_replays":exact_gap_constructed,
        "G5_separator":True,
        "global_collatz":"UNKNOWN"
    },sort_keys=True))


if __name__=="__main__":
    main()
