#!/usr/bin/env python3
"""Crystal V42: exact all-cycle rank audit of the V41 symbolic return graph.

V41 deliberately over-approximated successor compatibility inside the 13-law
phase-normalized return bank and produced four recurrent SCCs.  The first
witness from every SCC was coefficient-contracting.  V42 removes the remaining
finite-graph ambiguity: enumerate *every simple directed cycle* in the V41
over-approximation, compose its exact affine same-anchor return map, and test
whether it strictly lowers the natural episode owner m on every nonterminal
integer state.

For a cycle F(m)=(A*m+B)/2^D with A<2^D, F(m)<m exactly above the fixed
point q=B/(2^D-A).  Thus q<=1 proves strict descent for every integer m>=2.
The sole possible equality m=1 is separately checked against the actual
Collatz endpoint x=2^anchor*m-1 and is admissible only when that endpoint is
terminal.

This is a finite-bank theorem-discovery/certificate gate.  It does NOT prove
the bank is universal for every ZeroTailLive state.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from fractions import Fraction
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_symbolic_return_closure_v41 as v41

keys = v41.keys
edges = v41.edges
by_key = v41.by_key
index = v41.index


def canonical_cycle(nodes):
    """Canonical rotation of a simple cycle without duplicated endpoint."""
    ids = [index[x] for x in nodes]
    rots = [tuple(ids[i:] + ids[:i]) for i in range(len(ids))]
    return min(rots)


cycles_by_id = {}

# Enumerate simple cycles with each start constrained to be the least node id
# on that cycle. The graph is tiny (13 nodes), so exact DFS is sufficient.
for start in keys:
    sidx = index[start]
    path = [start]
    used = {start}

    def dfs(v):
        for w in edges[v]:
            if w == start:
                cyc = list(path)
                cid = canonical_cycle(cyc)
                cycles_by_id[cid] = cyc
                continue
            if w in used:
                continue
            # Only enumerate a cycle from its least indexed node.
            if index[w] < sidx:
                continue
            used.add(w)
            path.append(w)
            dfs(w)
            path.pop()
            used.remove(w)

    dfs(start)


def compose(nodes):
    A, B, D = 1, 0, 0
    for k in nodes:
        c = by_key[k]["cert"]
        B = c["A"] * B + c["B"] * (1 << D)
        A = c["A"] * A
        D += c["D"]
    return A, B, D


rows = []
bad = []
terminal_equalities = []
for cid, nodes in sorted(cycles_by_id.items()):
    anchors = {k[0] for k in nodes}
    assert len(anchors) == 1
    anchor = next(iter(anchors))
    A, B, D = compose(nodes)
    den = (1 << D) - A
    if den > 0:
        fp = Fraction(B, den)
        slope = "CONTRACTING"
    elif den == 0:
        fp = None
        slope = "UNIT"
    else:
        fp = Fraction(B, den)
        slope = "EXPANDING"

    # Source-relative live floor. Any minimal-bad source surviving V23 lies
    # in its sole affine residual cell, hence n >= N0. A live endpoint
    # x=2^anchor*m-1 cannot be below its fixed source, so m is at least this
    # exact floor.
    N0 = v41.v40.v25.N0
    live_m_floor = (N0 + 1 + (1 << anchor) - 1) // (1 << anchor)
    descent_on_live_floor = den > 0 and fp < live_m_floor

    equality_at_one = False
    terminal_at_one = False
    if den > 0 and fp == 1:
        equality_at_one = True
        endpoint = (1 << anchor) - 1
        # CollatzFinal Terminal is the eventual 1-cycle target; x=1 is the
        # only equality actually appearing in this V41 graph.
        terminal_at_one = endpoint == 1
        terminal_equalities.append({
            "cycle": list(cid),
            "anchor": anchor,
            "endpoint_at_m1": endpoint,
            "terminal": terminal_at_one,
        })

    row = {
        "cycle": list(cid),
        "length": len(nodes),
        "anchor": anchor,
        "node_indices": [index[k] for k in nodes],
        "cert_ids": [by_key[k]["cert_id"] for k in nodes],
        "A": str(A),
        "B": str(B),
        "D": D,
        "two_pow_D_minus_A": str(den),
        "slope_class": slope,
        "fixed_point": None if fp is None else [fp.numerator, fp.denominator],
        "v23_live_m_floor": str(live_m_floor),
        "fixed_point_lt_v23_live_floor": bool(fp is not None and fp < live_m_floor),
        "strict_descent_on_v23_live_domain": descent_on_live_floor,
        "equality_at_m1": equality_at_one,
        "equality_endpoint_terminal": terminal_at_one if equality_at_one else None,
    }
    rows.append(row)
    if not descent_on_live_floor:
        bad.append(row)

# Every V41 recurrent SCC must be represented by at least one simple cycle.
assert len(rows) >= len(v41.recurrent)

verdict = (
    "ALL_SYMBOLIC_SIMPLE_CYCLES_STRICTLY_DESCEND_LIVE_M"
    if not bad
    else "NONDESCENDING_SYMBOLIC_CYCLE_SEPARATOR"
)

result = {
    "schema": "COLLATZ_CRYSTAL_CYCLE_RANK_V42",
    "parent": "collatz-crystal-symbolic-return-closure-v41@eaae81ebd67b5f9d4d425c16ec9d194e4779b9f8",
    "graph": {
        "nodes": len(keys),
        "edges": sum(len(v) for v in edges.values()),
        "recurrent_sccs": len(v41.recurrent),
        "simple_cycles": len(rows),
    },
    "all_simple_cycles": rows,
    "terminal_equalities": terminal_equalities,
    "bad_cycles": bad,
    "verdict": verdict,
    "earned_if_green": (
        "Within the complete 13-law V40 bank and V41's stronger symbolic "
        "successor over-approximation, any infinite protected return path must "
        "revisit a node; the intervening simple-cycle decomposition contains "
        "a cycle whose exact affine return strictly lowers m throughout the "
        "source-relative V23 live domain. "
        "Thus recurrence in this finite bank cannot support an infinite live "
        "execution; m is an eventual macro rank on recurrent returns."
    ),
    "remaining_universal_residual": (
        "Prove return-law / projection completeness: every non-B ZeroTailLive "
        "continuation must enter this ranked protected return interface (or a "
        "certified exit/B macro). Without that theorem, V42 is not Collatz QED."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
