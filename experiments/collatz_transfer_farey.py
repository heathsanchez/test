#!/usr/bin/env python3
"""
Rigorous arithmetic certificate for the first potentially dangerous
coefficient contraction in the shortcut Collatz map.

All transcendental comparisons use rational enclosures for ln(2), ln(3)
from the atanh series. No floating-point arithmetic is used for claims.

Mathematical ingredients:
1. If a parity prefix of length t has q odd steps, then
     T^t(n) = (3^q n + A)/2^t.
2. At its first coefficient contraction, 3^q < 2^t and all proper
   prefixes satisfy 3^{q_s} >= 2^s.
3. Writing odd positions p_j (0-indexed), prefix survival implies
     p_j <= floor((j-1) log_2 3).
   Therefore the intercept is maximized by the latest-odd mechanical word,
   and termwise
     A < q * 3^{q-1}.
   Hence any additive rescue threshold satisfies
     x_* = A/(2^t-3^q) < q/(3 epsilon),
   where epsilon = t ln 2 - q ln 3 > 0,
   using e^epsilon - 1 > epsilon.
4. The last safe lower approximant and next upper approximant below the
   live resonance are Farey neighbors. Thus no lower rational q/t closer
   to alpha=ln2/ln3 can occur with denominator below their mediant.
5. For the live latest-odd word, Denjoy-Koksma applied to
     f(x)=(1/3)2^{-x}
   gives
     A/3^q <= q/(6 ln 2) + 2/3,
   because the live q is the sum of two consecutive convergent
   denominators and Var(f)=1/3 on the circle.
"""

from fractions import Fraction

L = 2075 * (1 << 60)

# Last safe lower convergent q0/t0 and next upper convergent qu/tu.
q0, t0 = 6586818670, 10439860591
qu, tu = 65470613321, 103768467013
# Their mediant: first unresolved live resonance.
q1, t1 = q0 + qu, t0 + tu

def ln_bounds_atanh(x: Fraction, terms: int = 220):
    """Return rational lower/upper bounds for 2*atanh(x)."""
    assert 0 < x < 1
    s = Fraction(0)
    x2 = x * x
    p = x
    for k in range(terms):
        s += p / (2 * k + 1)
        p *= x2
    lo = 2 * s
    # Tail <= x^(2N+1)/((2N+1)(1-x^2)).
    N = terms
    tail = 2 * (x ** (2 * N + 1)) / ((2 * N + 1) * (1 - x2))
    hi = lo + tail
    return lo, hi

ln2_lo, ln2_hi = ln_bounds_atanh(Fraction(1, 3))  # ln 2
ln3_lo, ln3_hi = ln_bounds_atanh(Fraction(1, 2))  # ln 3

alpha_lo = ln2_lo / ln3_hi
alpha_hi = ln2_hi / ln3_lo

r0 = Fraction(q0, t0)
ru = Fraction(qu, tu)
r1 = Fraction(q1, t1)

assert r0 < alpha_lo
assert alpha_hi < ru
assert r1 < alpha_lo
assert qu * t0 - q0 * tu == 1
assert (q1, t1) == (72057431991, 114208327604)

# Farey-neighbor fact:
# any reduced fraction strictly between r0 and ru has denominator >= t0+tu.
# Thus any q/t < alpha with t < t1 must satisfy q/t <= r0.

delta_lo = alpha_lo - r0
assert delta_lo > 0

# For any earlier first contraction:
# q/(3 epsilon) <= alpha / (3 ln3 (alpha-r0)).
# Use upper numerator / lower denominator enclosure.
previous_rescue_ceiling = alpha_hi / (3 * ln3_lo * delta_lo)
assert previous_rescue_ceiling < L

# At the live resonance, the coarse q/(3 epsilon) certificate fails.
eps1_lo = t1 * ln2_lo - q1 * ln3_hi
eps1_hi = t1 * ln2_hi - q1 * ln3_lo
assert 0 < eps1_lo < eps1_hi
coarse_live_lower = Fraction(q1, 1) / (3 * eps1_hi)
assert coarse_live_lower > L

# Rigorous Denjoy-Koksma rescue ceiling for the extremal latest-odd word:
# A/3^q <= q/(6 ln2) + 2/3
# and (2^t-3^q)/3^q = exp(eps)-1 >= eps.
dk_numerator_hi = Fraction(q1, 1) / (6 * ln2_lo) + Fraction(2, 3)
dk_live_ceiling = dk_numerator_hi / eps1_lo
dk_live_ceiling_int = (dk_live_ceiling.numerator + dk_live_ceiling.denominator - 1) // dk_live_ceiling.denominator
assert dk_live_ceiling_int < (1 << 72)
assert dk_live_ceiling_int > L

def decimal_ratio(x: Fraction, digits=30):
    # deterministic decimal rendering from exact rational
    scale = 10 ** digits
    n = x.numerator * scale // x.denominator
    s = str(n).rjust(digits + 1, "0")
    return s[:-digits] + "." + s[-digits:]

print("FAREY_NEIGHBORS",
      f"{q0}/{t0}",
      f"{qu}/{tu}",
      "det=1")
print("LIVE_MEDIANT", f"{q1}/{t1}")
print("LIVE_LOWER_BOUND", L)
print("PREVIOUS_RESCUE_CEILING_LT",
      previous_rescue_ceiling.numerator // previous_rescue_ceiling.denominator + 1)
print("EPS_LIVE_LO", decimal_ratio(eps1_lo, 40))
print("EPS_LIVE_HI", decimal_ratio(eps1_hi, 40))
print("COARSE_LIVE_CERTIFICATE_FAILS_GT", L)
print("DK_LIVE_RESCUE_CEILING", dk_live_ceiling_int)
print("THEOREM",
      "every first coefficient contraction with t < 114208327604 "
      "forces descent for every n >= 2075*2^60")
print("BOUND",
      "at t=114208327604, even the extremal latest-odd rescue "
      f"requires n <= {dk_live_ceiling_int}")
