#!/usr/bin/env python3
"""Crystal V37: complete the cost-aware chamber by normalizing B presentations.

Scientific target
-----------------
V27 classifies a 12-odd window with raw two-cost >19 as B before checking
whether the same endpoint residue has a cheaper canonical reverse
representation already present in the chamber bank.

This experiment asks the exact semantic question:

  Is B a genuinely new future state, or merely a noncanonical cost-20
  presentation of an existing <=19-cost state?

If every B endpoint residue is already represented, normalize it exactly like
K, obtain a complete 2-edge-per-state finite graph, and test whether V32's
c=19 Bellman potential extends without a negative reduced edge/cycle.

This does NOT by itself prove Collatz.  It is the cheapest one-shot test of the
main finite-graph hole in the ROS ranked-normalization route.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from contextlib import redirect_stdout
import hashlib, io, json, sys

with redirect_stdout(io.StringIO()):
    import collatz_crystal_cost_aware_chamber_v27 as v27
    import collatz_crystal_k_density_tradeoff_v32 as v32

best = v27.best
MOD = v27.MOD
N = len(best)

def canonical_target(raw_word):
    S = sum(raw_word)
    C = v27.cocycle(raw_word)
    r = (C * pow(1 << S, -1, MOD)) % MOD
    if r not in best:
        return None
    bS, bC, bw = best[r]
    if (S, C) == (bS, bC):
        cls = "I"
        drop = 0
    else:
        assert bS < S or (bS == S and bC > C)
        cls = "R"  # canonical rewrite; subsumes old K and any normalized B
        drop = S - bS
        assert drop >= 0
    return r, cls, drop, S, C, bS, bC

full_edges = []
old_class = Counter()
normalized_class = Counter()
b_rows = []
missing_b = []

for u, (_S, _C, w) in sorted(best.items()):
    for bit in (0, 1):
        nw = v27.next_window(w, bit)
        old, old_target = v27.classify_word(nw)
        old_class[(bit, old)] += 1
        z = canonical_target(nw)
        if old == "B":
            assert bit == 0 and sum(nw) == 20
            if z is None:
                missing_b.append((u, bit, nw))
                continue
            v, cls, drop, rawS, rawC, bestS, bestC = z
            b_rows.append({
                "u": u, "v": v, "drop": drop,
                "rawS": rawS, "bestS": bestS,
                "rawC": rawC, "bestC": bestC,
            })
        else:
            assert z is not None
            v, cls, drop, rawS, rawC, bestS, bestC = z
            assert v == old_target
            if old == "I":
                assert cls == "I" and drop == 0
            else:
                assert old == "K" and cls == "R"
        normalized_class[(bit, cls, drop)] += 1
        full_edges.append((u, v, bit, cls, drop))

assert old_class == Counter({
    (0, "B"): 15947,
    (0, "I"): 11422,
    (0, "K"): 100,
    (1, "I"): 23287,
    (1, "K"): 4182,
})

# Full-graph Bellman certificate if B is semantically normalized.
full_graph = len(missing_b) == 0
potential_extension = None
zero_summary = None
cycle_witness = None

if full_graph:
    assert len(full_edges) == 2 * N == 54938

    # First test the already-qualified V32 potential directly.
    old_dist = v32.dist
    neg_old = []
    zero_old = 0
    min_old = 10**9
    for u, v, bit, cls, drop in full_edges:
        w = 19*bit - 12 + 19*drop
        rc = w + old_dist[u] - old_dist[v]
        min_old = min(min_old, rc)
        zero_old += (rc == 0)
        if rc < 0 and len(neg_old) < 100:
            neg_old.append((u, v, bit, cls, drop, rc))

    # Independently recompute a complete Bellman potential.  Starting every
    # node at zero is a zero-cost super-source.
    adj = defaultdict(list)
    for u, v, bit, cls, drop in full_edges:
        adj[u].append((v, bit, cls, drop))

    dist = {v: 0 for v in best}
    q = deque(best)
    inq = set(best)
    relax_count = {v: 0 for v in best}
    relaxations = 0
    negative_cycle = False
    neg_vertex = None

    while q and not negative_cycle:
        u = q.popleft(); inq.discard(u)
        du = dist[u]
        for v, bit, cls, drop in adj[u]:
            wt = 19*bit - 12 + 19*drop
            cand = du + wt
            if cand < dist[v]:
                dist[v] = cand
                relax_count[v] += 1
                relaxations += 1
                if relax_count[v] > N:
                    negative_cycle = True
                    neg_vertex = v
                    break
                if v not in inq:
                    q.append(v); inq.add(v)

    min_rc = None
    neg_rc = []
    zero_edges = []
    if not negative_cycle:
        min_rc = 10**9
        for e in full_edges:
            u, v, bit, cls, drop = e
            wt = 19*bit - 12 + 19*drop
            rc = wt + dist[u] - dist[v]
            min_rc = min(min_rc, rc)
            if rc < 0 and len(neg_rc) < 100:
                neg_rc.append((*e, rc))
            if rc == 0:
                zero_edges.append(e)
        assert not neg_rc
        assert min_rc >= 0

        # Recurrent SCCs of the exact zero-reduced boundary.
        zadj = defaultdict(list)
        for e in zero_edges:
            zadj[e[0]].append(e)

        sys.setrecursionlimit(200000)
        index = {}
        low = {}
        stack = []
        on = set()
        comps = []
        counter = 0

        def strong(x):
            nonlocal counter
            index[x] = low[x] = counter
            counter += 1
            stack.append(x); on.add(x)
            for e in zadj.get(x, ()):
                y = e[1]
                if y not in index:
                    strong(y)
                    low[x] = min(low[x], low[y])
                elif y in on:
                    low[x] = min(low[x], index[y])
            if low[x] == index[x]:
                cc = []
                while True:
                    y = stack.pop(); on.remove(y); cc.append(y)
                    if y == x:
                        break
                comps.append(cc)

        for x in best:
            if x not in index:
                strong(x)

        recurrent = []
        for cc in comps:
            S = set(cc)
            ee = [e for e in zero_edges if e[0] in S and e[1] in S]
            cyc = len(cc) > 1 or any(e[0] == e[1] for e in ee)
            if cyc:
                recurrent.append((cc, ee))

        recurrent.sort(key=lambda z: (-len(z[0]), min(z[0])))
        rows = []
        for cc, ee in recurrent:
            rows.append({
                "states": len(cc),
                "edges": len(ee),
                "odd_steps": sum(e[2] for e in ee),
                "drop_sum": sum(e[4] for e in ee),
                "classes": dict(Counter(e[3] for e in ee)),
                "normalized_B_edges": sum(
                    1 for e in ee
                    if e[3] == "R" and e[2] == 0 and e[4] > 0
                ),
                "sample_states": sorted(cc)[:20],
            })

        zero_summary = {
            "zero_edges": len(zero_edges),
            "recurrent_components": len(recurrent),
            "components": rows[:100],
            "any_normalized_B_on_recurrent_zero_boundary":
                any(r["normalized_B_edges"] for r in rows),
        }

    potential_rows = [[v, dist[v]] for v in sorted(dist)]
    potential_sha = hashlib.sha256(
        json.dumps(potential_rows, separators=(",", ":")).encode()
    ).hexdigest()

    potential_extension = {
        "old_v32_potential_min_reduced_cost": min_old,
        "old_v32_potential_negative_examples": neg_old,
        "old_v32_potential_zero_edges": zero_old,
        "full_recomputed_negative_cycle": negative_cycle,
        "negative_cycle_vertex": neg_vertex,
        "relaxations": relaxations,
        "full_min_reduced_cost": min_rc,
        "potential_sha256": potential_sha,
    }

result = {
    "schema": "COLLATZ_CRYSTAL_BIADIC_RANKED_NORMALIZATION_V37",
    "parents": {
        "V27": "collatz-crystal-cost-aware-chamber-v27",
        "V32": "collatz-crystal-k-density-tradeoff-v32",
        "V36": "collatz-crystal-source-admitted-return-v36@2bc7f481eb0a2ea2130f545d0ba4cd4d5718360d",
    },
    "states": N,
    "old_classification": {
        f"{bit}:{cls}": n for (bit, cls), n in sorted(old_class.items())
    },
    "B_normalization": {
        "old_B_edges": old_class[(0, "B")],
        "normalized_B_edges": len(b_rows),
        "missing_B_targets": len(missing_b),
        "drop_histogram": dict(Counter(r["drop"] for r in b_rows)),
        "best_cost_histogram": dict(Counter(r["bestS"] for r in b_rows)),
        "first_missing": [
            {"u": u, "bit": bit, "word": list(w)}
            for u, bit, w in missing_b[:50]
        ],
        "first_normalized": b_rows[:50],
    },
    "complete_normalized_graph": full_graph,
    "normalized_edges": len(full_edges),
    "normalized_classification": {
        f"{bit}:{cls}:d{drop}": n
        for (bit, cls, drop), n in sorted(normalized_class.items())
    },
    "potential_extension": potential_extension,
    "zero_reduced_boundary": zero_summary,
    "scientific_verdict": (
        "B_IS_NONCANONICAL_PRESENTATION_AND_FULL_GRAPH_NORMALIZES"
        if full_graph
        else "B_HAS_GENUINELY_UNREPRESENTED_ENDPOINT_RESIDUES"
    ),
    "next_residual": (
        "If the complete graph is Bellman-safe, use its zero-reduced recurrent "
        "boundary as the finite semantic quotient and attach the exact "
        "source-admission / bi-adic cell guards.  A rank failure must emit the "
        "first exact natural-compatible recurrent cell."
    ),
    "universal_status": "UNKNOWN",
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
