#!/usr/bin/env python3
"""ACC GS-Sub V4: representative-aware search in exact atomic cost.

V2/V3 first searched the GS-Sub quotient and only afterwards compiled the fixed
quotient trajectory into official ACC moves.  The verified residual from the
carry-compiler experiments is that short quotient paths can be catastrophically
expensive after exact compilation.  This solver changes only that justified
boundary: search states are exact relator representatives and edge weights are
the number of official atomic moves required for a GS-Sub transition.

The GS-Sub proposal language, ACSolverX pin, official verifier pin and final
admission rules are unchanged.  A small per-quotient representative beam keeps
multiple physical orientations because their future atomic costs differ.  Every
edge is replayed exactly by the V3 carry compiler before it enters the frontier,
and every complete candidate is replayed by the pinned official verifier.
"""

from __future__ import annotations

import argparse
import heapq
import json
import sys
import time
from pathlib import Path

import solver_v3_gssub_carry as carry

v2 = carry.v2
TARGET = v2.TARGET


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--snapshot-ac-file")
    p.add_argument("--max-nodes", type=int, default=400000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--representatives-per-quotient", type=int, default=12)
    p.add_argument("--search-seconds", type=int, default=6000)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def quotient_neighbor_keys(ns, state, max_len):
    """Return the exact ACSolverX GS-Sub canonical neighbors of one exact state."""
    reduce_relator = ns["reduce_relator_nj"]
    canonical_pair = ns["canonical_pair_nj"]
    state_to_key = ns["state_to_key"]
    str_to_arr = ns["str_to_arr"]
    get_neighbors = ns["get_neighbors_nj"]

    key = v2.gssub_key(ns, state)
    r1a, r2a = str_to_arr(key[0]), str_to_arr(key[1])
    out = set()
    for nr1, nr2 in get_neighbors(r1a, r2a):
        nr1r = reduce_relator(nr1)
        nr2r = reduce_relator(nr2)
        if len(nr1r) + len(nr2r) >= max_len:
            continue
        c1, c2 = canonical_pair(nr1r, nr2r)
        out.add(state_to_key((c1, c2)))
    return out


def reconstruct(parent, parent_edge, state):
    chunks = []
    cur = state
    while parent.get(cur) is not None:
        chunks.append(parent_edge[cur])
        cur = parent[cur]
    chunks.reverse()
    path = ()
    for edge in chunks:
        path += tuple(edge)
    return path


def representative_atomic_search(
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
    """Bounded uniform-cost search over exact representatives.

    The cost of an edge is its already-replayed official atomic move count.
    A quotient key may retain several exact representatives because cyclic and
    inverse orientations have different future compilation costs.  The live
    record is a hard upper bound: no state whose accumulated atomic cost can no
    longer produce a strict record is admitted.
    """
    start = time.time()
    counter = 0
    initial_key = v2.gssub_key(ns, initial)
    pq = [(0, v2.total_len(initial), counter, initial)]
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

    while pq and nodes < max_nodes and time.time() - start < seconds:
        g, _tot, _serial, state = heapq.heappop(pq)
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
        suffix = reverse_paths.get(state)
        if suffix is not None and g + len(suffix) < strict_bound:
            prefix = reconstruct(parent, parent_edge, state)
            return prefix + tuple(suffix), {
                "code": "strict_candidate",
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
                "seconds": round(time.time() - start, 3),
            }

        desired_keys = quotient_neighbor_keys(ns, state, quotient_total_cap)
        transitions += len(desired_keys)
        for desired in desired_keys:
            cands = v2.compiled_superneighbor_candidates(core, ns, state, desired, total_cap)
            if not cands:
                hit = v2.compiled_superneighbors(core, ns, state, total_cap).get(desired)
                if hit is not None:
                    cands = [hit]
            compiled_edges += len(cands)

            for nxt, edge in cands:
                ng = g + len(edge)
                if ng >= strict_bound:
                    bound_prunes += 1
                    continue
                if ng >= best_g.get(nxt, 10**18):
                    exact_prunes += 1
                    continue

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
                heapq.heappush(pq, (ng, v2.total_len(nxt), counter, nxt))
                max_frontier = max(max_frontier, len(pq))

    reason = "node_cap" if nodes >= max_nodes else "time_cap" if time.time() - start >= seconds else "frontier_exhausted"
    return None, {
        "code": reason,
        "nodes": nodes,
        "quotient_keys_seen": len(quotient_keys_seen),
        "exact_states_seen": len(best_g),
        "transitions": transitions,
        "compiled_edges": compiled_edges,
        "representative_prunes": rep_prunes,
        "exact_prunes": exact_prunes,
        "bound_prunes": bound_prunes,
        "max_frontier": max_frontier,
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

    if args.snapshot_ac_file:
        snapshot_obj, live = v2.snapshot_file_map(args.snapshot_ac_file)
    else:
        snapshot_obj, live = v2.snapshot_map("ac")
    save_json(out / "snapshot_ac_start.json", snapshot_obj)
    live_row = live[args.target_id]
    live_best = live_row.get("currentBestLength")
    if not isinstance(live_best, int):
        report = {
            "experiment": "acc-gssub-v4-atomic-representative-search",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_status": live_row.get("status"),
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("ATOMIC_SEARCH", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)

    t0 = time.time()
    reverse_paths, reverse_hist = v2.build_reverse(
        core, args.reverse_depth, args.reverse_cap
    )
    reverse_seconds = round(time.time() - t0, 3)
    print("REVERSE", json.dumps({
        "states": len(reverse_paths),
        "hist": reverse_hist,
        "seconds": reverse_seconds,
    }, sort_keys=True), flush=True)

    atomics, search = representative_atomic_search(
        core,
        ns,
        exact,
        reverse_paths,
        strict_bound=live_best,
        max_nodes=args.max_nodes,
        quotient_total_cap=qcap,
        total_cap=limits["max_total_relator_length"],
        reps_per_key=max(1, args.representatives_per_quotient),
        seconds=args.search_seconds,
    )

    report = {
        "experiment": "acc-gssub-v4-atomic-representative-search",
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

    submission = ""
    if atomics is not None:
        verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
        report["verdict"] = verdict
        report["verified"] = bool(verdict.get("ok"))
        report["candidate_length"] = len(atomics)
        report["strict_vs_frozen_live"] = len(atomics) < live_best
        if verdict.get("ok") and len(atomics) < live_best:
            submission = f"{args.target_id}: {json.dumps(list(atomics), separators=(',', ':'))}\n"

    (out / "submission_v4.txt").write_text(submission, encoding="utf-8")
    save_json(out / "report.json", report)
    print("ATOMIC_SEARCH", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
