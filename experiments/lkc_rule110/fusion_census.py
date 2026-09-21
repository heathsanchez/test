#!/usr/bin/env python3
"""Exact Rule-110 fusion census for the Lean Kernel Challenge experiment.

This does not assume fusion is beneficial. It:
  * independently checks the Rule-110 truth table against a Boolean formula,
  * constructs exact k-step local functions for k in {1,2,4,8},
  * measures reduced ordered BDD node count and ANF monomial count,
  * cross-checks the bit-packed 256-cell implementation against a cell-list
    implementation on deterministic random cyclic rows.

The result is evidence for whether direct T^k compilation is structurally
promising before encoding a larger Lean proof.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

MASK256 = (1 << 256) - 1


def rule110_table(l: int, c: int, r: int) -> int:
    return (0, 1, 1, 1, 0, 1, 1, 0)[(l << 2) | (c << 1) | r]


def rule110_formula(l: int, c: int, r: int) -> int:
    return int(((not l) and (c or r)) or (l and (c ^ r)))


def local_k(bits: list[int], steps: int) -> int:
    row = bits[:]
    for _ in range(steps):
        row = [rule110_formula(row[i], row[i + 1], row[i + 2])
               for i in range(len(row) - 2)]
    assert len(row) == 1
    return row[0]


def truth_table(steps: int) -> list[int]:
    n = 2 * steps + 1
    out = []
    for x in range(1 << n):
        bits = [(x >> i) & 1 for i in range(n)]
        out.append(local_k(bits, steps))
    return out


def anf_stats(vals: list[int], n: int) -> tuple[int, int]:
    a = vals[:]
    for i in range(n):
        bit = 1 << i
        for mask in range(1 << n):
            if mask & bit:
                a[mask] ^= a[mask ^ bit]
    monomials = [m for m, coeff in enumerate(a) if coeff]
    return len(monomials), max((m.bit_count() for m in monomials), default=0)


def reorder(vals: list[int], n: int, order: list[int]) -> list[int]:
    out = [0] * (1 << n)
    for new_idx in range(1 << n):
        old_idx = 0
        for depth, var in enumerate(order):
            bit = (new_idx >> (n - 1 - depth)) & 1
            old_idx |= bit << var
        out[new_idx] = vals[old_idx]
    return out


def robdd_nodes(vals: list[int], n: int, order: list[int]) -> int:
    vals = reorder(vals, n, order)
    uniq: dict[tuple[int, int, int], int] = {}

    def rec(lo: int, hi: int, depth: int) -> int:
        first = vals[lo]
        constant = True
        for i in range(lo + 1, hi):
            if vals[i] != first:
                constant = False
                break
        if constant:
            return first
        mid = (lo + hi) // 2
        low = rec(lo, mid, depth + 1)
        high = rec(mid, hi, depth + 1)
        if low == high:
            return low
        key = (depth, low, high)
        node = uniq.get(key)
        if node is None:
            node = len(uniq) + 2
            uniq[key] = node
        return node

    rec(0, len(vals), 0)
    return len(uniq)


def rotl256(x: int, k: int = 1) -> int:
    k %= 256
    return ((x << k) | (x >> (256 - k))) & MASK256 if k else x & MASK256


def rotr256(x: int, k: int = 1) -> int:
    k %= 256
    return ((x >> k) | (x << (256 - k))) & MASK256 if k else x & MASK256


def bstep(x: int) -> int:
    left = rotl256(x)
    right = rotr256(x)
    return (MASK256 ^ (((MASK256 ^ x) & (MASK256 ^ right))
                       | (left & x & right))) & MASK256


def list_step(x: int) -> int:
    bits = [(x >> i) & 1 for i in range(256)]
    out = 0
    for i in range(256):
        v = rule110_table(bits[(i - 1) % 256], bits[i], bits[(i + 1) % 256])
        out |= v << i
    return out


def iter_fn(fn, x: int, k: int) -> int:
    for _ in range(k):
        x = fn(x)
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="rule110-fusion.json")
    ap.add_argument("--random-rows", type=int, default=64)
    args = ap.parse_args()

    for l in (0, 1):
        for c in (0, 1):
            for r in (0, 1):
                assert rule110_table(l, c, r) == rule110_formula(l, c, r)

    rows = []
    for k in (1, 2, 4, 8):
        n = 2 * k + 1
        vals = truth_table(k)
        anf_count, anf_degree = anf_stats(vals, n)
        # Natural dependency direction for this asymmetric CA is right-to-left.
        rtl_order = list(reversed(range(n)))
        ltr_order = list(range(n))
        rows.append({
            "steps": k,
            "radius": k,
            "inputs": n,
            "truth_rows": 1 << n,
            "ones": sum(vals),
            "anf_monomials": anf_count,
            "anf_degree": anf_degree,
            "robdd_nodes_right_to_left": robdd_nodes(vals, n, rtl_order),
            "robdd_nodes_left_to_right": robdd_nodes(vals, n, ltr_order),
        })

    rng = random.Random(110)
    packed_checks = 0
    for _ in range(args.random_rows):
        x = rng.getrandbits(256)
        for k in (1, 2, 4, 8):
            assert iter_fn(bstep, x, k) == iter_fn(list_step, x, k)
            packed_checks += 1

    result = {
        "status": "VERIFIED_RULE110_FUSION_CENSUS",
        "truth_table_formula_cases": 8,
        "packed_cross_checks": packed_checks,
        "fusion": rows,
        "interpretation": (
            "Direct truth-function fusion is exact, but structural size must beat "
            "repeated bstep before promotion. The 8-step ROBDD/ANF census is a "
            "negative control against assuming that fusion is automatically cheaper."
        ),
    }

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
