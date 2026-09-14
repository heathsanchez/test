#!/usr/bin/env python3
"""Causal end-to-end test for one certified local official microbridge.

The change is intentionally tiny and scoped: replace exactly one already-frozen
compiler transition by the shorter official atomic bridge discovered by the
independent microbridge probe, then use the *existing* compiler transition
language for the rest of the same immutable quotient route.

This is not a general compiler change.  It asks whether the local separator
actually causes an end-to-end verified gain.  Removing the proposal restores
the frozen exact-closure baseline, so the baseline is the ablation control.
"""
from __future__ import annotations

import argparse
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
    ap.add_argument("--closure-result", required=True)
    ap.add_argument("--closure-candidate", required=True)
    ap.add_argument("--microbridge-result", required=True)
    ap.add_argument("--policy", default="current", choices=["current", "mask3"])
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    ap.add_argument("--reverse-depth", type=int, default=7)
    ap.add_argument("--reverse-cap", type=int, default=250000)
    ap.add_argument("--exact-state-cap", type=int, default=100000)
    ap.add_argument("--out-dir", required=True)
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

    closure = json.loads(Path(a.closure_result).read_text())
    proposal = json.loads(Path(a.microbridge_result).read_text())
    assert closure["challenge_id"] == proposal["challenge_id"], (closure, proposal)
    assert closure["policy"] == proposal["policy"] == a.policy, (closure.get("policy"), proposal.get("policy"))
    assert closure["closure_status"] == "COMPLETE", closure
    assert proposal["status"] == "COMPILER_TRANSITION_LANGUAGE_SEPARATOR_FOUND", proposal
    assert proposal["warrant_status"] == "VERIFIED_SEPARATOR", proposal

    cid = closure["challenge_id"]
    sid = closure["stable_id"]
    baseline = parse_candidate(Path(a.closure_candidate), cid)
    baseline_len = len(baseline)
    assert baseline_len == closure["exact_atomic_cost"], (baseline_len, closure["exact_atomic_cost"])

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

    # Reproduce the exact frozen quotient route.
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
    if qpath is None:
        raise RuntimeError("immutable quotient route did not reproduce")

    qkeys = [path_state_key(ns, q) for q in qpath]
    route_sha = hashlib.sha256(
        json.dumps(qkeys, separators=(",", ":"), sort_keys=False).encode()
    ).hexdigest()
    assert route_sha == closure["source_result_sha256"], (route_sha, closure["source_result_sha256"])
    assert route_sha == proposal["route_sha256"], (route_sha, proposal["route_sha256"])

    # Ground the ablation baseline.
    bv = core.verify(c, list(baseline), c["move_spec_version"], limits)
    bstable = baseline + (16, 15)
    bsv = stable_core.verify(sc, list(bstable), sc["move_spec_version"], limits)
    assert bv.get("ok") and bsv.get("ok"), (bv, bsv)

    # Segment the exact baseline by quotient transitions to recover the exact
    # state/prefix immediately before the certified local change.
    target_step = int(proposal["quotient_step"])
    state = exact_initial
    qi = 0
    segment_moves = []
    prefix = []
    start_state = None
    baseline_segment = None
    baseline_end_state = None
    for m in baseline:
        if qi == target_step - 1 and start_state is None:
            start_state = state
        state = core.apply_move(state, m)
        segment_moves.append(m)
        if qi + 1 < len(qkeys) and gssub_key(ns, state) == qkeys[qi + 1]:
            if qi + 1 == target_step:
                baseline_segment = tuple(segment_moves)
                baseline_end_state = state
                break
            prefix.extend(segment_moves)
            qi += 1
            segment_moves = []

    if start_state is None or baseline_segment is None:
        raise RuntimeError(("could_not_recover_target_segment", target_step, qi))
    assert tuple(baseline_segment) == tuple(proposal["current_segment_moves"]), (
        baseline_segment, proposal["current_segment_moves"]
    )

    bridge = tuple(int(x) for x in proposal["shorter_path"])
    changed_state = start_state
    for m in bridge:
        changed_state = core.apply_move(changed_state, m)
    assert gssub_key(ns, changed_state) == tuple(qkeys[target_step]), (
        gssub_key(ns, changed_state), qkeys[target_step]
    )

    # Continue with exact closure over the existing compiler language from the
    # changed exact representative.  No further new transition is introduced.
    rt = time.time()
    reverse_paths, reverse_hist = build_reverse(core, a.reverse_depth, a.reverse_cap)
    reverse_seconds = time.time() - rt

    active = {changed_state: 0}
    parents = []
    layer_stats = []
    closure_status = "COMPLETE"
    capped_at_step = None
    ct = time.time()

    for step_index in range(target_step + 1, len(qkeys)):
        desired = qkeys[step_index]
        nxt_best = {}
        nxt_parent = {}
        raw_candidates = 0
        for s, cost in active.items():
            cands = compiled_superneighbor_candidates(
                core, ns, s, desired, limits["max_total_relator_length"]
            )
            if not cands:
                hit = compiled_superneighbors(
                    core, ns, s, limits["max_total_relator_length"]
                ).get(desired)
                if hit is not None:
                    cands = [hit]
            raw_candidates += len(cands)
            for nxt, edge in cands:
                nc = cost + len(edge)
                old = nxt_best.get(nxt)
                if old is None or nc < old:
                    nxt_best[nxt] = nc
                    nxt_parent[nxt] = (s, tuple(edge))

        layer_stats.append({
            "step": step_index,
            "input_exact_states": len(active),
            "raw_candidates": raw_candidates,
            "distinct_exact_states": len(nxt_best),
            "best_cost": min(nxt_best.values()) if nxt_best else None,
        })
        if not nxt_best:
            closure_status = "CERTIFIED_INADEQUATE_EXISTING_CONTINUATION_LANGUAGE"
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

    candidate = None
    suffix_len = None
    continuation_cost = None
    if closure_status == "COMPLETE":
        finals = []
        for s, cost in active.items():
            suffix = exact_terminal_suffix(core, s, reverse_paths)
            if suffix is not None:
                finals.append((cost + len(suffix), s, tuple(suffix)))
        if not finals:
            closure_status = "CERTIFIED_INADEQUATE_EXISTING_TERMINAL_BRIDGE"
        else:
            continuation_cost, final_state, suffix = min(finals, key=lambda x: x[0])
            suffix_len = len(suffix)
            edges = []
            cur = final_state
            for layer in reversed(parents):
                prev, edge = layer[cur]
                edges.append(edge)
                cur = prev
            edges.reverse()
            continuation = tuple(m for edge in edges for m in edge) + suffix
            candidate = tuple(prefix) + bridge + continuation

    continuation_seconds = time.time() - ct
    result = {
        "experiment": "ACC_MDA_SCOPED_MICROBRIDGE_CAUSAL_REPAIR_V1",
        "challenge_id": cid,
        "policy": a.policy,
        "route_sha256": route_sha,
        "proposal_rank": proposal["rank"],
        "proposal_step": target_step,
        "proposal_warrant": proposal["warrant_status"],
        "baseline_segment_cost": len(baseline_segment),
        "proposal_segment_cost": len(bridge),
        "local_saving": len(baseline_segment) - len(bridge),
        "proposal_same_exact_end_state": changed_state == baseline_end_state,
        "baseline_atomic_length": baseline_len,
        "baseline_verified": True,
        "closure_status": closure_status,
        "capped_at_step": capped_at_step,
        "reverse_states": len(reverse_paths),
        "reverse_hist": reverse_hist,
        "reverse_seconds": reverse_seconds,
        "continuation_seconds": continuation_seconds,
        "continuation_cost_after_proposal": continuation_cost,
        "terminal_suffix_len": suffix_len,
        "layer_stats": layer_stats,
        "full_candidate_length": len(candidate) if candidate is not None else None,
        "end_to_end_saving": baseline_len - len(candidate) if candidate is not None else None,
        "ablation_length": baseline_len,
        "causal_gain": bool(candidate is not None and len(candidate) < baseline_len),
        "promotion_scope": "none",
        "global_inheritance_authorized": False,
        "claim_boundary": (
            "One certified local bridge on one immutable target/route. "
            "End-to-end gain earns only a scoped causal repair; transfer must be "
            "shown before compiling a general capability."
        ),
    }

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if candidate is not None:
        v = core.verify(c, list(candidate), c["move_spec_version"], limits)
        stable = candidate + (16, 15)
        sv = stable_core.verify(sc, list(stable), sc["move_spec_version"], limits)
        result["ac_verdict"] = v
        result["stable_verdict"] = sv
        if not v.get("ok") or not sv.get("ok"):
            raise RuntimeError(("scoped repair invalid", v, sv))
        (out / "candidate_ac.txt").write_text(
            f"{cid}: {json.dumps(list(candidate), separators=(',', ':'))}\n",
            encoding="utf-8",
        )

    save(out / "result.json", result)
    print("MDA_SCOPED_MICROBRIDGE_REPAIR", json.dumps({
        "cid": cid,
        "rank": proposal["rank"],
        "step": target_step,
        "local_saving": result["local_saving"],
        "closure_status": closure_status,
        "baseline": baseline_len,
        "candidate": result["full_candidate_length"],
        "end_to_end_saving": result["end_to_end_saving"],
        "causal_gain": result["causal_gain"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
