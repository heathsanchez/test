#!/usr/bin/env python3
"""Freeze or reveal a discriminator between surviving ACC orbit refinements.

Surviving V2 candidates:
  inv := S2-invariant multiset of relator inversion bits
  rot := S2-invariant multiset of relator cyclic-rotation coordinates

FREEZE mode inspects only present/local information. It finds an earliest pair
of exact representatives that:
  * share the current GS-Sub quotient,
  * tie on immediate one-step atomic cost,
  * but inv and rot make opposite merge/split predictions.

No two-step future consequence is computed in FREEZE mode.

REVEAL mode takes such a frozen pair and computes its exact two-step
continuation costs on the immutable quotient route. Whichever candidate's
merge/split prediction matches consequence wins that discriminator.
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


def setup(args):
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

    acc = Path(args.acc_root)
    sys.path.insert(0, str(acc / "competition" / "tools"))
    from verifier import core

    source = json.loads(Path(args.source_result).read_text())
    assert source["experiment"] == "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1", source
    assert source["policy"] == args.policy, (source.get("policy"), args.policy)
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
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = load_gssub(Path(args.acsolverx_root))

    if args.policy == "current":
        solver = ns["ACRelatorSolver"](
            r0, r1, max_nodes=args.max_nodes, max_len=qcap,
            verbose=False, stop_early=False,
        )
        found = solver.solve()
        if len(found) == 3:
            qpath, nodes, _ = found
        else:
            qpath, nodes = found[:2]
    else:
        qpath, nodes, _ = solve_subset_priority(ns, r0, r1, args.max_nodes, qcap, 3)
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
        if len(nxt_best) > args.state_cap:
            return None, {"status": "UNKNOWN_SEARCH", "distinct": len(nxt_best), "raw": raw}
        return nxt_best, {
            "status": "COMPLETE" if nxt_best else "NO_TRANSITION",
            "distinct": len(nxt_best),
            "raw": raw,
            "best_cost": min(nxt_best.values()) if nxt_best else None,
        }

    def fiber_coordinate(state, qkey):
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
                    c = {
                        "slot0": slot0,
                        "inv0": int(a0[1]),
                        "rot0": int(a0[2]),
                        "inv1": int(a1[1]),
                        "rot1": int(a1[2]),
                    }
                    assignments.append((
                        a0[3] + a1[3],
                        (c["slot0"], c["inv0"], c["rot0"], c["inv1"], c["rot1"]),
                        c,
                    ))
        if not assignments:
            return None
        assignments.sort(key=lambda z: (z[0], z[1]))
        return assignments[0][2]

    def orbit_code(coord, field):
        if field == "inv":
            return tuple(sorted((coord["inv0"], coord["inv1"])))
        if field == "rot":
            return tuple(sorted((coord["rot0"], coord["rot1"])))
        raise ValueError(field)

    return {
        "root": root,
        "core": core,
        "source": source,
        "cid": cid,
        "limits": limits,
        "ns": ns,
        "exact_initial": exact_initial,
        "qsig": qsig,
        "route_sha": route_sha,
        "propagate": propagate,
        "fiber_coordinate": fiber_coordinate,
        "orbit_code": orbit_code,
    }


def freeze(args, env):
    cid, qsig = env["cid"], env["qsig"]
    propagate = env["propagate"]
    fiber_coordinate = env["fiber_coordinate"]
    orbit_code = env["orbit_code"]
    active = {env["exact_initial"]: 0}
    trace = []
    witness = None

    max_layer = min(args.max_selection_layer, len(qsig) - 3)
    for layer in range(max_layer + 1):
        if layer > 0:
            active, meta = propagate(active, qsig[layer])
            trace.append({"layer": layer, "advance": meta})
            if active is None or not active:
                break

        groups = defaultdict(list)
        for st in sorted(active, key=repr):
            one, meta = propagate({st: 0}, qsig[layer + 1])
            if one is None or not one:
                continue
            groups[min(one.values())].append(st)

        for cost in sorted(groups):
            sts = sorted(groups[cost], key=repr)
            if len(sts) < 2:
                continue
            annotated = []
            for st in sts[:args.rep_cap]:
                coord = fiber_coordinate(st, qsig[layer])
                if coord is None:
                    continue
                annotated.append((st, coord))
            for (a, ca), (b, cb) in itertools.combinations(annotated, 2):
                inv_same = orbit_code(ca, "inv") == orbit_code(cb, "inv")
                rot_same = orbit_code(ca, "rot") == orbit_code(cb, "rot")
                if inv_same == rot_same:
                    continue
                witness = {
                    "challenge_id": cid,
                    "policy": args.policy,
                    "route_sha256": env["route_sha"],
                    "selection_layer": layer,
                    "one_step_cost": cost,
                    "quotient_key": list(qsig[layer]),
                    "next_quotient_keys": [list(qsig[layer + 1]), list(qsig[layer + 2])],
                    "state_a": [list(a[0]), list(a[1])],
                    "state_b": [list(b[0]), list(b[1])],
                    "past_cost_a": active[a],
                    "past_cost_b": active[b],
                    "coord_a": ca,
                    "coord_b": cb,
                    "inv_code_a": list(orbit_code(ca, "inv")),
                    "inv_code_b": list(orbit_code(cb, "inv")),
                    "rot_code_a": list(orbit_code(ca, "rot")),
                    "rot_code_b": list(orbit_code(cb, "rot")),
                    "inv_prediction": "MERGE" if inv_same else "SPLIT",
                    "rot_prediction": "MERGE" if rot_same else "SPLIT",
                }
                break
            if witness is not None:
                break
        if witness is not None:
            break

    out = {
        "experiment": "ACC_MDA_ORBIT_CANDIDATE_DISCRIMINATOR_V1_FREEZE",
        "challenge_id": cid,
        "policy": args.policy,
        "route_sha256": env["route_sha"],
        "status": "FROZEN_CANDIDATE_DISAGREEMENT" if witness else "NO_DISAGREEMENT_IN_SCOPE",
        "witness": witness,
        "trace": trace,
        "future_consequence_observed": False,
        "claim_boundary": (
            "Freeze uses quotient identity, immediate one-step cost, and the two "
            "already-frozen orbit candidates only. Two-step future cost is not computed."
        ),
    }
    save(Path(args.out_dir) / "freeze.json", out)
    print("MDA_ORBIT_DISAGREE_FREEZE", json.dumps({
        "cid": cid,
        "policy": args.policy,
        "status": out["status"],
        "layer": None if witness is None else witness["selection_layer"],
        "inv_prediction": None if witness is None else witness["inv_prediction"],
        "rot_prediction": None if witness is None else witness["rot_prediction"],
    }, sort_keys=True))


def reveal(args, env):
    frozen = json.loads(Path(args.frozen_pair).read_text())
    assert frozen["status"] == "FROZEN_CANDIDATE_DISAGREEMENT", frozen
    w = frozen["witness"]
    assert w["challenge_id"] == env["cid"], (w, env["cid"])
    assert w["policy"] == args.policy, (w, args.policy)
    assert w["route_sha256"] == env["route_sha"], (w, env["route_sha"])

    propagate = env["propagate"]
    a = (tuple(w["state_a"][0]), tuple(w["state_a"][1]))
    b = (tuple(w["state_b"][0]), tuple(w["state_b"][1]))
    keys = [tuple(x) for x in w["next_quotient_keys"]]

    costs = []
    metas = []
    for st in (a, b):
        cur = {st: 0}
        mm = []
        for key in keys:
            cur, meta = propagate(cur, key)
            mm.append(meta)
            if cur is None or not cur:
                break
        costs.append(None if cur is None or not cur else min(cur.values()))
        metas.append(mm)

    if any(x is None for x in costs):
        status = "UNKNOWN_SEARCH"
        actual = None
        winner = None
    else:
        actual = "MERGE" if costs[0] == costs[1] else "SPLIT"
        winners = [
            name for name in ("inv", "rot")
            if w[f"{name}_prediction"] == actual
        ]
        assert len(winners) == 1, (w, actual, winners)
        winner = winners[0]
        status = "CERTIFIED_CANDIDATE_SEPARATOR"

    out = {
        "experiment": "ACC_MDA_ORBIT_CANDIDATE_DISCRIMINATOR_V1_REVEAL",
        "challenge_id": env["cid"],
        "policy": args.policy,
        "route_sha256": env["route_sha"],
        "frozen_witness": w,
        "future2_cost_a": costs[0],
        "future2_cost_b": costs[1],
        "future_meta": metas,
        "actual_future_relation": actual,
        "winner": winner,
        "loser": None if winner is None else ("rot" if winner == "inv" else "inv"),
        "status": status,
        "global_inheritance_authorized": False,
        "claim_boundary": (
            "One pre-frozen candidate-disagreement pair; future consequence is "
            "exact two-step continuation cost on the immutable route."
        ),
    }
    save(Path(args.out_dir) / "reveal.json", out)
    print("MDA_ORBIT_DISAGREE_REVEAL", json.dumps({
        "cid": env["cid"],
        "policy": args.policy,
        "costs": costs,
        "actual": actual,
        "winner": winner,
        "status": status,
    }, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["freeze", "reveal"])
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--source-result", required=True)
    ap.add_argument("--policy", required=True, choices=["current", "mask3"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frozen-pair")
    ap.add_argument("--state-cap", type=int, default=512)
    ap.add_argument("--rep-cap", type=int, default=16)
    ap.add_argument("--max-selection-layer", type=int, default=12)
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    args = ap.parse_args()
    env = setup(args)
    if args.mode == "freeze":
        freeze(args, env)
    else:
        if not args.frozen_pair:
            raise ValueError("--frozen-pair required in reveal mode")
        reveal(args, env)


if __name__ == "__main__":
    main()
