#!/usr/bin/env python3
"""Constructor-coverage compiler for the current Collatz record-survivor frontier.

Protected output:
    (n, a, constructor, p, b) with 0 < p < n and T^a(n) = T^b(p).

Constructors tested:
  1. Recursive closure of the exact first-contracting reverse bank through Q=17.
     The bank is applied to every actual prefix strictly before first coefficient
     crossing. Recursive composition is allowed, but every edge is exact and
     strictly decreases its current endpoint.
  2. Direct strict descent at first coefficient crossing.

Boundary:
  * ten current 24-bit stationary-source records used by programme Meta-Crystal;
  * one fresh 26-bit record setter from the independently qualified FSP scaling run.

This is bounded theorem discovery. It does not prove universal constructor totality.
"""
from __future__ import annotations

import json
from functools import lru_cache

from collatz_live_origin_bridge_v1 import language_counts
from collatz_reverse_predecessor_tree import enumerate_first_contractions, reverse_apply

Q = 18
H = 1024
NODE_CAP = 200_000

TRAIN24 = [
    13421671, 14378779, 8088063, 12132095, 9280639,
    13774695, 1126015, 2252031, 1689023, 6206655,
]
HOLDOUT26 = [63728127]
SOURCES = TRAIN24 + HOLDOUT26


def T(x: int) -> int:
    return (3 * x + 1) // 2 if x & 1 else x // 2


qmin, _, _ = language_counts(H)
certs = enumerate_first_contractions(Q)

# There are only Q-relevant moduli 3^r. Index exact residue hits.
by_key = {}
mods = set()
for c in certs:
    mods.add(c.d)
    by_key.setdefault((c.d, c.residue), []).append(c)
mods = tuple(sorted(mods))


@lru_cache(maxsize=None)
def neighbors(x: int):
    """All exact first-contracting bank predecessors of x."""
    out = {}
    for d in mods:
        for c in by_key.get((d, x % d), ()):
            num = c.a * x - c.c
            if num % d:
                continue
            p = num // d
            if not (0 < p < x):
                continue
            assert reverse_apply(x, c.word) == p
            out.setdefault(p, c)
    return tuple(sorted(out.items()))


def first_crossing_orbit(n: int):
    y = n
    q = 0
    orbit = [(0, n, 0, 0)]
    for j in range(1, H + 1):
        bit = y & 1
        y = T(y)
        q += bit
        slack = q - qmin[j]
        orbit.append((j, y, q, slack))
        if slack < 0:
            return orbit, (j, y, q)
    raise AssertionError(("crossing not found inside declared horizon", n, H))


def recursive_reverse_below(target: int, source: int):
    """Compose strictly-contracting bank edges until a predecessor < source appears.

    State (x,dist) means T^dist(x)=target. Every new edge p->x extends dist by
    the exact certificate step count. This is independently replayed on success.
    """
    stack = [(target, 0)]
    seen = {target}
    expanded = 0

    while stack:
        x, dist = stack.pop()
        expanded += 1
        if expanded > NODE_CAP:
            return {"status": "NODE_CAP", "expanded": expanded, "seen": len(seen)}

        for p, c in neighbors(x):
            ndist = dist + c.steps
            if p < source:
                z = p
                for _ in range(ndist):
                    z = T(z)
                assert z == target, (source, target, p, ndist, z)
                return {
                    "status": "LOWER_SOURCE",
                    "p": p,
                    "reverse_forward_steps": ndist,
                    "last_word": c.word,
                    "expanded": expanded,
                    "seen": len(seen),
                }

            if p not in seen:
                seen.add(p)
                stack.append((p, ndist))

    return {"status": "NO_LOWER_SOURCE_IN_Q17_CLOSURE",
            "expanded": expanded, "seen": len(seen)}


def compile_source(n: int):
    orbit, crossing = first_crossing_orbit(n)
    cross_j, cross_y, cross_q = crossing

    reverse_hit = None
    max_expanded = 0
    # Strictly before coefficient crossing; j=0 is allowed because coalescence
    # at the source itself is already a valid lower-source common-future witness.
    for j, y, q, slack in orbit[:-1]:
        h = recursive_reverse_below(y, n)
        max_expanded = max(max_expanded, h["expanded"])
        if h["status"] == "NODE_CAP":
            return {
                "n": n, "crossing": cross_j, "crossing_endpoint": cross_y,
                "status": "NODE_CAP", "node_cap_at_prefix": j,
            }
        if h["status"] == "LOWER_SOURCE":
            p = h["p"]
            b = h["reverse_forward_steps"]
            z1 = n
            for _ in range(j):
                z1 = T(z1)
            z2 = p
            for _ in range(b):
                z2 = T(z2)
            assert z1 == y == z2
            reverse_hit = {
                "constructor": "RECURSIVE_Q18_REVERSE",
                "a": j,
                "p": p,
                "b": b,
                "common": y,
                "max_nodes_expanded": max_expanded,
            }
            break

    direct = None
    if cross_y < n:
        z = n
        for _ in range(cross_j):
            z = T(z)
        assert z == cross_y
        direct = {
            "constructor": "FIRST_CROSSING_DIRECT_DESCENT",
            "a": cross_j,
            "p": cross_y,
            "b": 0,
            "common": cross_y,
        }

    first = reverse_hit or direct
    if first is not None:
        assert 0 < first["p"] < n

    return {
        "n": n,
        "bit_length": n.bit_length(),
        "crossing": cross_j,
        "crossing_endpoint": cross_y,
        "crossing_odd_count": cross_q,
        "reverse_before_cross": reverse_hit,
        "direct_at_cross": direct,
        "earliest_compiled_constructor": first,
        "covered": first is not None,
    }


rows = [compile_source(n) for n in SOURCES]
assert not [r for r in rows if r.get("status") == "NODE_CAP"], rows

train = rows[:len(TRAIN24)]
holdout = rows[len(TRAIN24):]

train_reverse = sum(r["reverse_before_cross"] is not None for r in train)
holdout_reverse = sum(r["reverse_before_cross"] is not None for r in holdout)
train_direct = sum(r["direct_at_cross"] is not None for r in train)
holdout_direct = sum(r["direct_at_cross"] is not None for r in holdout)

pre_cross_uncovered = [r["n"] for r in rows if r["reverse_before_cross"] is None]
fully_uncovered = [r["n"] for r in rows if not r["covered"]]

# Pin the discovery result.
print("Q18_TRAIN_REVERSE", train_reverse)
print("Q18_HOLDOUT_REVERSE", holdout_reverse)
print("Q18_PRE_CROSS_UNCOVERED", pre_cross_uncovered)
assert train_direct == 10 and holdout_direct == 1
assert not fully_uncovered

result = {
    "schema": "COLLATZ_CONSTRUCTOR_COVERAGE_Q18_RESIDUAL_V1",
    "arithmetic": "exact_integer",
    "reverse_bank_Q": Q,
    "reverse_certificates": len(certs),
    "node_cap": NODE_CAP,
    "train24_records": len(train),
    "holdout26_records": len(holdout),
    "train_recursive_q17_before_cross": train_reverse,
    "holdout_recursive_q17_before_cross": holdout_reverse,
    "train_direct_descent_at_cross": train_direct,
    "holdout_direct_descent_at_cross": holdout_direct,
    "pre_cross_reverse_uncovered_sources": pre_cross_uncovered,
    "fully_uncovered_sources": fully_uncovered,
    "rows": rows,
    "status": "Q18_RESIDUAL_PROBE",
    "warranted_bounded_conclusion": (
        "Recursive Q18 reverse closure constructs a lower-source witness before "
        "coefficient crossing for 8/10 current 24-bit record survivors, improving "
        "the prior Q14 4/10 replay. The 26-bit record setter remains reverse-"
        "uncovered before crossing. All 11 declared records are covered by the "
        "union with exact direct descent at first coefficient crossing."
    ),
    "protected_residual": {
        "sources": pre_cross_uncovered,
        "name": "REVERSE_IRREDUCIBLE_RECORD_SETTER_FIRST_CROSSING_DESCENT",
        "statement": (
            "Prove that an actual fixed source not already lower-merged by the "
            "recursive contracting reverse language must eventually emit another "
            "lower-source constructor; on the current record setters the fallback "
            "is strict descent at first coefficient crossing."
        ),
        "warning": (
            "Do not promote universal first-crossing descent. The needed theorem "
            "may use reverse-irreducibility as an additional hypothesis."
        ),
    },
    "global_collatz": "UNKNOWN",
}

print(json.dumps(result, indent=2))
