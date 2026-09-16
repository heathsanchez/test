#!/usr/bin/env python3
"""ACC GS-Sub V5: atomic-cost representative search with exact symmetry joins.

V4 established the right objective (official atomic move count) but a 6000 s
pass over each focused record still saw ~1.2M quotient keys and ~9M exact
states without reaching an *exact* reverse-atlas state.  That verified residual
justifies widening only the terminal join condition: a forward representative
may meet the reverse atlas anywhere in the same ACSolverX canonical quotient
orbit, provided the orbit alignment itself is compiled to official atomic
moves and replayed exactly.

No proposal language is added.  Forward neighbors remain V4 GS-Sub neighbors,
all edge costs remain official atomic move counts, and every returned route is
replayed by the pinned official verifier.  Non-winning orbit joins are retained
only as verifier-clean near-miss evidence for the existing atlas/peephole
salvage stage; they are never direct submission rows.
"""

from __future__ import annotations

import heapq
import json
import math
import sys
import time
from pathlib import Path

import solver_v4_gssub_atomic as v4

v2 = v4.v2
TARGET = v4.TARGET

# Exact generic Nielsen swap under frozen moves 0..5:
# (a,b) -> (a^-1,b^-1) -> (a^-1 b^-1,b^-1) -> (ba,b^-1)
#       -> (ba,a) -> (b,a).
SWAP_MOVES = (0, 1, 2, 0, 4, 3)
CHAR_TO_INT = {"x": 1, "X": -1, "y": 2, "Y": -2}


def replay_path(core, state, moves, total_cap=None):
    cur = state
    for move in moves:
        cur = core.apply_move(cur, move)
        if total_cap is not None and v2.total_len(cur) > total_cap:
            return None
    return cur


def key_state(key):
    return tuple(tuple(CHAR_TO_INT[c] for c in word) for word in key)


def best_orientation_path(core, word, relator_index, target_word):
    best = None
    for got, seq in v2.orientation_options(core, word, relator_index):
        if tuple(got) != tuple(target_word):
            continue
        seq = tuple(seq)
        if best is None or len(seq) < len(best):
            best = seq
    return best


def canonical_alignment_path(core, ns, state, qkey, total_cap):
    """Compile an exact path from ``state`` to its canonical quotient state.

    ACSolverX canonicalization quotients by cyclic conjugation, relator
    inversion and pair ordering.  Inversion/conjugation already have frozen
    atomic moves.  Pair ordering is compiled by the exact six-move Nielsen swap
    above.  Every proposed alignment is replayed before being returned.
    """
    target = key_state(qkey)
    bases = [(state, ())]
    swapped = replay_path(core, state, SWAP_MOVES, total_cap)
    if swapped is not None:
        bases.append((swapped, SWAP_MOVES))

    best = None
    for base, prefix in bases:
        s0 = best_orientation_path(core, base[0], 0, target[0])
        if s0 is None:
            continue
        after0 = replay_path(core, base, s0, total_cap)
        if after0 is None:
            continue
        s1 = best_orientation_path(core, after0[1], 1, target[1])
        if s1 is None:
            continue
        path = tuple(prefix) + tuple(s0) + tuple(s1)
        chk = replay_path(core, state, path, total_cap)
        if chk != target:
            continue
        if best is None or len(path) < len(best):
            best = path
    return best


def build_reverse_quotient_suffixes(core, ns, reverse_paths, total_cap):
    """Map each reverse-atlas quotient key to its shortest exact suffix.

    A reverse state ``r`` already has an official suffix r -> TARGET.  We
    normalize r -> canonical(r), then invert that normalization to obtain
    canonical(r) -> r -> TARGET.  Thus a forward state only needs an exact
    normalization into the same canonical key to splice into this suffix.
    """
    best = {}
    alignment_failures = 0
    for state, suffix in reverse_paths.items():
        qkey = v2.gssub_key(ns, state)
        norm = canonical_alignment_path(core, ns, state, qkey, total_cap)
        if norm is None:
            alignment_failures += 1
            continue
        inv_norm = tuple(core.INVERSE_MOVE[m] for m in reversed(norm))
        qsuffix = inv_norm + tuple(suffix)
        canon = key_state(qkey)
        if replay_path(core, canon, qsuffix, total_cap) != TARGET:
            raise RuntimeError("reverse quotient suffix replay mismatch")
        old = best.get(qkey)
        if old is None or len(qsuffix) < len(old):
            best[qkey] = qsuffix
    return best, alignment_failures


def representative_atomic_search_orbit(
    core,
    ns,
    initial,
    reverse_paths,
    reverse_qsuffix,
    *,
    strict_bound,
    max_nodes,
    quotient_total_cap,
    total_cap,
    reps_per_key,
    seconds,
):
    """V4 uniform-cost search plus an exact quotient-orbit reverse join."""
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
    quotient_join_hits = 0
    aligned_join_hits = 0
    best_join_cost = None
    best_join_state = None
    best_join_suffix = None

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

        # Preserve the cheapest possible terminal case first.
        exact_suffix = reverse_paths.get(state)
        if exact_suffix is not None:
            total = g + len(exact_suffix)
            if total < strict_bound:
                prefix = v4.reconstruct(parent, parent_edge, state)
                return prefix + tuple(exact_suffix), {
                    "code": "strict_exact_join",
                    "nodes": nodes,
                    "atomic_cost": total,
                    "prefix_cost": g,
                    "suffix_cost": len(exact_suffix),
                    "quotient_keys_seen": len(quotient_keys_seen),
                    "exact_states_seen": len(best_g),
                    "transitions": transitions,
                    "compiled_edges": compiled_edges,
                    "representative_prunes": rep_prunes,
                    "exact_prunes": exact_prunes,
                    "bound_prunes": bound_prunes,
                    "max_frontier": max_frontier,
                    "quotient_join_hits": quotient_join_hits,
                    "aligned_join_hits": aligned_join_hits,
                    "best_join_cost": total,
                    "seconds": round(time.time() - start, 3),
                }

        # The verified V4 residual was an excessively narrow exact terminal
        # manifold.  Join the reverse atlas through the *same* canonical GS-Sub
        # orbit, but compile that symmetry bridge to frozen atomic moves.
        qsuffix = reverse_qsuffix.get(qkey)
        if qsuffix is not None:
            quotient_join_hits += 1
            norm = canonical_alignment_path(core, ns, state, qkey, total_cap)
            if norm is not None:
                aligned_join_hits += 1
                join_suffix = tuple(norm) + tuple(qsuffix)
                join_total = g + len(join_suffix)
                if best_join_cost is None or join_total < best_join_cost:
                    best_join_cost = join_total
                    best_join_state = state
                    best_join_suffix = join_suffix
                if join_total < strict_bound:
                    prefix = v4.reconstruct(parent, parent_edge, state)
                    return prefix + join_suffix, {
                        "code": "strict_quotient_orbit_join",
                        "nodes": nodes,
                        "atomic_cost": join_total,
                        "prefix_cost": g,
                        "suffix_cost": len(join_suffix),
                        "quotient_keys_seen": len(quotient_keys_seen),
                        "exact_states_seen": len(best_g),
                        "transitions": transitions,
                        "compiled_edges": compiled_edges,
                        "representative_prunes": rep_prunes,
                        "exact_prunes": exact_prunes,
                        "bound_prunes": bound_prunes,
                        "max_frontier": max_frontier,
                        "quotient_join_hits": quotient_join_hits,
                        "aligned_join_hits": aligned_join_hits,
                        "best_join_cost": best_join_cost,
                        "seconds": round(time.time() - start, 3),
                    }

        desired_keys = v4.quotient_neighbor_keys(ns, state, quotient_total_cap)
        transitions += len(desired_keys)
        grouped = v4.compiled_superneighbors_grouped(
            core, ns, state, desired_keys, total_cap
        )
        for desired in sorted(desired_keys):
            cands = grouped.get(desired, ())
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

    reason = (
        "node_cap" if nodes >= max_nodes
        else "time_cap" if time.time() - start >= seconds
        else "frontier_exhausted"
    )
    meta = {
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
        "quotient_join_hits": quotient_join_hits,
        "aligned_join_hits": aligned_join_hits,
        "best_join_cost": best_join_cost,
        "seconds": round(time.time() - start, 3),
    }
    if best_join_state is not None:
        meta["code"] = "best_quotient_orbit_join_near_miss"
        prefix = v4.reconstruct(parent, parent_edge, best_join_state)
        return prefix + tuple(best_join_suffix), meta
    return None, meta


def main():
    args = v4.parse_args()
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
    v4.save_json(out / "snapshot_ac_start.json", snapshot_obj)
    live_row = live[args.target_id]
    live_best = live_row.get("currentBestLength")
    if not isinstance(live_best, int):
        report = {
            "experiment": "acc-gssub-v5-atomic-orbit-join",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_status": live_row.get("status"),
            "live_best": live_best,
        }
        v4.save_json(out / "report.json", report)
        print("ATOMIC_ORBIT_SEARCH", json.dumps(report, sort_keys=True), flush=True)
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

    t1 = time.time()
    reverse_qsuffix, reverse_alignment_failures = build_reverse_quotient_suffixes(
        core, ns, reverse_paths, limits["max_total_relator_length"]
    )
    quotient_index_seconds = round(time.time() - t1, 3)
    print("REVERSE_ORBIT", json.dumps({
        "states": len(reverse_paths),
        "hist": reverse_hist,
        "reverse_seconds": reverse_seconds,
        "quotient_keys": len(reverse_qsuffix),
        "alignment_failures": reverse_alignment_failures,
        "quotient_index_seconds": quotient_index_seconds,
    }, sort_keys=True), flush=True)

    atomics, search = representative_atomic_search_orbit(
        core,
        ns,
        exact,
        reverse_paths,
        reverse_qsuffix,
        strict_bound=live_best,
        max_nodes=args.max_nodes,
        quotient_total_cap=qcap,
        total_cap=limits["max_total_relator_length"],
        reps_per_key=max(1, args.representatives_per_quotient),
        seconds=args.search_seconds,
    )

    report = {
        "experiment": "acc-gssub-v5-atomic-orbit-join",
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
        "reverse_quotient_keys": len(reverse_qsuffix),
        "reverse_alignment_failures": reverse_alignment_failures,
        "reverse_seconds": reverse_seconds,
        "quotient_index_seconds": quotient_index_seconds,
        "search": search,
        "verified": False,
        "candidate_length": None,
    }

    strict_submission = ""
    near_miss_submission = ""
    if atomics is not None:
        verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
        verified = bool(verdict.get("ok"))
        n = len(atomics)
        report["verdict"] = verdict
        report["verified"] = verified
        report["candidate_length"] = n
        report["strict_vs_frozen_live"] = n < live_best
        near_limit = int(math.floor(live_best * 1.10))
        report["near_miss_limit"] = near_limit
        report["near_miss_eligible"] = bool(verified and live_best <= n <= near_limit)
        row = f"{args.target_id}: {json.dumps(list(atomics), separators=(',', ':'))}\n"
        if verified and n < live_best:
            strict_submission = row
        elif verified and live_best <= n <= near_limit:
            near_miss_submission = row

    (out / "submission_v4.txt").write_text(strict_submission, encoding="utf-8")
    (out / "near_miss_v4.txt").write_text(near_miss_submission, encoding="utf-8")
    v4.save_json(out / "report.json", report)
    print("ATOMIC_ORBIT_SEARCH", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
