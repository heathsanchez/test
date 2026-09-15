#!/usr/bin/env python3
"""Exact coefficient-resonance schedule for the forward/reverse Collatz bridge.

Define c_k as the least integer c with

    3^c > 2^k.

This is the first coefficient-supercritical odd-step count at binary depth k.

Two elementary integer facts explain the observed bridge schedule globally:

1. c_{k+1} is either c_k or c_k+1.

   Monotonicity gives c_{k+1} >= c_k, while

       3^(c_k+1) > 3*2^k > 2^(k+1)

   gives c_{k+1} <= c_k+1.

2. c_{k+3} <= c_k+2.

       3^(c_k+2) > 9*2^k > 8*2^k = 2^(k+3).

   Hence across any three successive increments, at most two are 1.
   Therefore at least one increment is 0: a resonance occurs at least every
   three binary depths.

At a resonance k, c_k=c_{k-1}=c. Minimality at k-1 gives

    3^(c-1) < 2^(k-1)

(the equality case is impossible for positive powers of distinct primes), so

    2*3^(c-1) < 2^k < 3^c.

Thus the critical forward coefficient is supercritical, but composing the
single reverse-O predecessor multiplies it by 2/3 and makes it subcritical.

This file uses only integer arithmetic.  The finite scan is a regression and
schedule generator; the bounded-gap argument above is the general proof.
"""

from __future__ import annotations

import argparse


def critical_c(k: int) -> int:
    assert k >= 0
    target = 1 << k
    p = 1
    c = 0
    while p <= target:
        p *= 3
        c += 1
    return c


def is_resonance(k: int) -> bool:
    assert k >= 1
    return critical_c(k) == critical_c(k - 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-k", type=int, default=10000)
    args = ap.parse_args()
    K = args.max_k
    assert K >= 6

    cs = [critical_c(k) for k in range(K + 4)]
    resonances = []

    for k in range(1, K + 1):
        delta = cs[k] - cs[k - 1]
        assert delta in (0, 1), (k, cs[k - 1], cs[k])

        if delta == 0:
            c = cs[k]
            assert 3**c > 2**k
            # k=1 is the sole degenerate equality 2*3^0 = 2^1.
            # From k>=2 the exponents are positive and equality between
            # powers of 2 and 3 is impossible, giving the strict bridge flip.
            if k >= 2:
                assert 2 * 3 ** (c - 1) < 2**k
            resonances.append(k)

    # Integer form of the global <=3-gap proof.
    for k in range(0, K):
        assert cs[k + 3] <= cs[k] + 2, (k, cs[k], cs[k + 3])

    gaps = [b - a for a, b in zip(resonances, resonances[1:])]
    assert gaps
    assert max(gaps) <= 3
    # Once the initial k=3 resonance is passed, this specific 2/3 vs 3/2
    # rotation produces exactly 2/3 gaps in the checked schedule.
    assert set(gaps).issubset({2, 3})

    observed_bridge_levels = [6, 9, 11, 14, 17, 19, 22, 25, 28, 30, 33]
    predicted = [k for k in resonances if 6 <= k <= 34]
    assert predicted == observed_bridge_levels, (predicted, observed_bridge_levels)

    print("BRIDGE_RESONANCE_MAX_K", K)
    print("BRIDGE_RESONANCE_LEVELS_6_34", ",".join(map(str, predicted)))
    print("BRIDGE_RESONANCE_GAPS", ",".join(map(str, sorted(set(gaps)))))
    print("BRIDGE_RESONANCE_MAX_GAP", max(gaps))
    print("OBSERVED_BRIDGE_LEVELS_MATCH_EXACT_COEFFICIENT_RESONANCE")
    print("VERIFIED_EXACT_BRIDGE_RESONANCE_SCHEDULE")


if __name__ == "__main__":
    main()
