#!/usr/bin/env python3
"""V53: nonpositive-budget protected return-kernel falsifier.

Parents:
  V51 affine-budget composition theorem (Lean-green): a positive cumulative
  fixed-floor budget cannot be manufactured from component budgets that are
  all nonpositive.
  V52 prospective bi-adic port: the frozen Q2 x Q3 + five owner-bit interface
  is future-functional on a large untouched source family.

Therefore the live bounded residual is not "find a cumulative macro".  It is:
can a source-coherent post-zero-tail execution remain forever among individual
same-anchor returns that have no immediate owner descent and no positive
fixed-floor budget?

This gate reuses V52's exact prospective source family.  It removes every
return that already makes progress, quotients the survivors by the source-free
frozen bi-adic key, and computes the recurrent SCC / elimination rank.  It also
measures how many low source-parameter bits would be needed to split any
bounded recurrent collisions.

Bounded falsifier only.  Acyclicity does NOT prove Collatz; universal promotion
still requires an all-depth completeness/successor theorem for the quotient.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from math import gcd
import hashlib
import io
import json
import sys

with redirect_stdout(io.StringIO()):
    import collatz_crystal_biadic_port_v46 as v46
    import collatz_crystal_nearest_centre_v45 as v45
    import collatz_crystal_dynamic_owner_separator_v43 as v43
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

FROZEN_C = 5
BASE_DEPTH = 9
SUFFIX_BITS = 30
MOD3 = 3 ** 6
CAP = 1600

MOTIFS = {
    "N00011101": "00011101",
    "N11100010": "11100010",
    "N01011001": "01011001",
    "N10100110": "10100110",
    "N001011101": "001011101",
    "N110100010": "110100010",
}

assert v46.selected["CANONICAL_NEAREST"] == FROZEN_C

def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b

def pattern_bits(pattern: str) -> int:
    x = 0
    for i in range(SUFFIX_BITS):
        x |= int(pattern[i % len(pattern)]) << i
    return x

M2 = 1 << (BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)

def crt_parameter(r: int, a: int, pattern: str) -> int:
    t2 = r + (pattern_bits(pattern) << BASE_DEPTH)
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % (1 << BASE_DEPTH) == r
    assert t % MOD3 == a
    return t

def frozen_nearest(anchor: int, m: int):
    bank = v45.centres.get(anchor)
    if bank is None:
        return None
    exact = []
    scored = []
    for centre in bank:
        cid = v45.center_id[(anchor, centre)]
        val = v45.center_distance_v3(m, centre)
        if val is None:
            exact.append(cid)
        else:
            scored.append((val, cid))
    if exact:
        ids = tuple(sorted(exact))
        return {"canonical": ids[0], "ids": ids, "radius": "INF"}
    if not scored:
        return None
    best = max(v for v, _ in scored)
    ids = tuple(sorted(cid for v, cid in scored if v == best))
    return {"canonical": ids[0], "ids": ids, "radius": best}

def reduced_key(e):
    c = e["cert"]
    ns = frozen_nearest(e["anchor"], e["m0"])
    if ns is None:
        return None
    forced = c["D"] + 1
    extra = (e["m0"] >> forced) & ((1 << FROZEN_C) - 1)
    return (
        e["anchor"],
        forced,
        c["rho"],
        ns["canonical"],
        ns["radius"],
        extra,
    )

def classify_event(e):
    c = e["cert"]
    anchor = e["anchor"]
    L = ceil_div(v25.N0 + 1, 1 << anchor)
    A = c["A"]
    B = c["B"]
    P = 1 << c["D"]
    assert A * e["m0"] + B == P * e["m1"]
    below_floor = e["m0"] < L
    W = (P - A) * L - B
    immediate = e["m1"] < e["m0"]
    floor_progress = (not below_floor) and A < P and W > 0
    progress = immediate or floor_progress
    return {
        "L": L,
        "A": A,
        "B": B,
        "P": P,
        "D": c["D"],
        "W": W,
        "below_floor": below_floor,
        "coefficient_contracting": A < P,
        "immediate_progress": immediate,
        "floor_progress": floor_progress,
        "progress": progress,
        "residual": not progress,
    }

def tarjan(nodes, succ):
    sys.setrecursionlimit(max(200000, 5 * len(nodes) + 100))
    idx = 0
    ind = {}
    low = {}
    stack = []
    on = set()
    comps = []
    def visit(v):
        nonlocal idx
        ind[v] = low[v] = idx
        idx += 1
        stack.append(v)
        on.add(v)
        for w in succ.get(v, ()):
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
    for v in sorted(nodes, key=repr):
        if v not in ind:
            visit(v)
    recurrent = []
    for cc in comps:
        cyc = len(cc) > 1 or any(v in succ.get(v, ()) for v in cc)
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
        dead = {x for x in live if not (succ.get(x, set()) & live)}
        layers.append(len(dead))
        if not dead:
            break
        for x in dead:
            rank[x] = level
        live -= dead
        level += 1
    return rank, live, layers

stats = Counter()
rows = []
transitions = []
censored = []
weird_positive = []
missing_key = []
sources = 0

for r in v43.LIVE:
    for a in range(MOD3):
        for motif, pattern in MOTIFS.items():
            t = crt_parameter(r, a, pattern)
            n = v25.N0 + v25.NC * t
            name = f"v53-r{r}-a{a}-{motif}"
            rr = v40.actual_episode_returns(name, n, CAP)
            sources += 1
            if rr["note"] == "ordinary exit before zero-tail":
                stats["EXIT_PRE_ZERO"] += 1
                continue
            stats["POST_ZERO_SOURCE"] += 1

            if rr["first_exit"] is None:
                stats["SOURCE_CENSORED"] += 1
                if len(censored) < 20:
                    censored.append({"source": str(n), "t": str(t), "name": name})

            by = defaultdict(list)
            for e in rr["events"]:
                k = reduced_key(e)
                if k is None:
                    stats["MISSING_FROZEN_KEY"] += 1
                    if len(missing_key) < 20:
                        missing_key.append({
                            "source": str(n), "t": str(t),
                            "anchor": e["anchor"], "depth": [e["k0"], e["k1"]],
                        })
                    continue
                cl = classify_event(e)
                row = {
                    "source": n,
                    "t": t,
                    "motif": motif,
                    "anchor": e["anchor"],
                    "k0": e["k0"],
                    "k1": e["k1"],
                    "key": k,
                    "m0": e["m0"],
                    "m1": e["m1"],
                    **cl,
                }
                rows.append(row)
                by[e["anchor"]].append(row)
                stats["RETURN_ROWS"] += 1
                if cl["below_floor"]:
                    stats["BELOW_DECLARED_FLOOR"] += 1
                if cl["immediate_progress"]:
                    stats["IMMEDIATE_PROGRESS"] += 1
                elif cl["floor_progress"]:
                    stats["POSITIVE_BUDGET_PROGRESS"] += 1
                else:
                    stats["RESIDUAL_ROWS"] += 1
                    if cl["W"] > 0:
                        stats["RESIDUAL_POSITIVE_BUDGET"] += 1
                        if len(weird_positive) < 20:
                            weird_positive.append({
                                "source": str(n), "t": str(t),
                                "anchor": e["anchor"],
                                "depth": [e["k0"], e["k1"]],
                                "A": str(cl["A"]), "B": str(cl["B"]),
                                "P": str(cl["P"]), "W": str(cl["W"]),
                                "m0": str(e["m0"]), "m1": str(e["m1"]),
                            })
                    else:
                        stats["RESIDUAL_NONPOSITIVE_BUDGET"] += 1

            for anchor, es in by.items():
                es.sort(key=lambda z: (z["k0"], z["k1"]))
                for i, cur in enumerate(es):
                    if not cur["residual"]:
                        continue
                    if i + 1 < len(es):
                        nxt = es[i + 1]
                        contiguous = cur["k1"] == nxt["k0"]
                        if not contiguous:
                            stats["NONCONTIGUOUS_SAME_ANCHOR"] += 1
                        transitions.append({
                            "t": t,
                            "source": n,
                            "anchor": anchor,
                            "src": cur,
                            "dst": nxt,
                            "kind": "RESIDUAL" if nxt["residual"] else "PROGRESS",
                        })
                        if nxt["residual"]:
                            stats["RESIDUAL_TO_RESIDUAL"] += 1
                        else:
                            stats["RESIDUAL_TO_PROGRESS"] += 1
                    else:
                        ex = rr["first_exit"]
                        if ex is not None and ex["depth"] >= cur["k1"]:
                            stats["RESIDUAL_TO_EXIT"] += 1
                            transitions.append({
                                "t": t,
                                "source": n,
                                "anchor": anchor,
                                "src": cur,
                                "dst": None,
                                "kind": "EXIT",
                            })
                        else:
                            stats["CENSORED_RESIDUAL_TAIL"] += 1

def graph_for_source_bits(bits: int):
    mask = (1 << bits) - 1 if bits else 0
    def key(row):
        base = row["key"]
        return base if bits == 0 else (base, row["t"] & mask)

    nodes = set()
    succ = defaultdict(set)
    edge_rows = 0
    for tr in transitions:
        if not tr["src"]["residual"]:
            continue
        u = key(tr["src"])
        nodes.add(u)
        succ.setdefault(u, set())
        if tr["kind"] == "RESIDUAL":
            v = key(tr["dst"])
            nodes.add(v)
            succ[u].add(v)
            succ.setdefault(v, set())
            edge_rows += 1
    recurrent = tarjan(nodes, succ)
    rank, leftover, layers = elimination_rank(nodes, succ)
    return {
        "source_bits": bits,
        "nodes": len(nodes),
        "edges": sum(len(v) for v in succ.values()),
        "edge_rows": edge_rows,
        "recurrent_sccs": len(recurrent),
        "largest_scc": max((len(c) for c in recurrent), default=0),
        "leftover_nodes": len(leftover),
        "elimination_layers": layers,
        "max_rank": max(rank.values(), default=None),
        "first_sccs": [
            [repr(x) for x in sorted(cc, key=repr)[:12]]
            for cc in recurrent[:8]
        ],
    }

frontier = {str(b): graph_for_source_bits(b) for b in range(0, 13)}
base_graph = frontier["0"]

if stats["SOURCE_CENSORED"] or stats["CENSORED_RESIDUAL_TAIL"]:
    verdict = "CENSORED_NO_PROMOTION"
elif stats["MISSING_FROZEN_KEY"]:
    verdict = "FROZEN_KEY_INCOMPLETE"
elif stats["BELOW_DECLARED_FLOOR"]:
    verdict = "DECLARED_FLOOR_SEPARATOR"
elif stats["RESIDUAL_POSITIVE_BUDGET"]:
    verdict = "POSITIVE_BUDGET_NONPROGRESS_SEPARATOR"
elif base_graph["recurrent_sccs"]:
    verdict = "SOURCE_FREE_NONPOSITIVE_BUDGET_KERNEL_RECURRENT"
else:
    verdict = "SOURCE_FREE_NONPOSITIVE_BUDGET_KERNEL_ACYCLIC_ON_PROSPECTIVE_CORPUS"

sample_residual = []
for row in rows:
    if row["residual"] and len(sample_residual) < 30:
        sample_residual.append({
            "source": str(row["source"]),
            "t": str(row["t"]),
            "anchor": row["anchor"],
            "depth": [row["k0"], row["k1"]],
            "key": repr(row["key"]),
            "A": str(row["A"]),
            "B": str(row["B"]),
            "P": str(row["P"]),
            "W": str(row["W"]),
            "m0": str(row["m0"]),
            "m1": str(row["m1"]),
        })

result = {
    "schema": "COLLATZ_CRYSTAL_NONPOSITIVE_BUDGET_KERNEL_V53",
    "parents": {
        "V51": "collatz-crystal-affine-budget-v51@125b9b1b3120ece06d8fed09f76b10a8e6aea263",
        "V52": "collatz-crystal-biadic-port-prospective-v52@3232f8a437be77db05927e6f679640b5aceebe4c",
    },
    "challenge": {
        "exact_sources_tested": sources,
        "live_binary_cells": len(v43.LIVE),
        "ternary_classes": MOD3,
        "motifs": list(MOTIFS),
        "cap": CAP,
        "frozen_extra_owner_bits": FROZEN_C,
    },
    "stats": dict(sorted(stats.items())),
    "source_free_graph": base_graph,
    "source_bit_frontier": frontier,
    "weird_positive_budget_nonprogress": weird_positive,
    "missing_frozen_keys": missing_key,
    "censored_sources": censored,
    "sample_residual_rows": sample_residual,
    "verdict": verdict,
    "interpretation": (
        "V51 removes cumulative batching as a source of new positive budget. "
        "V53 therefore keeps only individual returns that make neither immediate "
        "owner progress nor source-independent fixed-floor progress, then asks "
        "whether V52's source-free frozen bi-adic quotient still carries a "
        "recurrent protected kernel."
    ),
    "promotion_boundary": (
        "Acyclicity on this prospective corpus is bounded discovery evidence. "
        "QED still requires an all-depth/source-independent theorem that every "
        "lawful zero-tail residual transition is represented by this quotient "
        "and decreases the induced rank, or elimination of any exact recurrent "
        "cell emitted here."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
