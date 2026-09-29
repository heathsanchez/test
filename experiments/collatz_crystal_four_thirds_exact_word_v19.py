#!/usr/bin/env python3
"""Crystal V19: exact bias-word admission at the four-thirds deficit-one boundary.

This is a consequence-pruned symbolic type scan, not a source census and not
a post-boundary trajectory search.

Inputs already WARRANTED by V17/V18:
  * minimal-bad source classes n mod 24 in {3,7,15,19};
  * q = floor(4n/3), hence q mod 32 in {4,9,20,25};
  * deficit-one boundary q+1 = qmin(k);
  * odd normalized endpoint p satisfies n <= p < 2n and p mod 8 != 5;
  * universal exact bias min/max envelopes.

For any such (n,k,q,p), the required affine bias is
    B = 2^k p - 3^q n.
An exact q-odd parity word has the unique representation
    B = sum_j 3^(q-1-j) 2^(i_j),   0 <= i_0 < ... < i_(q-1) < k.
The 2-adic valuation of the current residual uniquely determines each i_j,
so the grammar is deterministically decodable.  V19 tests the exact grammar
only on the near-resonant V18 deficit types.

Finite type evidence only; universal Collatz remains UNKNOWN.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json

H = 4096
SOURCE_Q_MOD32 = {4, 9, 20, 25}
SOURCE_MOD24 = {3, 7, 15, 19}

def qmin_rows(H: int):
    p2 = p3 = 1
    qm = 0
    lag_q = 0
    lag_B = 0
    rows = []
    for k in range(1, H + 1):
        p2 <<= 1
        if p3 < p2:
            p3 *= 3
            qm += 1
        target_lag = max(0, qm - 1)
        if target_lag == lag_q + 1:
            lag_B = 3 * lag_B + (1 << (k - 1))
            lag_q += 1
        assert target_lag == lag_q
        q = qm - 1
        if q <= 0 or q % 32 not in SOURCE_Q_MOD32:
            continue
        if q % 4 == 0:
            n = 3 * q // 4
        elif q % 4 == 1:
            n = (3 * q + 1) // 4
        else:
            continue
        if n % 24 not in SOURCE_MOD24:
            continue
        D = (1 << k) - 3 ** q
        assert D > 0
        rows.append({
            "k": k, "q": q, "n": n, "D": D, "lag_B": lag_B,
            "near": lag_B >= D * n,
            "payment_gap": lag_B - D * n,
        })
    return rows

def bias_min(q: int) -> int:
    return 3 ** q - 2 ** q

def bias_max(k: int, q: int) -> int:
    return (1 << (k - q)) * bias_min(q)

def decode_bias_word(k: int, q: int, B: int):
    """Unique exact bias-word decoder.

    If B is the bias of a q-odd length-k word, its least 2-adic bit is the
    first odd position because every later term carries a strictly larger
    power of two.  Peel that forced term and repeat.
    """
    if q == 0:
        return {"status": "OK", "positions": []} if B == 0 else {
            "status": "RESIDUAL", "step": 0, "residual": B, "positions": []}
    positions = []
    prev = -1
    p3 = 3 ** (q - 1)
    for step in range(q):
        if B <= 0:
            return {"status": "B_NONPOS", "step": step, "residual": B,
                    "positions": positions}
        lowbit = B & -B
        i = lowbit.bit_length() - 1
        if i <= prev:
            return {"status": "NONINCREASING", "step": step, "position": i,
                    "residual": B, "positions": positions}
        if i >= k:
            return {"status": "POSITION_GE_K", "step": step, "position": i,
                    "residual": B, "positions": positions}
        term = p3 << i
        if term > B:
            return {"status": "TERM_GT_B", "step": step, "position": i,
                    "residual": B, "required_term": term,
                    "positions": positions}
        B -= term
        positions.append(i)
        prev = i
        if step + 1 < q:
            assert p3 % 3 == 0
            p3 //= 3
    if B != 0:
        return {"status": "RESIDUAL", "step": q, "residual": B,
                "positions": positions}
    return {"status": "OK", "positions": positions}

def encode_word(positions):
    B = 0
    for i in positions:
        B = 3 * B + (1 << i)
    return B

# Independent decoder sanity over every word through k=12.
decoder_sanity = 0
for k in range(0, 13):
    for mask in range(1 << k):
        positions = [i for i in range(k) if (mask >> i) & 1]
        B = encode_word(positions)
        d = decode_bias_word(k, len(positions), B)
        assert d["status"] == "OK"
        assert d["positions"] == positions
        decoder_sanity += 1

rows = qmin_rows(H)
near = [r for r in rows if r["near"]]
closed = [r for r in rows if not r["near"]]

counts = Counter()
by_source_class = defaultdict(Counter)
by_q = {}
first_failures = []
exceptional_types = set()
max_term_failure_step = -1
max_term_failure = None

for r in near:
    k, q, n = r["k"], r["q"], r["n"]
    P, A = 1 << k, 3 ** q
    loB, hiB = bias_min(q), bias_max(k, q)
    local = Counter()
    for p in range(n, 2 * n):
        if p % 2 == 0 or p % 8 == 5:
            continue
        B = P * p - A * n
        counts["candidate_odd_normalized_endpoints"] += 1
        if not (loB <= B <= hiB):
            counts["bias_envelope_rejections"] += 1
            continue
        counts["pass_universal_bias_envelope"] += 1
        d = decode_bias_word(k, q, B)
        local[d["status"]] += 1
        counts["fail_" + d["status"]] += 1
        by_source_class[n % 24][d["status"]] += 1
        if d["status"] == "OK":
            counts["exact_bias_words"] += 1
            # Regression guard: any admitted word must reconstruct exactly.
            assert encode_word(d["positions"]) == B
        else:
            if len(first_failures) < 40:
                first_failures.append({
                    "k": k, "q": q, "n": n, "p": p,
                    "source_mod24": n % 24,
                    "status": d["status"], "step": d.get("step"),
                    "position": d.get("position"),
                    "residual_bits": d.get("residual", 0).bit_length()
                        if isinstance(d.get("residual"), int) and d.get("residual", 0) >= 0 else None,
                })
            if d["status"] != "TERM_GT_B":
                exceptional_types.add((k, q, n))
            else:
                s = d["step"]
                if s > max_term_failure_step:
                    max_term_failure_step = s
                    max_term_failure = {
                        "k": k, "q": q, "n": n, "p": p,
                        "step": s, "position": d.get("position"),
                    }
    by_q[str(q)] = {
        "k": k, "n": n, "source_mod24": n % 24,
        "candidate_endpoints": sum(local.values()),
        "failure_kinds": dict(sorted(local.items())),
    }

assert len(rows) == 511
assert len(closed) == 196
assert len(near) == 315
assert counts["candidate_odd_normalized_endpoints"] == 114495
assert counts["bias_envelope_rejections"] == 2
assert counts["pass_universal_bias_envelope"] == 114493
assert counts["exact_bias_words"] == 0
assert counts["fail_TERM_GT_B"] == 114471
assert counts["fail_POSITION_GE_K"] == 10
assert counts["fail_RESIDUAL"] == 10
assert counts["fail_B_NONPOS"] == 2
assert {q for _, q, _ in exceptional_types} == {4, 9, 36, 41}
assert max_term_failure_step == 68

generic_q52_plus = all(
    all(kind == "TERM_GT_B" for kind, num in row["failure_kinds"].items() if num)
    for q, row in by_q.items() if int(q) >= 52
)

result = {
    "schema": "COLLATZ_CRYSTAL_FOUR_THIRDS_EXACT_WORD_V19",
    "declared_boundary": {
        "qmin_depth": H,
        "source_census": False,
        "post_boundary_trajectory_search": False,
        "input_types": len(rows),
        "near_resonant_types": len(near),
    },
    "decoder": {
        "law": "successive v2 of the bias residual uniquely forces the odd positions",
        "exhaustive_sanity_words_k_le_12": decoder_sanity,
    },
    "raw_candidate_endpoints": counts["candidate_odd_normalized_endpoints"],
    "bias_envelope_rejections": counts["bias_envelope_rejections"],
    "candidate_endpoints": counts["pass_universal_bias_envelope"],
    "exact_bias_words": counts["exact_bias_words"],
    "failure_counts": {
        k.removeprefix("fail_"): v
        for k, v in sorted(counts.items()) if k.startswith("fail_")
    },
    "source_class_failure_counts": {
        str(c): dict(sorted(v.items())) for c, v in sorted(by_source_class.items())
    },
    "exceptional_non_TERM_GT_B_types": [
        {"k": k, "q": q, "n": n} for k, q, n in sorted(exceptional_types)
    ],
    "generic_q52_plus_all_TERM_GT_B_on_declared_boundary": generic_q52_plus,
    "max_TERM_GT_B_peel_step": max_term_failure_step,
    "max_TERM_GT_B_witness": max_term_failure,
    "first_failures": first_failures,
    "candidate": {
        "name": "FourThirdsDeficitExactBiasWordExclusion",
        "statement": (
            "for every four-thirds deficit-one type with a normalized odd endpoint "
            "p in [n,2n), the required affine bias is not in the exact q-odd bias grammar"
        ),
        "status": "BOUNDED_CANDIDATE_ONLY",
    },
    "next_residual": {
        "name": "UNIVERSAL_EXACT_BIAS_WORD_EXCLUSION",
        "statement": (
            "prove the bounded zero symbolically. The dominant separator is TERM_GT_B: "
            "after peeling a source-forced initial odd prefix, the remaining required "
            "bias is smaller than the universal minimum bias for the remaining odd count. "
            "Do not replace this with a larger source census."
        ),
        "exceptional_small_q": sorted({q for _, q, _ in exceptional_types}),
        "survival_branch_still_open": True,
        "universal": "UNKNOWN",
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
