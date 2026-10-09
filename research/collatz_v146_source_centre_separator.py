"""V146 exact, SOURCE-ATTACHED finite-centre semantic separator.

This module never mistakes arbitrary finite no-descent prefixes for
genuine infinite NoExit or a least positive nonconvergent source.
No unqualified proof of universal Collatz convergence is claimed.
"""
from __future__ import annotations
from fractions import Fraction
import json


def shortcut(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def affine(n: int, k: int):
    x = n
    alpha = 0
    bias = 0
    trace = [x]
    for j in range(k):
        if x % 2:
            bias = 3 * bias + 2**j
            alpha += 1
        x = shortcut(x)
        trace.append(x)
    assert 2**k * x == 3**alpha * n + bias
    centre = Fraction(-(bias + 2**k), 3**alpha)
    return dict(source=n, clock=k, endpoint=x, odd_count=alpha,
                bias=bias, trace=trace,
                centre_numerator=centre.numerator,
                centre_denominator=centre.denominator)


def shadow_source(t: int) -> int:
    n = 27
    for _ in range(t):
        n = 64 * n + 91
    return n


def shadow_case(t: int):
    B = 6*t + 5
    Q = 2**B
    n = shadow_source(t)
    a = affine(n, 3)
    assert n % 8 == 3
    assert n % 4 == 3
    assert a["trace"] == [n, shortcut(n), 2*(Q-1), Q-1]
    assert all(x >= n for x in a["trace"])
    assert 9*n+13 == 8*Q
    assert (a["centre_numerator"], a["centre_denominator"]) == (-13,9)
    assert (a["endpoint"]+1) % Q == 0
    assert ((3**a["odd_count"])*n+a["bias"]+2**3) % (Q*8) == 0
    return dict(t=t, B=B, Q=Q, n=n, affine=a,
                actual_three_step_prefix_nondescending=True,
                positive_original_source_mod_four=3,
                eventual_no_exit_claimed=False)


def predeclared_centre_falsifier(centres):
    assert all(isinstance(d,int) and d>=0 for d in centres)
    M=max(centres,default=0)
    t=0
    while 2**(6*t+5) <= 13+9*M:
        t+=1
    case=shadow_case(t)
    Q=case["Q"];n=case["n"]
    assert all(0<n+d<Q for d in centres)
    assert all((n+d)%Q != 0 for d in centres)
    return dict(centre_count=len(centres),largest_magnitude=M,
                witnessed_precision=case["B"],
                original_source=n,
                exact_endpoint=case["affine"]["endpoint"],
                no_predeclared_negative_integer_centre_matches=True,
                infinite_no_exit_premise_asserted=False)


def main():
    # Positive coalescence is NOT source-centre observational equivalence:
    # 21 and 3 meet at endpoint 8 via independent (3,2) clocks.
    a=affine(21,3);b=affine(3,2)
    assert a["endpoint"]==b["endpoint"]==8
    assert (a["centre_numerator"],a["centre_denominator"])==(-3,1)
    assert (b["centre_numerator"],b["centre_denominator"])==(-1,1)
    assert a["clock"]!=b["clock"]

    # Even fixed n=1 has different actual pulled centres at k=0 and 2,
    # despite unchanged terminal future equivalence.
    fixed=[affine(1,k) for k in (0,2,4,6,8)]
    assert len({(v["centre_numerator"],v["centre_denominator"])
                for v in fixed})==len(fixed)

    exact_families=[shadow_case(t) for t in range(9)]
    sets=[
        [],[0],[1],[3],[5],[0,1,3],
        list(range(12)),[0,1,2,3,5,7,11,13,19,27,41],
        [0,1,100,1024,2048],
        [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],
        [5,13,27,45,81,91,127,255,511],
        [2**j for j in range(16)]
    ]
    centre_separators=[predeclared_centre_falsifier(s) for s in sets]
    assert all(v["no_predeclared_negative_integer_centre_matches"]
               for v in centre_separators)

    # Keep historical V115 source countercontrol separate from the new
    # mod-4=3, 27-root example.
    v115=[]
    for B in (1,3,5,7,9,11,13,15,17):
        n=(2**(B+2)-5)//3
        assert 3*n+5==2**(B+2)
        q=2**B
        h=affine(n,2)
        assert h["endpoint"]==q-1
        assert n%4==1
        assert Fraction(h["centre_numerator"],h["centre_denominator"])==Fraction(-5,3)
        v115.append({"B":B,"n":n,"source_mod4":1})

    return {
      "schema":"COLLATZ_V146_EXACT_SOURCE_CENTRE_TRANSPORT_SEPARATOR",
      "parent_theorem":"V95 exact affine source cocycle",
      "protected_future":"actual two-clock smaller-positive-source coalescence",
      "different_true_coalescent_source_centres":{
         "a":21,"p":3,"clocks":[3,2],"meeting_endpoint":8,
         "centres":["-3","-1"],
         "future_class_does_not_force_source_centre_identity":True,
      },
      "fixed_source_terminal_class_changing_centres":[
          {"clock":x["clock"],"numerator":x["centre_numerator"],
           "denominator":x["centre_denominator"]} for x in fixed],
      "old_v115_sources_mod4_one":v115,
      "new_source27_root_odd_mod4_three_prefixes":exact_families,
      "predeclared_finite_nonpositive_integer_centres":centre_separators,
      "new_exact_source_centre":"-13/9",
      "universal_finite_centre_original_source_no_exit_bridge_proven":False,
      "new_family_has_infinite_no_exit_proven":False,
      "finite_prefix_is_not_least_bad_source_proof":True,
      "global_collatz":"UNKNOWN",
      "qed":False,
    }


if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))
