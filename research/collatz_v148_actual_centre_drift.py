"""V148 exact protected-centre transition audit; no finite-horizon QED.

Every actually visited odd n step scales (A,R) by 3, preserving
the rational source centre. Every even step leaves A fixed and adds
2^k to R, giving a STRICTLY more negative rational centre.

The symbolic no-eventual-stabilization claim is separately proved in
Lean using the V141 theorem that all positive natural orbits visit
even states arbitrarily late. Finite exact controls are not proof of
universal Collatz convergence or divergence.
"""
from __future__ import annotations
from fractions import Fraction
import json


def T(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2


def audit(source:int,steps:int=256):
    assert source>0
    n=source
    A=1
    R=1
    bias=0
    alpha=0
    classes=[]
    strict_even=0
    invariant_odd=0
    for k in range(steps):
        old=Fraction(-R,A)
        assert A==3**alpha
        assert R==bias+(1<<k)
        assert (A*source+R)==(1<<k)*(n+1)
        assert A%2==1
        n1=T(n)
        if n%2:
            a1=3*A
            r1=3*R
            bias=3*bias+(1<<k)
            alpha+=1
            assert Fraction(-r1,a1)==old
            invariant_odd+=1
        else:
            a1=A
            r1=R+(1<<k)
            assert Fraction(-r1,a1)<old
            assert a1*R<A*r1
            strict_even+=1
        A,R,n=a1,r1,n1
        classes.append((R,A))
    # Two positions share the class exactly if their value Fraction(-R,A) agrees.
    # Odd visits can make equality consecutive, but any intervening even
    # visit irreversibly destroys equality for all subsequent clocks.
    return {
      "source":source,
      "steps":steps,
      "odd_class_invariants":invariant_odd,
      "even_strict_new_classes":strict_even,
      "different_classes":strict_even+1,
      "terminal_flag":source in (1,2),
      "first_end_centre":str(Fraction(-R,A)),
      "source_centre_observation_verified_all_prefixes":True
    }


def terminal_closed_form(m:int):
    # Even clocks 2m of the true 1 -> 2 -> 1 trajectory.
    a=3**m
    r=2*4**m-a
    c=Fraction(-r,a)
    assert c==1-Fraction(2*4**m,3**m)
    return {"m":m,"numerator":c.numerator,
            "denominator":c.denominator}


def main():
    cases=[audit(n,96) for n in range(1,501)]
    term=[terminal_closed_form(m) for m in range(20)]
    cs=[Fraction(d["numerator"],d["denominator"]) for d in term]
    assert all(cs[i+1]<cs[i] for i in range(len(cs)-1))
    assert cases[0]["terminal_flag"] and cases[0]["different_classes"]>=40
    assert sum(x["even_strict_new_classes"] for x in cases)>10000
    assert all(c["source_centre_observation_verified_all_prefixes"]
               for c in cases)
    shadow=audit(27,128)
    # n=27, k=0,1,2 are odd. k=2 has even endpoint 62 and k=3
    # source centre -13/9, agreeing with V146.
    x=27
    A=1;R=1
    for k in range(3):
        if x%2: A*=3;R*=3
        else: R+=1<<k
        x=T(x)
    assert x==31 and Fraction(-R,A)==Fraction(-13,9)
    return {
      "schema":"COLLATZ_V148_ACTUAL_RATIONAL_CENTRE_DRIFT_AUDIT",
      "exact_finite_source_cases":len(cases),
      "steps_per_source":96,
      "even_steps_strictly_change_observation_class":True,
      "odd_steps_preserve_observation_class":True,
      "source_relative_affine_identity_checked":True,
      "terminal_one_already_has_many_distinct_centre_classes":True,
      "terminal_one_closed_form_even_clocks":term,
      "v146_shadow_source27_after_three_steps_centre":"-13/9",
      "source27_sample":shadow,
      "universal_no_eventually_fixed_centre_requires_lean":True,
      "finiteness_of_actual_evolving_v147_classes_as_no_exit_bar_supported":False,
      "new_general_source_forcing_theorem_proven":False,
      "global_collatz":"UNKNOWN",
      "qed":False
    }


if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))
