#!/usr/bin/env python3
"""Crystal V28: exact cycle-weight certificate for the V27 recurrent identity SCC.

Parent:
  collatz-crystal-cost-aware-chamber-v27@f11de4820166b3d87e6a5bb0d571334fe8d97449

V27 leaves one 3,302-state recurrent cost-aware identity SCC.  V28 answers
schema #21 exactly on that SCC: can a recurrent identity cycle have
nonexpanding Collatz coefficient?

For every identity edge label b in {0,1}, assign integer weight
    w(b) = 19*b - 12.
For a directed cycle with k ordinary steps and q odd steps, the cycle weight is
    19*q - 12*k.
A Bellman-Ford potential certificate proves every directed cycle has
nonnegative weight.  An exact zero-weight cycle proves the minimum ratio is
q/k = 12/19.  Since 3^12 > 2^19, every recurrent identity cycle satisfies
3^q > 2^k.

Consequently an eventually periodic parity tail entirely inside this SCC cannot
come from a positive natural orbit: its repeated affine block has positive
cocycle B and a unique 2-adic periodic point B/(2^k-3^q), which is negative
because 3^q>2^k.  The remaining residual is therefore an aperiodic
source-realizable path through the SCC, with the canonical source/carry/M
register retained.

This is an exact finite graph certificate plus an elementary affine consequence.
It does not exclude aperiodic SCC paths and does not prove Collatz.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
import hashlib
import io
import json

# V27 is intentionally a top-level qualification script; suppress its JSON when
# importing the exact chamber objects.
with redirect_stdout(io.StringIO()):
    import collatz_crystal_cost_aware_chamber_v27 as v27

SCC = set(v27.recurrent[0])
assert len(SCC) == 3302

edges = []
for u in sorted(SCC):
    for bit, (cls, v) in v27.graph[u].items():
        if cls == "I" and v in SCC:
            edges.append((u, v, bit, 19*bit - 12))

assert len(edges) == 4788
assert sum(bit == 1 for _u, _v, bit, _w in edges) == 3302
assert sum(bit == 0 for _u, _v, bit, _w in edges) == 1486

# Exact no-negative-cycle certificate.  Distances begin at zero for every node,
# equivalent to a zero-cost super-source.  At convergence:
#   dist[v] <= dist[u] + w(u,v)
# hence reduced_cost = w + dist[u] - dist[v] >= 0 for every edge.  Summing
# reduced costs around any directed cycle gives the original cycle weight.
dist = {v: 0 for v in SCC}
relax_rounds = 0
for i in range(len(SCC)):
    changed = False
    for u, v, _bit, w in edges:
        cand = dist[u] + w
        if cand < dist[v]:
            dist[v] = cand
            changed = True
    if not changed:
        relax_rounds = i + 1
        break
else:
    raise AssertionError("negative cycle detected in recurrent identity SCC")

reduced = []
for u, v, bit, w in edges:
    rc = w + dist[u] - dist[v]
    assert rc >= 0
    reduced.append((u, v, bit, w, rc))

# A cycle made entirely of zero reduced-cost edges witnesses that the lower
# bound 19*q-12*k >= 0 is sharp.
zero_adj = defaultdict(list)
for u, v, bit, _w, rc in reduced:
    if rc == 0:
        zero_adj[u].append((v, bit))

# Tarjan SCCs on zero-reduced graph.
index = {}
low = {}
stack = []
on = set()
comps = []
counter = 0

def strong(v: int):
    global counter
    index[v] = counter
    low[v] = counter
    counter += 1
    stack.append(v)
    on.add(v)
    for w, _bit in zero_adj.get(v, ()):
        if w not in index:
            strong(w)
            low[v] = min(low[v], low[w])
        elif w in on:
            low[v] = min(low[v], index[w])
    if low[v] == index[v]:
        cc = []
        while True:
            w = stack.pop()
            on.remove(w)
            cc.append(w)
            if w == v:
                break
        comps.append(cc)

for v in SCC:
    if v not in index:
        strong(v)

zero_recurrent = []
for cc in comps:
    s = set(cc)
    cyc = len(cc) > 1 or any(v == w for v in cc for w, _b in zero_adj.get(v, ()))
    if cyc:
        zero_recurrent.append(s)

assert zero_recurrent, "sharp 12/19 cycle witness missing"

# Extract one concrete zero-weight cycle.
Z = zero_recurrent[0]
start = next(iter(Z))
seen = {}
path_nodes = []
path_bits = []
v = start
while v not in seen:
    seen[v] = len(path_nodes)
    path_nodes.append(v)
    opts = [(w,b) for w,b in zero_adj[v] if w in Z]
    assert opts
    w,b = opts[0]
    path_bits.append(b)
    v = w
j = seen[v]
cycle_nodes = path_nodes[j:]
cycle_bits = path_bits[j:]
k = len(cycle_bits)
q = sum(cycle_bits)
weight = 19*q - 12*k
assert weight == 0
assert 19*q == 12*k
assert q > 0 and k > 0
assert 3**12 > 2**19
assert 3**q > 2**k

# Generic affine fact for a nonempty parity word with at least one odd step:
# 2^k T^k(x) = 3^q x + B, B>0.  If that word were repeated forever from a
# 2-adic point x, shift-periodicity forces T^k(x)=x, hence
#   (2^k-3^q)x = B.
# Here 2^k-3^q<0 and B>0, so the unique periodic point is negative.
# We emit the graph-side universal certificate and keep the aperiodic case open.

potential_payload = {
    "nodes": len(SCC),
    "edges": len(edges),
    "potential": [[v, dist[v]] for v in sorted(SCC)],
}
potential_sha = hashlib.sha256(
    json.dumps(potential_payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()

result = {
    "schema": "COLLATZ_CRYSTAL_CYCLE_EXCLUSION_V28",
    "parent": "collatz-crystal-cost-aware-chamber-v27@f11de4820166b3d87e6a5bb0d571334fe8d97449",
    "recurrent_identity_scc": {
        "states": len(SCC),
        "identity_edges": len(edges),
        "one_edges": sum(bit == 1 for _u,_v,bit,_w in edges),
        "zero_edges": sum(bit == 0 for _u,_v,bit,_w in edges),
    },
    "cycle_weight_certificate": {
        "edge_weight": "19*bit-12",
        "relax_rounds": relax_rounds,
        "all_reduced_costs_nonnegative": True,
        "potential_sha256": potential_sha,
        "theorem": "for every directed SCC cycle: 19*q - 12*k >= 0",
        "sharp_ratio": "q/k = 12/19",
        "sharp_cycle": {
            "ordinary_length": k,
            "odd_steps": q,
            "weight": weight,
            "bits": "".join(map(str, cycle_bits)),
            "first_states": cycle_nodes[:32],
        },
    },
    "coefficient_consequence": {
        "base_inequality": {"3^12": 3**12, "2^19": 2**19},
        "universal_cycle_factor": "3^q > 2^k",
        "eventually_periodic_positive_natural_tail": "EXCLUDED",
        "reason": (
            "a repeated parity block has positive affine cocycle B; "
            "shift-periodicity gives x=B/(2^k-3^q)<0 in Z_2/Q"
        ),
    },
    "scientific_verdict": (
        "PERIODIC_RECURRENT_IDENTITY_ROUTE_REJECTED; "
        "APERIODIC_SOURCE_REALIZABLE_SCC_ROUTE_REMAINS"
    ),
    "next_residual": (
        "Intersect the 3302-state SCC with the exact source-product carry/M "
        "register and exclude aperiodic live paths. Do not widen chamber cost "
        "or raw parameter depth."
    ),
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2, sort_keys=True))
