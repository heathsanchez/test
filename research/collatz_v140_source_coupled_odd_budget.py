"""V140 exact source-coupled odd-prefix arithmetic; global Collatz remains open."""
from __future__ import annotations
import json

def shortcut(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2

def canonical(n:int):
    u=n+1
    m=0
    while u%2==0:
        u//=2
        m+=1
    assert u>0 and u%2==1 and n+1==2**m*u
    x=n
    for _ in range(m):
        assert x%2==1
        x=shortcut(x)
    assert x==3**m*u-1 and x%2==0
    return m,u,x

def main():
    finite=10001
    records=[canonical(n) for n in range(finite)]
    assert len(records)==finite
    assert all(x[2]%2==0 for x in records)
    adverse=[]
    for K in [1,2,4,8,16,32,64,128,256]:
        n=(1<<K)-1
        m,u,y=canonical(n)
        assert m==K and u==1 and y==3**K-1
        adverse.append({
          'K':K, 'source_digits':len(str(n)),
          'exact_first_even_clock':m,
          'finite_prefix_not_unbounded_source':True
        })
    return {
      'schema':'COLLATZ_V140_SOURCE_COUPLED_ODD_BUDGET_EXACT',
      'finite_natural_sources':finite,
      'source_specific_budget':'v2(n+1)',
      'first_even_clock_equals_budget_for_all_tested':True,
      'symbolic_endpoint':'T^m(n)=3^m*u-1 for n+1=2^m*u, odd u',
      'mersenne_negative_controls':adverse,
      'arbitrarily_long_finite_odd_prefixes_preserved':True,
      'perpetual_odd_positive_natural_tail_excluded_only_by_formal_theorem':True,
      'all_parity_alternating_divergent_orbits_excluded':False,
      'nonterminal_positive_cycles_excluded':False,
      'collatz_all_natural_sources_good_proven':False,
      'global_collatz':'UNKNOWN','qed':False
    }

if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
