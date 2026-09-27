#!/usr/bin/env python3
"""Exact Crystal audit of post-tail h=0 carry excursions.

Declared boundary:
  * every positive odd source n < 2^24
  * exact shortcut Collatz
  * depth <= 512
  * only states after n < 2^j (source-product tail already zero)
  * only live coefficient states h_j = q_j-qmin(j) >= 0

A carry excursion is the exact affine map between consecutive safe h=0 states.
When the same exact excursion map reappears on one source path, compose the
intervening excursion maps and inspect the resulting affine cycle fixed point.

This is bounded theorem discovery.  It does not infer a universal rank.
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


def compose(macros):
    """Compose F(x)=(3^r*x+A)/2^b in execution order."""
    a = 1
    B = 0
    D = 0
    R = 0
    for b, r, A, _word in macros:
        B = (3 ** r) * B + A * (1 << D)
        a *= 3 ** r
        D += b
        R += r
    return a, B, D, R


qmin = qmin_table(DEPTH)
stats = {k: Counter() for k in ("train", "holdout")}
max_ratio = {k: None for k in ("train", "holdout")}
max_fp = {k: None for k in ("train", "holdout")}
max_cycle_len = {k: None for k in ("train", "holdout")}
violations = {k: [] for k in ("train", "holdout")}
unresolved = []
max_crossing = (0, None)

for n in range(3, 1 << BITS, 2):
    group = "train" if n < (1 << TRAIN_BITS) else "holdout"
    freeze = n.bit_length()

    y = n
    q = 0
    prev_boundary = None

    # Current excursion affine accumulator.
    mb = mr = mA = mword = 0

    # Sequence of completed exact excursion maps and endpoint after each map.
    seq = []
    last_idx = {}
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

        macro = (mb, mr, mA, mword)
        assert (1 << mb) * y == (3 ** mr) * start_y + mA
        stats[group]["macros"] += 1

        # A repeated exact map label induces one exact composed affine cycle:
        # start just after the earlier occurrence and execute the intervening
        # maps plus the new occurrence.
        if macro in last_idx:
            i = last_idx[macro]
            exec_macros = [m for m, _endpoint in seq[i + 1 :]] + [macro]
            entry = seq[i][1]

            a, B, D, R = compose(exec_macros)
            assert a * entry + B == (1 << D) * y

            C = (1 << D) - a
            assert C != 0
            fp = Fraction(B, C)

            stats[group]["cycles"] += 1
            if fp > 0:
                stats[group]["positive_fp"] += 1
            else:
                stats[group]["nonpositive_fp"] += 1
            if fp.denominator == 1:
                stats[group]["integer_fp"] += 1
            if fp > 0 and fp.denominator == 1:
                stats[group]["positive_integer_fp"] += 1

            if fp >= n:
                stats[group]["fixed_point_ge_source"] += 1
                if len(violations[group]) < 20:
                    violations[group].append(
                        {
                            "source": n,
                            "fixed_point": [fp.numerator, fp.denominator],
                            "entry": entry,
                            "exit": y,
                            "D": D,
                            "R": R,
                            "cycle_maps": len(exec_macros),
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
                        "entry": entry,
                        "exit": y,
                        "D": D,
                        "R": R,
                        "cycle_maps": len(exec_macros),
                    },
                )

            old = max_fp[group]
            if old is None or fp > old[0]:
                max_fp[group] = (
                    fp,
                    {
                        "source": n,
                        "fixed_point": [fp.numerator, fp.denominator],
                        "entry": entry,
                        "exit": y,
                        "D": D,
                        "R": R,
                        "cycle_maps": len(exec_macros),
                    },
                )

            old = max_cycle_len[group]
            if old is None or len(exec_macros) > old[0]:
                max_cycle_len[group] = (
                    len(exec_macros),
                    {
                        "source": n,
                        "fixed_point": [fp.numerator, fp.denominator],
                        "D": D,
                        "R": R,
                    },
                )

        last_idx[macro] = len(seq)
        seq.append((macro, y))
        prev_boundary = (j, y, q)
        mb = mr = mA = mword = 0

    if not crossed:
        unresolved.append(n)

assert not unresolved, unresolved[:20]
assert max_crossing == (287, 13421671), max_crossing

# Pin the exact census so future code changes cannot silently alter authority.
assert stats["train"]["cycles"] == 7191, stats["train"]
assert stats["holdout"]["cycles"] == 278006, stats["holdout"]
assert stats["train"]["fixed_point_ge_source"] == 0, stats["train"]
assert stats["holdout"]["fixed_point_ge_source"] == 0, stats["holdout"]

result = {
    "schema": "COLLATZ_CRYSTAL_CARRY_EXCURSION_AFFINE_V1",
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
    "max_cycle_map_length": {
        k: v[1] if v is not None else None for k, v in max_cycle_len.items()
    },
    "violations": violations,
    "status": "BOUNDED_AFFINE_CYCLE_SEPARATOR_SURVIVES",
    "warranted_bounded_conclusion": (
        "On the complete declared 24-bit source boundary, every repeated exact "
        "post-tail h=0 excursion-map cycle has affine fixed point strictly below "
        "its original source."
    ),
    "promotion_boundary": (
        "No universal source-local affine rank is proved. Repeated-map cycles are "
        "only one branch of an infinite zero-EXIT execution."
    ),
    "residual": {
        "name": "APERIODIC_OR_EVENTUALLY_POSITIVE_CARRY",
        "next": (
            "attack exact source-coherent paths that either use infinitely many "
            "novel h=0 excursion maps or eventually stop returning to h=0"
        ),
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
