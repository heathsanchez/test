"""V168B: rigorous *single clock-block* weighted terminal coverage gain.

Theorem (elementary arithmetic plus independent exact audit): for shortcut
T(n)=n/2 (even), (3n+1)/2 (odd), define U_H(n) to be 1 if positive n has
not hit {1,2} by real clock H and 0 otherwise, and
S(H)=sum_{n>=1} U_H(n)/n^(3/2).
Then S(60) < (4/5)*S(40). This is an infinite-original-source statement,
but concerns only a fixed horizon 40->60. It says nothing about contraction
for all later clocks or dyadic source scales; global Collatz UNKNOWN.

The exact finite witness uses all positive n<2^18 with integral flooring of
Q/n^(3/2) and a rigorous upper bound on the infinite tail. No floats,
probability assumptions, or convergence premise occur in certification.
"""
from math import isqrt
import json


def T(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def main() -> None:
    X, Q = 1 << 18, 10**12
    clocks = (40, 60)
    xs = list(range(X))
    states = {}
    for h in range(clocks[1] + 1):
        if h in clocks:
            b = bytearray((z != 1 and z != 2) for z in xs)
            b[0] = 0
            states[h] = b
        if h < clocks[1]:
            xs = [T(z) for z in xs]
    A, B = states[40], states[60]
    a_count, b_count, new_count = 0, 0, 0
    lowerA, newLower, residue2Lower = 0, 0, 0
    Q2 = Q*Q
    for n in range(1, X):
        floor_weight = isqrt(Q2 // (n*n*n))
        if A[n]:
            a_count += 1
            lowerA += floor_weight
            if n % 3 == 2:
                residue2Lower += floor_weight
            if not B[n]:
                new_count += 1
                newLower += floor_weight
        if B[n]:
            assert A[n], 'terminal class must be closed'
            b_count += 1
    assert a_count == 229259
    assert b_count == 164657
    assert new_count == 64602
    assert lowerA == 125286327534
    assert newLower == 26452894380
    finiteAUpper = lowerA + a_count
    assert finiteAUpper == 125286556793
    # Integral tail: sum_{n>=X} n^(-3/2) <= 2/sqrt(X-1) < 1/250.
    assert X-1 > 500*500
    assert Q % 250 == 0
    D = finiteAUpper + Q // 250
    ratioNumer = D - newLower
    assert D == 129286556793
    assert residue2Lower == 43282288053
    # A pointwise finite-clock residue-2 anti-bias bound is FALSE:
    # exact infinite weighted residue-2 share of the H40 timeout set > 1/3.
    assert 3*residue2Lower > D
    assert ratioNumer == 102833662413
    assert 5*ratioNumer < 4*D
    out = {
        'schema':'COLLATZ_V168B_GLOBAL_ORIGINAL_SOURCE_SINGLE_BLOCK_GAIN',
        'tooling':'PURE_PYTHON_INT_ISQRT_EXACT_FINITE_PLUS_INTEGRAL_TAIL',
        'source_cutoff_exclusive':X, 'clock_from':40,'clock_to':60,
        'weight':'n^(-3/2)', 'Q':Q,
        'uncertified_at_40_below_cutoff':a_count,
        'uncertified_at_60_below_cutoff':b_count,
        'newly_certified_between_41_and_60_below_cutoff':new_count,
        'S40_finite_lower_units':lowerA,
        'S40_finite_upper_units':finiteAUpper,
        'new_terminal_weight_lower_units':newLower,
        'tail_upper_units':Q//250,
        'S40_infinite_upper_units':D,
        'S40_residue2_lower_units':residue2Lower,
        'finite_clock_R2_strictly_exceeds_one_third':3*residue2Lower>D,
        'S60_over_S40_upper_num':ratioNumer,
        'S60_over_S40_upper_den':D,
        'strictly_less_than_four_fifths':5*ratioNumer<4*D,
        'all_scale_positive_gain_proved':False,
        'global_collatz':'UNKNOWN', 'qed':False,
    }
    print(json.dumps(out, sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
