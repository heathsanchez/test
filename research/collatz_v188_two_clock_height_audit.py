"""V188 -- independent exact true source/clock inverse-height audit.

Universal real T(n) law:
   2*(T(n)+1) <= 3*(n+1), ALL n>=0.
Thus ALL p,j:
   2^j*(T^j(p)+1) <= 3^j*(p+1).

For a TRUE positive Mersenne source n=2^K-1, all its first K
endpoints satisfy T^i(n)+1=3^i*2^(K-i).
For ANY clock pair j<=i<=K and ANY genuine companion source p
meeting that endpoint, the inverse lower bound forces p>=n.

This is a certified NECESSARY clock surplus j>i for ANY smaller
positive source that meets the original Mersenne's first K
endpoints. It does not establish such a companion source exists.

The non-Collatz G5/G7 maps violate the exact +1 inverse growth
bound; do not transport this +1 warrant to them.

GLOBAL COLLATZ UNKNOWN, NO QED.
"""
from __future__ import annotations
import json,hashlib
from pathlib import Path


def T(n:int,c:int=1)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+c)//2


def orbit(n:int,k:int,c:int=1)->int:
    for _ in range(k):
        n=T(n,c)
    return n


def inspect() -> dict:
    count=0; equality=0; checked_sources=0
    for K in range(0,34):
        n=(1<<K)-1
        y=n
        for i in range(K+1):
            assert y+1==pow(3,i)*(1<<(K-i))
            for j in range(i+1):
                # lower bound on predecessor source, with only genuine
                # step arithmetic, no inverse tree enumeration:
                # 3^j*(p+1) >= 2^j*(y+1).
                lower=((1<<j)*(y+1)+pow(3,j)-1)//pow(3,j)-1
                assert lower>=n,(K,i,j,lower,n)
                if j==i:
                    assert lower==n
                    equality+=1
                if n>0 and K<=11:
                    # Independent source search: every smaller candidate
                    # at every clock <=i must FAIL to hit this endpoint.
                    for p in range(1,n):
                        if orbit(p,j)==y:
                            raise AssertionError((K,i,j,p,y))
                        checked_sources+=1
                count+=1
            if i<K:
                assert y&1
                y=T(y)
    assert count>6000 and equality>500
    assert checked_sources>500000
    return {
      'real_all_clock_inverse_comparison_cases':count,
      'exact_equality_at_original_same_clock_cases':equality,
      'bruteforce_smaller_positive_source_failure_checks':checked_sources,
      'all_companion_clock_j_le_original_i_implies_source_at_least_Mersenne':True,
    }


def negative_control()->dict:
    for c in (5,7):
        assert 2*(T(1,c)+1)>3*(1+1)
    assert 2*(T(1,1)+1)==3*(1+1)
    return {'G5_G7_fail_true_plus_one_inverse_growth':True,
            'same_source_shortcut_T1_satisfies_exact_equality':True}


def main()->None:
    out={
      'schema':'COLLATZ_V188_TWO_CLOCK_MERSENNE_HEIGHT_SEPARATOR',
      'map':'true shortcut odd=(3n+1)/2, even=n/2',
      'finite_exact_independent_audit':inspect(),
      'negative_intercept_controls':negative_control(),
      'Lean_universal_inverse_growth_proof_requested':True,
      'Lean_any_smaller_meeting_requires_later_companion_clock_requested':True,
      'no_convergence_of_Mersenne_family_proved':True,
      'future_late_companion_meeting_event_unknown':True,
      'global_collatz':'UNKNOWN','qed':False,
    }
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/v188-two-clock.json').write_text(
      json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({
      'schema':out['schema'],
      **out['finite_exact_independent_audit'],
      'global_collatz':'UNKNOWN'},sort_keys=True))


if __name__=='__main__':
    main()
