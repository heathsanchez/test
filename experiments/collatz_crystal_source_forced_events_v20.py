#!/usr/bin/env python3
"""Crystal V20: source-forced event compression of V19.

This is NOT a source census and does not follow the orbit beyond the four-thirds
boundary.  It consumes exactly the deterministic V18/V19 deficit-one type
interface.

For an exact q-odd affine word of length k with source n and endpoint p,

    2^k p = 3^q n + B.

After j forced odd insertions write

    B_j = 2^k p - 3^(q-j) C_j.

Because 2^k p is divisible by 2^k and 3 is odd, the next odd position is
forced by i_j = v2(C_j) whenever i_j < k.  Peeling that term gives

    C_(j+1) = 3 C_j + 2^i_j.

Thus the exact-word decoder is a source-only recurrence.  If

    3^(q-j-1) C_(j+1) > 2^k p,

the next mandatory term is already larger than the remaining bias
(TERM_GT_B).

At a V17 deficit-one odd boundary the normalized endpoint obeys
n <= p < 2n, p odd, p != 5 mod 8, while a minimal-bad source is 3 or 7 mod 8.
Hence p <= 2n-3.  Testing p_max=2n-3 is consequence-maximal:
TERM_GT_B there excludes every allowed smaller endpoint at once.

The declared qmin depth is deliberately a symbolic-type horizon, not a source
range.  A bounded zero is discovery evidence only.
"""
from collections import Counter
import json

H = 100_000
SOURCE_Q_MOD32 = {4, 9, 20, 25}
SOURCE_MOD24 = {3, 7, 15, 19}

def v2(x: int) -> int:
    assert x > 0
    return (x & -x).bit_length() - 1

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
            "k": k, "q": q, "n": n,
            "near": lag_B >= D * n,
            "lag_payment_gap": lag_B - D * n,
        })
    return rows

def source_forced_peel(n: int, k: int, q: int, p: int):
    threshold = (1 << k) * p
    C = n
    pow3 = 3 ** q
    positions = []
    for j in range(q):
        # Remaining bias B_j = threshold - pow3*C.
        if pow3 * C >= threshold:
            return {
                "status": "B_NONPOS", "step": j,
                "position": None, "C": C,
            }
        i = v2(C)
        if i >= k:
            return {
                "status": "POSITION_GE_K", "step": j,
                "position": i, "C": C,
            }
        Cnext = 3 * C + (1 << i)
        pow3 //= 3
        positions.append(i)
        # Equivalent to mandatory next term > remaining bias.
        if pow3 * Cnext > threshold:
            return {
                "status": "TERM_GT_B", "step": j,
                "position": i, "C": Cnext,
            }
        C = Cnext
    if C == threshold:
        return {
            "status": "OK", "step": q,
            "position": positions[-1] if positions else None, "C": C,
        }
    return {
        "status": "RESIDUAL", "step": q,
        "position": positions[-1] if positions else None, "C": C,
    }

rows = qmin_rows(H)
near = [r for r in rows if r["near"]]
closed = [r for r in rows if not r["near"]]

counts = Counter()
exceptions = []
max_peel = None
first_generic = []

for r in near:
    k, q, n = r["k"], r["q"], r["n"]
    assert n % 8 in (3, 7)
    pmax = 2 * n - 3
    assert n <= pmax < 2 * n
    assert pmax % 2 == 1
    assert pmax % 8 != 5
    out = source_forced_peel(n, k, q, pmax)
    counts[out["status"]] += 1
    row = {
        "k": k, "q": q, "n": n, "p_max": pmax,
        "status": out["status"], "peel_step": out["step"],
        "forced_position": out["position"],
    }
    if out["status"] != "TERM_GT_B":
        exceptions.append(row)
    else:
        if len(first_generic) < 20:
            first_generic.append(row)
        if max_peel is None or out["step"] > max_peel["peel_step"]:
            max_peel = row

# Cross-check the V19 boundary exactly.
v19_rows = [r for r in near if r["k"] <= 4096]
v19_counts = Counter()
for r in v19_rows:
    n, k, q = r["n"], r["k"], r["q"]
    v19_counts[source_forced_peel(n, k, q, 2*n-3)["status"]] += 1

# Discovery result on the enlarged *type* horizon.
assert len([r for r in qmin_rows(4096)]) == 511
assert len(v19_rows) == 315
assert len(rows) == 12501
assert len(near) == 7669
assert counts["TERM_GT_B"] == 7665
assert {(e["q"], e["status"]) for e in exceptions} == {
    (4, "B_NONPOS"),
    (9, "POSITION_GE_K"),
    (36, "RESIDUAL"),
    (41, "POSITION_GE_K"),
}
assert all(
    source_forced_peel(r["n"], r["k"], r["q"], 2*r["n"]-3)["status"] == "TERM_GT_B"
    for r in near if r["q"] >= 52
)
assert max_peel is not None and max_peel["peel_step"] == 122

result = {
    "schema": "COLLATZ_CRYSTAL_SOURCE_FORCED_EVENTS_V20",
    "declared_boundary": {
        "qmin_depth": H,
        "source_census": False,
        "endpoint_enumeration": False,
        "post_boundary_trajectory_search": False,
        "relevant_types": len(rows),
        "near_resonant_types": len(near),
        "v19_near_types_replayed": len(v19_rows),
    },
    "source_forced_recurrence": {
        "initial": "C_0=n",
        "forced_position": "i_j=v2(C_j)",
        "step": "C_(j+1)=3*C_j+2^i_j",
        "residual": "B_j=2^k*p-3^(q-j)*C_j",
        "term_obstruction":
            "3^(q-j-1)*C_(j+1)>2^k*p => TERM_GT_B",
    },
    "endpoint_compression": {
        "hardest_endpoint": "p_max=2*n-3",
        "reason":
            "minimal-bad n is 3 or 7 mod 8; 2n-1 is 5 mod 8 and excluded; "
            "TERM_GT_B at p_max implies it for every allowed p<=p_max",
    },
    "failure_counts": dict(sorted(counts.items())),
    "exceptions": exceptions,
    "all_q_ge_52_TERM_GT_B_on_declared_type_boundary": True,
    "max_peel": max_peel,
    "first_generic_failures": first_generic,
    "v19_pmax_failure_counts": dict(sorted(v19_counts.items())),
    "candidate": {
        "name": "FourThirdsDeficitSourceForcedTerm",
        "statement":
            "for every relevant deficit-one four-thirds type with q>=52, "
            "the source-forced recurrence reaches TERM_GT_B at p_max=2n-3",
        "status": "BOUNDED_CANDIDATE_ONLY",
    },
    "residual": {
        "generic_deficit":
            "prove FourThirdsDeficitSourceForcedTerm symbolically, without a depth horizon",
        "finite_exception_q": [4, 9, 36, 41],
        "survival_branch":
            "still independently open: exact source-admission/source-order progress "
            "when qmin(k)<=q at the odd four-thirds boundary",
        "universal": "UNKNOWN",
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
