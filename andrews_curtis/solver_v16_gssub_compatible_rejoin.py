#!/usr/bin/env python3
"""ACC GS-Sub V16: exact carried rejoins ranked by physical suffix compatibility.

V15 found the strongest competitive residual so far on ac-04501: a carried
bridge with optimistic quotient lower bound 449 survived four exact suffix
steps to a raw final lower bound of 464 against a strict live record of 464.
Only one atomic move separates that state from a record steal.  The failure is
therefore not lack of quotient progress or compiler language; it is bridge
selection.  V15 ranked rejoins by quotient position and prefix cost, while the
physical representative can make the next baseline edges materially cheaper or
more expensive.

V16 changes only that justified boundary.  It generates the same V15 bridge
set with the same replayed exact carried-state language, then probes each bridge
for a short exact continuation along the known ACSolverX baseline route.  Rejoin
candidates are ranked by the resulting exact lower bound before the unchanged
V13 strict compiler, pinned official verifier, near-miss salvage and fresh live
publication gate run.
"""

from __future__ import annotations

import math
import os
import time

import solver_v2_gssub as v2
import solver_v9_gssub_skeleton_lookahead as v9
import solver_v13_gssub_exact_prefix as v13
import solver_v14_gssub_grouped_prefix as v14


def compatibility_probe(
    core,
    ns,
    bridge,
    baseline_keys,
    total_cap,
    *,
    lookahead,
    beam_width,
):
    """Exact short-horizon cost of following the baseline from a carried bridge."""
    j = int(bridge["rejoin_index"])
    baseline_steps = len(baseline_keys) - 1
    max_steps = min(max(0, int(lookahead)), baseline_steps - j)
    if max_steps <= 0:
        return {
            "code": "terminal_rejoin",
            "steps": 0,
            "lower_bound": int(bridge["cost"]),
            "best_cost": int(bridge["cost"]),
            "beam": 1,
            "raw_candidates": 0,
        }

    beam = [(bridge["state"], int(bridge["cost"]))]
    raw_total = 0
    layers = []
    for off in range(1, max_steps + 1):
        desired = baseline_keys[j + off]
        by_exact = {}
        raw = 0
        for state, cost in beam:
            for nxt, edge in v9.candidate_edges(core, ns, state, desired, total_cap):
                raw += 1
                raw_total += 1
                nc = cost + len(edge)
                prev = by_exact.get(nxt)
                if prev is None or nc < prev:
                    by_exact[nxt] = nc
        if not by_exact:
            return {
                "code": "dead",
                "steps": off - 1,
                "failed_step": off,
                "lower_bound": math.inf,
                "best_cost": None,
                "beam": 0,
                "raw_candidates": raw_total,
                "layers": layers,
            }
        ranked = sorted(
            ((nc, v2.total_len(nxt), nxt) for nxt, nc in by_exact.items()),
            key=lambda x: (x[0], x[1], x[2]),
        )
        kept = ranked[: max(1, int(beam_width))]
        beam = [(nxt, nc) for nc, _total, nxt in kept]
        remaining = baseline_steps - (j + off)
        layers.append({
            "step": off,
            "raw": raw,
            "distinct_exact": len(by_exact),
            "beam": len(beam),
            "best_cost": min(cost for _state, cost in beam),
            "lower_bound": min(cost for _state, cost in beam) + remaining,
        })

    best_cost = min(cost for _state, cost in beam)
    remaining = baseline_steps - (j + max_steps)
    return {
        "code": "ok",
        "steps": max_steps,
        "lower_bound": int(best_cost + remaining),
        "best_cost": int(best_cost),
        "beam": len(beam),
        "raw_candidates": raw_total,
        "layers": layers,
    }


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
    """V15 bridge generation plus exact physical compatibility screening."""
    start = time.time()
    initial_key = v2.gssub_key(ns, exact_initial)
    baseline_path, baseline_nodes, baseline_seconds = v13.complete_suffix(
        ns, initial_key, max_nodes=100000, max_len=qcap
    )
    if baseline_path is None:
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

        reserve = max(1, int(beam_width) // 8)
        on_route = []
        for x in pool:
            _score, nc, nxt, atomics, qkey = x
            j = latest_index.get(qkey)
            if j is not None and j > 0:
                optimistic = nc + (baseline_steps - j)
                on_route.append((optimistic, nc, -j, x))
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
        max_rejoin = max((b["rejoin_index"] for b in bridges.values()), default=None)
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

    lookahead = max(1, int(os.environ.get("ACC_REJOIN_LOOKAHEAD", "6")))
    probe_beam = max(1, int(os.environ.get("ACC_REJOIN_PROBE_BEAM", "64")))
    probe_cap = max(1, int(os.environ.get("ACC_REJOIN_PROBE_CAP", "0")))
    if probe_cap <= 1:
        probe_cap = len(bridge_list)

    probed = []
    probe_raw = 0
    probe_dead = 0
    probe_start = time.time()
    for b in bridge_list[:probe_cap]:
        pm = compatibility_probe(
            core, ns, b, baseline_keys, total_cap,
            lookahead=lookahead, beam_width=probe_beam,
        )
        probe_raw += int(pm.get("raw_candidates") or 0)
        if pm.get("code") == "dead":
            probe_dead += 1
        item = dict(b)
        item["compatibility_probe"] = pm
        item["compatibility_lb"] = pm.get("lower_bound", math.inf)
        probed.append(item)

    # Unprobed bridges remain available only behind every physically screened
    # bridge.  In the intended focused run probe_cap covers the full bridge set.
    for b in bridge_list[probe_cap:]:
        item = dict(b)
        item["compatibility_probe"] = {"code": "not_probed"}
        item["compatibility_lb"] = math.inf
        probed.append(item)

    probed.sort(key=lambda b: (
        b["compatibility_lb"], b["optimistic_baseline_cost"], b["excess"],
        -b["rejoin_index"], b["cost"], b["total"], b["qkey"],
    ))
    finals = probed[: max(1, int(prefix_count))]

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
        fallback.sort(key=lambda x: (x["score"], x["cost"], x["total"], x["qkey"]))
        finals = fallback[: max(1, int(prefix_count))]

    finite_lbs = [b["compatibility_lb"] for b in probed if math.isfinite(b["compatibility_lb"])]
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
        "max_rejoin_index": max((b["rejoin_index"] for b in bridge_list), default=None),
        "compatibility_lookahead": lookahead,
        "compatibility_probe_beam": probe_beam,
        "compatibility_probed": min(probe_cap, len(bridge_list)),
        "compatibility_probe_raw": probe_raw,
        "compatibility_dead": probe_dead,
        "best_compatibility_lb": min(finite_lbs) if finite_lbs else None,
        "probe_seconds": round(time.time() - probe_start, 3),
        "seconds": round(time.time() - start, 3),
    }


v13.exact_prefix_search = exact_prefix_search

if __name__ == "__main__":
    v13.main()
