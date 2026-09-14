#!/usr/bin/env python3
"""Probe whether the existing fixed-route compiler transition language misses a
strictly shorter official micro-bridge.

The source is an already verified exact-closure certificate on an immutable
quotient route.  We segment that certificate by quotient transition, select one
of the most expensive segments, and run an independent breadth-first search in
the *official atomic move graph* for any shorter path from the same exact
starting state to the same next quotient class.

Finding one is a separator: the current compiler transition language omitted a
real official consequence.  Not finding one is only a certificate when the
entire shorter-depth BFS completes under the official limits; hitting the cap is
UNKNOWN_SEARCH.

This is a diagnostic probe.  A found local bridge is not promoted until a later
end-to-end route replay proves prospective gain and ablation proves causality.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import time
from pathlib import Path


def parse_candidate(path: Path, cid: str) -> tuple[int, ...]:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        q, rhs = line.split(":", 1)
        if q.strip() == cid:
            return tuple(json.loads(rhs.strip()))
    raise RuntimeError(("candidate_missing", cid, str(path)))


def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--source-result", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--policy", required=True, choices=["current", "mask3"])
    ap.add_argument("--rank", type=int, default=0, help="0 = most expensive quotient segment")
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    ap.add_argument("--bfs-state-cap", type=int, default=600000)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        challenge_maps,
        gssub_key,
        int_word_to_str,
        load_gssub,
        path_state_key,
        total_len,
    )
    sys.path.insert(0, str(root / "acc_competitive"))
    from reach_v2_priority_language import solve_subset_priority

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition" / "tools"))
    from verifier import core

    source = json.loads(Path(a.source_result).read_text())
    cid = source["challenge_id"]
    assert source["policy"] == a.policy, (source["policy"], a.policy)
    candidate = parse_candidate(Path(a.candidate), cid)

    manifest = json.loads(
        (acc / "competition" / "tools" / "verifier" / "data" / "manifest.json").read_text()
    )
    limits = manifest["limits"]
    ac_by, _ = challenge_maps(manifest)
    c = ac_by[cid]
    exact_initial = tuple(tuple(w) for w in c["initial_relators"])
    r0, r1 = int_word_to_str(exact_initial[0]), int_word_to_str(exact_initial[1])
    initial_total = total_len(exact_initial)
    qcap = min(a.max_quotient_total, max(initial_total + 36, 48))

    ns = load_gssub(Path(a.acsolverx_root))

    # Reproduce immutable quotient route.
    if a.policy == "current":
        solver = ns["ACRelatorSolver"](
            r0, r1,
            max_nodes=a.max_nodes,
            max_len=qcap,
            verbose=False,
            stop_early=False,
        )
        found = solver.solve()
        if len(found) == 3:
            qpath, nodes, _ = found
        else:
            qpath, nodes = found[:2]
    else:
        qpath, nodes, _ = solve_subset_priority(ns, r0, r1, a.max_nodes, qcap, 3)

    if qpath is None:
        raise RuntimeError("immutable quotient route did not reproduce")

    qkeys = [path_state_key(ns, q) for q in qpath]
    raw = json.dumps(qkeys, separators=(",", ":"), sort_keys=False).encode()
    route_sha = hashlib.sha256(raw).hexdigest()
    assert route_sha == source["source_result_sha256"], (route_sha, source["source_result_sha256"])

    # Verify the source candidate and segment only the quotient-following prefix.
    v = core.verify(c, list(candidate), c["move_spec_version"], limits)
    assert v.get("ok") is True, v

    segments = []
    state = exact_initial
    qi = 0
    seg_start = state
    seg_moves = []
    for move_index, m in enumerate(candidate):
        state = core.apply_move(state, m)
        seg_moves.append(m)
        if qi + 1 < len(qkeys) and gssub_key(ns, state) == qkeys[qi + 1]:
            segments.append({
                "quotient_step": qi + 1,
                "start_state": seg_start,
                "end_state": state,
                "desired_key": qkeys[qi + 1],
                "moves": tuple(seg_moves),
                "cost": len(seg_moves),
                "end_move_index": move_index,
            })
            qi += 1
            seg_start = state
            seg_moves = []
            if qi == len(qkeys) - 1:
                break

    if qi != len(qkeys) - 1:
        raise RuntimeError(("candidate_does_not_follow_route", qi, len(qkeys)-1))

    ranked = sorted(
        segments,
        key=lambda x: (-x["cost"], x["quotient_step"])
    )
    if a.rank < 0 or a.rank >= len(ranked):
        raise ValueError(("rank_out_of_range", a.rank, len(ranked)))
    seg = ranked[a.rank]
    start = tuple(tuple(w) for w in seg["start_state"])
    desired = tuple(seg["desired_key"])
    current_cost = int(seg["cost"])

    # Search only paths STRICTLY shorter than the current verified micro-bridge.
    # The search is over the real official transition function, with the same
    # relator-length limit as the verifier.
    target_depth = current_cost - 1
    t0 = time.time()
    q = collections.deque([(start, ())])
    seen = {start: 0}
    found_path = None
    found_state = None
    expanded = 0
    hit_cap = False

    # If the segment cost is already 1 there can be no shorter nonempty bridge.
    if target_depth >= 1:
        while q:
            s, path = q.popleft()
            d = len(path)
            if d >= target_depth:
                continue
            expanded += 1
            if expanded > a.bfs_state_cap:
                hit_cap = True
                break
            for m in range(core.NUM_MOVES):
                n = core.apply_move(s, m)
                if total_len(n) > limits["max_total_relator_length"]:
                    continue
                nd = d + 1
                old = seen.get(n)
                if old is not None and old <= nd:
                    continue
                seen[n] = nd
                np = path + (m,)
                if gssub_key(ns, n) == desired:
                    found_path = np
                    found_state = n
                    q.clear()
                    break
                q.append((n, np))
            if found_path is not None:
                break

    seconds = time.time() - t0

    if found_path is not None:
        status = "COMPILER_TRANSITION_LANGUAGE_SEPARATOR_FOUND"
        warrant = "VERIFIED_SEPARATOR"
    elif hit_cap:
        status = "UNKNOWN_SEARCH"
        warrant = "UNKNOWN_SEARCH"
    else:
        status = "NO_SHORTER_MICROBRIDGE_IN_EXHAUSTED_DEPTH"
        warrant = "BOUNDED_COMPLETE"

    result = {
        "experiment": "ACC_MDA_LOCAL_OFFICIAL_MICROBRIDGE_V1",
        "challenge_id": cid,
        "policy": a.policy,
        "route_sha256": route_sha,
        "rank": a.rank,
        "quotient_step": seg["quotient_step"],
        "current_segment_cost": current_cost,
        "current_segment_moves": list(seg["moves"]),
        "strict_search_max_depth": target_depth,
        "bfs_state_cap": a.bfs_state_cap,
        "expanded_states": expanded,
        "seen_states": len(seen),
        "hit_cap": hit_cap,
        "seconds": seconds,
        "status": status,
        "warrant_status": warrant,
        "shorter_path": list(found_path) if found_path is not None else None,
        "shorter_cost": len(found_path) if found_path is not None else None,
        "local_saving": (
            current_cost - len(found_path)
            if found_path is not None
            else 0
        ),
        "found_state_same_as_source_end": (
            found_state == tuple(tuple(w) for w in seg["end_state"])
            if found_state is not None
            else None
        ),
        "promotion_authorized": False,
        "next_if_separator": (
            "splice the found exact representative into fixed-route continuation, "
            "re-optimize downstream using existing closure, replay V0/Q_t, and ablate"
        ),
        "claim_boundary": (
            "One quotient transition on one frozen route. A found path proves the "
            "existing compiler transition language omitted a shorter official bridge. "
            "No separator plus cap => UNKNOWN_SEARCH; exhaustive no-separator is local only."
        ),
    }

    out = Path(a.out_dir)
    save(out / "result.json", result)
    print("MDA_LOCAL_MICROBRIDGE", json.dumps({
        "cid": cid,
        "policy": a.policy,
        "rank": a.rank,
        "step": seg["quotient_step"],
        "current_cost": current_cost,
        "status": status,
        "expanded": expanded,
        "shorter_cost": result["shorter_cost"],
        "saving": result["local_saving"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
