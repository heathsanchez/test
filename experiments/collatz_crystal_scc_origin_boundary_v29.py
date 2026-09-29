#!/usr/bin/env python3
"""Crystal V29: exact supercritical-density certificate on the V27 recurrent SCC.

Parent authority:
  collatz-crystal-cost-aware-chamber-v27
  f11de4820166b3d87e6a5bb0d571334fe8d97449

V27 exposed one recurrent cost-aware identity SCC of 3302 states.  This gate
does not pretend that the finite 3-adic SCC is itself a natural-source proof.
It asks for the strongest consequence that is valid on the SCC alone.

For every identity edge u -b-> v, b in {0,1}, seek an integer potential h with

    19*b - 12 + h(u) - h(v) >= 0.

Summing along a path gives

    19*ones - 12*length >= h(last) - h(first),

so every infinite SCC path has liminf odd density at least 12/19.  A tight
zero-reduced-cost cycle certifies equality is attained by the symbolic SCC.

Since 3^12 > 2^19, 12/19 is strictly above the Collatz critical density
log(2)/log(3).  Excluding positive-natural realization of such an infinite
supercritical SCC path still requires a source/origin theorem.  This gate keeps
that boundary explicit.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
import sys

O = 12
MOD = 3 ** O

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

# Exact V27 cost-aware chamber.
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

graph = {}
outcomes = Counter()
for r, (_S, _C, w) in best.items():
    row = {}
    for bit in (0, 1):
        nw = next_window(w, bit)
        cls, nr = classify_word(nw)
        row[bit] = (cls, nr)
        outcomes[(bit, cls)] += 1
    graph[r] = row

assert outcomes == Counter({
    (0, "B"): 15_947,
    (0, "I"): 11_422,
    (0, "K"): 100,
    (1, "I"): 23_287,
    (1, "K"): 4_182,
})

# Tarjan SCCs on identity-only transitions.
sys.setrecursionlimit(200_000)
adj = {
    r: [nr for _bit, (cls, nr) in row.items() if cls == "I"]
    for r, row in graph.items()
}
index = {}
low = {}
stack = []
on_stack = set()
sccs = []
counter = 0

def strong(v: int):
    global counter
    index[v] = counter
    low[v] = counter
    counter += 1
    stack.append(v)
    on_stack.add(v)
    for w in adj[v]:
        if w not in index:
            strong(w)
            low[v] = min(low[v], low[w])
        elif w in on_stack:
            low[v] = min(low[v], index[w])
    if low[v] == index[v]:
        cc = []
        while True:
            w = stack.pop()
            on_stack.remove(w)
            cc.append(w)
            if w == v:
                break
        sccs.append(cc)

for v in adj:
    if v not in index:
        strong(v)

recurrent = []
for cc in sccs:
    if len(cc) > 1:
        recurrent.append(cc)
    elif cc and cc[0] in adj[cc[0]]:
        recurrent.append(cc)
recurrent.sort(key=len, reverse=True)
assert len(recurrent) == 1
assert len(recurrent[0]) == 3302
R = set(recurrent[0])

# Exact internal edges and first earned source-free separator.
internal = []
internal_pattern = Counter()
zero_exits = Counter()
for u in R:
    inside_bits = []
    for bit, (cls, v) in graph[u].items():
        if cls == "I" and v in R:
            internal.append((u, v, bit))
            inside_bits.append(bit)
        elif bit == 0:
            zero_exits[cls if cls != "I" else "I_OUTSIDE"] += 1
    internal_pattern[tuple(inside_bits)] += 1

assert len(internal) == 4788
assert internal_pattern == Counter({(1,): 1816, (0, 1): 1486})
assert zero_exits == Counter({"I_OUTSIDE": 1023, "B": 792, "K": 1})

# Difference-constraint certificate for odd-density >= 12/19.
# Edge weight w=19*b-12.  No negative cycle is equivalent to existence of h
# with w+h(u)-h(v)>=0.  Bellman-Ford from a zero super-source constructs h.
vertices = sorted(R)
h = {v: 0 for v in vertices}
converged_round = None
for it in range(len(vertices)):
    changed = False
    for u, v, bit in internal:
        w = 19 * bit - 12
        nv = h[u] + w
        if nv < h[v]:
            h[v] = nv
            changed = True
    if not changed:
        converged_round = it
        break
assert converged_round is not None

reduced = []
for u, v, bit in internal:
    rc = (19 * bit - 12) + h[u] - h[v]
    assert rc >= 0
    reduced.append((u, v, bit, rc))

# A cycle in the zero-reduced-cost subgraph proves the lower bound is tight.
zero_adj = defaultdict(list)
for u, v, bit, rc in reduced:
    if rc == 0:
        zero_adj[u].append((v, bit))

color = {}
parent = {}
parent_bit = {}
tight_cycle = None

def dfs_cycle(v: int):
    global tight_cycle
    color[v] = 1
    for w, bit in zero_adj.get(v, ()):
        if tight_cycle is not None:
            return
        if color.get(w, 0) == 0:
            parent[w] = v
            parent_bit[w] = bit
            dfs_cycle(w)
        elif color.get(w) == 1:
            back_bits = []
            cur = v
            while cur != w:
                back_bits.append(parent_bit[cur])
                cur = parent[cur]
            bits = list(reversed(back_bits)) + [bit]

            rev_nodes = [v]
            cur = v
            while cur != w:
                cur = parent[cur]
                rev_nodes.append(cur)
            nodes = list(reversed(rev_nodes))
            tight_cycle = {"nodes": nodes, "bits": bits}
            return
    color[v] = 2

for v in vertices:
    if color.get(v, 0) == 0:
        dfs_cycle(v)
        if tight_cycle is not None:
            break

assert tight_cycle is not None
L = len(tight_cycle["bits"])
Q = sum(tight_cycle["bits"])
assert 19 * Q == 12 * L
assert L == 19 and Q == 12

critical_gap = 3 ** 12 - 2 ** 19
assert critical_gap == 7153 and critical_gap > 0

potential_rows = [[v, h[v]] for v in vertices]
potential_sha = hashlib.sha256(
    json.dumps(potential_rows, separators=(",", ":")).encode()
).hexdigest()

result = {
    "schema": "COLLATZ_CRYSTAL_SCC_ORIGIN_BOUNDARY_V29",
    "parent": "collatz-crystal-cost-aware-chamber-v27@f11de4820166b3d87e6a5bb0d571334fe8d97449",
    "recurrent_identity_scc": {
        "states": len(R),
        "internal_edges": len(internal),
        "internal_edge_pattern": {
            "only_bit_1": internal_pattern[(1,)],
            "both_bits_0_1": internal_pattern[(0, 1)],
        },
        "zero_edge_exits": dict(sorted(zero_exits.items())),
    },
    "exact_density_certificate": {
        "numerator": 12,
        "denominator": 19,
        "edge_weight": "19*b-12",
        "potential_min": min(h.values()),
        "potential_max": max(h.values()),
        "bellman_ford_converged_round": converged_round,
        "negative_reduced_edges": 0,
        "zero_reduced_edges": sum(rc == 0 for *_x, rc in reduced),
        "potential_sha256": potential_sha,
        "path_inequality": "19*ones-12*length >= h(last)-h(first)",
        "liminf_odd_density_lower_bound": "12/19",
        "tight_cycle": {
            "length": L,
            "odd_bits": Q,
            "bits": "".join(map(str, tight_cycle["bits"])),
            "states": tight_cycle["nodes"],
        },
    },
    "critical_density_separation": {
        "exact_integer_inequality": "3^12 > 2^19",
        "gap": critical_gap,
        "consequence": "12/19 > log(2)/log(3)",
    },
    "scientific_verdict": (
        "WARRANTED_FINITE_GRAPH: every infinite path that remains in the V27 "
        "recurrent identity SCC has liminf odd density at least 12/19, and the "
        "bound is tight on the symbolic SCC. This alone does not prove that a "
        "positive natural Collatz orbit cannot realize such an aperiodic path."
    ),
    "next_residual": {
        "name": "POSITIVE_NATURAL_REALIZABILITY_OF_SUPERCRITICAL_SCC_PATH",
        "statement": (
            "Intersect the exact 12/19 density-potential certificate with the "
            "canonical (q,R,Y)/M source-carry recursion. Prove that an eventually-"
            "zero source-lift tail cannot remain forever in this supercritical "
            "identity SCC, or force a K/B/M1 lower-source exit."
        ),
        "forbidden_shortcuts": [
            "raw deeper parameter census",
            "3-adic SCC alone",
            "new fitted scalar rank",
        ],
    },
    "external_bridge_boundary": {
        "peer_reviewed_monks_yazinski_2004": (
            "only gives critical-density lower bound for divergent rational 2-adics; "
            "not sufficient to exclude this SCC"
        ),
        "lopez_stoll_arxiv_2101_12747": (
            "claims equality at the critical density for divergent rational 2-adics; "
            "treat as CANDIDATE until independently verified/formalized"
        ),
    },
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2, sort_keys=True))
