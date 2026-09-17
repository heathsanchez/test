#!/usr/bin/env python3
"""ACC GS-Sub V19: bounded local suffix surgery around the one-move residual.

V18 removed the fresh-ACSolverX suffix handoff as a confounder.  With the exact
stored baseline suffix, ac-04501 still reaches an official-move lower bound of
464 against the live record 464, with strict compilation dying in steps 3--4.
That closes fixed-baseline continuation as a strict-steal route.

V19 changes only the justified boundary: before accepting that fixed suffix, it
allows a short exact detour in the unchanged V14/V9 candidate language and
looks for a second rejoin to a later key on the frozen baseline.  Every local
edge is replayed by grouped_candidate_edges.  Rejoined states are then handed
back to the unchanged V13 live-bound compiler and pinned final verifier.  The
search/compiler language, near-miss path, quota gate and strict-only publisher
remain unchanged.
"""

from __future__ import annotations

import math
import os
import time

import solver_v2_gssub as v2
import solver_v13_gssub_exact_prefix as v13
import solver_v14_gssub_grouped_prefix as v14
import solver_v18_gssub_baseline_suffix_reuse as v18  # noqa: F401  (installs V18 patches)


_original_compile_seeded_suffix = v13.compile_seeded_suffix


def _rank_local_pool(best_exact, baseline_latest, qsteps, depth, beam_width, exact_per_key):
    per_key = {}
    for nc, atomics, nxt, qkey in best_exact.values():
        j = baseline_latest.get(qkey)
        if j is not None and j > 0:
            # Prefer exact states that have already reached a later baseline key,
            # ranked by their admissible final lower bound.
            score = (0, nc + (qsteps - j), -j, nc, v2.total_len(nxt))
        else:
            # Preserve a compact diversity beam for genuine off-route detours.
            excess = nc - depth
            score = (1, excess, v2.total_len(nxt), nc, qkey)
        per_key.setdefault(qkey, []).append((score, nc, nxt, atomics, qkey))

    pool = []
    for vals in per_key.values():
        vals.sort(key=lambda x: x[0])
        pool.extend(vals[: max(1, int(exact_per_key))])
    pool.sort(key=lambda x: x[0])
    return pool[: max(1, int(beam_width))]


def local_suffix_surgery_compile(
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
    """Try the exact frozen suffix, then a bounded off-route double rejoin."""
    start = time.time()

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
        seconds=seconds,
        label=label,
    )
    if direct is not None:
        meta = dict(direct_meta)
        meta.update({"suffix_surgery": False, "suffix_surgery_reason": "direct_ok"})
        return direct, meta

    qsteps = len(suffix_path) - 1
    if qsteps <= 0:
        meta = dict(direct_meta)
        meta.update({"suffix_surgery": False, "suffix_surgery_reason": "no_suffix"})
        return direct, meta

    max_depth = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_DEPTH", "6")))
    local_beam = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_BEAM", "64")))
    exact_per_key = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_EXACT_PER_KEY", "2")))
    hit_cap = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_HIT_CAP", "16")))
    qcap = max(2, int(os.environ.get("ACC_SUFFIX_SURGERY_QCAP", str(total_cap + 1))))

    baseline_latest = {}
    for i, qstate in enumerate(suffix_path):
        baseline_latest[v2.path_state_key(ns, qstate)] = i

    # state, full atomic path from the original problem, exact accumulated cost
    frontier = [(seed_state, tuple(seed_path), int(seed_cost))]
    hits = {}
    layers = []
    generated = 0
    bound_prunes = 0

    for depth in range(1, max_depth + 1):
        if time.time() - start >= seconds:
            break
        best_exact = {}
        raw = 0
        layer_prunes = 0

        for state, path, cost in frontier:
            if time.time() - start >= seconds:
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
                    hprev = hits.get(hsig)
                    if hprev is None or nc < hprev["cost"]:
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

        kept = _rank_local_pool(
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

    ranked_hits = sorted(
        hits.values(),
        key=lambda h: (
            h["lower_bound"], -h["rejoin_index"], h["cost"], h["total"], h["depth"]
        ),
    )
    competitive_hits = [h for h in ranked_hits if h["lower_bound"] < ceiling_exclusive]

    attempts = []
    for rank, hit in enumerate(competitive_hits[:hit_cap], 1):
        elapsed = time.time() - start
        remaining_seconds = max(0.0, seconds - elapsed)
        if remaining_seconds < 1.0:
            break
        k = hit["rejoin_index"]
        cand, cm = _original_compile_seeded_suffix(
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
            seconds=remaining_seconds,
            label=f"{label}-surgery-{rank}-k{k}",
        )
        attempts.append({
            "rank": rank,
            "rejoin_index": k,
            "local_depth": hit["depth"],
            "local_cost": hit["cost"],
            "optimistic_final_lb": hit["lower_bound"],
            "compile_code": cm.get("code"),
            "compile_atomic_cost": cm.get("atomic_cost"),
            "compile_step": cm.get("step"),
            "compile_min_raw_lower_bound": cm.get("min_raw_lower_bound"),
        })
        if cand is not None:
            meta = dict(cm)
            meta.update({
                "suffix_surgery": True,
                "suffix_surgery_code": "ok",
                "suffix_surgery_rejoin_index": k,
                "suffix_surgery_local_depth": hit["depth"],
                "suffix_surgery_local_cost": hit["cost"],
                "suffix_surgery_optimistic_final_lb": hit["lower_bound"],
                "suffix_surgery_generated": generated,
                "suffix_surgery_hits": len(ranked_hits),
                "suffix_surgery_competitive_hits": len(competitive_hits),
                "suffix_surgery_attempts": attempts,
                "suffix_surgery_layers": layers,
                "suffix_surgery_seconds": round(time.time() - start, 3),
                "direct_failure": direct_meta,
            })
            return cand, meta

    meta = dict(direct_meta)
    meta.update({
        "suffix_surgery": True,
        "suffix_surgery_code": (
            "time_cap" if time.time() - start >= seconds else "no_compiled_steal"
        ),
        "suffix_surgery_depth": max_depth,
        "suffix_surgery_beam": local_beam,
        "suffix_surgery_generated": generated,
        "suffix_surgery_bound_prunes": bound_prunes,
        "suffix_surgery_hits": len(ranked_hits),
        "suffix_surgery_competitive_hits": len(competitive_hits),
        "suffix_surgery_best_lb": (
            ranked_hits[0]["lower_bound"] if ranked_hits else math.inf
        ),
        "suffix_surgery_attempts": attempts,
        "suffix_surgery_layers": layers,
        "suffix_surgery_seconds": round(time.time() - start, 3),
    })
    return None, meta


# V18 remains authoritative for prefix/rejoin selection and exact frozen suffixes.
# Only V13's suffix compiler receives the bounded local-detour wrapper.
v13.compile_seeded_suffix = local_suffix_surgery_compile

if __name__ == "__main__":
    v13.main()
