#!/usr/bin/env python3
"""ACC GS-Sub V11: lazy exact-overhead quotient skeleton search.

V10 established a concrete search-engine residual rather than a mathematical
one: exact canonical-edge overhead scoring dominated the search.  In 900 s the
0.05-weight runs expanded only 474 states for ac-01910 and 796 for ac-04501,
while eagerly compiling 35,016 and 50,286 quotient edges respectively.  That
is too little quotient progress to test the compiler-aware skeleton hypothesis.

V11 keeps the same quotient language, the same exact V10 edge-overhead score,
and the same V9 exact fixed-skeleton compiler.  It changes only *when* an edge
is scored.  Neighbor edges enter the priority queue with the admissible local
overhead lower bound 0.  Exact edge overhead is computed only when that edge
proposal reaches the front of the queue.  After scoring, the destination state
is reinserted at its exact V10 priority.

This is a lazy evaluation of the existing V10 objective, not a cheaper proxy:

    total_relator_length + weight * cumulative_exact_estimated_overhead.

All candidate certificates are still compiled to official atomic ACC moves,
replayed by the pinned official verifier, and publication remains fresh-live,
strict-record-only and quota gated by the workflow.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path

import solver_v2_gssub as v2
import solver_v9_gssub_skeleton_lookahead as v9
import solver_v10_gssub_overhead_skeleton as v10


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--snapshot-ac-file", required=True)
    p.add_argument("--overhead-weight", type=float, required=True)
    p.add_argument("--max-nodes", type=int, default=120000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--search-seconds", type=int, default=900)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--strict-beam", type=int, default=256)
    p.add_argument("--near-beam", type=int, default=64)
    p.add_argument("--compile-seconds", type=int, default=600)
    p.add_argument("--near-compile-seconds", type=int, default=180)
    p.add_argument("--near-miss-frac", type=float, default=0.10)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def lazy_compiler_aware_quotient_search(
    core,
    ns,
    exact_initial,
    *,
    max_nodes,
    max_len,
    total_cap,
    overhead_weight,
    seconds,
):
    reduce_relator = ns["reduce_relator_nj"]
    canonical_pair = ns["canonical_pair_nj"]
    state_to_key = ns["state_to_key"]
    str_to_arr = ns["str_to_arr"]
    get_neighbors = ns["get_neighbors_nj"]

    r0 = v2.int_word_to_str(exact_initial[0])
    r1 = v2.int_word_to_str(exact_initial[1])
    initial = canonical_pair(reduce_relator(str_to_arr(r0)), reduce_relator(str_to_arr(r1)))
    ikey = state_to_key(initial)
    initial_len = len(initial[0]) + len(initial[1])

    start = time.time()
    serial = 0
    # Heap entry:
    #   state: (priority, 1, serial, "state", key, exact_oh, depth, total)
    #   edge : (optimistic_priority, 0, serial, "edge", source_key,
    #           source_exact_oh, source_depth, desired_key, desired_total)
    # Edge proposals sort before equal-priority states so an exact score is
    # established before claiming that frontier layer is exhausted.
    pq = [(float(initial_len), 1, serial, "state", ikey, 0, 0, initial_len)]

    best_overhead = {ikey: 0}
    best_depth = {ikey: 0}
    parent = {ikey: None}
    cache = {}

    nodes = 0
    generated = 0
    edge_evaluations = 0
    stale_edges = 0
    stale_states = 0
    dominated_edge_proposals = 0
    exact_relaxations = 0
    max_frontier = 1
    min_total = initial_len
    max_depth = 0

    def key_to_state(key):
        return (str_to_arr(key[0]), str_to_arr(key[1]))

    while pq and nodes < max_nodes and time.time() - start < seconds:
        item = heapq.heappop(pq)
        _pri, _kind_order, _serial, kind = item[:4]

        if kind == "edge":
            _p, _ko, _s, _k, source, source_oh, source_depth, desired, ntotal = item
            if best_overhead.get(source) != source_oh or best_depth.get(source) != source_depth:
                stale_edges += 1
                continue

            # Since local overhead is nonnegative, an already-known destination
            # no worse than the parent's exact overhead cannot be improved by
            # this proposal.
            old = best_overhead.get(desired)
            old_depth = best_depth.get(desired)
            nd = source_depth + 1
            if old is not None and (old < source_oh or (old == source_oh and old_depth <= nd)):
                dominated_edge_proposals += 1
                continue

            local_oh = v10.compiler_edge_overhead(core, ns, source, desired, total_cap, cache)
            edge_evaluations += 1
            noh = source_oh + local_oh
            old = best_overhead.get(desired)
            old_depth = best_depth.get(desired)
            if old is not None and (noh > old or (noh == old and nd >= old_depth)):
                continue

            best_overhead[desired] = noh
            best_depth[desired] = nd
            parent[desired] = source
            exact_relaxations += 1
            serial += 1
            pri = float(ntotal) + float(overhead_weight) * float(noh) + 1e-6 * nd
            heapq.heappush(pq, (pri, 1, serial, "state", desired, noh, nd, ntotal))
            max_frontier = max(max_frontier, len(pq))
            continue

        _p, _ko, _s, _k, key, oh, depth, total = item
        if best_overhead.get(key) != oh or best_depth.get(key) != depth:
            stale_states += 1
            continue

        nodes += 1
        max_depth = max(max_depth, depth)
        min_total = min(min_total, total)
        r1a, r2a = key_to_state(key)
        if len(r1a) == 1 and len(r2a) == 1:
            keys = []
            cur = key
            while cur is not None:
                keys.append(cur)
                cur = parent[cur]
            keys.reverse()
            path = [key_to_state(k) for k in keys]
            return path, {
                "code": "ok",
                "nodes": nodes,
                "generated": generated,
                "quotient_steps": len(path) - 1,
                "estimated_overhead": oh,
                "edge_cache": len(cache),
                "edge_evaluations": edge_evaluations,
                "exact_relaxations": exact_relaxations,
                "stale_edges": stale_edges,
                "stale_states": stale_states,
                "dominated_edge_proposals": dominated_edge_proposals,
                "max_frontier": max_frontier,
                "max_depth": max_depth,
                "min_total": min_total,
                "seconds": round(time.time() - start, 3),
            }

        # Canonical quotient neighbors can contain duplicate keys.  Deduplicate
        # before adding lazy edge proposals; no exact compiler work is done here.
        proposed = {}
        for nr1, nr2 in get_neighbors(r1a, r2a):
            nr1r = reduce_relator(nr1)
            nr2r = reduce_relator(nr2)
            ntotal = len(nr1r) + len(nr2r)
            if ntotal >= max_len:
                continue
            c1, c2 = canonical_pair(nr1r, nr2r)
            knew = state_to_key((c1, c2))
            prev_total = proposed.get(knew)
            if prev_total is None or ntotal < prev_total:
                proposed[knew] = ntotal

        nd = depth + 1
        for knew, ntotal in proposed.items():
            old = best_overhead.get(knew)
            old_depth = best_depth.get(knew)
            if old is not None and (old < oh or (old == oh and old_depth <= nd)):
                dominated_edge_proposals += 1
                continue
            serial += 1
            generated += 1
            optimistic = float(ntotal) + float(overhead_weight) * float(oh) + 1e-6 * nd
            heapq.heappush(
                pq,
                (optimistic, 0, serial, "edge", key, oh, depth, knew, ntotal),
            )
        max_frontier = max(max_frontier, len(pq))

    code = "node_cap" if nodes >= max_nodes else "time_cap" if time.time() - start >= seconds else "frontier_exhausted"
    return None, {
        "code": code,
        "nodes": nodes,
        "generated": generated,
        "edge_cache": len(cache),
        "edge_evaluations": edge_evaluations,
        "exact_relaxations": exact_relaxations,
        "stale_edges": stale_edges,
        "stale_states": stale_states,
        "dominated_edge_proposals": dominated_edge_proposals,
        "max_frontier": max_frontier,
        "max_depth": max_depth,
        "min_total": min_total,
        "seconds": round(time.time() - start, 3),
    }


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
            "experiment": "acc-gssub-v11-lazy-exact-overhead",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("LAZY_OVERHEAD", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)

    quotient_path, qmeta = lazy_compiler_aware_quotient_search(
        core,
        ns,
        exact,
        max_nodes=args.max_nodes,
        max_len=qcap,
        total_cap=limits["max_total_relator_length"],
        overhead_weight=args.overhead_weight,
        seconds=args.search_seconds,
    )
    print(
        "LAZY_OVERHEAD_QUOTIENT",
        json.dumps({"challenge_id": args.target_id, "weight": args.overhead_weight, **qmeta}, sort_keys=True),
        flush=True,
    )

    report = {
        "experiment": "acc-gssub-v11-lazy-exact-overhead",
        "official_commit": "99a65377c5c4f412cd9af7b8d31c41464a855736",
        "acsolverx_commit": "6a12515fe1d95178a483b76d5553266e61122417",
        "challenge_id": args.target_id,
        "overhead_weight": args.overhead_weight,
        "live_status": live_row.get("status"),
        "live_best": live_best,
        "live_k_teams": live_row.get("kTeams"),
        "initial_total": initial_total,
        "quotient_total_cap": qcap,
        "quotient_search": qmeta,
        "verified": False,
        "candidate_length": None,
    }

    atomics = None
    strict_meta = None
    near_meta = None
    if quotient_path is not None:
        reverse_paths, reverse_hist = v2.build_reverse(core, args.reverse_depth, args.reverse_cap)
        report["reverse_states"] = len(reverse_paths)
        report["reverse_hist"] = reverse_hist
        qsteps = len(quotient_path) - 1
        report["quotient_steps"] = qsteps
        report["strict_overhead_budget_before_suffix"] = live_best - 1 - qsteps

        atomics, strict_meta = v9.compile_fixed_skeleton(
            core,
            ns,
            exact,
            quotient_path,
            reverse_paths,
            limits["max_total_relator_length"],
            ceiling_exclusive=live_best,
            beam_width=args.strict_beam,
            seconds=args.compile_seconds,
            label="strict",
        )
        if atomics is None:
            near_ceiling = int(math.floor(live_best * (1.0 + args.near_miss_frac)))
            atomics, near_meta = v9.compile_fixed_skeleton(
                core,
                ns,
                exact,
                quotient_path,
                reverse_paths,
                limits["max_total_relator_length"],
                ceiling_exclusive=near_ceiling + 1,
                beam_width=args.near_beam,
                seconds=args.near_compile_seconds,
                label="near",
            )
    report["strict_compile"] = strict_meta
    report["near_compile"] = near_meta

    any_text = ""
    strict_text = ""
    if atomics is not None:
        verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
        if not verdict.get("ok"):
            raise RuntimeError(("pinned_verifier_failure", args.target_id, verdict))
        report["verified"] = True
        report["verdict"] = verdict
        report["candidate_length"] = len(atomics)
        report["strict_vs_frozen_live"] = len(atomics) < live_best
        report["near_miss_vs_frozen_live"] = (
            live_best <= len(atomics) <= int(math.floor(live_best * (1.0 + args.near_miss_frac)))
        )
        any_text = f"{args.target_id}: {json.dumps(list(atomics), separators=(',', ':'))}\n"
        if len(atomics) < live_best:
            strict_text = any_text

    (out / "candidate_any.txt").write_text(any_text, encoding="utf-8")
    (out / "submission_v11.txt").write_text(strict_text, encoding="utf-8")
    save_json(out / "report.json", report)
    print("LAZY_OVERHEAD", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
