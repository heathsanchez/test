#!/usr/bin/env python3
"""Exact valuation-signature quotient for the deterministic Collatz cone.

No global Collatz claim is made here. The script verifies three reductions:

1. Every inverse-odd opportunity inside an odd-to-odd block is dominated by
   the final odd state.
2. Consecutive accelerated steps with valuation a=1 collapse exactly.
3. On the first macro (x=n), closure depends only on the valuation pair (v,b),
   not on the odd core.
"""

from collections import defaultdict
import json
import math


def v2(x: int) -> int:
    assert x > 0
    return (x & -x).bit_length() - 1


def T(x: int) -> int:
    return (3 * x + 1) // 2 if x & 1 else x // 2


def cone_at(y: int, n: int) -> bool:
    return y % 3 == 2 and (2 * y - 1) // 3 < n


def macro(x: int):
    assert x > 1 and x & 1
    v = v2(x + 1)
    m = (x + 1) >> v
    k = v - 1
    w = pow(3, k) * ((x + 1) >> k) - 1
    assert w == 2 * pow(3, v - 1) * m - 1
    z = pow(3, v) * m - 1
    b = v2(z)
    assert b >= 1
    u = z >> b
    assert u & 1
    return v, b, b + 1, w, u


def macro_closes(n: int, b: int, u: int) -> bool:
    return u < n or (b % 2 == 0 and 2 * u < 3 * n + 1)


def scan_macro_block(n: int, x: int):
    assert x >= n and x & 1
    v, b, a_term, w, u = macro(x)
    y = x
    events = []
    steps = 0
    for _ in range(v - 1):
        aa = v2(3 * y + 1)
        assert aa == 1
        y = T(y)
        steps += 1
        events.append((steps, y, y < n, cone_at(y, n)))
        assert y & 1
    assert y == w
    aa = v2(3 * y + 1)
    assert aa == a_term
    s = 3 * y + 1
    for j in range(1, aa + 1):
        yy = s >> j
        steps += 1
        events.append((steps, yy, yy < n, cone_at(yy, n)))
    assert events[-1][1] == u
    return events, (v, b, u)


def pair_closes(v: int, b: int) -> bool:
    direct = (1 << (v + b)) > pow(3, v)
    cone = b % 2 == 0 and 3 * (1 << (v + b - 1)) > pow(3, v)
    return direct or cone


def trace(n: int, max_macros: int = 10000):
    assert n > 1 and n & 1
    x = n
    out = []
    if cone_at(n, n):
        return [("t0", True, n)]
    for _ in range(max_macros):
        v, b, _a, _w, u = macro(x)
        close = macro_closes(n, b, u)
        out.append(((v, b), close, u))
        if close:
            return out
        x = u
    raise RuntimeError(("macro cap", n, x, max_macros))


def verify_block_equivalence(limit: int):
    checked_blocks = 0
    for n in range(3, limit + 1, 2):
        x = n
        if cone_at(n, n):
            continue
        for _ in range(10000):
            events, (v, b, u) = scan_macro_block(n, x)
            literal = any(d or c for _t, _y, d, c in events)
            collapsed = macro_closes(n, b, u)
            if literal != collapsed:
                raise AssertionError(("block mismatch", n, x, v, b, u, events))
            checked_blocks += 1
            if collapsed:
                break
            x = u
        else:
            raise AssertionError(("block cap", n))
    return checked_blocks


def verify_first_pair_quotient(limit: int):
    seen = defaultdict(set)
    counts = defaultdict(int)
    checked = 0
    for n in range(3, limit + 1, 2):
        v, b, _a, _w, u = macro(n)
        actual = macro_closes(n, b, u)
        predicted = pair_closes(v, b)
        if actual != predicted:
            raise AssertionError(("pair criterion mismatch", n, v, b, u, actual, predicted))
        seen[(v, b)].add(actual)
        counts[(v, b, actual)] += 1
        checked += 1
    mixed = [k for k, vals in seen.items() if len(vals) != 1]
    if mixed:
        raise AssertionError(("mixed pair outcome", mixed[:20]))
    return checked, len(seen), counts


def verify_signature_prefix_quotient(K: int):
    lo = 1 << K
    hi = 1 << (K + 1)
    seen = defaultdict(set)
    prefix_count = 0
    max_macros = 0
    max_seed = 0
    for n in range(lo + 1, hi, 2):
        tr = trace(n)
        if tr[0][0] == "t0":
            continue
        prefix = []
        macro_count = 0
        for pair, closes, _u in tr:
            prefix.append(pair)
            seen[tuple(prefix)].add(closes)
            prefix_count += 1
            macro_count += 1
            if closes:
                break
        if macro_count > max_macros:
            max_macros = macro_count
            max_seed = n
    mixed = [p for p, vals in seen.items() if len(vals) != 1]
    if mixed:
        raise AssertionError(("mixed signature outcome", mixed[:5]))
    return {
        "K": K,
        "odd": 1 << (K - 1),
        "distinct_prefixes": len(seen),
        "prefix_observations": prefix_count,
        "max_macros": max_macros,
        "max_macro_seed": max_seed,
    }


def fixed_h_counterfamily(max_h: int):
    for H in range(2, max_h + 1):
        n = (1 << H) - 1
        y = n
        for j in range(1, H + 1):
            y = T(y)
            formula = pow(3, j) * (1 << (H - j)) - 1
            assert y == formula
            assert y >= n
            if y % 3 == 2:
                p = (2 * y - 1) // 3
                assert p >= n
    return max_h - 1


def grammar_diagnostic(vmax: int):
    alpha = math.log2(1.5)
    rows = []
    for v in range(1, vmax + 1):
        bad = [
            b for b in range(1, max(8, int(alpha * v) + 8))
            if not pair_closes(v, b)
        ]
        max_bad = max(bad) if bad else 0
        rows.append((v, max_bad, max_bad / v))
        if v >= 2:
            assert not pair_closes(v, 1)
    tail = rows[-16:]
    return {
        "vmax": vmax,
        "unbounded_nonclosing_family": "(v,1) for every v>=2",
        "tail": [
            {"v": v, "max_nonclosing_b": b, "ratio": r}
            for v, b, r in tail
        ],
        "alpha_log2_3_over_2": alpha,
    }


def main():
    block_limit = 1 << 16
    pair_limit = 1 << 22
    signature_K = 18

    blocks = verify_block_equivalence(block_limit)
    print("ODD_BLOCK_CONE_COLLAPSE", json.dumps({
        "limit": block_limit,
        "checked_macro_blocks": blocks,
        "rule": "b odd => direct only; b even => direct or 2u<3n+1",
    }, separators=(",", ":")))
    print("VERIFIED_ODD_BLOCK_CONE_COLLAPSE")

    checked, pair_count, counts = verify_first_pair_quotient(pair_limit)
    nonclosing_pairs = sorted(
        (v, b, c) for (v, b, close), c in counts.items() if not close
    )
    print("FIRST_MACRO_PAIR_QUOTIENT", json.dumps({
        "odd_inputs_checked": checked,
        "distinct_pairs": pair_count,
        "nonclosing_pair_cells": len(nonclosing_pairs),
        "largest_nonclosing_cells": nonclosing_pairs[-12:],
    }, separators=(",", ":")))
    print("VERIFIED_FIRST_MACRO_PAIR_QUOTIENT")

    sig = verify_signature_prefix_quotient(signature_K)
    print("SIGNATURE_PREFIX_QUOTIENT", json.dumps(sig, separators=(",", ":")))
    print("VERIFIED_SIGNATURE_PREFIX_OUTCOME_CONSISTENCY")

    hcount = fixed_h_counterfamily(256)
    print("FIXED_H_COUNTERFAMILY", json.dumps({
        "H_values_verified": hcount,
        "family": "n=2^H-1",
        "consequence": "no universal fixed T-step horizon can prove the cone law",
    }, separators=(",", ":")))
    print("VERIFIED_FIXED_H_IMPOSSIBILITY_FAMILY")

    gram = grammar_diagnostic(4096)
    print("VALUATION_GRAMMAR_DIAGNOSTIC", json.dumps(gram, separators=(",", ":")))
    print("PARAMETRIC_VALUATION_REQUIRED")
    print("FINAL_GATE=VALUATION_SIGNATURE_QUOTIENT_VERIFIED")


if __name__ == "__main__":
    main()
