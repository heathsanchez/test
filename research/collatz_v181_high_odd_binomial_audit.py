"""V181 exact all-scale high-odd arithmetic and binomial tail control.

For every positive m and every genuine source n>=2^(10m), Lean
formally proves if oddCount(n,5m)<=3m then T^(5m)(n)<n.

The all-scale parity-word COUNT is a separate elementary consequence
of the exact parity-word bijection: each binary word of length 5m
occurs once among source residues modulo 2^(5m). The surviving
NECESSARY high-odd words, with count A_m = sum binom(5m,a) for
a>=3m+1, satisfy the exact rational Chernoff-style bound

  A_m / 2^(5m) <= (3125 / 3456)^m.

Proof: 3^a*2^(5m-a)>=3^(3m)*2^(2m) on that tail, while
sum binom(5m,a)3^a2^(5m-a)=5^(5m) by binomial theorem.
The inequality is math, but its all-m proof is NOT a separate
Lean formalization in this module; the numerical audit replays
integer inequalities for selected m exactly.

This is a source-height-sensitive density sieve. As m grows,
the n>=2^(10m) threshold ALSO grows. A fixed hypothetical least
bad source does NOT satisfy that threshold for arbitrary m.
No Collatz QED is implied.
"""
from __future__ import annotations
from math import comb
from fractions import Fraction
import json
from pathlib import Path

def T(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def clock(n:int,k:int):
    a=0
    for _ in range(k):
        a+=n%2
        n=T(n)
    return n,a

def main():
    cases=0
    parity_cases=0
    # Small horizons: exact real original sources far above the
    # theorem's independent source-height threshold.
    for k in range(1,13):
        bound=1<<(2*k)
        for r in range(1<<k):
            n=bound+r
            y,a=clock(n,k)
            if 3**a<(1<<k):
                assert y<n,(n,k,a,y)
            cases+=1
    # Confirm unique finite parity words for independently checked k.
    for k in range(1,13):
        words=set()
        for r in range(1<<k):
            n=r;bits=0
            for i in range(k):
                bits|=(n&1)<<i
                n=T(n) if n>0 else 0
            assert bits not in words
            words.add(bits)
        assert len(words)==1<<k
        parity_cases+=len(words)

    rows=[]
    for m in (1,2,4,8,16,32,64,128):
        k=5*m
        surviving=sum(comb(k,j) for j in range(3*m+1,k+1))
        # Exact integer bound; NO approximate floating comparisons.
        lhs=surviving*(3**(3*m))*(2**(2*m))
        rhs=5**(5*m)
        assert lhs<=rhs
        assert surviving>0
        exact=Fraction(surviving,2**k)
        upper=Fraction(3125,3456)**m
        assert exact<=upper and upper<1
        rows.append({
            'm':m,'shortcut_clock_k':k,
            'least_bad_odd_steps_must_be_at_least':3*m+1,
            'source_height_threshold_power_of_two':10*m,
            'necessary_candidate_parity_words':surviving,
            'all_binary_parity_words':2**k,
            'tail_fraction_numerator':exact.numerator,
            'tail_fraction_denominator':exact.denominator,
            'rational_upper_bound_numerator':upper.numerator,
            'rational_upper_bound_denominator':upper.denominator,
            'exact_integer_binomial_bound_verified':True,
        })
    # For EVERY chosen scale an explicit large POSITIVE Mersenne source
    # satisfies the high-odd condition, so the NECESSARY inequality
    # does not eliminate all integer sources at any finite scale.
    # The witness changes with m; it is never a divergent trajectory.
    mersenne_controls=[]
    for m in (1,2,4,8,16,32,64,128):
        K=10*m+1
        n=(1<<K)-1
        endpoint,a=clock(n,5*m)
        assert n>=1<<(10*m)
        assert a==5*m>3*m
        assert endpoint==3**(5*m)*(1<<(5*m+1))-1
        mersenne_controls.append({
            'm':m,'source_bit_depth':K,
            'actual_first_5m_odd_steps':a,
            'source_exceeds_the_height_threshold':True
        })
    # Protected generalized other-basin control: not true +1.
    G=lambda x: x//2 if x%2==0 else (3*x+7)//2
    assert [G(x) for x in (5,11,20,10)]==[11,20,10,5]
    assert [G(x) for x in (7,14)]==[14,7]
    out={
        'schema':'COLLATZ_V181_SOURCE_HEIGHT_CONDITIONED_PARITY_TAIL',
        'real_natural_source_clock_replays':cases,
        'independent_parity_word_bijection_replays':parity_cases,
        'necessary_high_odd_binomial_tail_rows':rows,
        'all_m_rational_tail_bound':'(3125/3456)^m',
        'binomial_infinite_m_inequality_separately_lean_formalized':False,
        'all_source_5m_barrier_formally_requested':True,
        'source_height_threshold_not_uniform_in_m':True,
        'fixed_bad_integer_does_not_satisfy_height_condition_for_all_m':True,
        'mersenne_high_odd_finite_scale_witnesses':mersenne_controls,
        'each_scale_has_an_explicit_positive_high_odd_witness':True,
        'synthetic_G7_distinct_future_cycles_protected':True,
        'global_collatz':'UNKNOWN','qed':False
    }
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/v181-tail.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
       'schema':out['schema'],
       'replayed_source_clocks':cases,
       'binomial_rows':len(rows),
       'last_m':rows[-1]['m'],
       'global_collatz':'UNKNOWN'
    },sort_keys=True))

if __name__=='__main__':
    main()
