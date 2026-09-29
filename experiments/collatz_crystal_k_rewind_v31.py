#!/usr/bin/env python3
"""Crystal V31: exact affine compression of every V27 K rewind.

Parents:
  collatz-crystal-cost-aware-chamber-v27@f11de4820166b3d87e6a5bb0d571334fe8d97449
  collatz-crystal-cost20-contraction-v30@f07e244b2ae64277037f0d51ece84b4a91067ae7

V30 makes every 12-odd cost >=20 block a genuine strict local descent once
its start is >=262.  Therefore the remaining non-B escape mechanism in the
cost-aware chamber is K: the same endpoint residue admits a strictly better
reverse predecessor than the raw shifted 12-odd window.

V31 compiles ALL K transitions, not a sample, and asks for the smallest exact
algebra carried by them.  It proves that 4,282 K transitions collapse to a
tiny affine rewind alphabet.

For a raw reverse predecessor x and canonical cheaper predecessor p:

  lower-cost K (d = rawCost-bestCost > 0):
      2^d p = x + E

  same-cost K:
      p = x - delta

The endpoint y determines both predecessors.  The exact finite chamber proves
p < x for every K transition whenever y >= 86.

This is a local owner-rewind certificate.  It does NOT prove p is below the
original Collatz source, nor that infinitely many K rewinds are impossible.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json

O = 12
MOD = 3 ** O

PARENT_V27 = "collatz-crystal-cost-aware-chamber-v27@f11de4820166b3d87e6a5bb0d571334fe8d97449"
PARENT_V30 = "collatz-crystal-cost20-contraction-v30@f07e244b2ae64277037f0d51ece84b4a91067ae7"


def compositions(total: int, parts: int):
    for cuts in combinations(range(1, total), parts - 1):
        p = 0
        w = []
        for c in cuts + (total,):
            w.append(c - p)
            p = c
        yield tuple(w)


def cocycle(w: tuple[int, ...]) -> int:
    c = 0
    for i, a in enumerate(w):
        c = (1 << a) * c + 3 ** i
    return c


# Complete V27 chamber, independently reconstructed.
all_by_res = defaultdict(list)
for S in range(12, 20):
    inv = pow(1 << S, -1, MOD)
    for w in compositions(S, O):
        C = cocycle(w)
        r = (C * inv) % MOD
        all_by_res[r].append((S, C, w))

best = {
    r: min(vals, key=lambda x: (x[0], -x[1], x[2]))
    for r, vals in all_by_res.items()
}

assert len(best) == 27_469
assert Counter(S for S, _C, _w in best.values()) == Counter({
    12: 1, 13: 12, 14: 66, 15: 286,
    16: 991, 17: 2892, 18: 7274, 19: 15947,
})


def word_to_bits(w: tuple[int, ...]) -> tuple[int, ...]:
    out = []
    for a in reversed(w):
        out.append(1)
        out.extend([0] * (a - 1))
    return tuple(out)


def bits_to_word(bits: tuple[int, ...]) -> tuple[int, ...]:
    assert bits and bits[0] == 1 and sum(bits) == O
    ones = [i for i, b in enumerate(bits) if b]
    seg = []
    for j, i in enumerate(ones):
        nxt = ones[j + 1] if j + 1 < len(ones) else len(bits)
        seg.append(nxt - i)
    return tuple(reversed(seg))


def next_window(w: tuple[int, ...], bit: int) -> tuple[int, ...]:
    bits = list(word_to_bits(w))
    bits.append(bit)
    if bit == 1:
        ones = [i for i, b in enumerate(bits) if b]
        assert len(ones) == O + 1
        bits = bits[ones[1]:]
    assert sum(bits) == O
    return bits_to_word(tuple(bits))


def classify_word(w: tuple[int, ...]):
    S = sum(w)
    if S > 19:
        return "B", None
    C = cocycle(w)
    r = (C * pow(1 << S, -1, MOD)) % MOD
    bS, bC, bw = best[r]
    if (S, C) == (bS, bC):
        assert w == bw
        return "I", r
    assert bS < S or (bS == S and bC > C)
    return "K", r


k_rows = []
lower_rows = []
same_rows = []

for source_residue, (_S, _C, w) in sorted(best.items()):
    for bit in (0, 1):
        nw = next_window(w, bit)
        cls, target_residue = classify_word(nw)
        if cls != "K":
            continue

        rawS = sum(nw)
        rawC = cocycle(nw)
        bestS, bestC, bestW = best[target_residue]
        assert bestS <= rawS

        # For any endpoint y in target_residue mod 3^12:
        #   x=(2^rawS*y-rawC)/3^12
        #   p=(2^bestS*y-bestC)/3^12.
        # The target residue makes both integers.
        A = (1 << rawS) - (1 << bestS)
        B = rawC - bestC
        endpoint_threshold = 1 if B < 0 else B // A + 1
        # y>=threshold implies A*y>B, exactly p<x.
        assert A * endpoint_threshold > B
        if endpoint_threshold > 1:
            assert A * (endpoint_threshold - 1) <= B

        base = {
            "source_residue": source_residue,
            "bit": bit,
            "target_residue": target_residue,
            "raw_cost": rawS,
            "best_cost": bestS,
            "endpoint_threshold_for_strict_rewind": endpoint_threshold,
        }

        if bestS < rawS:
            d = rawS - bestS
            diff = rawC - (1 << d) * bestC
            assert diff % MOD == 0
            E = diff // MOD

            # Exact identity:
            # 2^d p = (2^rawS*y - 2^d*bestC)/MOD
            #         = x + (rawC-2^d*bestC)/MOD
            #         = x + E.
            row = {
                **base,
                "kind": "LOWER_COST",
                "cost_drop": d,
                "E": E,
                "law": f"2^{d}*p=x+({E})",
            }
            lower_rows.append(row)
        else:
            assert bestS == rawS and bestC > rawC
            diff = bestC - rawC
            assert diff % MOD == 0
            delta = diff // MOD
            assert delta > 0
            # p=(2^S*y-bestC)/MOD=x-delta.
            row = {
                **base,
                "kind": "SAME_COST_HIGHER_COCYCLE",
                "delta": delta,
                "law": f"p=x-{delta}",
            }
            same_rows.append(row)

        k_rows.append(row)

assert len(k_rows) == 4_282
assert len(lower_rows) == 3_832
assert len(same_rows) == 450

cost_drop_hist = Counter(r["cost_drop"] for r in lower_rows)
assert cost_drop_hist == Counter({1: 3702, 2: 107, 3: 13, 4: 9, 5: 1})

same_delta_hist = Counter(r["delta"] for r in same_rows)
assert same_delta_hist == Counter({2: 369, 4: 66, 6: 6, 8: 9})

e_alphabet = {
    d: sorted({r["E"] for r in lower_rows if r["cost_drop"] == d})
    for d in range(1, 6)
}
assert e_alphabet == {
    1: [-13, -11, -9, -7, -5, -3, -1, 1, 3, 5, 7],
    2: [-15, -13, -11, -7, -5, -3, -1, 1, 3, 11],
    3: [-23, -19, -17, -15, -9, -3, -1],
    4: [-31, -27, -25, -23, -17, -11, -9, -1],
    5: [-33],
}
assert min(r["E"] for r in lower_rows) == -33
assert max(r["E"] for r in lower_rows) == 11

bit_hist = Counter(r["bit"] for r in k_rows)
assert bit_hist == Counter({1: 4182, 0: 100})

max_threshold = max(r["endpoint_threshold_for_strict_rewind"] for r in k_rows)
assert max_threshold == 86
worst_rows = [
    r for r in k_rows
    if r["endpoint_threshold_for_strict_rewind"] == max_threshold
]
assert worst_rows

# Strong finite consequence: every K rewrite lowers its own raw predecessor
# whenever the endpoint is at least 86.  This does not compare p with the
# original Collatz source.
for r in k_rows:
    assert r["endpoint_threshold_for_strict_rewind"] <= 86

payload = {
    "schema": "COLLATZ_CRYSTAL_K_REWIND_V31",
    "parents": {
        "cost_aware_chamber": PARENT_V27,
        "cost20_contraction": PARENT_V30,
    },
    "chamber": {
        "odd_steps": O,
        "modulus": MOD,
        "contexts": len(best),
        "K_transitions": len(k_rows),
        "bit_histogram": dict(sorted(bit_hist.items())),
    },
    "lower_cost_rewinds": {
        "count": len(lower_rows),
        "cost_drop_histogram": dict(sorted(cost_drop_hist.items())),
        "E_by_cost_drop": {str(k): v for k, v in sorted(e_alphabet.items())},
        "E_min": min(r["E"] for r in lower_rows),
        "E_max": max(r["E"] for r in lower_rows),
        "generic_law": "2^d*p=x+E, d in {1,2,3,4,5}",
    },
    "same_cost_rewinds": {
        "count": len(same_rows),
        "delta_histogram": dict(sorted(same_delta_hist.items())),
        "generic_law": "p=x-delta, delta in {2,4,6,8}",
    },
    "strict_rewind_certificate": {
        "endpoint_floor": 86,
        "statement": (
            "For every one of the 4,282 K transitions, every admissible "
            "endpoint y>=86 has canonical K predecessor p strictly smaller "
            "than the raw shifted-window predecessor x."
        ),
        "worst_rows": worst_rows[:8],
    },
    "scientific_verdict": (
        "ALL_K_REWINDS_COMPRESS_TO_FINITE_AFFINE_OWNER_ALPHABET; "
        "INFINITE_K_SOURCE_REALIZABILITY_REMAINS_UNKNOWN"
    ),
    "next_residual": {
        "name": "INFINITE_K_REWIND_EXCLUSION",
        "statement": (
            "Compose the finite K affine owner alphabet with the exact "
            "source-relative/canonical-M register. Prove that one fixed "
            "positive natural no-OrdinaryExit source cannot realize infinitely "
            "many K rewinds; local p<x is not by itself source-order descent."
        ),
        "forbidden_shortcuts": [
            "deeper raw parameter census",
            "larger 3-adic chamber",
            "treat local predecessor descent as original-source descent",
        ],
    },
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
payload["certificate_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()

print(json.dumps(payload, indent=2, sort_keys=True))
