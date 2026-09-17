#!/usr/bin/env python3
"""ACC GS-Sub V20: repeated exact suffix surgery for the one-move residual.

V19 found many verifier-replayed local detours for ac-04501 with optimistic
physical lower bounds as low as 453 against the live record 464, but every
candidate died when handed back to the rigid frozen-baseline suffix compiler.
The failure repeated immediately after rejoin: a single local repair was not
enough to preserve a cheap physical representative through the next obstacle.

V20 changes only that verified boundary.  The candidate language is unchanged.
After each exact local detour rejoins a later key on the frozen baseline, the
same surgery may be applied again to the remaining suffix, for a small bounded
number of rounds.  Every local edge is replayed through grouped_candidate_edges;
every final candidate still goes through V13's pinned official verifier.
"""

from __future__ import annotations

import math
import os
import time

import solver_v2_gssub as v2
import solver_v13_gssub_exact_prefix as v13
import solver_v14_gssub_grouped_prefix as v14
import solver_v18_gssub_baseline_suffix_reuse as v18  # noqa: F401
import solver_v19_gssub_local_suffix_surgery as v19  # noqa: F401


_original_compile_seeded_suffix = v19._original_compile_seeded_suffix


def _collect_local_hits(
    core,
    ns,
    seed_state,
    seed_path,
    seed_cost,
    suffix_path,
    total_cap,
    *,
    ceiling_exclusive,
    deadline,
):
    qsteps = len(suffix_path) - 1
    if qsteps <= 0:
        return [], {
            "code": "no_suffix",
            "generated": 0,
            "layers": [],
            "best_lb": None,
        }

    max_depth = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_DEPTH", "3")))
    local_beam = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_BEAM", "32")))
    exact_per_key = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_EXACT_PER_KEY", "2")))
    qcap = max(2, int(os.environ.get("ACC_SUFFIX_SURGERY_QCAP", str(total_cap + 1))))

    baseline_latest = {}
    for i, qstate in enumerate(suffix_path):
        baseline_latest[v2.path_state_key(ns, qstate)] = i

    frontier = [(seed_state, tuple(seed_path), int(seed_cost))]
    hits = {}
    layers = []
    generated = 0
    bound_prunes = 0

    for depth in range(1, max_depth + 1):
        if time.time() >= deadline:
            break
        best_exact = {}
        raw = 0
        layer_prunes = 0

        for state, path, cost in frontier:
            if time.time() >= deadline:
                break
            for qkey, nxt, edge in v14.grouped_candidate_edges(
                core, ns, state, total_cap, qcap
            ):
                raw += 1
                generated += 1
                nc = cost + len(edge)
                if nc >= ceiling_exclusive:
                    layer_prunes += 1
                    bound_prunes += 1
                    continue

                atomics = path + tuple(edge)
                sig = (qkey, nxt)
                prev = best_exact.get(sig)
                if prev is None or nc < prev[0]:
                    best_exact[sig] = (nc, atomics, nxt, qkey)

                j = baseline_latest.get(qkey)
                if j is not None and j > 0:
                    lb = nc + (qsteps - j)
                    hsig = (j, nxt)
                    old = hits.get(hsig)
                    if old is None or nc < old["cost"]:
                        hits[hsig] = {
                            "state": nxt,
                            "path": atomics,
                            "cost": int(nc),
                            "rejoin_index": int(j),
                            "lower_bound": int(lb),
                            "depth": int(depth),
                            "total": v2.total_len(nxt),
                        }

        if not best_exact:
            layers.append({
                "depth": depth,
                "raw": raw,
                "distinct_exact": 0,
                "beam": 0,
                "hits": len(hits),
                "bound_prunes": layer_prunes,
            })
            break

        kept = v19._rank_local_pool(
            best_exact, baseline_latest, qsteps, depth, local_beam, exact_per_key
        )
        frontier = [(nxt, atomics, nc) for _score, nc, nxt, atomics, _qkey in kept]
        layers.append({
            "depth": depth,
            "raw": raw,
            "distinct_exact": len(best_exact),
            "beam": len(frontier),
            "hits": len(hits),
            "best_hit_lb": min((h["lower_bound"] for h in hits.values()), default=None),
            "best_cost": min((x[2] for x in frontier), default=None),
            "bound_prunes": layer_prunes,
        })

    ranked = sorted(
        hits.values(),
        key=lambda h: (
            h["lower_bound"], -h["rejoin_index"], h["cost"], h["total"], h["depth"]
        ),
    )
    return ranked, {
        "code": "time_cap" if time.time() >= deadline else "ok",
        "depth": max_depth,
        "beam": local_beam,
        "generated": generated,
        "bound_prunes": bound_prunes,
        "hits": len(ranked),
        "competitive_hits": sum(1 for h in ranked if h["lower_bound"] < ceiling_exclusive),
        "best_lb": ranked[0]["lower_bound"] if ranked else None,
        "layers": layers,
    }


def _recursive_compile(
    core,
    ns,
    seed_state,
    seed_path,
    seed_cost,
    suffix_path,
    reverse_paths,
    total_cap,
    *,
    ceiling_exclusive,
    beam_width,
    deadline,
    label,
    rounds_left,
    round_index,
):
    remaining = deadline - time.time()
    if remaining < 1.0:
        return None, {
            "code": "time_cap",
            "label": label,
            "recursive_surgery": True,
            "round": round_index,
            "rounds_left": rounds_left,
        }

    direct, direct_meta = _original_compile_seeded_suffix(
        core,
        ns,
        seed_state,
        seed_path,
        seed_cost,
        suffix_path,
        reverse_paths,
        total_cap,
        ceiling_exclusive=ceiling_exclusive,
        beam_width=beam_width,
        seconds=remaining,
        label=f"{label}-direct-r{round_index}",
    )
    if direct is not None:
        meta = dict(direct_meta)
        meta.update({
            "recursive_surgery": round_index > 0,
            "recursive_surgery_code": "ok",
            "recursive_surgery_rounds_used": round_index,
        })
        return direct, meta

    if rounds_left <= 0 or len(suffix_path) <= 1:
        meta = dict(direct_meta)
        meta.update({
            "recursive_surgery": round_index > 0,
            "recursive_surgery_code": "round_limit",
            "recursive_surgery_rounds_used": round_index,
        })
        return None, meta

    ranked_hits, search_meta = _collect_local_hits(
        core,
        ns,
        seed_state,
        seed_path,
        seed_cost,
        suffix_path,
        total_cap,
        ceiling_exclusive=ceiling_exclusive,
        deadline=deadline,
    )
    competitive = [h for h in ranked_hits if h["lower_bound"] < ceiling_exclusive]
    hit_cap = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_HIT_CAP", "6")))
    attempts = []

    for rank, hit in enumerate(competitive[:hit_cap], 1):
        remaining = deadline - time.time()
        if remaining < 2.0:
            break
        k = int(hit["rejoin_index"])
        if k <= 0 or k >= len(suffix_path):
            continue

        # Share the remaining wall-clock budget across the best few physical
        # rejoins instead of letting a single recursive branch monopolize it.
        slots = max(1, min(3, hit_cap - rank + 1))
        child_seconds = max(2.0, remaining / slots)
        child_deadline = min(deadline, time.time() + child_seconds)

        cand, cm = _recursive_compile(
            core,
            ns,
            hit["state"],
            hit["path"],
            hit["cost"],
            suffix_path[k:],
            reverse_paths,
            total_cap,
            ceiling_exclusive=ceiling_exclusive,
            beam_width=beam_width,
            deadline=child_deadline,
            label=f"{label}-r{round_index + 1}-h{rank}-k{k}",
            rounds_left=rounds_left - 1,
            round_index=round_index + 1,
        )
        attempts.append({
            "rank": rank,
            "rejoin_index": k,
            "local_depth": hit["depth"],
            "local_cost": hit["cost"],
            "optimistic_final_lb": hit["lower_bound"],
            "child_code": cm.get("code"),
            "child_recursive_code": cm.get("recursive_surgery_code"),
            "child_rounds_used": cm.get("recursive_surgery_rounds_used"),
        })
        if cand is not None:
            meta = dict(cm)
            meta.update({
                "recursive_surgery": True,
                "recursive_surgery_code": "ok",
                "recursive_surgery_rounds_used": max(
                    int(meta.get("recursive_surgery_rounds_used", 0)), round_index + 1
                ) if False else int(cm.get("recursive_surgery_rounds_used", round_index + 1)),
                "recursive_surgery_parent_round": round_index,
                "recursive_surgery_rejoin_index": k,
                "recursive_surgery_local_depth": hit["depth"],
                "recursive_surgery_local_cost": hit["cost"],
                "recursive_surgery_optimistic_final_lb": hit["lower_bound"],
                "recursive_surgery_search": search_meta,
                "recursive_surgery_attempts": attempts,
                "direct_failure": direct_meta,
            })
            return cand, meta

    meta = dict(direct_meta)
    meta.update({
        "recursive_surgery": True,
        "recursive_surgery_code": (
            "time_cap" if time.time() >= deadline else "no_recursive_steal"
        ),
        "recursive_surgery_rounds_used": round_index,
        "recursive_surgery_rounds_left": rounds_left,
        "recursive_surgery_search": search_meta,
        "recursive_surgery_attempts": attempts,
        "recursive_surgery_best_lb": (
            competitive[0]["lower_bound"] if competitive else math.inf
        ),
    })
    return None, meta


def recursive_suffix_surgery_compile(
    core,
    ns,
    seed_state,
    seed_path,
    seed_cost,
    suffix_path,
    reverse_paths,
    total_cap,
    *,
    ceiling_exclusive,
    beam_width,
    seconds,
    label,
):
    rounds = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_ROUNDS", "2")))
    deadline = time.time() + max(1.0, float(seconds))
    return _recursive_compile(
        core,
        ns,
        seed_state,
        seed_path,
        seed_cost,
        suffix_path,
        reverse_paths,
        total_cap,
        ceiling_exclusive=ceiling_exclusive,
        beam_width=beam_width,
        deadline=deadline,
        label=label,
        rounds_left=rounds,
        round_index=0,
    )


v13.compile_seeded_suffix = recursive_suffix_surgery_compile

if __name__ == "__main__":
    v13.main()
