#!/usr/bin/env python3
"""Discover the smallest quotient-fiber distinction forced by future consequence.

The candidate language is not hand-authored ACC structure.  It is exactly the
coordinate system of the symmetry information already discarded by the current
GS-Sub quotient:

  slot0 : which canonical quotient component exact relator 0 maps to
  inv0  : whether relator 0 must be inverted to reach that component
  rot0  : cyclic-conjugation steps for relator 0
  inv1  : whether relator 1 must be inverted
  rot1  : cyclic-conjugation steps for relator 1

We first freeze the earliest group of exact representatives that the current
quotient merges and whose immediate one-step atomic consequence is identical.
Only then do we reveal a two-step continuation cost.  If the future splits the
group, exhaustive subset search over the five quotient-fiber coordinates finds
all minimum refinements that reproduce the observed future partition.

This script changes no solver behavior.  It is a representation diagnostic.
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


FEATURES = ("slot0", "inv0", "rot0", "inv1", "rot1")


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
    ap.add_argument("--state-cap", type=int, default=512)
    ap.add_argument("--rep-cap", type=int, default=16)
    ap.add_argument("--max-selection-layer", type=int, default=8)
    a = ap.parse_args()

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        challenge_maps,
        compiled_superneighbor_candidates,
        compiled_superneighbors,
        int_word_to_str,
        load_gssub,
        orientation_options,
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

    # Reproduce immutable route.
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

    qsig = [path_state_key(ns, q) for q in qpath]
    route_sha = hashlib.sha256(
        json.dumps(qsig, separators=(",", ":"), sort_keys=False).encode()
    ).hexdigest()
    assert route_sha == source["quotient_path_sha256"], (route_sha, source["quotient_path_sha256"])

    def propagate(active, desired):
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
        if len(nxt_best) > a.state_cap:
            return None, {"status": "UNKNOWN_SEARCH", "distinct": len(nxt_best), "raw": raw}
        return nxt_best, {
            "status": "COMPLETE" if nxt_best else "NO_TRANSITION",
            "distinct": len(nxt_best),
            "raw": raw,
            "best_cost": min(nxt_best.values()) if nxt_best else None,
        }

    def fiber_coordinate(state, qkey):
        """Coordinate of exact state inside the symmetry fiber forgotten by qkey."""
        opts = []
        for i in (0, 1):
            word_opts = []
            for w, seq in orientation_options(core, state[i], i):
                s = int_word_to_str(w)
                inv = bool(seq and seq[0] == i)
                rot = len(seq) - (1 if inv else 0)
                word_opts.append((s, inv, rot, len(seq)))
            opts.append(word_opts)

        assignments = []
        for slot0 in (0, 1):
            slot1 = 1 - slot0
            m0 = [x for x in opts[0] if x[0] == qkey[slot0]]
            m1 = [x for x in opts[1] if x[0] == qkey[slot1]]
            for a0 in m0:
                for a1 in m1:
                    coord = {
                        "slot0": slot0,
                        "inv0": int(a0[1]),
                        "rot0": int(a0[2]),
                        "inv1": int(a1[1]),
                        "rot1": int(a1[2]),
                    }
                    assignments.append((a0[3] + a1[3], tuple(coord[k] for k in FEATURES), coord))
        if not assignments:
            return None
        assignments.sort(key=lambda x: (x[0], x[1]))
        return assignments[0][2]

    # Freeze earliest present-local tie, without seeing two-step future.
    active = {exact_initial: 0}
    selected_layer = None
    selected_cost = None
    selected_states = None
    trace = []
    selection_status = "NO_LOCAL_TIE"

    max_layer = min(a.max_selection_layer, len(qsig) - 3)
    for layer in range(max_layer + 1):
        if layer > 0:
            active, meta = propagate(active, qsig[layer])
            trace.append({"layer": layer, "advance": meta})
            if active is None:
                selection_status = "UNKNOWN_SEARCH"
                break
            if not active:
                selection_status = "NO_TRANSITION"
                break

        groups = defaultdict(list)
        one_meta = []
        for st in sorted(active, key=repr):
            one, meta = propagate({st: 0}, qsig[layer + 1])
            if one is None or not one:
                one_meta.append({"state": repr(st), "status": meta["status"]})
                continue
            c1 = min(one.values())
            groups[c1].append(st)
            one_meta.append({
                "state": repr(st),
                "status": "COMPLETE",
                "one_step_cost": c1,
                "endpoint_states": len(one),
            })
        ties = [(cost, sts) for cost, sts in groups.items() if len(sts) >= 2]
        if not ties:
            continue
        cost, sts = min(ties, key=lambda z: (-len(z[1]), z[0]))
        selected_layer = layer
        selected_cost = cost
        selected_states = sorted(sts, key=repr)[:a.rep_cap]
        selection_status = "FROZEN_LOCAL_TIE"
        trace.append({
            "layer": layer,
            "selection": True,
            "active_states": len(active),
            "tied_group_size": len(sts),
            "selected_count": len(selected_states),
            "one_step_cost": cost,
            "truncated": len(sts) > a.rep_cap,
            "one_step_meta": one_meta,
        })
        break

    if selected_states is None:
        result = {
            "experiment": "ACC_MDA_QUOTIENT_FIBER_GENESIS_V1",
            "challenge_id": cid,
            "policy": a.policy,
            "route_sha256": route_sha,
            "selection_status": selection_status,
            "status": "UNKNOWN_SEARCH" if selection_status == "UNKNOWN_SEARCH" else "NO_TIED_PRESENT",
            "trace": trace,
        }
        save(Path(a.out_dir) / "result.json", result)
        print("MDA_FIBER_GENESIS", json.dumps({
            "cid": cid, "policy": a.policy, "status": result["status"]
        }, sort_keys=True))
        return

    # Reveal the minimum already-warranted probe: horizon 2.
    rows = []
    unknown_future = False
    qkey = qsig[selected_layer]
    for i, st in enumerate(selected_states):
        coord = fiber_coordinate(st, qkey)
        cur = {st: 0}
        steps = []
        for k in (1, 2):
            cur, meta = propagate(cur, qsig[selected_layer + k])
            steps.append(meta)
            if cur is None or not cur:
                unknown_future = True
                break
        future2 = None if unknown_future or cur is None or not cur else min(cur.values())
        rows.append({
            "rep_id": i,
            "exact_state": [list(st[0]), list(st[1])],
            "past_cost": active[st],
            "one_step_cost": selected_cost,
            "fiber_coordinate": coord,
            "future2_cost": future2,
            "future_meta": steps,
        })

    if any(r["fiber_coordinate"] is None for r in rows):
        status = "UNKNOWN_FIBER_COORDINATE"
        minimal = []
        classes = None
    elif any(r["future2_cost"] is None for r in rows):
        status = "UNKNOWN_SEARCH"
        minimal = []
        classes = None
    else:
        labels = [r["future2_cost"] for r in rows]
        classes = len(set(labels))

        def part_for_features(subset):
            groups = {}
            for r in rows:
                key = tuple(r["fiber_coordinate"][f] for f in subset)
                groups.setdefault(key, []).append(r["rep_id"])
            return tuple(sorted(tuple(v) for v in groups.values()))

        def label_partition():
            groups = {}
            for r in rows:
                groups.setdefault(r["future2_cost"], []).append(r["rep_id"])
            return tuple(sorted(tuple(v) for v in groups.values()))

        target_part = label_partition()
        exact = []
        sufficient = []
        for k in range(1, len(FEATURES) + 1):
            for subset in itertools.combinations(FEATURES, k):
                p = part_for_features(subset)
                # Sufficient iff no feature-cell mixes two future labels.
                ok = True
                for cell in p:
                    if len({rows[j]["future2_cost"] for j in cell}) > 1:
                        ok = False
                        break
                if ok:
                    sufficient.append(list(subset))
                    if p == target_part:
                        exact.append(list(subset))
            if exact:
                break
        minimal = exact if exact else sufficient
        if classes > 1:
            status = "CERTIFIED_QUOTIENT_FIBER_FALSE_MERGE"
        else:
            status = "BOUNDED_NONSEPARATION"

    result = {
        "experiment": "ACC_MDA_QUOTIENT_FIBER_GENESIS_V1",
        "challenge_id": cid,
        "policy": a.policy,
        "route_sha256": route_sha,
        "route_steps": len(qsig) - 1,
        "route_search_seconds": route_search_seconds,
        "selection_layer": selected_layer,
        "selected_count": len(selected_states),
        "selected_one_step_cost": selected_cost,
        "quotient_key": list(qkey),
        "candidate_language": {
            "kind": "complete subset language of quotient-fiber symmetry coordinates",
            "features": list(FEATURES),
            "subset_count": 2 ** len(FEATURES) - 1,
        },
        "rows": rows,
        "future2_class_count": classes,
        "minimal_exact_refinements": minimal,
        "status": status,
        "representation_growth_authorized": status == "CERTIFIED_QUOTIENT_FIBER_FALSE_MERGE",
        "global_inheritance_authorized": False,
        "trace": trace,
        "claim_boundary": (
            "Earliest frozen same-quotient, same-one-step-cost group only. "
            "Candidate distinctions are restricted to coordinates of symmetries "
            "already erased by the existing quotient. Future consequence is the "
            "two-step continuation cost. Nonseparation is bounded only."
        ),
    }
    save(Path(a.out_dir) / "result.json", result)
    print("MDA_FIBER_GENESIS", json.dumps({
        "cid": cid,
        "policy": a.policy,
        "layer": selected_layer,
        "selected": len(selected_states),
        "future2_classes": classes,
        "minimal_refinements": minimal,
        "status": status,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
