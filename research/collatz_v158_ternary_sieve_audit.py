"""V158: exact arithmetic audit for true shortcut ternary-target sieve.

Mathematical target:
  T^k(n) mod 3 = 0  iff  n mod (3*2^k) = 0
for the TRUE odd successor (3*n+1)//2 and even halving.

The count at ANY positive cutoff X follows exactly:
  #{1<=n<X : 3|T^k(n)} = (X-1)//(3*2^k).

Controls:
 - the original source is attached, including n=0 as a separate
   algebraic edge case; no unbounded asymptotic claim is inferred;
 - for 0<n<2^k, no 3-divisible endpoint exists;
 - V154 synthetic two-basin map fails this genuine odd-law sieve
   at (n,k)=(3,2), so generic density+halving cannot substitute.

The Lean proof, not this bounded audit, is the universal authority.
"""
from __future__ import annotations

import json
from hashlib import sha256


def collatz_shortcut(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def synthetic_two_basin(n: int) -> int:
    assert n >= 0
    return n if n in (1, 3) else n//2


def main():
    xmax=1 << 16
    values=list(range(xmax))
    by_depth=[]
    measured_pairs=0
    for k in range(0,17):
        d=3*(1 << k)
        violations=0
        source_shortcut_zero_tail_bad=0
        rare=sum(v%3==0 for v in values[1:])
        expected=(xmax-1)//d
        assert rare==expected,(k,rare,expected)
        for n,v in enumerate(values):
            measured_pairs+=1
            if (v%3==0) != (n%d==0):
                violations+=1
            if 0<n<(1<<k) and v%3==0:
                source_shortcut_zero_tail_bad+=1
        assert violations==0
        assert source_shortcut_zero_tail_bad==0
        by_depth.append({
            "k":k,
            "cutoff_exclusive":xmax,
            "three_divisible_endpoint_count":rare,
            "exact_sieve_count":expected,
            "mod3_sieve_violations":violations,
            "zero_tail_positive_target_guard_violations":source_shortcut_zero_tail_bad,
        })
        values=[collatz_shortcut(n) for n in values]

    odd_checks=0
    for n in range(1,100_001,2):
        assert collatz_shortcut(n)%3==2
        odd_checks+=1

    # A stable positive source cannot generate a divisible-by-three
    # endpoint once its initial binary magnitude is exhausted.
    for n in (1,2,3,5,7,9,27,31,63,127,255,1023,8191,65535):
        v=n
        for k in range(0,25):
            if (1<<k)>n:
                assert v%3!=0,(n,k,v)
            v=collatz_shortcut(v)

    # The V154 synthetic model fails this theorem; this protects
    # reliance on the exact (3*n+1)/2 odd affine step.
    assert synthetic_two_basin(3)==3
    assert synthetic_two_basin(synthetic_two_basin(3))%3==0
    assert 0<3<(1<<2)
    assert collatz_shortcut(collatz_shortcut(3))%3!=0

    return {
        "schema":"COLLATZ_V158_EXACT_TERNARY_ENDPOINT_SIEVE",
        "true_odd_map":"(3*n+1)//2",
        "true_even_map":"n//2",
        "checked_source_cutoff_exclusive":xmax,
        "checked_time_depth_min":0,
        "checked_time_depth_max":16,
        "checked_source_clock_pairs":measured_pairs,
        "odd_successor_residue_checks":odd_checks,
        "every_sieve_identity_checked":True,
        "zero_tail_positive_three_guard_checked":True,
        "exact_dyadic_counts":by_depth,
        "synthetic_v154_countercontrol_breaks_true_odd_sieve":True,
        "pure_even_inverse_source_lineage":"n=(2^k)*T^k(n) when 3|T^k(n)",
        "external_mazur_predecessor_amplifier_built_locally":False,
        "universal_sparse_terminal_mass_proved":False,
        "any_second_future_class_excluded":False,
        "global_collatz":"UNKNOWN",
        "qed":False,
    }


if __name__=="__main__":
    print(json.dumps(main(),indent=2,sort_keys=True))
