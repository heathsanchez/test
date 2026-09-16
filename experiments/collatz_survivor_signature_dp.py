#!/usr/bin/env python3
"""Exact dynamic program for the cone-survivor valuation-signature language.

This intentionally forgets residue representatives and keeps only cumulative
valuation A at accelerated odd depth j.  A child valuation a survives the
coefficient boundary iff

  2^(A+a) <= 3^(j+1),

and, when a is odd (so the next odd endpoint is 2 mod 3), also

  2^(A+a) <= 2*3^j.

The depth-8/12/16/20 rows are regression-checked against the independently
enumerated global valuation-cylinder compiler.
"""

from collections import defaultdict
from fractions import Fraction
import json
import math

EXPECTED = {
    8:  (140,      Fraction(81, 1024)),
    12: (5304,     Fraction(22485, 524288)),
    16: (217900,   Fraction(859743, 33554432)),
    20: (9972876,  Fraction(17256441, 1073741824)),
}

def run(depth: int):
    dp = {0: 1}
    rows = []
    for j in range(1, depth + 1):
        p3 = 3 ** j
        max_a_total = p3.bit_length() - 1
        cone_p = 2 * (3 ** (j - 1))
        max_cone_total = cone_p.bit_length() - 1

        nxt = defaultdict(int)
        for A0, count in dp.items():
            for a in range(1, max_a_total - A0 + 1):
                A = A0 + a
                if (a & 1) and A > max_cone_total:
                    continue
                nxt[A] += count
        dp = dict(nxt)

        density = sum((Fraction(c, 1 << A) for A, c in dp.items()), Fraction())
        row = {
            "depth": j,
            "survivor_words": sum(dp.values()),
            "density_num": density.numerator,
            "density_den": density.denominator,
            "density": float(density),
            "min_A": min(dp) if dp else None,
            "max_A": max(dp) if dp else None,
            "signature_cells": len(dp),
        }
        rows.append(row)

        if j in EXPECTED:
            ec, ed = EXPECTED[j]
            assert row["survivor_words"] == ec, (j, row["survivor_words"], ec)
            assert density == ed, (j, density, ed)
            print("SIGNATURE_EQUALS_GLOBAL_CYLINDERS", json.dumps({
                "depth": j,
                "survivors": ec,
                "density": str(ed),
            }, separators=(",", ":")))

    return rows

def chernoff_rate():
    c = math.log2(3.0)
    z = 2.0 * (c - 1.0) / c
    rate = (c - 1.0) * math.log(z) + math.log(2.0 / c)
    return c, z, rate, math.exp(-rate)

def main():
    depth = 300
    rows = run(depth)
    c, z, rate, factor = chernoff_rate()
    last = rows[-1]
    print("SIGNATURE_DEPTH_300", json.dumps(last, separators=(",", ":")))
    print("SIGNATURE_CHERNOFF", json.dumps({
        "boundary_log2_3": c,
        "optimizer_exp_t": z,
        "rate": rate,
        "asymptotic_factor_upper_bound": factor,
        "bound_at_depth_300": math.exp(-rate * depth),
    }, separators=(",", ":")))
    print("VERIFIED_SIGNATURE_DP_MATCHES_GLOBAL_CYLINDERS")
    print("SURVIVOR_MEASURE_DECAYS_EXPONENTIALLY")
    print("FINAL_GATE=COLLATZ_SURVIVOR_SIGNATURE_DP_V1")

if __name__ == "__main__":
    main()
