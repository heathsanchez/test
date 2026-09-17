#!/usr/bin/env python3
"""ACC GS-Sub V12: compiler-aware prefix, cheap quotient completion.

V11 resolved the eager-scoring bottleneck but exposed the next residual: exact
compiler-aware scoring is useful locally yet too expensive globally.  On the
strict-steal targets the 0.05 runs reached depths 87 (ac-01910) and 52
(ac-04501) in 900 seconds, but generated multi-million proposal frontiers and
never completed the known 392/438-step quotient trajectories.  In contrast,
ordinary length-first GS-Sub reaches complete quotient solutions in only tens
of thousands of quotient pops.

V9 tells us where exact compiler awareness is actually required: the ordinary
skeleton already violates the strict physical bound by quotient step 2 on
ac-01910 and step 6 on ac-04501; even the 10% near-miss window dies by steps 9
and 24 respectively.  V12 therefore pays exact edge-overhead cost only across
a short prefix that covers that verified failure zone, keeps several low-
overhead prefix endpoints, and then completes each endpoint with the original
cheap ACSolverX length-first quotient search.  Each spliced skeleton is still
compiled by V9's exact live-bound compiler and every emitted certificate is
replayed by the pinned official verifier.

Search is proposal machinery only.  Publication remains fresh-live,
strict-record-only, and quota gated by the workflow.
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


OFFICIAL_COMMIT = "99a65377c5c4f412cd9af7b8d31c41464a855736"
ACSOLVERX_COMMIT = "6a12515fe1d95178a483b76d5553266e61122417"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--snapshot-ac-file", required=True)
    p.add_argument("--overhead-weight", type=float, required=True)
    p.add_argument("--prefix-depth", type=int, required=True)
    p.add_argument("--prefix-count", type=int, default=6)
    p.add_argument("--prefix-max-nodes", type=int, default=80000)
    p.add_argument("--prefix-seconds", type=int, default=360)
    p.add_argument("--suffix-max-nodes", type=int, default=90000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--strict-beam", type=int, default=256)
    p.add_argument("--near-beam", type=int, default=64)
    p.add_argument("--compile-seconds", type=int, default=420)
    p.add_argument("--near-compile-seconds", type=int, default=180)
    p.add_argument("--near-miss-frac", type=float, default=0.10)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compiler_aware_prefixes(
    core,
    ns,
    exact_initial,
    *,
    max_nodes,
    max_len,
    total_cap,
    overhead_weight,
    target_depth,
    prefix_count,
    seconds,
):
    """Collect low-estimated-overhead quotient prefixes at an exact depth.

    This is V11's lazy exact-overhead queue, intentionally stopped at the
    verified early compiler-failure boundary rather than trying to solve the
    whole quotient problem under expensive exact edge scoring.
    """
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
    pq = [(float(initial_len), 1, serial, "state", ikey, 0, 0, initial_len)]
    best_overhead = {ikey: 0}
    best_depth = {ikey: 0}
    parent = {ikey: None}
    cache = {}
    collected = []
    collected_keys = set()

    nodes = 0
    generated = 0
    edge_evaluations = 0
    exact_relaxations = 0
    stale_edges = 0
    stale_states = 0
    dominated_edge_proposals = 0
    max_frontier = 1
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
        if depth >= target_depth:
            if depth == target_depth and key not in collected_keys:
                keys = []
                cur = key
                while cur is not None:
                    keys.append(cur)
                    cur = parent[cur]
                keys.reverse()
                if len(keys) - 1 == target_depth:
                    collected.append({
                        "key": key,
                        "overhead": int(oh),
                        "total": int(total),
                        "path_keys": keys,
                    })
                    collected_keys.add(key)
                    if len(collected) >= prefix_count:
                        break
            # Prefix phase never pays to expand beyond the requested boundary.
            continue

        r1a, r2a = key_to_state(key)
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
            heapq.heappush(pq, (optimistic, 0, serial, "edge", key, oh, depth, knew, ntotal))
        max_frontier = max(max_frontier, len(pq))

    collected.sort(key=lambda x: (x["overhead"], x["total"], x["key"]))
    meta = {
        "code": "ok" if collected else ("time_cap" if time.time() - start >= seconds else "no_prefix"),
        "target_depth": target_depth,
        "prefixes": len(collected),
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
        "seconds": round(time.time() - start, 3),
        "best_prefix_overhead": collected[0]["overhead"] if collected else None,
        "worst_kept_prefix_overhead": collected[-1]["overhead"] if collected else None,
    }
    return collected, meta


def complete_suffix(ns, key, *, max_nodes, max_len):
    solver = ns["ACRelatorSolver"](
        key[0], key[1],
        max_nodes=max_nodes,
        max_len=max_len,
        verbose=False,
        stop_early=False,
    )
    t0 = time.time()
    found = solver.solve()
    if len(found) == 3:
        path, nodes, _seen = found
    else:
        path, nodes = found[:2]
    return path, int(nodes), round(time.time() - t0, 3)


def path_from_keys(ns, keys):
    str_to_arr = ns["str_to_arr"]
    return [(str_to_arr(k[0]), str_to_arr(k[1])) for k in keys]


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
            "experiment": "acc-gssub-v12-prefix-hybrid",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("PREFIX_HYBRID", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)

    prefixes, pmeta = compiler_aware_prefixes(
        core,
        ns,
        exact,
        max_nodes=args.prefix_max_nodes,
        max_len=qcap,
        total_cap=limits["max_total_relator_length"],
        overhead_weight=args.overhead_weight,
        target_depth=args.prefix_depth,
        prefix_count=args.prefix_count,
        seconds=args.prefix_seconds,
    )
    print(
        "PREFIX_HYBRID_PREFIX",
        json.dumps({"challenge_id": args.target_id, "weight": args.overhead_weight, **pmeta}, sort_keys=True),
        flush=True,
    )

    report = {
        "experiment": "acc-gssub-v12-prefix-hybrid",
        "official_commit": OFFICIAL_COMMIT,
        "acsolverx_commit": ACSOLVERX_COMMIT,
        "challenge_id": args.target_id,
        "overhead_weight": args.overhead_weight,
        "prefix_depth": args.prefix_depth,
        "live_status": live_row.get("status"),
        "live_best": live_best,
        "live_k_teams": live_row.get("kTeams"),
        "initial_total": initial_total,
        "quotient_total_cap": qcap,
        "prefix_search": pmeta,
        "skeletons": [],
        "verified": False,
        "candidate_length": None,
    }

    if not prefixes:
        (out / "candidate_any.txt").write_text("", encoding="utf-8")
        (out / "submission_v12.txt").write_text("", encoding="utf-8")
        save_json(out / "report.json", report)
        print("PREFIX_HYBRID", json.dumps(report, sort_keys=True), flush=True)
        return

    near_ceiling = int(math.floor(live_best * (1.0 + args.near_miss_frac)))
    reverse_paths = None
    reverse_hist = None
    best_any = None
    best_strict = None

    for rank, pref in enumerate(prefixes, 1):
        suffix_path, suffix_nodes, suffix_seconds = complete_suffix(
            ns,
            pref["key"],
            max_nodes=args.suffix_max_nodes,
            max_len=qcap,
        )
        smeta = {
            "prefix_rank": rank,
            "prefix_estimated_overhead": pref["overhead"],
            "prefix_total": pref["total"],
            "suffix_nodes": suffix_nodes,
            "suffix_seconds": suffix_seconds,
            "suffix_found": suffix_path is not None,
            "verified": False,
            "candidate_length": None,
        }
        if suffix_path is None:
            report["skeletons"].append(smeta)
            continue

        if v2.path_state_key(ns, suffix_path[0]) != pref["key"]:
            raise RuntimeError(("suffix_initial_key_mismatch", args.target_id, rank))

        prefix_path = path_from_keys(ns, pref["path_keys"])
        quotient_path = prefix_path + list(suffix_path[1:])
        qsteps = len(quotient_path) - 1
        smeta["quotient_steps"] = qsteps
        smeta["strict_overhead_budget_before_suffix"] = live_best - 1 - qsteps
        smeta["near_overhead_budget_before_suffix"] = near_ceiling - qsteps

        # If one compulsory multiplication per quotient transition already
        # exceeds the salvage ceiling, exact compilation cannot rescue it.
        if qsteps > near_ceiling:
            smeta["compile_code"] = "quotient_steps_exceed_near_ceiling"
            report["skeletons"].append(smeta)
            continue

        if reverse_paths is None:
            reverse_paths, reverse_hist = v2.build_reverse(core, args.reverse_depth, args.reverse_cap)
            report["reverse_states"] = len(reverse_paths)
            report["reverse_hist"] = reverse_hist

        atomics = None
        strict_meta = None
        near_meta = None
        if qsteps < live_best:
            atomics, strict_meta = v9.compile_fixed_skeleton(
                core, ns, exact, quotient_path, reverse_paths,
                limits["max_total_relator_length"],
                ceiling_exclusive=live_best,
                beam_width=args.strict_beam,
                seconds=args.compile_seconds,
                label=f"strict-prefix-{rank}",
            )
        else:
            strict_meta = {"code": "quotient_steps_not_strict", "quotient_steps": qsteps}

        if atomics is None:
            atomics, near_meta = v9.compile_fixed_skeleton(
                core, ns, exact, quotient_path, reverse_paths,
                limits["max_total_relator_length"],
                ceiling_exclusive=near_ceiling + 1,
                beam_width=args.near_beam,
                seconds=args.near_compile_seconds,
                label=f"near-prefix-{rank}",
            )

        smeta["strict_compile"] = strict_meta
        smeta["near_compile"] = near_meta
        if atomics is None:
            report["skeletons"].append(smeta)
            continue

        verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
        if not verdict.get("ok"):
            raise RuntimeError(("pinned_verifier_failure", args.target_id, rank, verdict))
        clen = len(atomics)
        smeta["verified"] = True
        smeta["candidate_length"] = clen
        smeta["strict_vs_frozen_live"] = clen < live_best
        smeta["near_miss_vs_frozen_live"] = live_best <= clen <= near_ceiling
        report["skeletons"].append(smeta)

        if best_any is None or clen < len(best_any):
            best_any = tuple(atomics)
        if clen < live_best and (best_strict is None or clen < len(best_strict)):
            best_strict = tuple(atomics)
            # A verified strict steal is sufficient for this phase; the
            # publisher will fresh-recheck the record before spending quota.
            break

    chosen = best_strict if best_strict is not None else best_any
    if chosen is not None:
        report["verified"] = True
        report["candidate_length"] = len(chosen)
        report["strict_vs_frozen_live"] = len(chosen) < live_best
        report["near_miss_vs_frozen_live"] = live_best <= len(chosen) <= near_ceiling

    any_text = ""
    strict_text = ""
    if chosen is not None:
        any_text = f"{args.target_id}: {json.dumps(list(chosen), separators=(',', ':'))}\n"
        if len(chosen) < live_best:
            strict_text = any_text
    (out / "candidate_any.txt").write_text(any_text, encoding="utf-8")
    (out / "submission_v12.txt").write_text(strict_text, encoding="utf-8")
    save_json(out / "report.json", report)
    print("PREFIX_HYBRID", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
