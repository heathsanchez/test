#!/usr/bin/env python3
"""Crystal V41: symbolic closure of the V40 phase-normalized return bank.

V40 found a 13-node acyclic source-biadic return graph on three frozen exact
sources.  This gate asks a stronger question without adding new return laws:

  If any V40 return law may follow any other law at the same anchor whenever
  the exact dyadic admissibility cylinders, the retained ternary cell
  congruences, and the fixed-source fibre residues are mutually compatible,
  does recurrence reappear?

The successor test deliberately OVER-APPROXIMATES the Q3 ball semantics by
retaining only the necessary congruence implied by each V40 cell.  Therefore:

  * acyclicity is strong evidence for the complete qualified 13-law bank;
  * a cycle is only a candidate separator until exact Q3/source coupling is
    replayed.

This is still not universal Collatz evidence: the V40 law bank itself was
mined from bounded exact traces.  The purpose is to separate "sample order made
the DAG" from "the qualified law bank is intrinsically well-founded."
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib, io, json
from math import gcd

with redirect_stdout(io.StringIO()):
    import collatz_crystal_phase_normalized_return_v40 as v40


def compat_pow_residue(a_res: int, a_depth: int, b_res: int, b_depth: int, p: int) -> bool:
    """Compatibility of x=a_res mod p^a_depth and x=b_res mod p^b_depth."""
    d = min(a_depth, b_depth)
    if d == 0:
        return True
    mod = p ** d
    return (a_res - b_res) % mod == 0


# V40 has one distinct protected node per exact event on the qualified bank.
events = []
for rr in v40.runs:
    events.extend(rr["events"])

by_key = {}
for e in events:
    k = e["source_key"]
    if k in by_key:
        # The V40 certificate had 13 nodes for 13 events.  Fail closed if a
        # later parent changes that fact.
        assert by_key[k]["cert_id"] == e["cert_id"]
    by_key[k] = e

assert len(events) == 13
assert len(by_key) == 13

keys = sorted(by_key, key=repr)
index = {k: i for i, k in enumerate(keys)}


def source_compatible(ka, kb):
    # source_key =
    # (anchor, d2, rho, r3, res3, source mod 2^d2, source mod 3^r3)
    _, da, _ra, ta, _za, sna2, sna3 = ka
    _, db, _rb, tb, _zb, snb2, snb3 = kb
    if not compat_pow_residue(sna2, da, snb2, db, 2):
        return False
    if ta is None or tb is None:
        # Exact zero-defect was absent from V40.  If a parent introduces it,
        # it is an obstruction that needs separate treatment.
        return False
    return compat_pow_residue(sna3, ta, snb3, tb, 3)


def dynamic_compatible(ea, eb):
    """Necessary exact congruence conditions for law eb to follow ea.

    ea maps m -> (A*m+B)/2^D.  The target must enter eb's exact 2-adic
    admissibility cylinder.  For Q3 we retain the necessary cell congruence
    only, intentionally over-approximating exact nearest-centre radius.
    """
    ka = ea["source_key"]
    kb = eb["source_key"]
    anchor_a, da, rho_a, ta, za, _s2a, _s3a = ka
    anchor_b, db, rho_b, tb, zb, _s2b, _s3b = kb
    if anchor_a != anchor_b:
        return False

    c = ea["cert"]
    A, B, D = c["A"], c["B"], c["D"]
    assert da == D + 1
    assert rho_a == c["rho"]

    # Exact preimage of the next dyadic cylinder under the affine return.
    mod2_depth = D + db
    mod2 = 1 << mod2_depth
    pre2 = ((1 << D) * rho_b - B) * pow(A, -1, mod2) % mod2
    if not compat_pow_residue(rho_a, da, pre2, mod2_depth, 2):
        return False

    # Necessary ternary congruence for the current and next protected cells.
    # A is a power of 3, so it is generally NOT invertible modulo 3^tb.
    # Solve A*m == 2^D*zb-B (mod 3^tb) by dividing out the exact gcd.
    if ta is None or tb is None:
        return False
    if tb:
        mod3 = 3 ** tb
        rhs = ((1 << D) * zb - B) % mod3
        g = gcd(A, mod3)
        if rhs % g:
            return False
        A1, rhs1, mod1 = A // g, rhs // g, mod3 // g
        if mod1 == 1:
            pre3, pre3_depth = 0, 0
        else:
            pre3 = (rhs1 * pow(A1, -1, mod1)) % mod1
            q = mod1
            pre3_depth = 0
            while q > 1:
                assert q % 3 == 0
                q //= 3
                pre3_depth += 1
    else:
        pre3, pre3_depth = 0, 0
    if not compat_pow_residue(za, ta, pre3, pre3_depth, 3):
        return False

    return True


edges = defaultdict(set)
edge_meta = {}
for ka in keys:
    ea = by_key[ka]
    for kb in keys:
        eb = by_key[kb]
        if not source_compatible(ka, kb):
            continue
        if not dynamic_compatible(ea, eb):
            continue
        edges[ka].add(kb)
        edge_meta[(ka, kb)] = {
            "from_cert": ea["cert_id"],
            "to_cert": eb["cert_id"],
            "anchor": ka[0],
        }
for k in keys:
    edges.setdefault(k, set())


def tarjan(nodes, succ):
    idx = 0
    ind, low = {}, {}
    stack, on = [], set()
    comps = []

    def visit(v):
        nonlocal idx
        ind[v] = low[v] = idx
        idx += 1
        stack.append(v)
        on.add(v)
        for w in succ[v]:
            if w not in ind:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], ind[w])
        if low[v] == ind[v]:
            cc = []
            while True:
                w = stack.pop()
                on.remove(w)
                cc.append(w)
                if w == v:
                    break
            comps.append(cc)

    for v in nodes:
        if v not in ind:
            visit(v)

    recurrent = []
    for cc in comps:
        s = set(cc)
        cyc = len(cc) > 1 or any(v in succ[v] for v in cc)
        if cyc:
            recurrent.append(cc)
    recurrent.sort(key=lambda c: (-len(c), repr(sorted(c, key=repr)[0])))
    return recurrent


def elimination_rank(nodes, succ):
    live = set(nodes)
    rank = {}
    layers = []
    level = 0
    while live:
        dead = {x for x in live if not (succ[x] & live)}
        layers.append(len(dead))
        if not dead:
            break
        for x in dead:
            rank[x] = level
        live -= dead
        level += 1
    return rank, live, layers


def one_cycle(cc):
    S = set(cc)
    seen = {}
    path = []

    def dfs(v):
        seen[v] = 1
        path.append(v)
        for w in edges[v]:
            if w not in S:
                continue
            if seen.get(w) == 1:
                j = path.index(w)
                return path[j:] + [w]
            if seen.get(w, 0) == 0:
                z = dfs(w)
                if z is not None:
                    return z
        path.pop()
        seen[v] = 2
        return None

    for v in cc:
        if seen.get(v, 0) == 0:
            z = dfs(v)
            if z is not None:
                return z
    return None


def compose_cycle(cycle):
    # cycle is [v0,...,vk,v0]. Execute certificate of each source node.
    A, B, D = 1, 0, 0
    nodes = cycle[:-1]
    for k in nodes:
        c = by_key[k]["cert"]
        B = c["A"] * B + c["B"] * (1 << D)
        A = c["A"] * A
        D += c["D"]
    C = (1 << D) - A
    fp = None if C == 0 else Fraction(B, C)
    return {
        "length": len(nodes),
        "A": str(A),
        "B": str(B),
        "D": D,
        "slope_class": "CONTRACTING" if A < (1 << D) else ("UNIT" if A == (1 << D) else "EXPANDING"),
        "fixed_point": None if fp is None else [fp.numerator, fp.denominator],
        "fixed_point_positive_integer": bool(fp is not None and fp.denominator == 1 and fp.numerator > 0),
        "node_indices": [index[k] for k in nodes],
        "cert_ids": [by_key[k]["cert_id"] for k in nodes],
    }


recurrent = tarjan(keys, edges)
rank, residual, layers = elimination_rank(keys, edges)
cycles = []
for cc in recurrent[:20]:
    cyc = one_cycle(cc)
    assert cyc is not None
    cycles.append(compose_cycle(cyc))

observed_edges = set()
for rr in v40.runs:
    by = defaultdict(list)
    for e in rr["events"]:
        by[e["anchor"]].append(e)
    for es in by.values():
        es.sort(key=lambda z: (z["k0"], z["k1"]))
        for a, b in zip(es, es[1:]):
            observed_edges.add((a["source_key"], b["source_key"]))

symbolic_edges = {(a, b) for a in keys for b in edges[a]}
new_edges = symbolic_edges - observed_edges

result = {
    "schema": "COLLATZ_CRYSTAL_SYMBOLIC_RETURN_CLOSURE_V41",
    "parent": "collatz-crystal-phase-normalized-return-v40@66bd8e707e00f5124d5201a81814a0ea47b2fdee",
    "bank": {
        "nodes": len(keys),
        "observed_edges": len(observed_edges),
        "symbolic_overapprox_edges": len(symbolic_edges),
        "new_symbolic_edges": len(new_edges),
        "anchors": sorted({k[0] for k in keys}),
    },
    "symbolic_graph": {
        "recurrent_sccs": len(recurrent),
        "largest_scc": max((len(c) for c in recurrent), default=0),
        "residual_nodes_after_elimination": len(residual),
        "elimination_layers": layers,
        "max_rank": max(rank.values(), default=None),
        "cycles": cycles,
    },
    "new_edges": [
        {
            "from_index": index[a],
            "to_index": index[b],
            "anchor": a[0],
            "from_key": repr(a),
            "to_key": repr(b),
            **edge_meta[(a, b)],
        }
        for a, b in sorted(new_edges, key=lambda z: (index[z[0]], index[z[1]]))
    ],
    "verdict": (
        "QUALIFIED_BANK_SYMBOLIC_OVERAPPROX_ACYCLIC"
        if not recurrent
        else "SYMBOLIC_RECURRENCE_SEPARATOR_FOUND"
    ),
    "interpretation": (
        "The graph contains every pairwise successor allowed by exact dyadic "
        "return-cylinder algebra, necessary Q3 congruence, and fixed-source "
        "residue compatibility within the 13-law V40 bank. Q3 radius is "
        "over-approximated, so acyclicity is stronger than exact-bank "
        "acyclicity; recurrence requires exact replay before promotion."
    ),
    "promotion_boundary": (
        "Even an acyclic V41 does not prove Collatz: universal QED still needs "
        "return-law completeness for every ZeroTailLive state and a Lean "
        "projection/successor theorem feeding V37 hprogress."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
