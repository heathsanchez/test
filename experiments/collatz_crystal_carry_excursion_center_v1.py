#!/usr/bin/env python3
"""Exact source-coherent audit of individual post-tail h=0 excursions.

For every positive odd source below 2^24, enumerate consecutive safe h=0
boundaries after the source-product tail is zero.  Each interval is represented
by its exact affine map

    2^b y' = 3^r y + A.

For contracting coefficient 3^r < 2^b, test whether the affine fixed point
A/(2^b-3^r) remains below the fixed original source.  This is a protected
source-coherent separator audit, not a universal proof.
"""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction

BITS = 24
DEPTH = 512
TRAIN_BITS = 18


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


qmin = qmin_table(DEPTH)
stats = {k: Counter() for k in ("train", "holdout")}
max_ratio = {k: None for k in ("train", "holdout")}
max_fp = {k: None for k in ("train", "holdout")}
max_len = {k: None for k in ("train", "holdout")}
violations = {k: [] for k in ("train", "holdout")}
unresolved = []
max_crossing = (0, None)

for n in range(3, 1 << BITS, 2):
    group = "train" if n < (1 << TRAIN_BITS) else "holdout"
    freeze = n.bit_length()

    y = n
    q = 0
    prev_boundary = None
    mb = mr = mA = mword = 0
    crossed = False

    for j in range(1, DEPTH + 1):
        bit = y & 1

        if prev_boundary is not None:
            if bit:
                mA = 3 * mA + (1 << mb)
                mr += 1
            mword |= bit << mb
            mb += 1

        if bit:
            y = (3 * y + 1) // 2
            q += 1
        else:
            y //= 2

        h = q - qmin[j]
        if h < 0:
            crossed = True
            if j > max_crossing[0]:
                max_crossing = (j, n)
            break

        if j < freeze or h != 0:
            continue

        stats[group]["boundary_states"] += 1

        if prev_boundary is None:
            prev_boundary = (j, y, q)
            mb = mr = mA = mword = 0
            continue

        start_j, start_y, start_q = prev_boundary
        assert mb > 0
        assert q - start_q == mr
        assert (1 << mb) * y == (3 ** mr) * start_y + mA

        C = (1 << mb) - 3 ** mr
        assert C != 0
        fp = Fraction(mA, C)

        stats[group]["macros"] += 1
        if C > 0:
            stats[group]["contracting_coefficient"] += 1
            if y < start_y:
                stats[group]["contracting_endpoint"] += 1
            else:
                stats[group]["noncontracting_endpoint_under_contracting_coefficient"] += 1
        else:
            stats[group]["expanding_coefficient"] += 1

        if fp > 0:
            stats[group]["positive_fp"] += 1
        else:
            stats[group]["nonpositive_fp"] += 1
        if fp.denominator == 1:
            stats[group]["integer_fp"] += 1

        if fp >= n:
            stats[group]["fixed_point_ge_source"] += 1
            if len(violations[group]) < 20:
                violations[group].append(
                    {
                        "source": n,
                        "start_depth": start_j,
                        "end_depth": j,
                        "fixed_point": [fp.numerator, fp.denominator],
                        "start_endpoint": start_y,
                        "end_endpoint": y,
                        "b": mb,
                        "r": mr,
                    }
                )

        ratio = fp / n
        old = max_ratio[group]
        if old is None or ratio > old[0]:
            max_ratio[group] = (
                ratio,
                {
                    "source": n,
                    "fixed_point": [fp.numerator, fp.denominator],
                    "ratio": [ratio.numerator, ratio.denominator],
                    "start_depth": start_j,
                    "end_depth": j,
                    "start_endpoint": start_y,
                    "end_endpoint": y,
                    "b": mb,
                    "r": mr,
                },
            )

        old = max_fp[group]
        if old is None or fp > old[0]:
            max_fp[group] = (
                fp,
                {
                    "source": n,
                    "fixed_point": [fp.numerator, fp.denominator],
                    "start_depth": start_j,
                    "end_depth": j,
                    "start_endpoint": start_y,
                    "end_endpoint": y,
                    "b": mb,
                    "r": mr,
                },
            )

        old = max_len[group]
        if old is None or mb > old[0]:
            max_len[group] = (
                mb,
                {
                    "source": n,
                    "fixed_point": [fp.numerator, fp.denominator],
                    "start_depth": start_j,
                    "end_depth": j,
                    "start_endpoint": start_y,
                    "end_endpoint": y,
                    "b": mb,
                    "r": mr,
                },
            )

        prev_boundary = (j, y, q)
        mb = mr = mA = mword = 0

    if not crossed:
        unresolved.append(n)

assert not unresolved, unresolved[:20]
assert max_crossing == (287, 13421671), max_crossing

# Exact frozen census.
assert stats["train"]["macros"] == 23078, stats["train"]
assert stats["holdout"]["macros"] == 885296, stats["holdout"]
assert stats["train"]["fixed_point_ge_source"] == 0, stats["train"]
assert stats["holdout"]["fixed_point_ge_source"] == 0, stats["holdout"]
assert (
    stats["train"]["contracting_coefficient"]
    == stats["train"]["contracting_endpoint"]
), stats["train"]
assert (
    stats["holdout"]["contracting_coefficient"]
    == stats["holdout"]["contracting_endpoint"]
), stats["holdout"]

result = {
    "schema": "COLLATZ_CRYSTAL_CARRY_EXCURSION_CENTER_V1",
    "arithmetic": "exact_integer_and_rational",
    "source_bits": BITS,
    "depth": DEPTH,
    "train_source_cap": 1 << TRAIN_BITS,
    "holdout_source_cap": 1 << BITS,
    "max_first_crossing": {
        "depth": max_crossing[0],
        "source": max_crossing[1],
    },
    "train": dict(stats["train"]),
    "holdout": dict(stats["holdout"]),
    "max_fixed_point_over_source_ratio": {
        k: v[1] if v is not None else None for k, v in max_ratio.items()
    },
    "max_fixed_point": {
        k: v[1] if v is not None else None for k, v in max_fp.items()
    },
    "max_excursion_length": {
        k: v[1] if v is not None else None for k, v in max_len.items()
    },
    "violations": violations,
    "status": "BOUNDED_SINGLE_EXCURSION_CENTER_SEPARATOR_SURVIVES",
    "warranted_bounded_conclusion": (
        "Every consecutive post-tail safe h=0 excursion in the declared complete "
        "24-bit source cover has affine fixed point below its original source; "
        "every contracting-coefficient excursion therefore contracts endpoint."
    ),
    "promotion_boundary": (
        "The inequality is not proved for arbitrary source scale, and endpoint "
        "is not a monotone rank because expanding-coefficient excursions remain."
    ),
    "residual": {
        "name": "SOURCE_COHERENT_EXPANDING_OR_APERIODIC_EXCURSIONS",
        "next": (
            "seek a recursively applicable source-local resource across expanding "
            "excursions without dropping actual source-path coherence"
        ),
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))

# qualification-trigger: 1
