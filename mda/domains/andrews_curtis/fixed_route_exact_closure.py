#!/usr/bin/env python3
"""Exact fixed-route compiler closure diagnostic for the ACC MDA.

This does not invent a new solver or compiler language.

It replays one already-frozen search policy on one already-frozen target,
asserts that the quotient route SHA-256 is identical to prior scientific
evidence, then removes the compiler beam heuristic entirely for that fixed
route.  It exhaustively keeps every exact representative reachable in the
existing compiler transition language, subject only to an explicit finite
state cap.

Purpose:
- distinguish compiler beam SEARCH insufficiency from
- inadequacy that remains even after exact fixed-route compilation.

If the finite state cap is hit, the correct result is UNKNOWN_SEARCH.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--source-result", required=True)
    ap.add_argument("--policy", required=True, choices=["current", "mask3"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    ap.add_argument("--reverse-depth", type=int, default=7)
    ap.add_argument("--reverse-cap", type=int, default=250000)
    ap.add_argument("--exact-state-cap", type=int, default=100000)
    a = ap.parse_args()

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse,
        challenge_maps,
        compiled_superneighbor_candidates,
        compiled_superneighbors,
        exact_terminal_suffix,
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
    from verifier import core, stable_core

    source = json.loads(Path(a.source_result).read_text())
    assert source["experiment"] == "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1", source
    assert source["policy"] == a.policy, (source.get("policy"), a.policy)
    cid = source["challenge_id"]
    sid = source["stable_id"]

    manifest = json.loads(
        (acc / "competition" / "tools" / "verifier" / "data" / "manifest.json").read_text()
    )
    limits = manifest["limits"]
    ac_by, sac_by = challenge_maps(manifest)
    c = ac_by[cid]
    sc = sac_by[sid]
    exact_initial = tuple(tuple(w) for w in c["initial_relators"])
    r0, r1 = int_word_to_str(exact_initial[0]), int_word_to_str(exact_initial[1])
    initial_total = total_len(exact_initial)
    qcap = min(a.max_quotient_total, max(initial_total + 36, 48))

    ns = load_gssub(Path(a.acsolverx_root))

    # Re-run exactly the retained search mechanism and demand route identity.
    st = time.time()
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
    search_seconds = time.time() - st

    if qpath is None:
        result = {
            "experiment": "ACC_MDA_FIXED_ROUTE_EXACT_COMPILER_CLOSURE_V1",
            "challenge_id": cid,
            "policy": a.policy,
            "status": "STALE_AUTHORITY",
            "reason": "previously frozen quotient route did not reproduce",
            "nodes": int(nodes),
        }
        save(Path(a.out_dir) / "result.json", result)
        print("MDA_FIXED_ROUTE_CLOSURE", json.dumps(result, sort_keys=True))
        return

    sig = [path_state_key(ns, q) for q in qpath]
    raw = json.dumps(sig, separators=(",", ":"), sort_keys=False).encode()
    route_sha = hashlib.sha256(raw).hexdigest()
    expected_sha = source.get("quotient_path_sha256")
    if route_sha != expected_sha:
        result = {
            "experiment": "ACC_MDA_FIXED_ROUTE_EXACT_COMPILER_CLOSURE_V1",
            "challenge_id": cid,
            "policy": a.policy,
            "status": "STALE_AUTHORITY",
            "reason": "quotient route hash mismatch",
            "expected_sha256": expected_sha,
            "actual_sha256": route_sha,
            "nodes": int(nodes),
        }
        save(Path(a.out_dir) / "result.json", result)
        print("MDA_FIXED_ROUTE_CLOSURE", json.dumps(result, sort_keys=True))
        return

    rt = time.time()
    reverse_paths, reverse_hist = build_reverse(core, a.reverse_depth, a.reverse_cap)
    reverse_seconds = time.time() - rt

    # Exact finite closure over the *existing* compiler transition language.
    # active maps exact state -> exact minimum accumulated atomic cost.
    active = {exact_initial: 0}
    parents = []
    layer_stats = []
    closure_status = "COMPLETE"
    capped_at_step = None

    ct = time.time()
    for step_index, qstate in enumerate(qpath[1:], 1):
        desired = path_state_key(ns, qstate)
        nxt_best = {}
        nxt_parent = {}
        raw_candidates = 0

        for state, cost in active.items():
            cands = compiled_superneighbor_candidates(core, ns, state, desired, limits["max_total_relator_length"])
            if not cands:
                hit = compiled_superneighbors(core, ns, state, limits["max_total_relator_length"]).get(desired)
                if hit is not None:
                    cands = [hit]
            raw_candidates += len(cands)
            for nxt, edge in cands:
                nc = cost + len(edge)
                old = nxt_best.get(nxt)
                if old is None or nc < old:
                    nxt_best[nxt] = nc
                    nxt_parent[nxt] = (state, tuple(edge))

        layer_stats.append({
            "step": step_index,
            "input_exact_states": len(active),
            "raw_candidates": raw_candidates,
            "distinct_exact_states": len(nxt_best),
            "best_cost": min(nxt_best.values()) if nxt_best else None,
        })

        if not nxt_best:
            closure_status = "CERTIFIED_INADEQUATE_TRANSITION_LANGUAGE"
            capped_at_step = step_index
            active = {}
            break

        if len(nxt_best) > a.exact_state_cap:
            closure_status = "UNKNOWN_SEARCH"
            capped_at_step = step_index
            active = {}
            break

        parents.append(nxt_parent)
        active = nxt_best

    exact_atomics = None
    terminal_suffix_len = None
    terminal_state = None
    exact_cost = None

    if closure_status == "COMPLETE":
        finals = []
        for state, cost in active.items():
            suffix = exact_terminal_suffix(core, state, reverse_paths)
            if suffix is not None:
                finals.append((cost + len(suffix), state, tuple(suffix)))
        if not finals:
            closure_status = "CERTIFIED_INADEQUATE_TERMINAL_BRIDGE"
        else:
            exact_cost, terminal_state, suffix = min(finals, key=lambda x: x[0])
            terminal_suffix_len = len(suffix)

            edges = []
            cur = terminal_state
            for layer in reversed(parents):
                prev, edge = layer[cur]
                edges.append(edge)
                cur = prev
            edges.reverse()
            exact_atomics = tuple(m for edge in edges for m in edge) + suffix

            # Ground the exact-closure result independently.
            v = core.verify(c, list(exact_atomics), c["move_spec_version"], limits)
            stable = exact_atomics + (16, 15)
            sv = stable_core.verify(sc, list(stable), sc["move_spec_version"], limits)
            if not v.get("ok") or not sv.get("ok"):
                raise RuntimeError(("exact closure produced invalid certificate", v, sv))

    compile_seconds = time.time() - ct

    live_best = source.get("frozen_ac_best")
    beam_best = source.get("best_atomic_length")
    qsteps = len(qpath) - 1
    route_floor = qsteps  # one official multiplication is necessary per GS-Sub transition

    if closure_status == "UNKNOWN_SEARCH":
        diagnosis = "UNKNOWN_SEARCH_COMPILER_EXACT_CLOSURE"
    elif closure_status.startswith("CERTIFIED_INADEQUATE"):
        diagnosis = "CERTIFIED_INADEQUATE_CURRENT_COMPILER_TRANSITION_LANGUAGE_ON_FIXED_ROUTE"
    elif exact_cost is None:
        diagnosis = "UNKNOWN_AUTHORITY"
    elif isinstance(live_best, int) and exact_cost <= live_best and isinstance(beam_best, int) and beam_best > live_best:
        diagnosis = "CERTIFIED_COMPILER_BEAM_INADEQUACY"
    elif isinstance(beam_best, int) and exact_cost < beam_best:
        diagnosis = "COMPILER_BEAM_PARTIAL_RESIDUAL"
    else:
        diagnosis = "BEAM_SEARCH_NOT_RESIDUAL_ON_FIXED_ROUTE"

    result = {
        "experiment": "ACC_MDA_FIXED_ROUTE_EXACT_COMPILER_CLOSURE_V1",
        "challenge_id": cid,
        "stable_id": sid,
        "policy": a.policy,
        "source_run_scope": "immutable prospective discriminator run 34796578203",
        "source_result_sha256": expected_sha,
        "route_reproduced": True,
        "nodes": int(nodes),
        "search_seconds": search_seconds,
        "quotient_steps": qsteps,
        "route_atomic_floor": route_floor,
        "frozen_live_best": live_best,
        "source_best_atomic": beam_best,
        "source_best_beam": source.get("best_verified_beam"),
        "exact_state_cap": a.exact_state_cap,
        "closure_status": closure_status,
        "capped_at_step": capped_at_step,
        "exact_atomic_cost": exact_cost,
        "terminal_suffix_len": terminal_suffix_len,
        "exact_improvement_vs_source": (
            beam_best - exact_cost
            if isinstance(beam_best, int) and isinstance(exact_cost, int)
            else None
        ),
        "exact_gap_to_frozen_live": (
            exact_cost - live_best
            if isinstance(exact_cost, int) and isinstance(live_best, int)
            else None
        ),
        "reverse_states": len(reverse_paths),
        "reverse_hist": reverse_hist,
        "reverse_seconds": reverse_seconds,
        "compile_seconds": compile_seconds,
        "layer_stats": layer_stats,
        "diagnosis": diagnosis,
        "growth_authorized": diagnosis.startswith("CERTIFIED_"),
        "claim_boundary": (
            "Fixed reproduced quotient route and existing exact compiler transition language only. "
            "UNKNOWN_SEARCH if exact-state closure exceeds the declared finite cap."
        ),
    }

    out = Path(a.out_dir)
    if exact_atomics is not None:
        (out / "candidate_ac.txt").parent.mkdir(parents=True, exist_ok=True)
        (out / "candidate_ac.txt").write_text(
            f"{cid}: {json.dumps(list(exact_atomics), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    save(out / "result.json", result)
    print("MDA_FIXED_ROUTE_CLOSURE", json.dumps({
        "cid": cid,
        "policy": a.policy,
        "closure_status": closure_status,
        "qsteps": qsteps,
        "route_floor": route_floor,
        "beam_best": beam_best,
        "exact_atomic": exact_cost,
        "live_best": live_best,
        "diagnosis": diagnosis,
        "capped_at_step": capped_at_step,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
