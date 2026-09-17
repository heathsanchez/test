#!/usr/bin/env python3
"""ACC GS-Sub V10: compiler-aware quotient skeleton discovery.

V9 established that the ordinary length-first quotient skeletons are already
noncompetitive within the exact carry compiler after only a handful of steps:
for ac-01910 the strict live bound dies at quotient step 2 (and the 10% near
bound at step 9); for ac-04501 strict dies at step 6 (near at step 24).
Therefore the next justified boundary is not wider exact compilation of those
same skeletons, but choosing quotient skeletons whose transitions are cheap to
realize physically.

This search stays entirely proposal-side.  It runs the public GS-Sub quotient
neighbor language, but augments its normal total-relator-length priority with a
cached local estimate of exact compiler overhead.  The estimate is obtained by
compiling the quotient edge from the canonical physical representative using
V3 carry-symmetry official moves:

    local_overhead = min_exact_atomic_edge_length - 1

(one multiplication is unavoidable per GS-Sub edge).  The search priority is

    total_relator_length + weight * cumulative_estimated_overhead.

Each resulting quotient skeleton is then compiled by V9's live-bound,
one-step-lookahead exact compiler and every emitted path is replayed by the
pinned official verifier.  Publication remains strict and fresh-live gated.
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
import solver_v3_gssub_carry as v3
import solver_v9_gssub_skeleton_lookahead as v9


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
    p.add_argument("--compile-seconds", type=int, default=900)
    p.add_argument("--near-compile-seconds", type=int, default=300)
    p.add_argument("--near-miss-frac", type=float, default=0.10)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def str_to_int_word(s):
    m = {"x": 1, "X": -1, "y": 2, "Y": -2}
    return tuple(m[ch] for ch in str(s))


def key_to_exact(key):
    return (str_to_int_word(key[0]), str_to_int_word(key[1]))


def compiler_edge_overhead(core, ns, key, desired, total_cap, cache):
    ck = (tuple(key), tuple(desired))
    got = cache.get(ck)
    if got is not None:
        return got
    state = key_to_exact(key)
    cands = v3.compiled_superneighbor_candidates_carry(core, ns, state, desired, total_cap)
    if not cands:
        hit = v2.compiled_superneighbors(core, ns, state, total_cap).get(desired)
        if hit is not None:
            cands = [hit]
    if not cands:
        # Proposal penalty only: this does not reject the edge from the quotient
        # graph.  It merely ranks an edge with no canonical exact realization
        # behind edges whose physical cost is known.
        val = 32
    else:
        val = max(0, min(len(edge) for _nxt, edge in cands) - 1)
    cache[ck] = val
    return val


def compiler_aware_quotient_search(
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

    start = time.time()
    serial = 0
    initial_len = len(initial[0]) + len(initial[1])
    pq = [(float(initial_len), 0, 0, serial, ikey)]
    best_overhead = {ikey: 0}
    best_depth = {ikey: 0}
    parent = {ikey: None}
    edge_overhead = {}
    cache = {}
    nodes = 0
    generated = 0
    max_frontier = 1
    min_total = initial_len
    max_depth = 0

    def key_to_state(key):
        return (str_to_arr(key[0]), str_to_arr(key[1]))

    while pq and nodes < max_nodes and time.time() - start < seconds:
        _pri, oh, depth, _serial, key = heapq.heappop(pq)
        if best_overhead.get(key) != oh or best_depth.get(key) != depth:
            continue
        nodes += 1
        max_depth = max(max_depth, depth)
        r1a, r2a = key_to_state(key)
        total = len(r1a) + len(r2a)
        min_total = min(min_total, total)
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
                "max_frontier": max_frontier,
                "max_depth": max_depth,
                "min_total": min_total,
                "seconds": round(time.time() - start, 3),
            }

        nd = depth + 1
        for nr1, nr2 in get_neighbors(r1a, r2a):
            nr1r = reduce_relator(nr1)
            nr2r = reduce_relator(nr2)
            ntotal = len(nr1r) + len(nr2r)
            if ntotal >= max_len:
                continue
            c1, c2 = canonical_pair(nr1r, nr2r)
            knew = state_to_key((c1, c2))
            local_oh = compiler_edge_overhead(core, ns, key, knew, total_cap, cache)
            noh = oh + local_oh
            old = best_overhead.get(knew)
            old_depth = best_depth.get(knew)
            if old is not None and (noh > old or (noh == old and nd >= old_depth)):
                continue
            best_overhead[knew] = noh
            best_depth[knew] = nd
            parent[knew] = key
            edge_overhead[knew] = local_oh
            serial += 1
            generated += 1
            pri = float(ntotal) + float(overhead_weight) * float(noh) + 1e-6 * nd
            heapq.heappush(pq, (pri, noh, nd, serial, knew))
            max_frontier = max(max_frontier, len(pq))

    return None, {
        "code": "node_cap" if nodes >= max_nodes else "time_cap" if time.time() - start >= seconds else "frontier_exhausted",
        "nodes": nodes,
        "generated": generated,
        "edge_cache": len(cache),
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
        c["challenge_id"]: c for c in manifest["challenges"]
        if c["challenge_id"].startswith("ac-")
    }
    c = ac_by_id[args.target_id]
    snapshot_obj, live = v2.snapshot_file_map(args.snapshot_ac_file)
    save_json(out / "snapshot_ac_start.json", snapshot_obj)
    live_row = live[args.target_id]
    live_best = live_row.get("currentBestLength")
    if not isinstance(live_best, int):
        report = {
            "experiment": "acc-gssub-v10-compiler-aware-skeleton",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("OVERHEAD_SKELETON", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)

    quotient_path, qmeta = compiler_aware_quotient_search(
        core, ns, exact,
        max_nodes=args.max_nodes,
        max_len=qcap,
        total_cap=limits["max_total_relator_length"],
        overhead_weight=args.overhead_weight,
        seconds=args.search_seconds,
    )
    print("OVERHEAD_QUOTIENT", json.dumps({
        "challenge_id": args.target_id,
        "weight": args.overhead_weight,
        **qmeta,
    }, sort_keys=True), flush=True)

    report = {
        "experiment": "acc-gssub-v10-compiler-aware-skeleton",
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
            core, ns, exact, quotient_path, reverse_paths,
            limits["max_total_relator_length"],
            ceiling_exclusive=live_best,
            beam_width=args.strict_beam,
            seconds=args.compile_seconds,
            label="strict",
        )
        if atomics is None:
            near_ceiling = int(math.floor(live_best * (1.0 + args.near_miss_frac)))
            atomics, near_meta = v9.compile_fixed_skeleton(
                core, ns, exact, quotient_path, reverse_paths,
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
    (out / "submission_v10.txt").write_text(strict_text, encoding="utf-8")
    save_json(out / "report.json", report)
    print("OVERHEAD_SKELETON", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
