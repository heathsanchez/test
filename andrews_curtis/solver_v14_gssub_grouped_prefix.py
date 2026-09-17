#!/usr/bin/env python3
"""ACC GS-Sub V14: grouped exact-prefix generation.

V13 established the right state variable (the carried exact representative),
but its prefix search timed out at depth 2--3 because it enumerated every
quotient neighbor and then reran the full exact compiler for each desired key.
That repeatedly recomputed the same orientation cross-products.

V14 changes only that verified residual.  For each retained exact state it
enumerates the V3 carry-symmetry/compiler candidate space once, buckets the
results by their quotient key, and then performs the same V13 beam selection.
The candidate language is unchanged: V2 signed/restored representatives and V3
carried source representatives are both present; V2 legacy fallback is added
only for quotient keys not covered by that language.  Every local edge is
replayed through the pinned official transition function before admission.

Suffix completion, live-bound exact compilation, pinned final verification,
near-miss salvage, quota checks and strict-only publication remain V13/workflow
authority.
"""

from __future__ import annotations

import time

import solver_v2_gssub as v2
import solver_v13_gssub_exact_prefix as v13


def _replay_exact(core, state, atomics, total_cap):
    cur = state
    for m in atomics:
        cur = core.apply_move(cur, m)
        if v2.total_len(cur) > total_cap:
            return None
    return cur


def grouped_candidate_edges(core, ns, state, total_cap, qcap):
    """Enumerate V9/V3 exact candidates once, grouped implicitly by qkey."""
    # nxt -> (qkey, shortest exact edge)
    best = {}

    def admit(nxt, atomics):
        if v2.total_len(nxt) > total_cap:
            return
        edge = tuple(atomics)
        chk = _replay_exact(core, state, edge, total_cap)
        if chk != nxt:
            raise RuntimeError("grouped exact edge replay mismatch")
        qkey = v2.gssub_key(ns, nxt)
        if len(qkey[0]) + len(qkey[1]) >= qcap:
            return
        prev = best.get(nxt)
        if prev is None or len(edge) < len(prev[1]):
            best[nxt] = (qkey, edge)

    # Cache the four physical orientation orbits once per exact state.
    orient = {
        (0, True): v2.orientation_options(core, state[0], 0),
        (1, True): v2.orientation_options(core, state[1], 1),
        (0, False): v2.orientation_options_no_invert(core, state[0], 0),
        (1, False): v2.orientation_options_no_invert(core, state[1], 1),
    }

    for i in (0, 1):
        j = 1 - i
        target_opts = orient[(i, True)]
        mul_pos = 2 if i == 0 else 4
        mul_neg = 3 if i == 0 else 5

        # V3 carry representatives: source rotations/inversions remain carried.
        for tw, tseq in target_opts:
            if not tw:
                continue
            for sw, sseq in orient[(j, True)]:
                if not sw:
                    continue
                for source_word, mul in ((sw, mul_pos), (core.invert(sw), mul_neg)):
                    if tw[-1] != -source_word[0]:
                        continue
                    new_word = core.free_reduce(tw + source_word)
                    nxt = (new_word, sw) if i == 0 else (sw, new_word)
                    admit(nxt, tuple(tseq) + tuple(sseq) + (mul,))

        # V2 signed/restored representatives: keep untouched source byte-exact.
        for tw, tseq in target_opts:
            if not tw:
                continue
            for sw, sseq in orient[(j, False)]:
                if not sw:
                    continue
                undo = tuple(core.INVERSE_MOVE[m] for m in reversed(sseq))
                for source_word, mul in ((sw, mul_pos), (core.invert(sw), mul_neg)):
                    if tw[-1] != -source_word[0]:
                        continue
                    new_word = core.free_reduce(tw + source_word)
                    nxt = (new_word, state[1]) if i == 0 else (state[0], new_word)
                    admit(nxt, tuple(tseq) + tuple(sseq) + (mul,) + undo)

    # Match V9's coverage fallback exactly: only quotient keys for which the
    # carry/signed language produced no candidate receive the legacy edge.
    covered = {qkey for qkey, _edge in best.values()}
    for qkey, (nxt, edge) in v2.compiled_superneighbors(core, ns, state, total_cap).items():
        if qkey in covered or len(qkey[0]) + len(qkey[1]) >= qcap:
            continue
        admit(nxt, edge)

    return [(qkey, nxt, edge) for nxt, (qkey, edge) in best.items()]


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
    """V13 beam policy with one grouped compiler enumeration per exact state."""
    start = time.time()
    frontier = [(exact_initial, (), 0)]
    layers = []
    generated = 0
    replayed_candidates = 0
    bound_prunes = 0
    grouped_states = 0

    for depth in range(1, target_depth + 1):
        if time.time() - start >= seconds:
            return [], {
                "code": "time_cap", "depth_reached": depth - 1,
                "generated": generated, "replayed_candidates": replayed_candidates,
                "grouped_states": grouped_states, "bound_prunes": bound_prunes,
                "layers": layers, "seconds": round(time.time() - start, 3),
            }

        best_exact = {}
        distinct_neighbor_keys = set()
        raw_grouped = 0
        for state, path, cost in frontier:
            if time.time() - start >= seconds:
                break
            grouped_states += 1
            edges = grouped_candidate_edges(core, ns, state, total_cap, qcap)
            raw_grouped += len(edges)
            replayed_candidates += len(edges)
            for qkey, nxt, edge in edges:
                distinct_neighbor_keys.add(qkey)
                nc = cost + len(edge)
                generated += 1
                if nc + (target_depth - depth) >= atomic_ceiling_exclusive:
                    bound_prunes += 1
                    continue
                sig = (qkey, nxt)
                prev = best_exact.get(sig)
                atomics = path + tuple(edge)
                if prev is None or nc < prev[0]:
                    best_exact[sig] = (nc, atomics, nxt, qkey)

        if not best_exact:
            code = "time_cap" if time.time() - start >= seconds else "frontier_exhausted"
            return [], {
                "code": code, "depth_reached": depth - 1,
                "generated": generated, "replayed_candidates": replayed_candidates,
                "grouped_states": grouped_states, "bound_prunes": bound_prunes,
                "layers": layers, "seconds": round(time.time() - start, 3),
            }

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
        kept = pool[: max(1, int(beam_width))]
        frontier = [(nxt, atomics, nc) for _score, nc, nxt, atomics, _qkey in kept]

        layers.append({
            "depth": depth,
            "input_beam": 1 if depth == 1 else layers[-1]["beam"],
            "grouped_edges": raw_grouped,
            "distinct_neighbor_keys": len(distinct_neighbor_keys),
            "distinct_exact": len(best_exact),
            "distinct_quotient": len(per_key),
            "pool": len(pool),
            "beam": len(frontier),
            "best_atomic_cost": min(x[2] for x in frontier),
            "best_excess": min(x[2] - depth for x in frontier),
            "best_total": min(v2.total_len(x[0]) for x in frontier),
        })

    finals = []
    for state, atomics, cost in frontier:
        qkey = v2.gssub_key(ns, state)
        excess = cost - target_depth
        score = v2.total_len(state) + overhead_weight * excess
        finals.append({
            "state": state, "path": atomics, "cost": int(cost),
            "qkey": qkey, "score": float(score),
            "total": v2.total_len(state), "excess": int(excess),
        })
    finals.sort(key=lambda x: (x["score"], x["cost"], x["total"], x["qkey"]))
    finals = finals[: max(1, int(prefix_count))]
    return finals, {
        "code": "ok", "depth_reached": target_depth,
        "generated": generated, "replayed_candidates": replayed_candidates,
        "grouped_states": grouped_states, "bound_prunes": bound_prunes,
        "layers": layers, "prefixes": len(finals),
        "best_prefix_cost": finals[0]["cost"] if finals else None,
        "best_prefix_excess": finals[0]["excess"] if finals else None,
        "seconds": round(time.time() - start, 3),
    }


# Keep V13's complete suffix/compiler/verifier/reporting path unchanged.
v13.exact_prefix_search = exact_prefix_search

if __name__ == "__main__":
    v13.main()
