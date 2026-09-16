#!/usr/bin/env python3
"""ACC GS-Sub V6: true-carry atomic search with goal-progress guidance.

V5 closed the implementation mismatch at the compiler boundary: source cyclic
and inverse symmetry is retained across quotient transitions and every edge is
replayed through the pinned official move semantics.  The V5 residual is now
search-order diffusion: millions of exact representatives and tens of millions
of compiled edges are generated while uniform-cost search pops only ~42k states
in 9000 seconds, with no terminal hit and no live-bound pruning.

V6 changes only that justified boundary.  Exact official atomic cost remains the
path cost used for dominance, representative retention, strict-live pruning and
final admission.  The priority queue additionally uses current total relator
length as a non-authoritative goal-progress heuristic:

    priority = atomic_cost + guide_weight * max(total_relator_length - 2, 0)

The compiler, GS-Sub proposal language, pins, reverse atlas, strict live bound,
and final pinned-verifier replay are unchanged.
"""

from __future__ import annotations

import heapq
import os
import time

import solver_v5_gssub_atomic_carry as v5

v4 = v5.v4
v2 = v4.v2

GUIDE_WEIGHT = float(os.environ.get("ACC_ATOMIC_GUIDE_WEIGHT", "4"))


def _priority(g, state):
    return float(g) + GUIDE_WEIGHT * max(0, v2.total_len(state) - 2)


def guided_representative_atomic_search(
    core,
    ns,
    initial,
    reverse_paths,
    *,
    strict_bound,
    max_nodes,
    quotient_total_cap,
    total_cap,
    reps_per_key,
    seconds,
):
    """Best-first exact-representative search with exact atomic-cost authority.

    The heuristic affects expansion order only.  All correctness/admission
    conditions continue to use exact official move count and exact replay.
    """
    start = time.time()
    counter = 0
    initial_key = v2.gssub_key(ns, initial)
    initial_total = v2.total_len(initial)
    pq = [(_priority(0, initial), 0, initial_total, counter, initial)]
    best_g = {initial: 0}
    parent = {initial: None}
    parent_edge = {}
    reps = {initial_key: {initial: 0}}

    nodes = 0
    quotient_keys_seen = {initial_key}
    transitions = 0
    compiled_edges = 0
    rep_prunes = 0
    exact_prunes = 0
    bound_prunes = 0
    max_frontier = 1
    min_total_popped = initial_total
    min_total_generated = initial_total
    min_g_at_min_total = 0

    while pq and nodes < max_nodes and time.time() - start < seconds:
        _f, g, _tot, _serial, state = heapq.heappop(pq)
        if best_g.get(state) != g:
            continue
        qkey = v2.gssub_key(ns, state)
        bucket = reps.get(qkey)
        if bucket is None or bucket.get(state) != g:
            continue
        if g >= strict_bound:
            bound_prunes += 1
            continue

        nodes += 1
        stot = v2.total_len(state)
        if stot < min_total_popped:
            min_total_popped = stot
            min_g_at_min_total = g

        suffix = reverse_paths.get(state)
        if suffix is not None and g + len(suffix) < strict_bound:
            prefix = v4.reconstruct(parent, parent_edge, state)
            return prefix + tuple(suffix), {
                "code": "strict_candidate",
                "guide_weight": GUIDE_WEIGHT,
                "nodes": nodes,
                "atomic_cost": g + len(suffix),
                "prefix_cost": g,
                "suffix_cost": len(suffix),
                "quotient_keys_seen": len(quotient_keys_seen),
                "exact_states_seen": len(best_g),
                "transitions": transitions,
                "compiled_edges": compiled_edges,
                "representative_prunes": rep_prunes,
                "exact_prunes": exact_prunes,
                "bound_prunes": bound_prunes,
                "max_frontier": max_frontier,
                "min_total_popped": min_total_popped,
                "min_total_generated": min_total_generated,
                "min_g_at_min_total": min_g_at_min_total,
                "seconds": round(time.time() - start, 3),
            }

        desired_keys = v4.quotient_neighbor_keys(ns, state, quotient_total_cap)
        transitions += len(desired_keys)
        grouped = v4.compiled_superneighbors_grouped(
            core, ns, state, desired_keys, total_cap
        )
        for desired in sorted(desired_keys):
            cands = grouped.get(desired, ())
            compiled_edges += len(cands)

            for nxt, edge in cands:
                ng = g + len(edge)
                if ng >= strict_bound:
                    bound_prunes += 1
                    continue
                if ng >= best_g.get(nxt, 10**18):
                    exact_prunes += 1
                    continue

                ntot = v2.total_len(nxt)
                min_total_generated = min(min_total_generated, ntot)
                nq = v2.gssub_key(ns, nxt)
                nb = reps.setdefault(nq, {})
                old = nb.get(nxt)
                if old is None and len(nb) >= reps_per_key:
                    worst_state, worst_cost = max(
                        nb.items(), key=lambda kv: (kv[1], v2.total_len(kv[0]))
                    )
                    if ng >= worst_cost:
                        rep_prunes += 1
                        continue
                    del nb[worst_state]
                    rep_prunes += 1

                best_g[nxt] = ng
                nb[nxt] = ng
                parent[nxt] = state
                parent_edge[nxt] = tuple(edge)
                quotient_keys_seen.add(nq)
                counter += 1
                heapq.heappush(
                    pq,
                    (_priority(ng, nxt), ng, ntot, counter, nxt),
                )
                max_frontier = max(max_frontier, len(pq))

    reason = (
        "node_cap"
        if nodes >= max_nodes
        else "time_cap"
        if time.time() - start >= seconds
        else "frontier_exhausted"
    )
    return None, {
        "code": reason,
        "guide_weight": GUIDE_WEIGHT,
        "nodes": nodes,
        "quotient_keys_seen": len(quotient_keys_seen),
        "exact_states_seen": len(best_g),
        "transitions": transitions,
        "compiled_edges": compiled_edges,
        "representative_prunes": rep_prunes,
        "exact_prunes": exact_prunes,
        "bound_prunes": bound_prunes,
        "max_frontier": max_frontier,
        "min_total_popped": min_total_popped,
        "min_total_generated": min_total_generated,
        "min_g_at_min_total": min_g_at_min_total,
        "seconds": round(time.time() - start, 3),
    }


# V5 has already installed the true-carry grouped compiler into v4. Replace
# only the expansion policy.
v4.representative_atomic_search = guided_representative_atomic_search


if __name__ == "__main__":
    v4.main()
