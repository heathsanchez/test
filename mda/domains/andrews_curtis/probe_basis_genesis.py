#!/usr/bin/env python3
"""Learn a minimal ACC probe basis from future-consequence false merges.

Instead of hand-writing another static feature language, use the dual side of
the state-test pairing. Candidate tests are only short sequences of official AC
moves. The observed consequence of a probe is the EXISTING GS-Sub quotient of
the state after that probe.

For each frozen route:
  1. find the earliest exact states merged by the current quotient and tied on
     immediate one-step atomic cost;
  2. reveal the already-warranted two-step continuation cost as the future label;
  3. evaluate every official probe of length 1 and 2 without changing the solver.

The synthesis job chooses a minimum common probe basis from development cases
only and then evaluates it on prospectively frozen held-out cases.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
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
    ap.add_argument("--state-cap", type=int, default=512)
    ap.add_argument("--rep-cap", type=int, default=16)
    ap.add_argument("--max-selection-layer", type=int, default=8)
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    a = ap.parse_args()

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        challenge_maps,
        compiled_superneighbor_candidates,
        compiled_superneighbors,
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

    # Freeze the same-present set before inspecting the two-step future.
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
        for st in sorted(active, key=repr):
            one, meta = propagate({st: 0}, qsig[layer + 1])
            if one is None or not one:
                continue
            groups[min(one.values())].append(st)
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
        })
        break

    if selected_states is None:
        out = {
            "experiment": "ACC_MDA_PROBE_BASIS_GENESIS_V1",
            "challenge_id": cid,
            "policy": a.policy,
            "route_sha256": route_sha,
            "status": "UNKNOWN_SEARCH" if selection_status == "UNKNOWN_SEARCH" else "NO_TIED_PRESENT",
            "selection_status": selection_status,
            "trace": trace,
        }
        save(Path(a.out_dir) / "result.json", out)
        print("MDA_PROBE_BASIS", json.dumps({"cid": cid, "status": out["status"]}, sort_keys=True))
        return

    # Future label: exact minimum cost through the next two frozen quotient transitions.
    rows = []
    future_unknown = False
    for i, st in enumerate(selected_states):
        cur = {st: 0}
        metas = []
        for k in (1, 2):
            cur, meta = propagate(cur, qsig[selected_layer + k])
            metas.append(meta)
            if cur is None or not cur:
                future_unknown = True
                break
        future2 = None if cur is None or not cur else min(cur.values())
        rows.append({
            "rep_id": i,
            "exact_state": [list(st[0]), list(st[1])],
            "past_cost": active[st],
            "one_step_cost": selected_cost,
            "future2_cost": future2,
            "future_meta": metas,
        })

    # Candidate tests are generated, not hand selected: every official sequence
    # of length 1 or 2. Observation is simply the current quotient after the test.
    probes = []
    for n in (1, 2):
        for seq in itertools.product(range(core.NUM_MOVES), repeat=n):
            probes.append(seq)

    def probe_id(seq):
        return ",".join(str(x) for x in seq)

    for row, st in zip(rows, selected_states):
        responses = {}
        for seq in probes:
            cur = st
            over = False
            for m in seq:
                cur = core.apply_move(cur, m)
                if total_len(cur) > limits["max_total_relator_length"]:
                    over = True
                    break
            if over:
                resp = ["OVER_CAP"]
            else:
                q = gssub_key(ns, cur)
                resp = ["Q", q[0], q[1]]
            responses[probe_id(seq)] = resp
        row["probe_responses"] = responses

    labels = [r["future2_cost"] for r in rows]
    out = {
        "experiment": "ACC_MDA_PROBE_BASIS_GENESIS_V1",
        "challenge_id": cid,
        "policy": a.policy,
        "route_sha256": route_sha,
        "route_steps": len(qsig) - 1,
        "selection_layer": selected_layer,
        "selected_count": len(selected_states),
        "selected_one_step_cost": selected_cost,
        "future2_class_count": None if future_unknown else len(set(labels)),
        "rows": rows,
        "probe_family": {
            "definition": "all official AC move sequences of length 1 or 2",
            "official_move_count": core.NUM_MOVES,
            "probe_count": len(probes),
            "observation": "existing GS-Sub quotient after probe; OVER_CAP if official limit exceeded",
        },
        "status": "UNKNOWN_SEARCH" if future_unknown else (
            "CERTIFIED_FALSE_MERGE_WITH_PROBE_TABLE"
            if len(set(labels)) > 1 else "BOUNDED_NONSEPARATION"
        ),
        "trace": trace,
        "claim_boundary": (
            "Probe table is observational only and changes no solver behavior. "
            "Future label is the exact two-step continuation cost on the frozen route."
        ),
    }
    save(Path(a.out_dir) / "result.json", out)
    print("MDA_PROBE_BASIS", json.dumps({
        "cid": cid,
        "policy": a.policy,
        "layer": selected_layer,
        "selected": len(selected_states),
        "future2_classes": out["future2_class_count"],
        "probes": len(probes),
        "status": out["status"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
