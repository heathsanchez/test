"""V147 exact adversarial tests for an observation-lawful rational centre quotient.

Source centres are exact pairs (A,R) representing c=-R/A, A odd.
The quotient is warranted only when A'R=AR'. It preserves dyadic
source congruence observations for all n,B (proved separately in Lean).

It does NOT collapse actual original source identity, clocks, or prove
that infinitely long no-merge histories admit a finite centre cover.
"""
from __future__ import annotations

from fractions import Fraction
from math import gcd
import json


def centre(A:int,R:int):
    assert A>0 and A%2==1 and R>=0
    return (A,R)


def equivalent(x,y):
    return y[0]*x[1]==x[0]*y[1]


def observes(x,n,B):
    assert B>=0 and n>=0
    return (x[0]*n+x[1])%(1<<B)==0


def shortcut(n):
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2


def shadow_source(t):
    n=27
    for _ in range(t):
        n=64*n+91
    return n


def known_odd_reductions():
    c=centre(9,13)
    C=centre(27,39)
    assert equivalent(c,C)
    assert Fraction(-c[1],c[0])==Fraction(-C[1],C[0])
    for n in list(range(128))+[27,1819,116507,7456539]:
        for B in range(22):
            assert observes(c,n,B)==observes(C,n,B)
    return 132*22


def check_exact_normalization(max_A=41,max_R=80):
    pairs=[centre(a,r) for a in range(1,max_A+1,2) for r in range(max_R)]
    seen={}
    for a,r in pairs:
        g=gcd(a,r)
        normalized=(a//g,r//g)
        # g odd, because a odd, so normalized denominator is odd.
        assert normalized[0]%2==1
        assert equivalent((a,r),normalized)
        if normalized in seen:
            assert equivalent((a,r),seen[normalized])
        else:
            seen[normalized]=(a,r)
    return len(pairs),len(seen)


def countercontrols():
    # Same future endpoint does not imply same source-centre observation:
    # T^3(21)=T^2(3)=8, yet c21=-3 and c3=-1.
    x=21
    for _ in range(3):x=shortcut(x)
    y=3
    for _ in range(2):y=shortcut(y)
    assert x==y==8
    left=centre(3,9)
    right=centre(9,9)
    assert not equivalent(left,right)
    different=[(n,B) for n in range(64) for B in range(1,10)
               if observes(left,n,B)!=observes(right,n,B)]
    assert different
    assert not any(equivalent(centre(9,13),centre(1,d)) for d in range(5000))

    # True 27-root sources all satisfy one rational centre class; the
    # starting integer differs at each increasing precision.
    shadows=[]
    for t in range(13):
        n=shadow_source(t)
        B=6*t+5
        q=1<<B
        assert 9*n+13 == 8*q
        assert observes(centre(9,13),n,B)
        z=n
        for _ in range(3):z=shortcut(z)
        assert z+1==q
        assert n%4==3
        shadows.append({'t':t,'source_digits':len(str(n)),
                        'precision':B,'centre':[-13,9],
                        'source_changes_with_t':True})
    return len(different),shadows


def main():
    comparisons=known_odd_reductions()
    samples,reduced=check_exact_normalization()
    diffs,shadows=countercontrols()
    return dict(
      schema='COLLATZ_V147_RATIONAL_CENTRE_OBSERVATION_QUOTIENT',
      quotient_equivalence='A_prime*R == A*R_prime, both A and A_prime odd',
      all_nB_sampled_congruence_comparisons=comparisons,
      finite_rational_pairs_checked=samples,
      canonical_reduced_pairs_seen=reduced,
      unequal_coalescent_centre_test_differences=diffs,
      positive_quotient_reuses_single_rational_centre_for_all_shadows=shadows,
      finite_integer_representative_for_minus_thirteen_ninths_exists=False,
      same_future_coalescence_implies_same_centre=False,
      quotient_is_declared_finite=False,
      source_identity_is_removed=False,
      independent_actual_two_clocks_are_removed=False,
      all_infinite_no_exit_source_centres_covered=False,
      global_collatz='UNKNOWN',
      qed=False
    )


if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
