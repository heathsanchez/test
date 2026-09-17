#!/usr/bin/env python3
"""ACC GS-Sub V15: exact low-overhead detours that rejoin a short quotient route.

V14 established two facts at once: grouped carried-prefix search can preserve
zero compiler excess for 10--16 quotient steps, but locally attractive prefixes
still consume the strict record slack because their eventual quotient suffixes
make little useful progress.  The residual is therefore goal progress inside
an exact low-overhead corridor, not another compiler-language change.

V15 keeps V14's exact grouped edge language and official-move replay unchanged.
It first obtains the ordinary ACSolverX short quotient route from the initial
state, then searches exact carried detours and records every state that rejoins
that route later.  Rejoin candidates are ranked by the physically meaningful
optimistic bound

    exact_prefix_cost + remaining_baseline_quotient_steps.

Only the search policy changes.  V13's seeded exact suffix compiler, pinned
verifier replay, near-miss handling, fresh live checks and strict-only
publication remain authoritative.
"""

from __future__ import annotations

import time

import solver_v2_gssub as v2
import solver_v13_gssub_exact_prefix as v13
import solver_v14_gssub_grouped_prefix as v14


def exact_prefix_search(
    core,
    ns,
    exact_initial,
    *,
    target_depth,
    beam_width,
    exact_per_key,
    prefix_count,
    qcap,
    total_cap,
    overhead_weight,
    atomic_ceiling_exclusive,
    seconds,
):
    """Search exact detours and retain the best later baseline rejoins."""
    start = time.time()
    initial_key = v2.gssub_key(ns, exact_initial)
    baseline_path, baseline_nodes, baseline_seconds = v13.complete_suffix(
        ns, initial_key, max_nodes=100000, max_len=qcap
    )
    if baseline_path is None:
        # A missing baseline route is an implementation/search residual, not a
        # reason to widen the compiler.  Fall back to V14 exactly.
        finals, meta = v14.exact_prefix_search(
            core, ns, exact_initial,
            target_depth=target_depth,
            beam_width=beam_width,
            exact_per_key=exact_per_key,
            prefix_count=prefix_count,
            qcap=qcap,
            total_cap=total_cap,
            overhead_weight=overhead_weight,
            atomic_ceiling_exclusive=atomic_ceiling_exclusive,
            seconds=max(1.0, seconds - (time.time() - start)),
        )
        meta = dict(meta)
        meta.update({
            "baseline_code": "not_found",
            "baseline_nodes": baseline_nodes,
            "baseline_seconds": baseline_seconds,
        })
        return finals, meta

    baseline_keys = [v2.path_state_key(ns, s) for s in baseline_path]
    baseline_steps = len(baseline_keys) - 1
    # If a quotient key occurs more than once, the latest occurrence has the
    # shortest remaining suffix and is the competitive rejoin point.
    latest_index = {}
    for i, key in enumerate(baseline_keys):
        latest_index[key] = i

    frontier = [(exact_initial, (), 0)]
    layers = []
    generated = 0
    replayed_candidates = 0
    bound_prunes = 0
    grouped_states = 0
    bridge_events = 0
    bridges = {}

    for depth in range(1, target_depth + 1):
        if time.time() - start >= seconds:
            break

        best_exact = {}
        distinct_neighbor_keys = set()
        raw_grouped = 0
        for state, path, cost in frontier:
            if time.time() - start >= seconds:
                break
            grouped_states += 1
            edges = v14.grouped_candidate_edges(core, ns, state, total_cap, qcap)
            raw_grouped += len(edges)
            replayed_candidates += len(edges)
            for qkey, nxt, edge in edges:
                distinct_neighbor_keys.add(qkey)
                nc = cost + len(edge)
                generated += 1
                if nc + (target_depth - depth) >= atomic_ceiling_exclusive:
                    bound_prunes += 1
                    continue
                atomics = path + tuple(edge)
                sig = (qkey, nxt)
                prev = best_exact.get(sig)
                if prev is None or nc < prev[0]:
                    best_exact[sig] = (nc, atomics, nxt, qkey)

                j = latest_index.get(qkey)
                if j is not None and j > 0:
                    bridge_events += 1
                    optimistic = nc + (baseline_steps - j)
                    bprev = bridges.get(sig)
                    item = {
                        "state": nxt,
                        "path": atomics,
                        "cost": int(nc),
                        "qkey": qkey,
                        "score": float(optimistic),
                        "total": v2.total_len(nxt),
                        "excess": int(nc - depth),
                        "depth": int(depth),
                        "rejoin_index": int(j),
                        "baseline_steps": int(baseline_steps),
                        "baseline_remaining": int(baseline_steps - j),
                        "optimistic_baseline_cost": int(optimistic),
                    }
                    if bprev is None or (
                        optimistic, nc, -j, item["total"]
                    ) < (
                        bprev["optimistic_baseline_cost"], bprev["cost"],
                        -bprev["rejoin_index"], bprev["total"]
                    ):
                        bridges[sig] = item

        if not best_exact:
            break

        # Keep V14's verified beam policy.  The new baseline signal is used to
        # select competitive rejoins, not to distort the exact edge language.
        per_key = {}
        for nc, atomics, nxt, qkey in best_exact.values():
            excess = nc - depth
            score = v2.total_len(nxt) + overhead_weight * excess
            per_key.setdefault(qkey, []).append((score, nc, nxt, atomics, qkey))

        pool = []
        for vals in per_key.values():
            vals.sort(key=lambda x: (x[0], x[1], v2.total_len(x[2]), x[4]))
            pool.extend(vals[: max(1, int(exact_per_key))])
        pool.sort(key=lambda x: (x[0], x[1], v2.total_len(x[2]), x[4]))

        # Reserve a small slice for best baseline-rejoin states seen in this
        # layer so a successful bridge can continue if a still later rejoin is
        # cheaper; the remaining beam is the unchanged local V14 ranking.
        reserve = max(1, int(beam_width) // 8)
        on_route = []
        off_route = []
        for x in pool:
            _score, nc, nxt, atomics, qkey = x
            j = latest_index.get(qkey)
            if j is not None and j > 0:
                optimistic = nc + (baseline_steps - j)
                on_route.append((optimistic, nc, -j, x))
            else:
                off_route.append(x)
        on_route.sort(key=lambda z: (z[0], z[1], z[2], z[3][0]))
        selected = [z[3] for z in on_route[:reserve]]
        selected_sigs = {(x[4], x[2]) for x in selected}
        for x in pool:
            if len(selected) >= max(1, int(beam_width)):
                break
            if (x[4], x[2]) in selected_sigs:
                continue
            selected.append(x)
            selected_sigs.add((x[4], x[2]))
        frontier = [(nxt, atomics, nc) for _score, nc, nxt, atomics, _qkey in selected]

        best_bridge = min(
            (b["optimistic_baseline_cost"] for b in bridges.values()),
            default=None,
        )
        max_rejoin = max(
            (b["rejoin_index"] for b in bridges.values()), default=None
        )
        layers.append({
            "depth": depth,
            "beam": len(frontier),
            "grouped_edges": raw_grouped,
            "distinct_neighbor_keys": len(distinct_neighbor_keys),
            "distinct_exact": len(best_exact),
            "distinct_quotient": len(per_key),
            "pool": len(pool),
            "best_atomic_cost": min(x[2] for x in frontier),
            "best_excess": min(x[2] - depth for x in frontier),
            "best_total": min(v2.total_len(x[0]) for x in frontier),
            "bridge_count": len(bridges),
            "best_bridge_optimistic": best_bridge,
            "max_rejoin_index": max_rejoin,
        })

    bridge_list = list(bridges.values())
    bridge_list.sort(key=lambda b: (
        b["optimistic_baseline_cost"], b["excess"],
        -b["rejoin_index"], b["cost"], b["total"], b["qkey"],
    ))
    finals = bridge_list[: max(1, int(prefix_count))]

    # If no later baseline state was reached, return the current V14 frontier
    # rather than fabricate a bridge result.  This still gives the downstream
    # verifier/compiler a valid diagnostic candidate set.
    if not finals and frontier:
        fallback = []
        depth = len(layers)
        for state, atomics, cost in frontier:
            qkey = v2.gssub_key(ns, state)
            excess = cost - depth
            score = v2.total_len(state) + overhead_weight * excess
            fallback.append({
                "state": state, "path": atomics, "cost": int(cost),
                "qkey": qkey, "score": float(score),
                "total": v2.total_len(state), "excess": int(excess),
                "depth": int(depth), "rejoin_index": None,
            })
        fallback.sort(key=lambda x: (
            x["score"], x["cost"], x["total"], x["qkey"]
        ))
        finals = fallback[: max(1, int(prefix_count))]

    return finals, {
        "code": "ok" if finals else "frontier_exhausted",
        "depth_reached": len(layers),
        "generated": generated,
        "replayed_candidates": replayed_candidates,
        "grouped_states": grouped_states,
        "bound_prunes": bound_prunes,
        "layers": layers,
        "prefixes": len(finals),
        "baseline_code": "ok",
        "baseline_steps": baseline_steps,
        "baseline_nodes": baseline_nodes,
        "baseline_seconds": baseline_seconds,
        "bridge_events": bridge_events,
        "distinct_bridges": len(bridges),
        "best_bridge_optimistic": (
            bridge_list[0]["optimistic_baseline_cost"] if bridge_list else None
        ),
        "best_rejoin_index": (
            bridge_list[0]["rejoin_index"] if bridge_list else None
        ),
        "max_rejoin_index": max(
            (b["rejoin_index"] for b in bridge_list), default=None
        ),
        "seconds": round(time.time() - start, 3),
    }


# Reuse the complete V13 suffix/compiler/verifier/reporting path unchanged.
v13.exact_prefix_search = exact_prefix_search

if __name__ == "__main__":
    v13.main()
