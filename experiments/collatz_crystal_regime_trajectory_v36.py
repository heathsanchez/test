#!/usr/bin/env python3
"""Crystal V36: source-regime trajectory certification.

Parent:
  collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385

Crystal transfer from the chess experiments:
- A final/root witness is not a protected consequence.
- The same local intervention can reverse consequence across a resource regime.
- Therefore certify the entire irreversible trajectory against the protected
  constraint and expose the minimum regime variable that separates outcomes.

For Collatz the protected constraint is original-source order.  Along a
canonical chamber path pi, write each owner prefix as

    m_i = A_i*m_0 + B_i.

A no-OrdinaryExit realization relative to source floor n requires EVERY prefix
owner to satisfy m_i >= n.  Hence the exact minimum source-headroom regime is

    G_pi(n) = max_i (n-B_i)/A_i,

including i=0.  This max-affine threshold composes exactly and is independent
of the final return drift.

This gate enumerates every first return to the V34 separator state 514835 up to
length 26 in the complete non-B chamber graph.  It falsifies final-return drift
as a consequence certifier and exhibits one exact 2-adic continuation guard
whose consequence changes solely with source-relative headroom.

This is a bounded theorem-discovery/qualification gate, not a Collatz proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json
import math

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_return_separator_v34 as v34

BASE = v34.BASE
N0 = v34.N0
MOD = v34.MOD
best = v34.best
edges = v34.edges
owner_map = v34.owner_map

MAX_LEN = 26

adj = defaultdict(list)
for e in edges:
    adj[e[0]].append(e)
for u in adj:
    adj[u].sort(key=lambda e: (e[2], e[1], e[3], e[4]))


def frac_pair(x: Fraction):
    return [x.numerator, x.denominator]


def frac_str(x: Fraction):
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def ceil_frac(x: Fraction) -> int:
    return -((-x.numerator) // x.denominator)


def least_congruent_ge(residue: int, modulus: int, floor: int) -> int:
    if residue >= floor:
        return residue
    return residue + ((floor - residue + modulus - 1) // modulus) * modulus


def compose_prefixes(path):
    A = Fraction(1)
    B = Fraction(0)
    prefixes = [(A, B)]
    for u, v, bit, cls, drop in path:
        a, b = owner_map(u, v, bit)
        B = a * B + b
        A = a * A
        prefixes.append((A, B))
    return prefixes


def trajectory_threshold(path, n: int):
    prefixes = compose_prefixes(path)
    threshold = Fraction(n)
    dominant_index = 0
    dominant_A = Fraction(1)
    dominant_B = Fraction(0)
    for i, (A, B) in enumerate(prefixes[1:], 1):
        t = (Fraction(n) - B) / A
        if t > threshold:
            threshold = t
            dominant_index = i
            dominant_A = A
            dominant_B = B
    return threshold, dominant_index, dominant_A, dominant_B, prefixes


def owner_values(prefixes, m: int):
    return [A * m + B for A, B in prefixes]


def return_fixed_point(A: Fraction, B: Fraction):
    if A == 1:
        return None
    return B / (1 - A)


def edge_json(e):
    u, v, bit, cls, drop = e
    return {"u":u, "v":v, "bit":bit, "class":cls, "drop":drop}


returns = []
length_hist = Counter()

# Enumerate first returns: BASE may occur only at the final vertex.
stack = [(BASE, tuple())]
while stack:
    u, path = stack.pop()
    if len(path) >= MAX_LEN:
        continue
    for e in reversed(adj[u]):
        v = e[1]
        np = path + (e,)
        if v == BASE:
            returns.append(np)
            length_hist[len(np)] += 1
        else:
            stack.append((v, np))

assert len(returns) == 18_414
assert dict(sorted(length_hist.items())) == {
    9:1, 10:2, 11:2, 12:2, 13:2, 14:4, 15:8, 16:16,
    17:34, 18:66, 19:129, 20:250, 21:478, 22:891, 23:1603,
    24:2775, 25:4634, 26:7517,
}

classes = Counter()
threshold_inverse_slopes = set()
false_safe = []
positive_fp = []
nonpositive_fp = 0
fp_at_or_above_source = 0

for path in returns:
    threshold, dom_i, dom_A, dom_B, prefixes = trajectory_threshold(path, N0)
    A, B = prefixes[-1]
    final_at_floor = A * N0 + B
    viable_at_floor = threshold <= N0
    final_expands_at_floor = final_at_floor > N0

    key = (
        "TRAJECTORY_VIABLE" if viable_at_floor else "TRAJECTORY_EXIT",
        "FINAL_EXPANDS" if final_expands_at_floor else "FINAL_CONTRACTS",
    )
    classes[key] += 1

    if threshold == N0:
        threshold_inverse_slopes.add(Fraction(1))
    else:
        threshold_inverse_slopes.add(1 / dom_A)

    if (not viable_at_floor) and final_expands_at_floor:
        false_safe.append((path, threshold, dom_i, dom_A, dom_B, prefixes, final_at_floor))

    fp = return_fixed_point(A, B)
    if fp is None or fp <= 0:
        nonpositive_fp += 1
    else:
        positive_fp.append(fp)
        if fp >= N0:
            fp_at_or_above_source += 1

assert classes == Counter({
    ("TRAJECTORY_VIABLE","FINAL_EXPANDS"):18_298,
    ("TRAJECTORY_EXIT","FINAL_EXPANDS"):86,
    ("TRAJECTORY_EXIT","FINAL_CONTRACTS"):30,
})
assert classes[("TRAJECTORY_VIABLE","FINAL_CONTRACTS")] == 0
assert len(false_safe) == 86

expected_inverse_slopes = {
    Fraction(1),
    Fraction(65536,59049),
    Fraction(2097152,1594323),
    Fraction(262144,177147),
    Fraction(32768,19683),
    Fraction(1048576,531441),
    Fraction(131072,59049),
    Fraction(524288,177147),
    Fraction(65536,19683),
    Fraction(262144,59049),
    Fraction(32768,6561),
}
assert threshold_inverse_slopes == expected_inverse_slopes

assert nonpositive_fp == 18_394
assert len(positive_fp) == 20
assert fp_at_or_above_source == 0
max_positive_fp = max(positive_fp)
assert max_positive_fp == Fraction(1_107_667, 502_829)

# Shortest false-safe return: final drift says "above source", but an
# irreversible prefix has already crossed below the original source.
false_safe.sort(key=lambda row: (len(row[0]), tuple((e[0],e[1],e[2]) for e in row[0])))
wpath, wthr, widx, wA, wB, wpref, wfinal = false_safe[0]
assert len(wpath) == 19
assert widx == 18
fA, fB = wpref[-1]
assert fA == Fraction(531441,524288)
assert fB == Fraction(371953,524288)
assert wthr == Fraction(1133367955888714852069405,19683)

floor_values = owner_values(wpref, N0)
assert floor_values[widx] == Fraction(1723246192489970711814813,65536)
assert floor_values[widx] < N0
assert wfinal > N0

# Exact 2-adic continuation guard for that SAME return word.
guard_residue, guard_modulus = v34.owner_guard(wpath)
assert guard_modulus == 1 << 32

# Exhibit the chess-style regime reversal inside one exact continuation
# cylinder: same chamber state, same return word, same 2-adic guard.
m_low = least_congruent_ge(guard_residue, guard_modulus, N0)
m_high = least_congruent_ge(guard_residue, guard_modulus, ceil_frac(wthr))
assert m_low < wthr <= m_high
assert m_low % guard_modulus == m_high % guard_modulus == guard_residue

low_vals = owner_values(wpref, m_low)
high_vals = owner_values(wpref, m_high)
assert min(low_vals) < N0
assert low_vals[-1] > N0
assert min(high_vals) >= N0
assert high_vals[-1] > N0

# The regime coordinate is source-relative headroom, not another chamber label.
low_min_i = min(range(len(low_vals)), key=lambda i: low_vals[i])
high_min_i = min(range(len(high_vals)), key=lambda i: high_vals[i])

result = {
    "schema":"COLLATZ_CRYSTAL_REGIME_TRAJECTORY_V36",
    "parent":"collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385",
    "chess_transfer":{
        "principle":(
            "Certify the whole consequential trajectory under its resource regime; "
            "do not certify from a final/root witness alone."
        ),
        "collatz_resource_regime":"source-relative canonical-owner headroom above the original source",
        "collatz_protected_consequence":"every irreversible owner prefix remains >= original source",
    },
    "exact_regime_law":{
        "path_prefix":"m_i=A_i*m_0+B_i",
        "threshold":"G_pi(n)=max_i (n-B_i)/A_i, including i=0",
        "integer_survival_condition":"m_0 >= ceil(G_pi(n)) together with the exact 2-adic path guard",
        "composition":"max-affine/tropical threshold pullback",
    },
    "first_return_census":{
        "base_state":BASE,
        "max_length":MAX_LEN,
        "first_returns":len(returns),
        "length_histogram":dict(sorted(length_hist.items())),
        "classification":{
            "trajectory_viable_final_expands":classes[("TRAJECTORY_VIABLE","FINAL_EXPANDS")],
            "trajectory_exit_final_expands":classes[("TRAJECTORY_EXIT","FINAL_EXPANDS")],
            "trajectory_exit_final_contracts":classes[("TRAJECTORY_EXIT","FINAL_CONTRACTS")],
            "trajectory_viable_final_contracts":classes[("TRAJECTORY_VIABLE","FINAL_CONTRACTS")],
        },
        "false_safe_final_drift_count":len(false_safe),
        "threshold_inverse_slope_regimes":[frac_str(x) for x in sorted(threshold_inverse_slopes)],
        "threshold_regime_count":len(threshold_inverse_slopes),
    },
    "shortest_false_safe_witness":{
        "length":len(wpath),
        "path":[edge_json(e) for e in wpath],
        "final_map":{
            "slope":frac_pair(fA),
            "intercept":frac_pair(fB),
            "final_at_source_floor":frac_pair(wfinal),
            "final_above_source_floor":wfinal>N0,
        },
        "trajectory":{
            "critical_prefix_index":widx,
            "owner_at_source_floor_critical_prefix":frac_pair(floor_values[widx]),
            "critical_prefix_below_source":floor_values[widx] < N0,
            "exact_start_threshold":frac_pair(wthr),
            "threshold_over_source":float(wthr/Fraction(N0)),
        },
        "same_2adic_guard_regime_reversal":{
            "guard_residue":guard_residue,
            "guard_modulus":guard_modulus,
            "low_headroom_owner":m_low,
            "low_headroom_min_owner":frac_pair(min(low_vals)),
            "low_headroom_min_prefix_index":low_min_i,
            "low_headroom_consequence":"ORDINARY_EXIT_INSIDE_RETURN_DESPITE_FINAL_EXPANSION",
            "high_headroom_owner":m_high,
            "high_headroom_min_owner":frac_pair(min(high_vals)),
            "high_headroom_min_prefix_index":high_min_i,
            "high_headroom_consequence":"FULL_RETURN_SOURCE_ORDER_VIABLE",
        },
    },
    "bounded_periodic_return_check":{
        "returns_checked":len(returns),
        "nonpositive_fixed_points":nonpositive_fp,
        "positive_fixed_points":len(positive_fp),
        "positive_fixed_points_at_or_above_source":fp_at_or_above_source,
        "max_positive_fixed_point":frac_pair(max_positive_fp),
        "interpretation":(
            "No first return through length 26 has a positive periodic fixed point "
            "at the V23 source scale. This is bounded evidence only."
        ),
    },
    "scientific_verdict":(
        "FINAL_RETURN_DRIFT_REJECTED_AS_CONSEQUENCE_CERTIFIER; "
        "SOURCE_RELATIVE_TRAJECTORY_HEADROOM_EARNED_AS_RESOURCE_REGIME; "
        "SAME_2ADIC_GUARD_HAS_OPPOSITE_SOURCE_ORDER_CONSEQUENCES_ACROSS_HEADROOM_REGIMES"
    ),
    "next_residual":{
        "name":"DYADIC_GUARD_X_TRAJECTORY_HEADROOM",
        "statement":(
            "Intersect the nested exact 2-adic owner/source-carry guard with the "
            "max-affine source-order trajectory threshold. Prove that no one fixed "
            "positive natural no-OrdinaryExit source can realize an infinite aperiodic "
            "path satisfying both constraints."
        ),
        "next_experiment":(
            "Compile threshold pullback as a protected consequence on graph edges and "
            "ask whether the product quotient (chamber state, dyadic guard, threshold "
            "regime) has any infinite source-realizable post-fixed component."
        ),
        "forbidden_shortcuts":[
            "final return drift or fixed-point sign as a standalone certificate",
            "deeper raw carry/residue census",
            "state-only owner rank",
            "treat local K rewind as original-source descent",
        ],
    },
    "universal_status":"UNKNOWN",
    "global_collatz":"UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
