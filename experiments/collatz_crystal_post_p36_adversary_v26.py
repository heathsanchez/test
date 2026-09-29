#!/usr/bin/env python3
"""Crystal V26: post-P36 natural-parameter adversary for the sole V23 cell.

Parent:
  collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc

Purpose:
1. Construct exactly a natural parameter t whose post-V24 shortcut parity
   corridor is the 389-bit prefix of (110)^omega.
2. Verify with integer arithmetic that this concrete source has no direct
   descent, no quarter-splice state, and no coefficient crossing through
   ordinary depth 448 (> the archived finite P36 boundary J=447).
3. Re-run the exact V25 lower-source reverse language on every parameter-prefix
   cell through depth 29 and require no D/S/M exit there.

This is a falsifier for any claim that V25's bounded zero-tail controls or the
finite P36 boundary by themselves close the V23 cell. It is NOT a Collatz
counterexample: lower-source status beyond parameter depth 29 remains UNKNOWN.
"""

from __future__ import annotations
from collections import defaultdict
import json

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
A59 = 91_182_490_942_926_966_077
C59 = 3**46

P36_BOUND = 447
PARITY_LEN = P36_BOUND - 59 + 1  # transitions at depths 59..447
REVERSE_PREFIX_DEPTH = 29


def shortcut(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2


def parity_residue(bits: list[int]) -> tuple[int, int]:
    """Unique x mod 2^L with the declared shortcut parity prefix."""
    r = 0
    mod = 1
    for i, bit in enumerate(bits):
        found = None
        for cand in (r, r + mod):
            x = cand
            for _ in range(i):
                x = shortcut(x)
            if (x & 1) == bit:
                found = cand
                break
        assert found is not None
        r = found
        mod <<= 1
    return r, mod


def fixed_prefix(N: int, S: int):
    out = []
    A, C = N, S
    q = 0
    j = 0
    while True:
        out.append((j, A, C, q))
        if C & 1:
            break
        if A & 1:
            A = (3*A + 1)//2
            C = 3*C//2
            q += 1
        else:
            A //= 2
            C //= 2
        j += 1
    return out


def direct_or_splice(prefix, N: int, S: int):
    for j, A, C, _q in prefix:
        if ((A < N and C <= S) or (A <= N and C < S)):
            return {"kind": "D", "depth": j}
        if C % 8 == 0 and A % 8 == 5 and A <= 4*N and C <= 4*S:
            return {"kind": "S", "depth": j}
    return None


def is_pow3(x: int):
    if x <= 0:
        return None
    k = 0
    while x % 3 == 0:
        x //= 3
        k += 1
    return k if x == 1 else None


def reverse_lower_witness(A: int, C: int, N: int, S: int):
    """Exact V25 uniform reverse E/O search at one odd-slope interface."""
    m = is_pow3(C)
    assert m is not None

    globalE = -1
    for o in range(m + 1):
        e = -1
        for z in range(1024):
            if C * (1 << (z + o)) <= S * (3**o):
                e = z
            else:
                break
        globalE = max(globalE, e)
    if globalE < 0:
        return None, 0

    # dp[E] is the exact set of reachable constants after the current O count.
    dp = {0: {A}}
    states = 1
    for o in range(m):
        nxt = defaultdict(set)
        o2 = o + 1
        for E, constants in dp.items():
            for a in constants:
                if a % 3 == 0:
                    continue
                parity = 0 if a % 3 == 2 else 1
                for e in range(parity, globalE - E + 1, 2):
                    E2 = E + e
                    ae = a << e
                    coeff_before = C * (1 << (E2 + o)) // (3**o)
                    if ae % 3 != 2 or coeff_before % 3:
                        continue
                    na = (2*ae - 1)//3
                    nc = (2*coeff_before)//3
                    states += 1

                    if na > 0 and ((na < N and nc <= S) or (na <= N and nc < S)):
                        return {
                            "p0": na,
                            "pSlope": nc,
                            "oddInverse": o2,
                            "evenLifts": E2,
                        }, states

                    rem = m - o2
                    if nc * (2**rem) > S * (3**rem):
                        continue
                    nxt[E2].add(na)
        dp = dict(nxt)
        if not dp:
            break
    return None, states


def classify_prefix_cell(d: int, r: int):
    N = N0 + NC*r
    S = NC*(1 << d)
    pref = fixed_prefix(N, S)
    assert pref[-1][0] == 59 + d
    ex = direct_or_splice(pref, N, S)
    if ex is not None:
        return ex, 0
    A, C = pref[-1][1], pref[-1][2]
    w, states = reverse_lower_witness(A, C, N, S)
    if w is not None:
        return {"kind": "M", "reverse": w}, states
    return None, states


def main():
    bits = ([1, 1, 0] * ((PARITY_LEN + 2)//3))[:PARITY_LEN]
    assert len(bits) == 389
    assert all(bits[i:i+3] != [1, 0, 0] for i in range(len(bits)-2))

    y_res, modulus = parity_residue(bits)
    t = ((y_res - A59) * pow(C59, -1, modulus)) % modulus
    assert 0 <= t < modulus
    assert t.bit_length() == 389

    n = N0 + NC*t
    y = A59 + C59*t
    k = 59
    q = 38

    first_direct = None
    first_splice = None
    first_cross = None
    min_gap = None

    for expected in bits:
        assert (y & 1) == expected
        gap = y - n
        min_gap = gap if min_gap is None else min(min_gap, gap)
        if y < n and first_direct is None:
            first_direct = k
        if y % 8 == 5 and y <= 4*n and first_splice is None:
            first_splice = k
        if 3**q < 2**k and first_cross is None:
            first_cross = k
        y = shortcut(y)
        if expected:
            q += 1
        k += 1

    # Include the terminal state at depth 448.
    gap = y - n
    min_gap = min(min_gap, gap)
    if y < n and first_direct is None:
        first_direct = k
    if y % 8 == 5 and y <= 4*n and first_splice is None:
        first_splice = k
    if 3**q < 2**k and first_cross is None:
        first_cross = k

    assert k == 448
    assert first_direct is None
    assert first_splice is None
    assert first_cross is None
    assert y >= n
    assert 3**q >= 2**k

    reverse_rows = []
    for d in range(REVERSE_PREFIX_DEPTH + 1):
        r = t % (1 << d) if d else 0
        ex, states = classify_prefix_cell(d, r)
        reverse_rows.append({
            "parameter_depth": d,
            "r": r,
            "reverse_states": states,
            "exit": ex,
        })
        assert ex is None

    result = {
        "schema": "COLLATZ_CRYSTAL_POST_P36_ADVERSARY_V26",
        "parent": "collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc",
        "natural_parameter": {
            "t": t,
            "bit_length": t.bit_length(),
            "source": n,
        },
        "parity_corridor": {
            "word": "110",
            "prefix_length": PARITY_LEN,
            "ordinary_start_depth": 59,
            "verified_through_state_depth": k,
            "odd_count_at_final_state": q,
            "no_100_subword": True,
        },
        "protected_checks": {
            "first_direct_descent": first_direct,
            "first_quarter_splice": first_splice,
            "first_coefficient_crossing": first_cross,
            "minimum_endpoint_minus_source": min_gap,
            "coefficient_nonnegative_at_448": 3**q >= 2**k,
        },
        "v25_reverse_prefix_recheck": {
            "through_parameter_depth": REVERSE_PREFIX_DEPTH,
            "all_no_exit": all(row["exit"] is None for row in reverse_rows),
            "total_reverse_states": sum(row["reverse_states"] for row in reverse_rows),
            "max_reverse_states_one_cell": max(row["reverse_states"] for row in reverse_rows),
            "rows": reverse_rows,
        },
        "scientific_verdict": (
            "BOUNDED_POST_P36_NATURAL_ADVERSARY: direct descent / quarter splice / "
            "coefficient crossing do not close this natural parameter through ordinary "
            "depth 448, and the exact V25 lower-source language also has no exit on its "
            "parameter-prefix cells through depth 29."
        ),
        "next_residual": (
            "Extend the joint 2-adic parity + 3-adic reverse-admissibility state, not raw "
            "parameter depth. Either derive a lower-source merge on this corridor after "
            "depth 29 or prove an origin/carry rank excluding arbitrarily long surviving "
            "natural prefixes."
        ),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
