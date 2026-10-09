"""V141 independent exact controls for parity and cycle necessity.

All sampled results are finite observations. Infinite recurrence, strict
cycle inequality, and minimal-source restrictions require the pinned Lean
proof, not samples. Global Collatz stays UNKNOWN.
"""
from __future__ import annotations
import json

def T(n):
    assert n > 0
    return n // 2 if n % 2 == 0 else (3*n+1) // 2

def odd_count(n, k):
    odds = 0
    x=n
    for _ in range(k):
        odds += x%2
        x=T(x)
    return odds,x

def first_hit_one_two(n, cap=2000):
    seen={}
    x=n
    hits=[]
    for k in range(cap+1):
        if x in (1,2):
            return k,x,seen,len(hits)
        if x in seen:
            raise AssertionError(("unexpected nonterminal cycle",n,k,seen[x]))
        seen[x]=k
        hits.append(x%2)
        x=T(x)
    raise AssertionError(("unresolved sample",n))

def main():
    count=5000
    records=[first_hit_one_two(n) for n in range(1,count+1)]
    assert all(k<2000 for k,x,seen,hits in records)
    assert T(1)==2 and T(2)==1
    alpha1,y=odd_count(1,2)
    alpha2,z=odd_count(2,2)
    assert (alpha1,y)==(1,1) and (alpha2,z)==(1,2)
    assert 3**alpha1 < 2**2 and 3**alpha2 < 2**2

    small_descent=0
    for n in range(2,20001):
        if n%2==0:
            assert T(n)<n
            small_descent+=1
        if n%4==1:
            assert T(T(n))<n
            small_descent+=1
    mersenne=[]
    for K in (2,4,8,16,32,64,128,256):
        x=2**K-1
        n=x
        for j in range(K):
            assert x%2==1
            assert x==3**j*2**(K-j)-1
            x=T(x)
        assert x%2==0 and x==3**K-1
        mersenne.append({"odd_prefix_steps":K,"source_digits":len(str(n)),
                          "uniform_parity_return_time_disproved":True,
                          "this_is_single_finite_source":True})
    return dict(
      schema="COLLATZ_V141_PARITY_PERIOD_NECESSITY_EXACT",
      finite_positive_sources=count,
      sampled_terminated_without_other_cycles=True,
      terminal_period=2,
      terminal_odd_count=1,
      terminal_multiplier_2power=4,
      terminal_multiplier_3power=3,
      local_source_descent_checks=small_descent,
      mersenne_adverse_corridors=mersenne,
      no_source_uniform_even_clock_bound=True,
      infinite_parity_recurrence_proved_by_samples=False,
      positive_nonterminal_cycles_excluded=False,
      unbounded_positive_mixed_parity_orbits_excluded=False,
      universal_collatz="UNKNOWN",
      qed=False
    )

if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))
