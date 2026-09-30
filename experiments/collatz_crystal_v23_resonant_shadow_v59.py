#!/usr/bin/env python3
"""V59: exact resonant V23 source whose V35 shadow crosses zero-tail.

V56 checked the pulled-back V35 expanding shadows through r=64 and found all
of them end before SourceProduct.tail becomes zero. That finite observation is
not universal.

The V35 expanding-return guard has a unique 2-adic fixed parameter
    t* = -17084 / 17635.
V36 pulls owner parameter back to the V23 source parameter by
    t_owner = t_owner0 + 3^47 * u,
    T = T0 + 2^14 * u.
Hence the infinite guard pulls back to one rational 2-adic source coordinate
    alpha = (t* - t_owner0) / 3^47 = N/D.

For K=11r, the least nonnegative u representing alpha mod 2^K satisfies
    D*u - N = h*2^K.
We exhibit an exact enormous phase r0 for which h=1. Then
    u=(2^K+N)/D
is an integer unusually small in its 2^K cylinder. Exact inequalities show the
corresponding natural source has bitlength K-1, while the r0-return shadow ends
at depth K+73. Thus the final six complete V34 expanding returns occur after
source-tail exhaustion (and one preceding return straddles it).

This does NOT assert no OrdinaryExit has already occurred. It is an exact
source/parity/shadow resonance certificate showing that the V35 mechanism can
leak into the zero-tail region; global Collatz remains UNKNOWN.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib, json, math

# Frozen V35/V36 constants.
A = 3**9
B = 2**11
R_ONE = 1260
C = 12118
T0 = 1_018_706
OWNER_T0 = 1_653_209_533_319_313_670_231_276
N0_V23 = 38_911_100_780_481_085_467
NC_V23 = 3_782_158_995_862_761_504_768
N0_SOURCE = 3_852_908_100_950_471_101_957_275_675

assert NC_V23 == (1 << 59) * 3**8

# Exact V35 fixed parameter.
tstar = Fraction(A * R_ONE - B * C, A - B)
assert tstar == Fraction(-17084, 17635)
assert B * tstar == A * (tstar - R_ONE) + B * C
# It is in the required first-return cylinder in the 2-adic sense.
assert (tstar.numerator * pow(tstar.denominator, -1, B)) % B == R_ONE

# Exact V36 pullback.
alpha = (tstar - OWNER_T0) / (3**47)
N, D = alpha.numerator, alpha.denominator
assert N == -9_718_116_706_695_365_524_842_856_448
assert D == 156_297_913_740_071_856_826_707_915
assert math.gcd(abs(N), D) == 1 and D & 1

# Verify the stored factorization of D exactly.
assert D == (3**46) * 5 * 3527

# The r-return guard is t* modulo 2^(11r): base + fixed-point recurrence.
def E_q(x: Fraction) -> Fraction:
    return Fraction(A, B) * (x - R_ONE) + C
assert E_q(tstar) == tstar

# Find/verify one exact phase with h=1:
#   D*u-N = 2^K  <=>  2^K == -N (mod D), K=11r.
g = pow(2, 11, D)
target = (-N) % D
order = 20_833_813_206_596_479_242_830_436
r0 = 18_596_324_321_486_882_488_974_937
assert 0 < r0 < order
assert order == (2**2) * (3**45) * 41 * 43
assert pow(g, order, D) == 1
for p in (2, 3, 41, 43):
    assert pow(g, order // p, D) != 1
assert pow(g, r0, D) == target

K = 11 * r0
assert K >= 200
# Therefore u=(2^K+N)/D is an exact positive integer, without materializing 2^K.
assert pow(2, K, D) == target
assert N < 0
# Positivity follows because 2^K>|N|; K is enormous and the K=200 check suffices.
assert (1 << 200) > abs(N)

# Natural source:
#   T = T0 + 2^14*u
#   n = n0 + (2^73*3^8)*u
F = (1 << 73) * (3**8)
assert NC_V23 * (1 << 14) == F

# Exact coefficient sandwich used to prove bitlength(n)=K-1.
assert 2 * F < D < 4 * F
K0 = 200
assert (D - 2 * F) * (1 << K0) > 2 * D * N0_SOURCE
assert (4 * F - D) * (1 << K0) > 4 * F * abs(N)
# Since both left sides grow with K, for K>=K0:
#   2^(K-2) <= n < 2^(K-1).
source_bitlength = K - 1
zero_tail_depth = K - 1

shadow_start = 73
shadow_end = 73 + 11 * r0
assert shadow_end == K + 73

# Return j (zero-indexed) starts at 73+11j and ends 11 steps later.
# Fully post-zero iff start >= K-1. Exactly j=r0-6,...,r0-1 qualify.
first_full_postzero_j = r0 - 6
assert shadow_start + 11 * first_full_postzero_j >= zero_tail_depth
assert shadow_start + 11 * (first_full_postzero_j - 1) < zero_tail_depth
fully_postzero_returns = r0 - first_full_postzero_j
assert fully_postzero_returns == 6
straddling_j = r0 - 7
assert shadow_start + 11 * straddling_j < zero_tail_depth
assert shadow_start + 11 * (straddling_j + 1) > zero_tail_depth

# Owner-guard congruence follows directly from u == alpha mod 2^K:
# owner_t0 + 3^47*u == t* mod 2^K.
# Verify the rational congruence modulo a representative finite power and
# record the symbolic equality for K.
for kk in (11, 22, 55, 110, 200):
    mod = 1 << kk
    astar = (tstar.numerator * pow(tstar.denominator, -1, mod)) % mod
    aalpha = (N * pow(D, -1, mod)) % mod
    assert (OWNER_T0 + (3**47) * aalpha - astar) % mod == 0

result = {
    "schema": "COLLATZ_CRYSTAL_V23_RESONANT_SHADOW_V59",
    "parents": {
        "V35": "collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385",
        "V36": "collatz-crystal-source-admitted-return-v36@2bc7f481eb0a2ea2130f545d0ba4cd4d5718360d",
        "V56": "collatz-crystal-v23-source-shadow-v56@8d2c353bf204d5bcb2145bb5cf37d3af611712e5",
    },
    "fixed_parameter": {
        "t_star": [tstar.numerator, tstar.denominator],
        "equation": "2^11*t = 3^9*(t-1260) + 2^11*12118",
    },
    "source_pullback": {
        "alpha": [N, D],
        "denominator_factorization": "3^46 * 5 * 3527",
        "law": "T=T0+2^14*u; owner_t=t_owner0+3^47*u",
    },
    "resonance": {
        "base_modulus": D,
        "generator": g,
        "generator_order": order,
        "r0": r0,
        "K": K,
        "verified_congruence": "2^(11*r0) == -N (mod D)",
        "h": 1,
        "symbolic_u": "u=(2^K+N)/D",
    },
    "source_size": {
        "symbolic_source": "n=n0+2^73*3^8*u",
        "proved_bitlength": source_bitlength,
        "zero_tail_depth": zero_tail_depth,
        "coefficient_sandwich": "2F < D < 4F, F=2^73*3^8",
        "inequality_base_K": K0,
    },
    "shadow": {
        "start_depth": shadow_start,
        "end_depth": shadow_end,
        "steps_after_zero_tail": shadow_end - zero_tail_depth,
        "fully_postzero_expanding_returns": fully_postzero_returns,
        "first_fully_postzero_return_index_zero_based": first_full_postzero_j,
        "one_preceding_return_straddles_zero_tail": True,
    },
    "verdict": "EXACT_V23_EXPANDING_SHADOW_RESONANCE_CROSSES_ZERO_TAIL",
    "interpretation": (
        "V56's pre-zero observation through r=64 is not universal. The exact "
        "V35 guard has a resonant V23 source phase at which six full expanding "
        "returns occur after SourceProduct.tail=0. This does not imply a live "
        "counterexample because OrdinaryExit is not excluded at those depths. "
        "It does prove that the pre-zero/post-zero handoff must be handled by "
        "the universal proof rather than by a fixed finite carry horizon."
    ),
    "promotion_boundary": (
        "Exact arithmetic/source-shadow certificate. No claim that the resonant "
        "source is ZeroTailLive or no-Exit throughout the post-zero suffix. "
        "Global Collatz remains UNKNOWN."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
