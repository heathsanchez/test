#!/usr/bin/env python3
"""ACC GS-Sub V7: excess-cost guided true-carry search.

V6 proved that absolute atomic-cost ordering is the wrong exploration currency
for the current strict-record regime.  Every GS-Sub transition necessarily pays
one official multiplication, so a 392-step quotient route already carries 392
unavoidable atomic moves.  The live records leave only a tiny budget for the
*extra* inversions/conjugations introduced by exact compilation.  Ordering by
raw g therefore strands the search among millions of shallow representatives
before it can reach the deep, low-overhead corridor.

V7 keeps all authorities unchanged (GS-Sub proposal language, V5 true-carry
compiler, exact official replay, pinned verifier, live bound).  It changes only
search order and representative retention to use excess compilation cost:

    excess = atomic_cost - quotient_depth
    priority = excess_weight * excess
             + guide_weight * max(total_relator_length - 2, 0)

Absolute atomic cost still controls dominance, live/near-miss admission and the
final official verifier.  A verifier-clean route up to the configured near-miss
margin is retained for post-mechanism atlas/peephole salvage; only a strict live
improvement may be published by the controller.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path

import solver_v5_gssub_atomic_carry as v5

v4 = v5.v4
v2 = v4.v2
TARGET = v2.TARGET


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--snapshot-ac-file", required=True)
    p.add_argument("--max-nodes", type=int, default=500000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--representatives-per-quotient", type=int, default=24)
    p.add_argument("--search-seconds", type=int, default=2400)
    p.add_argument("--excess-weight", type=float, default=32.0)
    p.add_argument("--guide-weight", type=float, default=1.0)
    p.add_argument("--near-miss-frac", type=float, default=0.10)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def priority(g, depth, state, excess_weight, guide_weight):
    excess = max(0, g - depth)
    # The tiny raw-g tie breaker keeps deterministic progress without restoring
    # V6's shallow-state bias.
    return (
        excess_weight * excess
        + guide_weight * max(0, v2.total_len(state) - 2)
        + 0.001 * g
    )


def excess_guided_search(
    core,
    ns,
    initial,
    reverse_paths,
    *,
    live_best,
    near_miss_frac,
    max_nodes,
    quotient_total_cap,
    total_cap,
    reps_per_key,
    seconds,
    excess_weight,
    guide_weight,
):
    start = time.time()
    counter = 0
    initial_key = v2.gssub_key(ns, initial)
    initial_total = v2.total_len(initial)

    # Candidate lengths strictly below this integer are worth retaining for
    # post-mechanism salvage.  Publication remains strict versus a fresh board.
    near_ceiling = max(live_best, int(math.floor(live_best * (1.0 + near_miss_frac))))
    search_bound = near_ceiling + 1

    pq = [(
        priority(0, 0, initial, excess_weight, guide_weight),
        0, 0, initial_total, counter, initial,
    )]
    best_g = {initial: 0}
    best_depth = {initial: 0}
    parent = {initial: None}
    parent_edge = {}
    # quotient key -> exact state -> (g, depth)
    reps = {initial_key: {initial: (0, 0)}}

    nodes = 0
    quotient_keys_seen = {initial_key}
    transitions = 0
    compiled_edges = 0
    rep_prunes = 0
    exact_prunes = 0
    bound_prunes = 0
    max_frontier = 1
    max_depth_popped = 0
    max_depth_generated = 0
    min_total_popped = initial_total
    min_total_generated = initial_total
    min_excess_popped = 0
    best_candidate = None
    best_candidate_cost = None
    best_candidate_meta = None

    while pq and nodes < max_nodes and time.time() - start < seconds:
        _f, g, depth, _tot, _serial, state = heapq.heappop(pq)
        if best_g.get(state) != g or best_depth.get(state) != depth:
            continue
        qkey = v2.gssub_key(ns, state)
        bucket = reps.get(qkey)
        if bucket is None or bucket.get(state) != (g, depth):
            continue

        active_bound = min(search_bound, best_candidate_cost or search_bound)
        if g >= active_bound:
            bound_prunes += 1
            continue

        nodes += 1
        max_depth_popped = max(max_depth_popped, depth)
        stot = v2.total_len(state)
        min_total_popped = min(min_total_popped, stot)
        min_excess_popped = min(min_excess_popped, max(0, g - depth))

        suffix = reverse_paths.get(state)
        if suffix is not None:
            cost = g + len(suffix)
            if cost < active_bound:
                prefix = v4.reconstruct(parent, parent_edge, state)
                candidate = prefix + tuple(suffix)
                best_candidate = candidate
                best_candidate_cost = cost
                best_candidate_meta = {
                    "prefix_cost": g,
                    "suffix_cost": len(suffix),
                    "quotient_depth": depth,
                    "excess_cost": max(0, g - depth),
                }
                # A frozen strict improvement is already publication-worthy;
                # final publication still requires a fresh live recheck.
                if cost < live_best:
                    break

        desired_keys = v4.quotient_neighbor_keys(ns, state, quotient_total_cap)
        transitions += len(desired_keys)
        grouped = v4.compiled_superneighbors_grouped(core, ns, state, desired_keys, total_cap)

        for desired in sorted(desired_keys):
            cands = grouped.get(desired, ())
            compiled_edges += len(cands)
            for nxt, edge in cands:
                ng = g + len(edge)
                nd = depth + 1
                active_bound = min(search_bound, best_candidate_cost or search_bound)
                if ng >= active_bound:
                    bound_prunes += 1
                    continue

                oldg = best_g.get(nxt)
                if oldg is not None and ng >= oldg:
                    exact_prunes += 1
                    continue

                ntot = v2.total_len(nxt)
                min_total_generated = min(min_total_generated, ntot)
                max_depth_generated = max(max_depth_generated, nd)
                nq = v2.gssub_key(ns, nxt)
                nb = reps.setdefault(nq, {})

                # For heuristic representative-beam pruning, keep exact
                # representatives with the smallest compilation excess first.
                # Correctness/admission still uses exact g and official replay.
                if nxt not in nb and len(nb) >= reps_per_key:
                    def rep_score(item):
                        st, (rg, rd) = item
                        return (max(0, rg - rd), rg, v2.total_len(st))
                    worst_state, worst_label = max(nb.items(), key=rep_score)
                    worst_score = rep_score((worst_state, worst_label))
                    new_score = (max(0, ng - nd), ng, ntot)
                    if new_score >= worst_score:
                        rep_prunes += 1
                        continue
                    del nb[worst_state]
                    rep_prunes += 1

                best_g[nxt] = ng
                best_depth[nxt] = nd
                nb[nxt] = (ng, nd)
                parent[nxt] = state
                parent_edge[nxt] = tuple(edge)
                quotient_keys_seen.add(nq)
                counter += 1
                heapq.heappush(
                    pq,
                    (
                        priority(ng, nd, nxt, excess_weight, guide_weight),
                        ng, nd, ntot, counter, nxt,
                    ),
                )
                max_frontier = max(max_frontier, len(pq))

    reason = (
        "strict_candidate" if best_candidate_cost is not None and best_candidate_cost < live_best
        else "near_candidate" if best_candidate_cost is not None
        else "node_cap" if nodes >= max_nodes
        else "time_cap" if time.time() - start >= seconds
        else "frontier_exhausted"
    )
    meta = {
        "code": reason,
        "excess_weight": excess_weight,
        "guide_weight": guide_weight,
        "live_best": live_best,
        "near_ceiling": near_ceiling,
        "nodes": nodes,
        "quotient_keys_seen": len(quotient_keys_seen),
        "exact_states_seen": len(best_g),
        "transitions": transitions,
        "compiled_edges": compiled_edges,
        "representative_prunes": rep_prunes,
        "exact_prunes": exact_prunes,
        "bound_prunes": bound_prunes,
        "max_frontier": max_frontier,
        "max_depth_popped": max_depth_popped,
        "max_depth_generated": max_depth_generated,
        "min_total_popped": min_total_popped,
        "min_total_generated": min_total_generated,
        "min_excess_popped": min_excess_popped,
        "best_candidate_cost": best_candidate_cost,
        "seconds": round(time.time() - start, 3),
    }
    if best_candidate_meta:
        meta.update(best_candidate_meta)
    return best_candidate, meta


def main():
    args = parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    acc_root = Path(args.acc_root).resolve()
    acsolverx_root = Path(args.acsolverx_root).resolve()

    sys.path.insert(0, str(acc_root / "competition" / "tools"))
    from verifier import core  # noqa: E402

    manifest = json.loads(
        (acc_root / "competition" / "tools" / "verifier" / "data" / "manifest.json").read_text()
    )
    limits = manifest["limits"]
    ac_by_id = {
        c["challenge_id"]: c
        for c in manifest["challenges"]
        if c["challenge_id"].startswith("ac-")
    }
    c = ac_by_id[args.target_id]

    snapshot_obj, live = v2.snapshot_file_map(args.snapshot_ac_file)
    save_json(out / "snapshot_ac_start.json", snapshot_obj)
    live_row = live[args.target_id]
    live_best = live_row.get("currentBestLength")
    if not isinstance(live_best, int):
        report = {
            "experiment": "acc-gssub-v7-excess-guided",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_status": live_row.get("status"),
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("EXCESS_GUIDED", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)

    t0 = time.time()
    reverse_paths, reverse_hist = v2.build_reverse(core, args.reverse_depth, args.reverse_cap)
    reverse_seconds = round(time.time() - t0, 3)
    print("REVERSE", json.dumps({
        "states": len(reverse_paths), "hist": reverse_hist, "seconds": reverse_seconds,
    }, sort_keys=True), flush=True)

    atomics, search = excess_guided_search(
        core, ns, exact, reverse_paths,
        live_best=live_best,
        near_miss_frac=args.near_miss_frac,
        max_nodes=args.max_nodes,
        quotient_total_cap=qcap,
        total_cap=limits["max_total_relator_length"],
        reps_per_key=max(1, args.representatives_per_quotient),
        seconds=args.search_seconds,
        excess_weight=args.excess_weight,
        guide_weight=args.guide_weight,
    )

    report = {
        "experiment": "acc-gssub-v7-excess-guided",
        "official_commit": "99a65377c5c4f412cd9af7b8d31c41464a855736",
        "acsolverx_commit": "6a12515fe1d95178a483b76d5553266e61122417",
        "challenge_id": args.target_id,
        "live_status": live_row.get("status"),
        "live_best": live_best,
        "live_k_teams": live_row.get("kTeams"),
        "initial_total": initial_total,
        "quotient_total_cap": qcap,
        "representatives_per_quotient": args.representatives_per_quotient,
        "reverse_states": len(reverse_paths),
        "reverse_seconds": reverse_seconds,
        "search": search,
        "verified": False,
        "candidate_length": None,
    }

    any_text = ""
    strict_text = ""
    if atomics is not None:
        verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
        report["verdict"] = verdict
        report["verified"] = bool(verdict.get("ok"))
        report["candidate_length"] = len(atomics)
        report["strict_vs_frozen_live"] = len(atomics) < live_best
        report["near_miss_vs_frozen_live"] = live_best <= len(atomics) <= int(math.floor(live_best * (1.0 + args.near_miss_frac)))
        if not verdict.get("ok"):
            raise RuntimeError(("pinned_verifier_failure", report))
        any_text = f"{args.target_id}: {json.dumps(list(atomics), separators=(',', ':'))}\n"
        if len(atomics) < live_best:
            strict_text = any_text

    (out / "candidate_any.txt").write_text(any_text, encoding="utf-8")
    (out / "submission_v7.txt").write_text(strict_text, encoding="utf-8")
    save_json(out / "report.json", report)
    print("EXCESS_GUIDED", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
