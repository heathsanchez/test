#!/usr/bin/env python3
"""Crystal adversarial test of the proposed bounded live-origin P-progress law.

Exact integer arithmetic only.  One scan of all odd sources below 2^26 builds
the nested origin windows P_j(2^m), then measures:
  (1) first envelope-contraction block length;
  (2) first strict loss of the natural resource P.

This is a rejection test for a *fixed small block horizon on P*, not a
rejection of abstract Fixed-Source Progress with another/state-dependent rank.
"""
from collections import defaultdict
import json

BITS = 26
DEPTH = 1024
BMAX = 256
CAPS = (20, 22, 24, 26)

def language_counts(depth: int):
    qmin = [0] * (depth + 1)
    q = 0
    p3 = 1
    for j in range(1, depth + 1):
        while p3 < (1 << j):
            p3 *= 3
            q += 1
        qmin[j] = q

    counts = {0: 1}
    live = [1]
    for j in range(1, depth + 1):
        nxt = defaultdict(int)
        for q, count in counts.items():
            for bit in (0, 1):
                qp = q + bit
                if qp >= qmin[j]:
                    nxt[qp] += count
        counts = dict(nxt)
        live.append(sum(counts.values()))
    return qmin, live

def first_crossing(n: int, qmin):
    y = n
    q = 0
    for j in range(1, len(qmin)):
        if y & 1:
            y = (3 * y + 1) // 2
            q += 1
        else:
            y //= 2
        if q < qmin[j]:
            return j
    return None

qmin, F = language_counts(DEPTH)
hist = [[0] * (BITS + 1) for _ in range(DEPTH + 1)]
max_cross_by_m = [None] * (BITS + 1)
unresolved = []

for n in range(1, 1 << BITS, 2):
    z = first_crossing(n, qmin)
    if z is None:
        unresolved.append(n)
        continue
    j = z
    m = n.bit_length()
    hist[j][m] += 1
    old = max_cross_by_m[m]
    if old is None or j > old[0]:
        max_cross_by_m[m] = (j, n)

assert not unresolved, unresolved[:10]

C = [[0] * (BITS + 1) for _ in range(DEPTH + 1)]
P = [[0] * (BITS + 1) for _ in range(DEPTH + 1)]
for j in range(1, DEPTH + 1):
    for m in range(1, BITS + 1):
        C[j][m] = C[j][m - 1] + hist[j][m]

for m in range(1, BITS + 1):
    P[0][m] = 1 << (m - 1)
    for j in range(1, DEPTH + 1):
        P[j][m] = P[j - 1][m] - C[j][m]
        assert P[j][m] >= 0

def envelope_good(j: int, b: int, m: int) -> bool:
    if P[j][m] == 0:
        return True
    a = P[j + b][m] * F[j]
    d = P[j][m] * F[j + b]
    e = (6 * (j + b)) // 125 - (6 * j) // 125 - b
    if e >= 0:
        return a <= (d << e)
    return (a << (-e)) <= d

states = []
for j in range(60, DEPTH - BMAX + 1):
    for m in range(1, BITS + 1):
        p = P[j][m]
        if not p:
            continue

        env_b = None
        loss_b = None
        for b in range(1, BMAX + 1):
            if loss_b is None and P[j + b][m] < p:
                loss_b = b
            if env_b is None and envelope_good(j, b, m):
                env_b = b
            if env_b is not None and loss_b is not None:
                break

        states.append({
            "j": j,
            "m": m,
            "P": p,
            "env_b": env_b,
            "loss_b": loss_b,
            "P_after_env": None if env_b is None else P[j + env_b][m],
            "P_after_loss": None if loss_b is None else P[j + loss_b][m],
        })

def prefix_cross(cap):
    candidates = []
    for m in range(1, cap + 1):
        if max_cross_by_m[m] is not None:
            candidates.append((max_cross_by_m[m][0], max_cross_by_m[m][1], m))
    return max(candidates)

def cap_summary(cap):
    xs = [s for s in states if s["m"] <= cap]
    env = max((s for s in xs if s["env_b"] is not None),
              key=lambda s: s["env_b"])
    loss = max((s for s in xs if s["loss_b"] is not None),
               key=lambda s: s["loss_b"])
    env_missing = [s for s in xs if s["env_b"] is None]
    loss_missing = [s for s in xs if s["loss_b"] is None]
    cj, cn, cm = prefix_cross(cap)
    return {
        "source_bits_cap": cap,
        "max_observed_first_crossing": cj,
        "first_source_attaining_max_crossing": cn,
        "source_bit_length_of_record": cm,
        "max_minimum_envelope_block": env["env_b"],
        "envelope_witness": env,
        "max_first_strict_P_loss_gap": loss["loss_b"],
        "strict_P_loss_witness": loss,
        "states_without_envelope_block_le_256": len(env_missing),
        "states_without_strict_P_loss_le_256": len(loss_missing),
    }

rows = [cap_summary(c) for c in CAPS]

# Reproduce the exact adversarial values found during Crystal discovery.
expected = {
    20: (183, 21, 22),
    22: (224, 26, 25),
    24: (287, 37, 38),
    26: (376, 63, 68),
}
for row in rows:
    got = (
        row["max_observed_first_crossing"],
        row["max_minimum_envelope_block"],
        row["max_first_strict_P_loss_gap"],
    )
    assert got == expected[row["source_bits_cap"]], (row["source_bits_cap"], got)

w21 = next(s for s in states if s["m"] <= 22 and s["env_b"] is not None and s["env_b"] > 21)
w32 = next(s for s in states if s["m"] <= 24 and s["env_b"] is not None and s["env_b"] > 32)

result = {
    "schema": "COLLATZ_FSP_BLOCK_SCALING_V0",
    "status": "FIXED_SMALL_P_BLOCK_HORIZON_REJECTED",
    "arithmetic": "exact_integer",
    "source_bits": BITS,
    "depth": DEPTH,
    "block_search_budget": BMAX,
    "caps": rows,
    "B21_counterexample": w21,
    "B32_counterexample": w32,
    "warranted_bounded_conclusion":
        "The proposed universal P/envelope progress horizons B=21 and B=32 are false; "
        "the exact required horizon grows across these nested source windows.",
    "not_rejected":
        "Abstract Fixed-Source Progress with a different well-founded rank, or "
        "state-dependent/eventual block length.",
    "corrected_closeout_target":
        "For every actual live fixed-source state, there exists some later live state "
        "with a strict decrease in a recursively applicable well-founded rank, or Exit. "
        "A source-independent finite B is not required for the minimal-counterexample argument.",
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
