"""V161 independent finite parity-population mixing and two-basin negative audit.

This is a BOUNDED exact audit, not a proof of asymptotic stopping-time
mass or global Collatz. The universal all-finite-horizon source-prefix
extension is Lean's job in FiniteParityPopulationMixing.lean.

For each k=0..7, h=0..7, r<2^k, the 2^h genuine sources
    n=r+2^k*q, 0<=q<2^h
realize all binary parity suffix words (T^k(n)%2,...,T^(k+h-1)(n)%2)
exactly once. Check both real shortcut and the synthetic two-basin map
S(even n)=n/2, S(odd n)=(n+3)/2, which has distinct absorbing
future classes {1,2} and {3}.
"""
from __future__ import annotations
import json
from collections import Counter


def shortcut(n):
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2


def two_basin(n):
    assert n>=0
    return n//2 if n%2==0 else (n+3)//2


def prefix(n,k,T):
    seq=[]
    for _ in range(k):
        seq.append(n&1)
        n=T(n)
    return seq,n


def parity_suffix(n,k,h,T):
    seen,end=prefix(n,k,T)
    out=[]
    for _ in range(h):
        out.append(end&1)
        end=T(end)
    return tuple(out)


def main():
    rows=[]
    tests=0
    source_transitions=0
    for k in range(8):
        for h in range(8):
            for T in (shortcut,two_basin):
                for r in range(1<<k):
                    values=[
                        parity_suffix(r+(1<<k)*q,k,h,T)
                        for q in range(1<<h)
                    ]
                    assert len(set(values))==(1<<h),(T.__name__,k,h,r)
                    assert len(values)==(1<<h)
                    tests+=1
                    source_transitions+=len(values)
                    if T is shortcut:
                        low,nk=prefix(r,k,T)
                        a=sum(low)
                        for q in (0,1,2,3,7):
                            nn=r+(1<<k)*q
                            _,result=prefix(nn,k,T)
                            assert result==nk+3**a*q
                    else:
                        _,nk=prefix(r,k,T)
                        for q in (0,1,2,3,7):
                            nn=r+(1<<k)*q
                            _,result=prefix(nn,k,T)
                            assert result==nk+q
            rows.append(dict(k=k,h=h,
              source_prefixes=(1<<k),
              future_suffix_words=(1<<h),
              per_map_genuine_sources=(1<<(k+h)),
              exact_parity_suffix_permutation=True,
              true_map_pass=True,
              synthetic_two_basin_pass=True))
    assert shortcut(1)==2 and shortcut(2)==1
    assert two_basin(1)==2 and two_basin(2)==1
    assert two_basin(3)==3
    assert tuple(prefix(3,20,two_basin)[0])==(1,)*20
    # Distinct future classes despite perfect finite parity-word mixing.
    assert all(two_basin(i) in (1,2) for i in (1,2))
    assert two_basin(3)==3
    return {
      'schema':'COLLATZ_V161_FINITE_SOURCE_POPULATION_PARITY_MIXING',
      'true_shortcut_odd_affine':'T(2x+1)=3x+2',
      'synthetic_odd_affine':'S(2x+1)=x+2',
      'synthetic_even_branch':'S(2x)=x',
      'binary_prefix_depths_checked':'0..7',
      'future_suffix_lengths_checked':'0..7',
      'prefix_suffix_map_checks':tests,
      'source_instances':source_transitions,
      'all_finite_suffix_words_exactly_once_for_both_maps':True,
      'synthetic_map_two_disjoint_positive_terminal_cycles':True,
      'synthetic_1_2_cycle':True,
      'synthetic_3_fixed':True,
      'synthetic_finite_mix_but_unique_terminal_basin':False,
      'nonnegative_zero_source_allowed_in_allzero_word':True,
      'source_positive_prefix_conditional':True,
      'per_depth':rows,
      'infinite_fixed_positive_source_mixing_proved':False,
      'sparse_terminal_exceptional_mass_proved':False,
      'global_collatz':'UNKNOWN','qed':False
    }


if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
