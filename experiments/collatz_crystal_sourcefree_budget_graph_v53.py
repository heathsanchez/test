#!/usr/bin/env python3
"""V53: source-free bad-budget recurrence graph.

V51 proved that a positive affine macro budget cannot be synthesized from a
block of entirely nonpositive individual budgets. Therefore V49's cumulative
macro presentation is consequence-redundant: the universal residual is an
infinite protected return itinerary with W <= 0 at every individual return.

V52 prospectively qualified a frozen local bi-adic representation, but its
functional key retained exact source t. V53 removes t completely and asks only
the weaker question required for eventual progress:

  Can the source-free bi-adic state support a recurrent all-W<=0 graph?

The frozen coordinates are:
  Q2 return cylinder (anchor, D+1, rho),
  nearest frozen V45 3-adic centre and radius,
  five owner bits beyond the forced Q2 cylinder.

We over-approximate across every accumulated V45 row plus the disjoint V52
prospective rows. A source-free recurrent SCC is a separator against a finite
rank on that quotient. Acyclicity is only bounded evidence and is useful only
when nodes are actually reused across distinct sources.

This is diagnostic / quotient discovery. Global Collatz remains UNKNOWN.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_biadic_port_prospective_v52 as v52

v45 = v52.v45
v25 = v52.v25

C = 5

def extra_bits(m0: int, forced_bits: int, c: int=C) -> int:
    return (m0 >> forced_bits) & ((1 << c) - 1) if c else 0

def live_floor(anchor: int) -> int:
    return (v25.N0 + 1 + (1 << anchor) - 1) // (1 << anchor)

def budget_from_sig(sig) -> int:
    anchor, A, B, D, _rho = sig[:5]
    return ((1 << D) - A) * live_floor(anchor) - B

def normalize_prior(row):
    anchor = row["sig"][0]
    ns = v45.nearest_cache[(anchor, row["m0"])]
    q2 = v45.q2(row)
    return {
        "cohort": "PRIOR",
        "source_name": row["source_name"],
        "source": row["source"],
        "t": row["t"],
        "sig": row["sig"],
        "m0": row["m0"],
        "m1": None,
        "q2": q2,
        "nearest_canonical": ns["canonical"],
        "nearest_radius": ns["radius"],
        "forced_bits": row["forced_bits"],
        "k0": row["k0"],
        "k1": row["k1"],
        "label": row["label"],
    }

def normalize_fresh(row):
    return {
        "cohort": "FRESH_V52",
        "source_name": row["source_name"],
        "source": row["source"],
        "t": row["t"],
        "sig": row["sig"],
        "m0": row["m0"],
        "m1": row["m1"],
        "q2": row["q2"],
        "nearest_canonical": row["nearest_canonical"],
        "nearest_radius": row["nearest_radius"],
        "forced_bits": row["forced_bits"],
        "k0": row["k0"],
        "k1": row["k1"],
        "label": row["label"],
    }

rows = [normalize_prior(z) for z in v45.rows]
rows.extend(normalize_fresh(z) for z in v52.rows)

# Fresh t values were explicitly disjoint from the accumulated parent corpus.
prior_t = {z["t"] for z in rows if z["cohort"] == "PRIOR"}
fresh_t = {z["t"] for z in rows if z["cohort"] == "FRESH_V52"}
assert prior_t.isdisjoint(fresh_t)

for z in rows:
    z["budget"] = budget_from_sig(z["sig"])
    z["bad"] = z["budget"] <= 0
    z["extra5"] = extra_bits(z["m0"], z["forced_bits"])
    # Any positive fixed-floor budget must descend on every live owner.
    if z["budget"] > 0 and z["m1"] is not None:
        assert z["m1"] < z["m0"]

def state_key(z, mode: str):
    anchor, d2, rho = z["q2"]
    centre = z["nearest_canonical"]
    radius = z["nearest_radius"]
    e = z["extra5"]
    if mode == "PORT_ONLY":
        return (anchor, e)
    if mode == "CENTRE_PORT":
        return (anchor, centre, e)
    if mode == "CENTRE_RADIUS_PORT":
        return (anchor, centre, radius, e)
    if mode == "DEPTH_CENTRE_RADIUS_PORT":
        return (anchor, d2, centre, radius, e)
    if mode == "FULL_FROZEN_PORT":
        return (anchor, d2, rho, centre, radius, e)
    raise KeyError(mode)

MODES = (
    "PORT_ONLY",
    "CENTRE_PORT",
    "CENTRE_RADIUS_PORT",
    "DEPTH_CENTRE_RADIUS_PORT",
    "FULL_FROZEN_PORT",
)

# Chronological exact same-anchor paths. Rows whose terminal outcome is an exit
# have no later row in their (source, anchor) group.
groups = defaultdict(list)
for z in rows:
    groups[(z["cohort"], z["source_name"], z["q2"][0])].append(z)
for g in groups.values():
    g.sort(key=lambda z: (z["k0"], z["k1"]))

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

    for v in nodes:
        if v not in ind:
            visit(v)

    recurrent = []
    for cc in comps:
        cyc = len(cc) > 1 or any(v in succ.get(v, ()) for v in cc)
        if cyc:
            recurrent.append(cc)
    recurrent.sort(key=lambda cc: (-len(cc), repr(sorted(cc, key=repr)[0])))
    return recurrent

def elimination_rank(nodes, succ):
    live = set(nodes)
    rank = {}
    layers = []
    level = 0
    while live:
        dead = {v for v in live if not (set(succ.get(v, ())) & live)}
        layers.append(len(dead))
        if not dead:
            break
        for v in dead:
            rank[v] = level
        live -= dead
        level += 1
    return rank, live, layers

def audit(mode: str):
    occ = Counter()
    sources = defaultdict(set)
    cohorts = defaultdict(set)
    examples = defaultdict(list)
    succ = defaultdict(set)
    edge_sources = defaultdict(set)
    positive_hits = 0
    exits = 0
    bad_occurrences = 0
    all_occurrences = 0

    for g in groups.values():
        for i, z in enumerate(g):
            all_occurrences += 1
            if not z["bad"]:
                continue
            bad_occurrences += 1
            k = state_key(z, mode)
            occ[k] += 1
            sources[k].add(z["source"])
            cohorts[k].add(z["cohort"])
            if len(examples[k]) < 4:
                examples[k].append(z)

            if i + 1 < len(g):
                nxt = g[i + 1]
                if nxt["bad"]:
                    w = state_key(nxt, mode)
                    succ[k].add(w)
                    edge_sources[(k, w)].add(z["source"])
                else:
                    positive_hits += 1
            else:
                exits += 1

    nodes = set(occ)
    for v in nodes:
        succ.setdefault(v, set())
    recurrent = tarjan(nodes, succ)
    rank, residual, layers = elimination_rank(nodes, succ)

    reused = [v for v in nodes if occ[v] > 1]
    cross_source = [v for v in nodes if len(sources[v]) > 1]
    cross_cohort = [v for v in nodes if len(cohorts[v]) > 1]

    first_scc = None
    if recurrent:
        cc = recurrent[0]
        S = set(cc)
        internal = []
        for a in cc:
            for b in succ[a]:
                if b in S:
                    internal.append((a, b))
        internal.sort(key=lambda e: (repr(e[0]), repr(e[1])))
        first_scc = {
            "size": len(cc),
            "nodes": [repr(x) for x in sorted(cc, key=repr)[:25]],
            "internal_edges": len(internal),
            "sample_edges": [
                {
                    "from": repr(a),
                    "to": repr(b),
                    "distinct_sources": len(edge_sources[(a, b)]),
                }
                for a, b in internal[:25]
            ],
            "sample_occurrences": [
                {
                    "node": repr(v),
                    "occurrences": occ[v],
                    "distinct_sources": len(sources[v]),
                    "cohorts": sorted(cohorts[v]),
                    "rows": [
                        {
                            "cohort": z["cohort"],
                            "source": str(z["source"]),
                            "t": str(z["t"]),
                            "depth": [z["k0"], z["k1"]],
                            "budget": str(z["budget"]),
                            "sig": repr(z["sig"]),
                        }
                        for z in examples[v]
                    ],
                }
                for v in sorted(cc, key=repr)[:8]
            ],
        }

    return {
        "mode": mode,
        "all_occurrences": all_occurrences,
        "bad_occurrences": bad_occurrences,
        "distinct_bad_nodes": len(nodes),
        "distinct_bad_edges": sum(len(x) for x in succ.values()),
        "positive_budget_next": positive_hits,
        "terminal_or_exit_after_bad": exits,
        "reused_nodes": len(reused),
        "cross_source_nodes": len(cross_source),
        "cross_cohort_nodes": len(cross_cohort),
        "max_node_occurrences": max(occ.values(), default=0),
        "max_distinct_sources_per_node": max((len(sources[v]) for v in nodes), default=0),
        "recurrent_sccs": len(recurrent),
        "largest_recurrent_scc": max((len(x) for x in recurrent), default=0),
        "residual_nodes_after_elimination": len(residual),
        "elimination_layers": layers,
        "max_rank_if_acyclic": max(rank.values(), default=None) if not recurrent else None,
        "first_recurrent_scc": first_scc,
    }

audits = {mode: audit(mode) for mode in MODES}

# Choose the coarsest source-free representation whose observed bad graph is
# acyclic AND which has genuine cross-source reuse. If none exists, emit the
# finest recurrent separator.
selected = None
for mode in MODES:
    z = audits[mode]
    if z["recurrent_sccs"] == 0 and z["cross_source_nodes"] > 0:
        selected = mode
        break

if selected is not None:
    verdict = "SOURCEFREE_BAD_BUDGET_GRAPH_ACYCLIC_BOUNDED"
else:
    verdict = "SOURCEFREE_RECURRENT_BAD_BUDGET_SEPARATOR"

result = {
    "schema": "COLLATZ_CRYSTAL_SOURCEFREE_BUDGET_GRAPH_V53",
    "parents": {
        "V51": "collatz-crystal-affine-budget-v51@a384d326c0b8014249852d895f1afb791a5b2efc",
        "V52": "collatz-crystal-biadic-port-prospective-v52@3232f8a437be77db05927e6f679640b5aceebe4c",
    },
    "corpus": {
        "prior_rows": len(v45.rows),
        "fresh_v52_rows": len(v52.rows),
        "total_rows": len(rows),
        "prior_sources": len({z["source"] for z in rows if z["cohort"] == "PRIOR"}),
        "fresh_sources": len({z["source"] for z in rows if z["cohort"] == "FRESH_V52"}),
    },
    "budget": {
        "definition": "W=((2^D)-A)*L_anchor-B",
        "live_floor": "L_anchor=ceil((V23.N0+1)/2^anchor)",
        "good": "W>0",
        "bad": "W<=0",
        "formal_parent": "V51 proves positive composite budget forces a positive component budget",
    },
    "audits": audits,
    "selected_coarsest_acyclic_reused_mode": selected,
    "verdict": verdict,
    "interpretation": (
        "Exact source t is absent from every V53 state. Recurrent SCCs are "
        "therefore source-free quotient separators, possibly synthesized by "
        "different concrete sources. Acyclicity is useful only when abstract "
        "nodes recur across distinct sources/cohorts."
    ),
    "promotion_boundary": (
        "Even an acyclic bounded graph is not an all-depth theorem: Q2 depth, "
        "rho, centre identity/radius and port transitions remain unbounded. "
        "The next theorem must prove source-coherent eventual W>0 or exit, or "
        "derive cumulative fixed-origin boundary loss in the equivalent M>=0 language."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
