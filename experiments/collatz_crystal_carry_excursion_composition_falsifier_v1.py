#!/usr/bin/env python3
"""Shortest exact falsifier for arbitrary composition of the excursion-centre law.

The bounded single-excursion audit suggests that consecutive post-tail safe h=0
excursions have affine fixed point below the original source.  This file tests
the stronger composition claim and pins its first small exact failures.

No global theorem is inferred.
"""
from __future__ import annotations

import json
from fractions import Fraction


def qmin_table(depth: int) -> list[int]:
    out = [0] * (depth + 1)
    q = 0
    p3 = 1
    for j in range(1, depth + 1):
        while p3 < (1 << j):
            p3 *= 3
            q += 1
        out[j] = q
    return out


def trace(n: int, depth: int):
    qmin = qmin_table(depth)
    y = n
    q = 0
    out = {0: (y, q, q - qmin[0])}
    for j in range(1, depth + 1):
        bit = y & 1
        if bit:
            y = (3 * y + 1) // 2
            q += 1
        else:
            y //= 2
        out[j] = (y, q, q - qmin[j])
    return out


cases = [
    {"source": 31, "start": 8, "end": 54},
    {"source": 47, "start": 7, "end": 53},
]

rows = []
for case in cases:
    n = case["source"]
    a = case["start"]
    b = case["end"]
    tr = trace(n, b)
    ya, qa, ha = tr[a]
    yb, qb, hb = tr[b]

    assert a >= n.bit_length()
    assert ha == 0 and hb == 0

    D = b - a
    R = qb - qa
    A = (1 << D) * yb - (3 ** R) * ya
    C = (1 << D) - 3 ** R
    assert A > 0 and C > 0

    fp = Fraction(A, C)
    assert fp >= n
    assert yb > ya

    internal = [
        j
        for j in range(a + 1, b)
        if j >= n.bit_length() and tr[j][2] == 0
    ]
    assert internal

    rows.append(
        {
            **case,
            "start_endpoint": ya,
            "end_endpoint": yb,
            "D": D,
            "R": R,
            "A": A,
            "C": C,
            "fixed_point": [fp.numerator, fp.denominator],
            "fixed_point_ge_source": True,
            "internal_safe_h0_returns": internal,
        }
    )

assert rows[0]["A"] == 228560124140735
assert rows[0]["C"] == 1738366812781
assert rows[0]["fixed_point"] == [228560124140735, 1738366812781]
assert rows[1]["fixed_point"] == rows[0]["fixed_point"]

result = {
    "schema": "COLLATZ_CRYSTAL_CARRY_EXCURSION_COMPOSITION_FALSIFIER_V1",
    "status": "COMPOSED_CENTER_RANK_REJECTED",
    "counterexamples": rows,
    "rejected": (
        "The below-source affine-centre property for consecutive safe h=0 "
        "excursions may not be promoted to arbitrary concatenations."
    ),
    "retained": (
        "The complete 24-bit consecutive-excursion audit remains a bounded "
        "candidate separator on its exact declared boundary."
    ),
    "residual": {
        "name": "RETURN_LOCAL_RESOURCE_ONLY",
        "next": (
            "if the consecutive-excursion separator is pursued, the resource "
            "must reset at each actual h=0 return and handle expanding returns "
            "without grouping them into an arbitrary longer macro"
        ),
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
