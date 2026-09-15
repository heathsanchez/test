#!/usr/bin/env python3
"""Exact product quotient of orthogonal global Collatz constructors.

This combines two independently verified strong-induction certificate families:

1. A 2-adic strong-sieve at depth B.  Among the 2^(B-1) odd residue
   classes b mod 2^B, only TWO_LIVE remain unresolved.  Every other odd
   class has an exact inherited/coalescence/immediate-descent certificate
   for every n = a*2^B+b with a>=1.

2. A reverse-predecessor bank modulo 3^Q.  Among all 3^Q residue classes,
   Q_KILLED have an exact positive predecessor p<n whose forward Collatz
   trajectory reaches n.

The moduli are coprime.  Therefore every pair

    (b mod 2^B, r mod 3^Q),  with b odd,

is represented by exactly one odd residue class modulo 2^B*3^Q (CRT).
Consequently the unresolved product is EXACTLY

    TWO_LIVE * (3^Q - Q_KILLED),

not a statistical independence estimate.

This script checks the arithmetic and CRT bijection on deterministic samples
and emits the exact mixed residual.  It does not assert that the residual is
closed; it names the remaining finite consequence space.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path


def crt(a: int, m: int, b: int, n: int) -> int:
    assert m > 0 and n > 0
    assert __import__("math").gcd(m, n) == 1
    t = ((b - a) * pow(m, -1, n)) % n
    x = a + m * t
    assert x % m == a % m
    assert x % n == b % n
    return x % (m * n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--two-bits", type=int, required=True)
    ap.add_argument("--two-live", type=int, required=True)
    ap.add_argument("--q", type=int, required=True)
    ap.add_argument("--q-killed", type=int, required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    B = args.two_bits
    Q = args.q
    M2 = 1 << B
    M3 = 3**Q
    odd2 = M2 // 2

    assert 0 <= args.two_live <= odd2
    assert 0 <= args.q_killed <= M3

    live3 = M3 - args.q_killed
    total = odd2 * M3
    residual = args.two_live * live3
    closed = total - residual
    residual_fraction = Fraction(residual, total)
    closed_fraction = Fraction(closed, total)

    # Exact deterministic CRT controls spanning both coordinate systems.
    b_samples = sorted({
        1,
        3,
        M2 - 1,
        ((M2 // 3) | 1),
        ((2 * M2 // 3) | 1),
    })
    r_samples = sorted({
        0,
        1,
        2,
        M3 // 3,
        M3 // 2,
        M3 - 1,
    })

    checks = 0
    for b in b_samples:
        assert 0 <= b < M2 and b & 1
        for r in r_samples:
            x = crt(b, M2, r, M3)
            assert x & 1
            assert x % M2 == b
            assert x % M3 == r
            checks += 1

    result = {
        "kind": "exact_global_strong_induction_constructor_product",
        "two_bits": B,
        "two_odd_classes": odd2,
        "two_live": args.two_live,
        "two_live_fraction": args.two_live / odd2,
        "q": Q,
        "q_total": M3,
        "q_killed": args.q_killed,
        "q_live": live3,
        "q_live_fraction": live3 / M3,
        "mixed_total_classes": total,
        "mixed_closed_classes": closed,
        "mixed_residual_classes": residual,
        "mixed_closed_fraction": float(closed_fraction),
        "mixed_residual_fraction": float(residual_fraction),
        "mixed_closed_fraction_exact": (
            f"{closed_fraction.numerator}/{closed_fraction.denominator}"
        ),
        "mixed_residual_fraction_exact": (
            f"{residual_fraction.numerator}/{residual_fraction.denominator}"
        ),
        "crt_controls": checks,
    }

    print(
        "GLOBAL_CONSTRUCTOR_PRODUCT",
        f"B={B}",
        f"two_live={args.two_live}/{odd2}",
        f"Q={Q}",
        f"q_live={live3}/{M3}",
        f"mixed_residual={residual}/{total}",
        f"residual_fraction={float(residual_fraction):.12f}",
        f"closed_fraction={float(closed_fraction):.12f}",
    )
    print("GLOBAL_CONSTRUCTOR_PRODUCT_CRT_CONTROLS", checks)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("VERIFIED_EXACT_GLOBAL_CONSTRUCTOR_PRODUCT_QUOTIENT")


if __name__ == "__main__":
    main()
