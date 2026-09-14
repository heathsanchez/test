#!/usr/bin/env python3
"""Bounded local quotient-route shortcut discriminator for ACC MDA.

Question:
  Is the dominant residual still explainable by inadequate SEARCH inside the
  already-retained GS-Sub route language, or must we keep route-language
  inadequacy alive?

Method:
  * reproduce one immutable quotient route exactly;
  * for every fixed-width window, exhaustively search the EXISTING GS-Sub
    neighbor graph for a strictly shorter path between the same quotient
    endpoints;
  * if a shortcut exists, splice only that route segment;
  * exact-close the spliced route through the EXISTING exact compiler language;
  * independently replay the official AC and Stable AC verifiers.

A found quotient shortcut is a certified separator proving the old search route
was not locally shortest in its own language.  It only becomes a causal
competitive repair if end-to-end exact atomic length improves.  Search caps
produce UNKNOWN_SEARCH, never inadequacy claims.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import time
from pathlib import Path


def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--source-result", required=True)
    ap.add_argument("--baseline-result", required=True)
    ap.add_argument("--policy", required=True, choices=["current", "mask3"])
    ap.add_argument("--window", type=int, default=4)
    ap.add_argument("--window-state-cap", type=int, default=100000)
    ap.add_argument("--exact-state-cap", type=int, default=100000)
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    ap.add_argument("--reverse-depth", type=int, default=7)
    ap.add_argument("--reverse-cap", type=int, default=250000)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    if a.window < 2:
        raise ValueError("window must be >=2")

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse,
        challenge_maps,
        compiled_superneighbor_candidates,
        compiled_superneighbors,
        exact_terminal_suffix,
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
    baseline = json.loads(Path(a.baseline_result).read_text())
    assert source["experiment"] == "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1", source
    assert source["policy"] == a.policy, (source.get("policy"), a.policy)
    assert baseline["experiment"] == "ACC_MDA_FIXED_ROUTE_EXACT_COMPILER_CLOSURE_V1", baseline
    assert baseline["policy"] == a.policy, (baseline.get("policy"), a.policy)
    assert baseline["challenge_id"] == source["challenge_id"], (baseline, source)
    assert baseline["closure_status"] == "COMPLETE", baseline

    cid = source["challenge_id"]
    sid = source["stable_id"]
    baseline_atomic = baseline["exact_atomic_cost"]
    baseline_qsteps = baseline["quotient_steps"]

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
    reduce_relator = ns["reduce_relator_nj"]
    canonical_pair = ns["canonical_pair_nj"]
    state_to_key = ns["state_to_key"]
    str_to_arr = ns["str_to_arr"]
    get_neighbors = ns["get_neighbors_nj"]

    def key_to_state(key):
        return (str_to_arr(key[0]), str_to_arr(key[1]))

    def quotient_neighbors(key):
        r1a, r2a = key_to_state(key)
        out = []
        seen_local = set()
        for nr1, nr2 in get_neighbors(r1a, r2a):
            nr1r = reduce_relator(nr1)
            nr2r = reduce_relator(nr2)
            if len(nr1r) + len(nr2r) >= qcap:
                continue
            c1, c2 = canonical_pair(nr1r, nr2r)
            knew = state_to_key((c1, c2))
            if knew in seen_local:
                continue
            seen_local.add(knew)
            out.append(knew)
        return out

    # Reproduce the frozen route and demand byte-level route identity.
    st = time.time()
    if a.policy == "current":
        solver = ns["ACRelatorSolver"](
            r0, r1, max_nodes=a.max_nodes, max_len=qcap,
            verbose=False, stop_early=False,
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
        raise RuntimeError("frozen route did not reproduce")

    sig = [path_state_key(ns, q) for q in qpath]
    route_sha = hashlib.sha256(
        json.dumps(sig, separators=(",", ":"), sort_keys=False).encode()
    ).hexdigest()
    assert route_sha == source["quotient_path_sha256"], (route_sha, source["quotient_path_sha256"])
    assert len(sig) - 1 == baseline_qsteps, (len(sig)-1, baseline_qsteps)

    # Exhaustive local BFS below the current window length.
    window_results = []
    shortcuts = []
    wt0 = time.time()
    for start_i in range(0, len(sig) - a.window):
        end_i = start_i + a.window
        start_key = sig[start_i]
        target_key = sig[end_i]
        q = collections.deque([start_key])
        depth = {start_key: 0}
        parent = {start_key: None}
        expanded = 0
        hit_cap = False
        found_key = None

        while q:
            key = q.popleft()
            d = depth[key]
            if d >= a.window - 1:
                continue
            expanded += 1
            if expanded > a.window_state_cap:
                hit_cap = True
                break
            for nk in quotient_neighbors(key):
                nd = d + 1
                if nk in depth and depth[nk] <= nd:
                    continue
                depth[nk] = nd
                parent[nk] = key
                if nk == target_key:
                    found_key = nk
                    q.clear()
                    break
                q.append(nk)
            if found_key is not None:
                break

        if found_key is not None:
            rev = []
            cur = found_key
            while cur is not None:
                rev.append(cur)
                cur = parent[cur]
            shortcut = list(reversed(rev))
            saving = a.window - (len(shortcut) - 1)
            rec = {
                "start_step": start_i,
                "end_step": end_i,
                "original_edges": a.window,
                "shortcut_edges": len(shortcut) - 1,
                "saving": saving,
                "expanded_states": expanded,
                "seen_states": len(depth),
                "status": "QUOTIENT_SHORTCUT_FOUND",
                "shortcut_keys": shortcut,
            }
            shortcuts.append(rec)
        else:
            rec = {
                "start_step": start_i,
                "end_step": end_i,
                "original_edges": a.window,
                "shortcut_edges": None,
                "saving": 0,
                "expanded_states": expanded,
                "seen_states": len(depth),
                "status": "UNKNOWN_SEARCH" if hit_cap else "NO_SHORTER_PATH_IN_EXHAUSTED_WINDOW",
            }
        window_results.append(rec)

    window_seconds = time.time() - wt0

    # Choose the strongest certified separator without peeking at downstream
    # compilation: max quotient-edge saving, then least search work, then
    # earliest window.
    chosen = None
    if shortcuts:
        chosen = min(
            shortcuts,
            key=lambda r: (-r["saving"], r["expanded_states"], r["start_step"])
        )

    new_sig = None
    exact_atomics = None
    exact_cost = None
    closure_status = None
    capped_at_step = None
    layer_stats = []
    reverse_seconds = None
    compile_seconds = None
    terminal_suffix_len = None

    if chosen is not None:
        i = chosen["start_step"]
        j = chosen["end_step"]
        sk = chosen["shortcut_keys"]
        new_sig = sig[: i + 1] + sk[1:] + sig[j + 1 :]
        assert new_sig[0] == sig[0] and new_sig[-1] == sig[-1]
        assert len(new_sig) - 1 == baseline_qsteps - chosen["saving"]

        rt = time.time()
        reverse_paths, reverse_hist = build_reverse(core, a.reverse_depth, a.reverse_cap)
        reverse_seconds = time.time() - rt

        active = {exact_initial: 0}
        parents = []
        closure_status = "COMPLETE"
        ct = time.time()

        for step_index, desired in enumerate(new_sig[1:], 1):
            nxt_best = {}
            nxt_parent = {}
            raw_candidates = 0
            for state, cost in active.items():
                cands = compiled_superneighbor_candidates(
                    core, ns, state, desired, limits["max_total_relator_length"]
                )
                if not cands:
                    hit = compiled_superneighbors(
                        core, ns, state, limits["max_total_relator_length"]
                    ).get(desired)
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
                closure_status = "CERTIFIED_INADEQUATE_EXISTING_COMPILER_TRANSITION_LANGUAGE"
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

        if closure_status == "COMPLETE":
            finals = []
            for state, cost in active.items():
                suffix = exact_terminal_suffix(core, state, reverse_paths)
                if suffix is not None:
                    finals.append((cost + len(suffix), state, tuple(suffix)))
            if not finals:
                closure_status = "CERTIFIED_INADEQUATE_EXISTING_TERMINAL_BRIDGE"
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

                v = core.verify(c, list(exact_atomics), c["move_spec_version"], limits)
                stable = exact_atomics + (16, 15)
                sv = stable_core.verify(sc, list(stable), sc["move_spec_version"], limits)
                if not v.get("ok") or not sv.get("ok"):
                    raise RuntimeError(("spliced exact route invalid", v, sv))

        compile_seconds = time.time() - ct
    else:
        reverse_hist = None

    unknown_windows = sum(r["status"] == "UNKNOWN_SEARCH" for r in window_results)
    complete_no = sum(r["status"] == "NO_SHORTER_PATH_IN_EXHAUSTED_WINDOW" for r in window_results)

    if chosen is None:
        if unknown_windows:
            diagnosis = "UNKNOWN_SEARCH_ROUTE_SHORTCUT"
        else:
            diagnosis = "NO_LOCAL_ROUTE_SHORTCUT_IN_EXHAUSTED_WIDTH"
    elif closure_status == "UNKNOWN_SEARCH":
        diagnosis = "CERTIFIED_ROUTE_SEARCH_INADEQUACY_CAUSAL_UNKNOWN"
    elif closure_status and closure_status.startswith("CERTIFIED_INADEQUATE"):
        diagnosis = "CERTIFIED_ROUTE_SEARCH_INADEQUACY_COMPILER_BLOCKED"
    elif isinstance(exact_cost, int) and exact_cost < baseline_atomic:
        diagnosis = "CERTIFIED_ROUTE_SEARCH_INADEQUACY_CAUSAL"
    else:
        diagnosis = "CERTIFIED_ROUTE_SEARCH_INADEQUACY_NONCAUSAL"

    result = {
        "experiment": "ACC_MDA_LOCAL_QUOTIENT_ROUTE_SHORTCUT_V1",
        "challenge_id": cid,
        "stable_id": sid,
        "policy": a.policy,
        "route_sha256": route_sha,
        "baseline_quotient_steps": baseline_qsteps,
        "baseline_exact_atomic": baseline_atomic,
        "window": a.window,
        "window_state_cap": a.window_state_cap,
        "windows_tested": len(window_results),
        "shortcut_count": len(shortcuts),
        "unknown_window_count": unknown_windows,
        "bounded_complete_no_shortcut_count": complete_no,
        "window_search_seconds": window_seconds,
        "route_reproduction_search_seconds": search_seconds,
        "chosen_shortcut": chosen,
        "spliced_quotient_steps": (len(new_sig)-1) if new_sig is not None else None,
        "closure_status": closure_status,
        "capped_at_step": capped_at_step,
        "exact_state_cap": a.exact_state_cap,
        "spliced_exact_atomic": exact_cost,
        "end_to_end_atomic_saving": (
            baseline_atomic - exact_cost
            if isinstance(exact_cost, int) else None
        ),
        "terminal_suffix_len": terminal_suffix_len,
        "reverse_seconds": reverse_seconds,
        "compile_seconds": compile_seconds,
        "layer_stats": layer_stats,
        "window_results": window_results,
        "diagnosis": diagnosis,
        "growth_beyond_existing_route_language_authorized": False,
        "claim_boundary": (
            f"All width-{a.window} windows on one immutable GS-Sub route. "
            "A found shortcut certifies local search-route inadequacy inside the "
            "existing route language. Failure is only bounded local evidence; "
            "caps remain UNKNOWN_SEARCH."
        ),
    }

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if exact_atomics is not None:
        (out / "candidate_ac.txt").write_text(
            f"{cid}: {json.dumps(list(exact_atomics), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    save(out / "result.json", result)
    print("MDA_ROUTE_SHORTCUT", json.dumps({
        "cid": cid,
        "policy": a.policy,
        "window": a.window,
        "shortcuts": len(shortcuts),
        "unknown_windows": unknown_windows,
        "chosen_saving": None if chosen is None else chosen["saving"],
        "baseline_qsteps": baseline_qsteps,
        "spliced_qsteps": result["spliced_quotient_steps"],
        "baseline_atomic": baseline_atomic,
        "spliced_atomic": exact_cost,
        "atomic_saving": result["end_to_end_atomic_saving"],
        "diagnosis": diagnosis,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
