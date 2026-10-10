"""V154 exact two-basin countermodel / epistemic separator.

A total deterministic map, deliberately DIFFERENT from Collatz, satisfies:
* f(2*n)=n for all n>0 (the genuine Collatz even branch).
* f(n)<n for every n>=4.
* for every a>=2, every integer in [a*2^t,(a+1)*2^t)
  reaches a at exactly t steps. These exact dyadic blocks imply positive
  LOWER NATURAL density of predecessors for EVERY positive fixed a.
* two permanently disjoint positive terminal basins {1} and {3}, each
  with asymptotic natural density 1/2.

The theorem shows density amplification plus descent alone cannot close
the actual conjecture: the specific odd affine equation must be used.
All toy claims are deliberately NOT promoted to actual Collatz.
"""
from __future__ import annotations
import json
from collections import Counter

def toy(n: int) -> int:
    assert n >= 0
    if n in (1,3):
        return n
    return n//2

def collatz(n: int) -> int:
    assert n > 0
    return n//2 if n%2==0 else (3*n+1)//2

def iterate(n: int, t: int):
    for _ in range(t):
        n=toy(n)
    return n

def roots_below(X: int):
    memo={1:1,3:3}
    c=Counter()
    for n in range(1,X):
        x=n
        path=[]
        while x not in memo:
            path.append(x)
            x=toy(x)
        for p in path:
            memo[p]=memo[x]
        c[memo[n]]+=1
    assert sum(c.values())==X-1
    return c

def proof_reachable(n: int,a:int):
    seen=set()
    while n not in seen and n>=a:
        if n==a:return True
        seen.add(n)
        n=toy(n)
    return n==a

def main():
    assert toy(1)==1 and toy(2)==1 and toy(3)==3
    for n in range(1,400_000):
        assert toy(2*n)==n
    for n in range(4,400_000):
        assert toy(n)<n
    difference=sum(1 for n in range(1,5000) if toy(n)!=collatz(n))
    assert difference>1000
    rows=[]
    for k in (8,10,12,14,16,18):
        X=1<<k
        c=roots_below(X)
        assert c[1]==X//2 and c[3]==X//2-1, (k,c)
        rows.append(dict(k=k,X=X,good_basin_count=c[1],
            bad_basin_count=c[3],root3_does_not_hit_one=True))
    checks=0
    for a in range(2,151):
        for t in range(0,12):
            step=1<<t
            for r in range(step):
                x=a*step+r
                assert iterate(x,t)==a
                checks+=1
    # Exact predecessor count at the dyadic cutoff: for
    # b=ceil(log2(a+1)), t=k-b, at least 2^t distinct starts
    # reach a below X=2^k. For a=1 use predecessor 2 -> 1.
    target_rows=[]
    for a in range(1,35):
        X=1<<15
        b=(a+1-1).bit_length()
        b=max(b,2)
        t=15-b
        y=max(a,2)
        lo=y<<t
        hi=(y+1)<<t
        assert hi<=X
        for x in range(lo,hi):
            assert proof_reachable(x,a)
        count=sum(1 for n in range(1,X) if proof_reachable(n,a))
        assert count>=1<<t
        target_rows.append(dict(target=a,cutoff=X,guaranteed_block_size=1<<t,
            observed_reaching_count=count,
            guaranteed_fraction_denominator=1<<b))
    return {
        'schema':'COLLATZ_V154_TWO_BASIN_DENSITY_COUNTERMODEL',
        'synthetic_not_actual_collatz':True,
        'all_even_doublings_preserved_in_tests':True,
        'every_n_ge_4_descends_in_one_step_in_tests':True,
        'all_targets_have_infinite_exact_dyadic_predecessor_blocks':True,
        'positive_lower_natural_density_for_each_target_via_intervals':True,
        'lower_density_bound_justification':'For a>=2 choose b with a+1<=2^b. For each X between 2^k and 2^(k+1), k>=b, the length-2^(k-b) block of predecessors below 2^k gives predecessor_count(X) >= X/2^(b+1). For a=1 use the a=2 predecessor block, followed by 2->1.',
        'number_of_ancestor_interval_assertions':checks,
        'different_from_true_collatz_on_many_odd_sources':difference,
        'two_disjoint_absorbing_positive_future_classes':[1,3],
        'positive_density_of_both_basins':True,
        'finite_dyadic_basin_exact_counts':rows,
        'positive_predecessor_density_sampled_targets':target_rows,
        'naive_amplifier_plus_strict_descent_to_qed':'REJECTED_BY_COUNTERMODEL',
        'actual_collatz_odd_affine_rule_not_satisfied':True,
        'actual_collatz_qed':False,'global_collatz':'UNKNOWN'
    }

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
