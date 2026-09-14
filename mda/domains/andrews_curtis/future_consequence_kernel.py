#!/usr/bin/env python3
"""Finite future-consequence kernel test for the ACC MDA.

This directly tests the state-test formalism on a frozen ACC route.

We look for exact states that the current quotient representation treats as the
same AND that have the same immediate one-step atomic consequence.  Selection
is frozen using only those present/local facts.  We then expose the tied states
to longer future continuations from the same frozen route.

If a later horizon separates them, we have a certified bounded false merge:

    same current representation + same immediate consequence
    but different future consequential signature.

No new solver, heuristic, compiler transition, or representation is introduced.
Caps yield UNKNOWN_SEARCH.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import time
from collections import defaultdict
from pathlib import Path


def save(path: Path, obj) -> None:
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
    ap.add_argument("--selection-state-cap", type=int, default=256)
    ap.add_argument("--future-state-cap", type=int, default=50000)
    ap.add_argument("--rep-cap", type=int, default=8)
    ap.add_argument("--horizons", default="2,4,8,16")
    a = ap.parse_args()

    horizons = sorted(set(int(x) for x in a.horizons.split(",") if x.strip()))
    if not horizons or min(horizons) < 2:
        raise ValueError("horizons must be >=2")
    max_h = max(horizons)

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        challenge_maps,
        compiled_superneighbor_candidates,
        compiled_superneighbors,
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
    assert source["experiment"] == "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1", source
    assert source["policy"] == a.policy, (source.get("policy"), a.policy)

    cid = source["challenge_id"]
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

    # Reproduce the immutable quotient route.
    t0 = time.time()
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
    route_search_seconds = time.time() - t0
    if qpath is None:
        raise RuntimeError("frozen route did not reproduce")

    sig = [path_state_key(ns, q) for q in qpath]
    route_sha = hashlib.sha256(
        json.dumps(sig, separators=(",", ":"), sort_keys=False).encode()
    ).hexdigest()
    assert route_sha == source["quotient_path_sha256"], (route_sha, source["quotient_path_sha256"])

    def propagate(active, desired, cap):
        """Exact closure for one fixed quotient transition."""
        nxt_best = {}
        raw = 0
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
            raw += len(cands)
            for nxt, edge in cands:
                nc = cost + len(edge)
                old = nxt_best.get(nxt)
                if old is None or nc < old:
                    nxt_best[nxt] = nc
        if len(nxt_best) > cap:
            return None, {"status": "UNKNOWN_SEARCH", "distinct": len(nxt_best), "raw": raw}
        if not nxt_best:
            return {}, {"status": "NO_TRANSITION", "distinct": 0, "raw": raw}
        return nxt_best, {
            "status": "COMPLETE",
            "distinct": len(nxt_best),
            "raw": raw,
            "best_cost": min(nxt_best.values()),
        }

    # Develop exact representatives along the frozen route until we find an
    # EARLIEST layer with a local-cost tie.  This freezes X before any longer
    # future consequence is inspected.
    active = {exact_initial: 0}
    layer_trace = []
    selected_layer = None
    selected_local_cost = None
    selected_states = None
    selection_status = "NO_TIED_PRESENT_FOUND"

    for layer_i in range(0, len(sig) - max_h):
        if layer_i > 0:
            desired = sig[layer_i]
            nxt, meta = propagate(active, desired, a.selection_state_cap)
            layer_trace.append({"layer": layer_i, **meta})
            if nxt is None:
                selection_status = "UNKNOWN_SEARCH_SELECTION_CLOSURE"
                break
            if not nxt:
                selection_status = "NO_TRANSITION_SELECTION_CLOSURE"
                break
            active = nxt

        if len(active) < 2:
            continue

        # One-step consequence only; longer horizons remain hidden at selection.
        desired1 = sig[layer_i + 1]
        groups = defaultdict(list)
        one_step_meta = []
        for st in sorted(active, key=repr):
            nxt1, meta1 = propagate({st: 0}, desired1, a.selection_state_cap)
            if nxt1 is None or not nxt1:
                one_step_meta.append({"state": repr(st), "status": meta1["status"]})
                continue
            c1 = min(nxt1.values())
            groups[c1].append(st)
            one_step_meta.append({
                "state": repr(st),
                "status": "COMPLETE",
                "one_step_cost": c1,
                "endpoint_exact_states": len(nxt1),
            })

        ties = [(cost, sts) for cost, sts in groups.items() if len(sts) >= 2]
        if not ties:
            continue

        # Deterministic, future-blind tie selection:
        # largest tied group; then lower immediate cost.
        cost, sts = min(ties, key=lambda z: (-len(z[1]), z[0]))
        sts = sorted(sts, key=repr)
        selected_layer = layer_i
        selected_local_cost = cost
        selected_states = sts[: a.rep_cap]
        selection_status = "FROZEN_LOCAL_TIE"
        layer_trace.append({
            "layer": layer_i,
            "selection": True,
            "active_exact_states": len(active),
            "tied_group_size": len(sts),
            "selected_count": len(selected_states),
            "selected_one_step_cost": cost,
            "selection_truncated": len(sts) > a.rep_cap,
            "one_step_meta": one_step_meta,
        })
        break

    if selected_states is None:
        result = {
            "experiment": "ACC_MDA_FUTURE_CONSEQUENCE_KERNEL_V1",
            "challenge_id": cid,
            "policy": a.policy,
            "route_sha256": route_sha,
            "route_steps": len(sig) - 1,
            "route_search_seconds": route_search_seconds,
            "selection_status": selection_status,
            "selection_layer": selected_layer,
            "layer_trace": layer_trace,
            "status": "UNKNOWN_SEARCH" if selection_status.startswith("UNKNOWN") else "NO_LOCAL_TIE_IN_TESTED_SCOPE",
            "claim_boundary": "No future-signature claim without a frozen same-quotient same-immediate-cost state set.",
        }
        save(Path(a.out_dir) / "result.json", result)
        print("MDA_KERNEL_PAIRING", json.dumps({
            "cid": cid, "policy": a.policy, "status": result["status"],
            "selection_status": selection_status,
        }, sort_keys=True))
        return

    # Now reveal the future.  Each test t_h is the next h quotient transitions
    # of the SAME frozen route.  e(x,t_h) is minimum official atomic cost to
    # realize that continuation under the existing exact compiler language.
    rows = []
    probe_complete = {h: True for h in horizons}
    ft0 = time.time()

    for idx, st in enumerate(selected_states):
        row = {
            "rep_id": idx,
            "state": [list(st[0]), list(st[1])],
            "past_min_cost": active[st],
            "quotient_key": list(sig[selected_layer]),
            "immediate_one_step_cost": selected_local_cost,
            "probes": {},
        }
        cur = {st: 0}
        unresolved = False
        for k in range(1, max_h + 1):
            if unresolved:
                if k in horizons:
                    row["probes"][str(k)] = {"status": "UNKNOWN_SEARCH", "cost": None}
                    probe_complete[k] = False
                continue
            desired = sig[selected_layer + k]
            nxt, meta = propagate(cur, desired, a.future_state_cap)
            if nxt is None:
                unresolved = True
                if k in horizons:
                    row["probes"][str(k)] = {"status": "UNKNOWN_SEARCH", "cost": None}
                    probe_complete[k] = False
                continue
            if not nxt:
                unresolved = True
                if k in horizons:
                    row["probes"][str(k)] = {"status": "NO_TRANSITION", "cost": None}
                continue
            cur = nxt
            if k in horizons:
                row["probes"][str(k)] = {
                    "status": "COMPLETE",
                    "cost": min(cur.values()),
                    "endpoint_exact_states": len(cur),
                }
        rows.append(row)

    future_seconds = time.time() - ft0

    # Use only fully observed horizons to define the bounded signature.
    complete_horizons = [
        h for h in horizons
        if all(r["probes"].get(str(h), {}).get("status") == "COMPLETE" for r in rows)
    ]

    def signature(row, hs):
        return tuple(row["probes"][str(h)]["cost"] for h in hs)

    full_partition = {}
    for r in rows:
        sigv = signature(r, complete_horizons) if complete_horizons else ()
        full_partition.setdefault(sigv, []).append(r["rep_id"])

    # Minimal probe basis reproducing the full observed row partition.
    def canonical_partition(hs):
        groups = {}
        for r in rows:
            groups.setdefault(signature(r, hs), []).append(r["rep_id"])
        return tuple(sorted(tuple(v) for v in groups.values()))

    full_part_key = canonical_partition(complete_horizons) if complete_horizons else (tuple(range(len(rows))),)
    minimal_bases = []
    if complete_horizons and len(full_part_key) > 1:
        for k in range(1, len(complete_horizons) + 1):
            for hs in itertools.combinations(complete_horizons, k):
                if canonical_partition(hs) == full_part_key:
                    minimal_bases.append(list(hs))
            if minimal_bases:
                break

    separated = len(full_part_key) > 1
    if not complete_horizons:
        status = "UNKNOWN_SEARCH"
    elif separated:
        status = "CERTIFIED_BOUNDED_DELAYED_FUTURE_SEPARATOR"
    else:
        status = "BOUNDED_NONSEPARATION"

    result = {
        "experiment": "ACC_MDA_FUTURE_CONSEQUENCE_KERNEL_V1",
        "challenge_id": cid,
        "policy": a.policy,
        "route_sha256": route_sha,
        "route_steps": len(sig) - 1,
        "route_search_seconds": route_search_seconds,
        "selection_status": selection_status,
        "selection_layer": selected_layer,
        "selected_count": len(selected_states),
        "selected_one_step_cost": selected_local_cost,
        "selected_same_quotient_key": list(sig[selected_layer]),
        "selection_rule": (
            "Earliest exact-closure layer with >=2 exact representatives sharing "
            "the same quotient key and identical minimum one-step atomic cost; "
            "largest tied group, then lowest one-step cost; future horizons hidden."
        ),
        "horizons_requested": horizons,
        "complete_horizons": complete_horizons,
        "rows": rows,
        "observed_row_classes": [list(x) for x in full_part_key],
        "observed_class_count": len(full_part_key),
        "minimal_probe_bases": minimal_bases,
        "future_seconds": future_seconds,
        "layer_trace": layer_trace,
        "status": status,
        "false_merge_witness": separated,
        "growth_authorized_scope": (
            "bounded representation refinement is warranted for predicting these "
            "tested continuation costs" if separated else None
        ),
        "global_route_language_growth_authorized": False,
        "claim_boundary": (
            "One immutable ac-04402 quotient route under one retained policy; "
            "same quotient representation and same immediate one-step atomic "
            "consequence; only the declared finite future horizons are tested. "
            "Nonseparation is not global equivalence; caps are UNKNOWN_SEARCH."
        ),
    }

    save(Path(a.out_dir) / "result.json", result)
    print("MDA_KERNEL_PAIRING", json.dumps({
        "cid": cid,
        "policy": a.policy,
        "layer": selected_layer,
        "selected": len(selected_states),
        "one_step_cost": selected_local_cost,
        "complete_horizons": complete_horizons,
        "classes": len(full_part_key),
        "minimal_probe_bases": minimal_bases,
        "status": status,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
