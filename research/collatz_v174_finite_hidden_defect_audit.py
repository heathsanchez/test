"""V174: exact bounded audits cannot certify universal future-class uniqueness.

For every finite source cutoff X and genuine shortcut horizon H, choose a
ONE-ARROW map S_a identical on ALL audited finite source/clock trajectories,
but with an independent fixed a != {1,2} in the globally unexamined region.

This is a finite-observation impossibility result, not a counterexample
to true Collatz and not a proof of global convergence.
"""
from __future__ import annotations
import json
from hashlib import sha256


def T(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def F(a: int,n: int)->int:
    return a if n==a else T(n)


def iterate(f,n: int,t: int)->int:
    for _ in range(t):
        n=f(n)
    return n


def run(X:int,H:int)->dict:
    assert X>=1 and H>=0
    a=6*(2**H*(X+1))+5
    assert a>=5 and a%2==1 and a%3==2
    assert F(a,a)==a and F(a,1)==2 and F(a,2)==1
    assert F(a,5 if a!=5 else 7)==T(5 if a!=5 else 7)
    assert T(a)!=a
    observed=0
    max_endpoint=0
    for n in range(X):
        t=n
        f=n
        for clock in range(H+1):
            assert f==t,(X,H,n,clock,a,t,f)
            assert t<=2**clock*n
            assert t<a
            observed+=1
            max_endpoint=max(max_endpoint,t)
            if clock<H:
                t=T(t)
                f=F(a,f)
    assert max_endpoint<a
    # The original terminal seed and the newly created fixed point
    # do not share future endpoints in the false map.
    for j in range(24):
        assert iterate(lambda n:F(a,n),a,j)==a
        assert iterate(lambda n:F(a,n),1,j) in (1,2)
    return {'X':X,'H':H,'hidden_source':str(a),
            'original_source_clock_pairs':observed,
            'max_observed_endpoint':max_endpoint,
            'all_audited_trajectories_equal':True,
            'independent_nonterminal_fixed_class_in_fake_map':True}


def main()->None:
    cases=[(1,0),(2,1),(9,4),(16,8),(33,12),
           (128,16),(256,12),(1024,8)]
    rows=[run(X,H) for X,H in cases]
    # Compare a less excessive optimally hidden source as a numerical
    # control; the Lean theorem uses the conservative explicit bound.
    n0,H0=128,12
    max_seen=max(iterate(T,n,t) for n in range(n0) for t in range(H0+1))
    a_opt=max_seen+1
    while a_opt%6!=5:
        a_opt+=1
    assert a_opt>max_seen and a_opt%3==2 and a_opt%2==1
    assert all(iterate(T,n,t)==iterate(lambda z:F(a_opt,z),n,t)
               for n in range(n0) for t in range(H0+1))
    out={'schema':'COLLATZ_V174_FINITE_AUDIT_HIDDEN_DEFECT_CONTROL',
         'audited_height_clock_pairs':rows,
         'tight_hidden_source_for_X128_H12':a_opt,
         'tight_hidden_source_max_audited_endpoint':max_seen,
         'logical_boundary':'ALL_FINITE_PREFIX_AGREEMENT_NOT_GLOBAL_ODD_AFFINE_LAW',
         'genuine_collatz_counterexample':False,
         'all_scale_anti_two_giant_proved':False,
         'global_collatz':'UNKNOWN','qed':False}
    print(json.dumps(out,sort_keys=True,indent=2))


if __name__=='__main__':
    main()
