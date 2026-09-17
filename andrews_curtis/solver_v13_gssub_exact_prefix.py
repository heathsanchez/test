#!/usr/bin/env python3
"""ACC GS-Sub V13: exact carry-aware prefix, cheap quotient completion.

V12 showed that canonical local edge-overhead is not the right residual signal:
its selected prefixes still failed exact compilation at steps 2--12.  V13
changes only that justified boundary.  The short prefix is searched in the
*actual official-move state space*: every retained prefix edge is a replayed
V3 carry-symmetry realization, and the carried exact representative plus its
true atomic cost is preserved.  From several such verified physical prefixes,
ordinary ACSolverX length-first search completes the quotient path cheaply;
only the suffix is then compiled from the retained exact representative.

Search remains proposal machinery.  Every emitted candidate is replayed by the
pinned official verifier.  Publication is handled by the strict fresh-live,
quota-gated workflow.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import solver_v2_gssub as v2
import solver_v9_gssub_skeleton_lookahead as v9

OFFICIAL_COMMIT = "99a65377c5c4f412cd9af7b8d31c41464a855736"
ACSOLVERX_COMMIT = "6a12515fe1d95178a483b76d5553266e61122417"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--snapshot-ac-file", required=True)
    p.add_argument("--prefix-depth", type=int, required=True)
    p.add_argument("--overhead-weight", type=float, required=True)
    p.add_argument("--prefix-beam", type=int, default=96)
    p.add_argument("--exact-per-key", type=int, default=3)
    p.add_argument("--prefix-count", type=int, default=8)
    p.add_argument("--prefix-seconds", type=int, default=420)
    p.add_argument("--suffix-max-nodes", type=int, default=90000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--strict-beam", type=int, default=256)
    p.add_argument("--near-beam", type=int, default=96)
    p.add_argument("--compile-seconds", type=int, default=420)
    p.add_argument("--near-compile-seconds", type=int, default=210)
    p.add_argument("--near-miss-frac", type=float, default=0.10)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def quotient_neighbors(ns, key, max_len):
    reduce_relator = ns["reduce_relator_nj"]
    canonical_pair = ns["canonical_pair_nj"]
    state_to_key = ns["state_to_key"]
    str_to_arr = ns["str_to_arr"]
    get_neighbors = ns["get_neighbors_nj"]
    r1, r2 = str_to_arr(key[0]), str_to_arr(key[1])
    out = set()
    for nr1, nr2 in get_neighbors(r1, r2):
        nr1r, nr2r = reduce_relator(nr1), reduce_relator(nr2)
        if len(nr1r) + len(nr2r) >= max_len:
            continue
        c1, c2 = canonical_pair(nr1r, nr2r)
        out.add(state_to_key((c1, c2)))
    return out


def exact_prefix_search(
    core,
    ns,
    exact_initial,
    *,
    target_depth,
    beam_width,
    exact_per_key,
    prefix_count,
    qcap,
    total_cap,
    overhead_weight,
    atomic_ceiling_exclusive,
    seconds,
):
    """Layered exact-state search for physically cheap quotient prefixes."""
    start = time.time()
    # state, atomics, cost
    frontier = [(exact_initial, (), 0)]
    layers = []
    generated = 0
    replayed_candidates = 0
    bound_prunes = 0

    for depth in range(1, target_depth + 1):
        if time.time() - start >= seconds:
            return [], {
                "code": "time_cap",
                "depth_reached": depth - 1,
                "generated": generated,
                "replayed_candidates": replayed_candidates,
                "bound_prunes": bound_prunes,
                "layers": layers,
                "seconds": round(time.time() - start, 3),
            }

        best_exact = {}
        desired_count = 0
        for state, path, cost in frontier:
            source_key = v2.gssub_key(ns, state)
            desireds = quotient_neighbors(ns, source_key, qcap)
            desired_count += len(desireds)
            for desired in desireds:
                cands = v9.candidate_edges(core, ns, state, desired, total_cap)
                replayed_candidates += len(cands)
                for nxt, edge in cands:
                    nc = cost + len(edge)
                    generated += 1
                    # Prefix still needs at least one move per future quotient
                    # layer, so exceeding the near ceiling already is useless.
                    if nc + (target_depth - depth) >= atomic_ceiling_exclusive:
                        bound_prunes += 1
                        continue
                    qkey = v2.gssub_key(ns, nxt)
                    sig = (qkey, nxt)
                    prev = best_exact.get(sig)
                    atomics = path + tuple(edge)
                    if prev is None or nc < prev[0]:
                        best_exact[sig] = (nc, atomics, nxt, qkey)

        if not best_exact:
            return [], {
                "code": "frontier_exhausted",
                "depth_reached": depth - 1,
                "generated": generated,
                "replayed_candidates": replayed_candidates,
                "bound_prunes": bound_prunes,
                "layers": layers,
                "seconds": round(time.time() - start, 3),
            }

        # Preserve exact-state diversity within each quotient key first, then
        # choose the best global beam.  The score uses *actual* accumulated
        # compiler excess, not canonical local estimates.
        per_key = {}
        for nc, atomics, nxt, qkey in best_exact.values():
            excess = nc - depth
            score = v2.total_len(nxt) + overhead_weight * excess
            per_key.setdefault(qkey, []).append((score, nc, nxt, atomics, qkey))

        pool = []
        for vals in per_key.values():
            vals.sort(key=lambda x: (x[0], x[1], v2.total_len(x[2]), x[4]))
            pool.extend(vals[: max(1, int(exact_per_key))])
        pool.sort(key=lambda x: (x[0], x[1], v2.total_len(x[2]), x[4]))
        kept = pool[: max(1, int(beam_width))]
        frontier = [(nxt, atomics, nc) for _score, nc, nxt, atomics, _qkey in kept]

        layers.append({
            "depth": depth,
            "input_beam": 1 if depth == 1 else layers[-1]["beam"],
            "desired_proposals": desired_count,
            "distinct_exact": len(best_exact),
            "distinct_quotient": len(per_key),
            "pool": len(pool),
            "beam": len(frontier),
            "best_atomic_cost": min(x[2] for x in frontier),
            "best_excess": min(x[2] - depth for x in frontier),
            "best_total": min(v2.total_len(x[0]) for x in frontier),
        })

    finals = []
    for state, atomics, cost in frontier:
        qkey = v2.gssub_key(ns, state)
        excess = cost - target_depth
        score = v2.total_len(state) + overhead_weight * excess
        finals.append({
            "state": state,
            "path": atomics,
            "cost": int(cost),
            "qkey": qkey,
            "score": float(score),
            "total": v2.total_len(state),
            "excess": int(excess),
        })
    finals.sort(key=lambda x: (x["score"], x["cost"], x["total"], x["qkey"]))
    finals = finals[: max(1, int(prefix_count))]
    return finals, {
        "code": "ok",
        "depth_reached": target_depth,
        "generated": generated,
        "replayed_candidates": replayed_candidates,
        "bound_prunes": bound_prunes,
        "layers": layers,
        "prefixes": len(finals),
        "best_prefix_cost": finals[0]["cost"] if finals else None,
        "best_prefix_excess": finals[0]["excess"] if finals else None,
        "seconds": round(time.time() - start, 3),
    }


def complete_suffix(ns, key, *, max_nodes, max_len):
    solver = ns["ACRelatorSolver"](
        key[0], key[1], max_nodes=max_nodes, max_len=max_len,
        verbose=False, stop_early=False,
    )
    t0 = time.time()
    found = solver.solve()
    if len(found) == 3:
        path, nodes, _seen = found
    else:
        path, nodes = found[:2]
    return path, int(nodes), round(time.time() - t0, 3)


def compile_seeded_suffix(
    core,
    ns,
    seed_state,
    seed_path,
    seed_cost,
    suffix_path,
    reverse_paths,
    total_cap,
    *,
    ceiling_exclusive,
    beam_width,
    seconds,
    label,
):
    """V9 live-bound compiler starting from a retained exact prefix state."""
    start = time.time()
    if not suffix_path:
        return None, {"code": "empty_suffix_path", "label": label}
    if v2.gssub_key(ns, seed_state) != v2.path_state_key(ns, suffix_path[0]):
        return None, {"code": "seed_key_mismatch", "label": label}

    qsteps = len(suffix_path) - 1
    beam = [(seed_state, tuple(seed_path), int(seed_cost))]
    total_bound_prunes = 0
    total_dead_next = 0
    layers = []

    for step_index, qstate in enumerate(suffix_path[1:], 1):
        if time.time() - start >= seconds:
            return None, {
                "code": "time_cap", "label": label, "step": step_index,
                "suffix_steps": qsteps, "beam": len(beam),
                "seconds": round(time.time() - start, 3),
            }
        desired = v2.path_state_key(ns, qstate)
        remaining = qsteps - step_index
        by_exact = {}
        raw = 0
        min_raw_lower_bound = None
        for state, path, cost in beam:
            for nxt, edge in v9.candidate_edges(core, ns, state, desired, total_cap):
                raw += 1
                nc = cost + len(edge)
                lb = nc + remaining
                if min_raw_lower_bound is None or lb < min_raw_lower_bound:
                    min_raw_lower_bound = lb
                if lb >= ceiling_exclusive:
                    total_bound_prunes += 1
                    continue
                prev = by_exact.get(nxt)
                if prev is None or nc < prev[0]:
                    by_exact[nxt] = (nc, path, tuple(edge))
        if not by_exact:
            return None, {
                "code": "live_bound_frontier_exhausted", "label": label,
                "step": step_index, "suffix_steps": qsteps,
                "input_beam": len(beam), "raw_candidates": raw,
                "min_raw_lower_bound": min_raw_lower_bound,
                "ceiling_exclusive": ceiling_exclusive,
                "bound_prunes": total_bound_prunes,
                "dead_next": total_dead_next,
                "seconds": round(time.time() - start, 3),
            }

        next_desired = (
            v2.path_state_key(ns, suffix_path[step_index + 1])
            if step_index < qsteps else None
        )
        ranked = []
        dead_next = 0
        for nxt, (nc, parent_path, edge) in by_exact.items():
            next_min = 0
            next_count = 0
            if next_desired is not None:
                next_min = 10**9
                next_remaining = remaining - 1
                for _n2, e2 in v9.candidate_edges(core, ns, nxt, next_desired, total_cap):
                    if nc + len(e2) + next_remaining < ceiling_exclusive:
                        next_count += 1
                        next_min = min(next_min, len(e2))
                if next_count == 0:
                    dead_next += 1
                    next_min = 10**6
            score = (nc + next_min, nc, -next_count, v2.total_len(nxt))
            ranked.append((score, nxt, parent_path, edge, nc))
        total_dead_next += dead_next
        ranked.sort(key=lambda x: x[0])
        kept = ranked[: max(1, int(beam_width))]
        beam = [(nxt, parent_path + edge, nc) for _s, nxt, parent_path, edge, nc in kept]
        if step_index <= 8 or step_index == qsteps or step_index % 25 == 0:
            layers.append({
                "step": step_index,
                "raw": raw,
                "distinct_exact": len(by_exact),
                "beam": len(beam),
                "best_cost": min(x[2] for x in beam),
                "best_optimistic_final": min(x[2] for x in beam) + remaining,
                "dead_next": dead_next,
            })

    finals = []
    for state, path, cost in beam:
        suffix = v2.exact_terminal_suffix(core, state, reverse_paths)
        if suffix is None:
            continue
        total_cost = cost + len(suffix)
        if total_cost >= ceiling_exclusive:
            continue
        atomics = path + tuple(suffix)
        finals.append((total_cost, atomics, len(suffix)))
    if not finals:
        return None, {
            "code": "no_exact_terminal_under_bound", "label": label,
            "suffix_steps": qsteps, "beam": len(beam),
            "best_prefix_cost": min((x[2] for x in beam), default=None),
            "ceiling_exclusive": ceiling_exclusive,
            "bound_prunes": total_bound_prunes,
            "dead_next": total_dead_next,
            "layers": layers,
            "seconds": round(time.time() - start, 3),
        }

    total_cost, atomics, suffix_len = min(finals, key=lambda x: x[0])
    return atomics, {
        "code": "ok", "label": label,
        "compiler": "exact-prefix-seeded-live-bound-v1",
        "suffix_steps": qsteps,
        "atomic_cost": total_cost,
        "terminal_suffix_len": suffix_len,
        "ceiling_exclusive": ceiling_exclusive,
        "beam_width": beam_width,
        "bound_prunes": total_bound_prunes,
        "dead_next": total_dead_next,
        "layers": layers,
        "seconds": round(time.time() - start, 3),
    }


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
        c["challenge_id"]: c for c in manifest["challenges"]
        if c["challenge_id"].startswith("ac-")
    }
    c = ac_by_id[args.target_id]
    snapshot_obj, live = v2.snapshot_file_map(args.snapshot_ac_file)
    save_json(out / "snapshot_ac_start.json", snapshot_obj)
    live_row = live[args.target_id]
    live_best = live_row.get("currentBestLength")
    if not isinstance(live_best, int):
        report = {
            "experiment": "acc-gssub-v13-exact-prefix",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("EXACT_PREFIX", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)
    near_limit = int(math.floor(live_best * (1.0 + args.near_miss_frac)))
    near_exclusive = near_limit + 1

    prefixes, pmeta = exact_prefix_search(
        core, ns, exact,
        target_depth=args.prefix_depth,
        beam_width=args.prefix_beam,
        exact_per_key=args.exact_per_key,
        prefix_count=args.prefix_count,
        qcap=qcap,
        total_cap=limits["max_total_relator_length"],
        overhead_weight=args.overhead_weight,
        atomic_ceiling_exclusive=near_exclusive,
        seconds=args.prefix_seconds,
    )
    print("EXACT_PREFIX_FRONTIER", json.dumps({
        "challenge_id": args.target_id,
        "prefix_depth": args.prefix_depth,
        "weight": args.overhead_weight,
        **pmeta,
    }, sort_keys=True), flush=True)

    report = {
        "experiment": "acc-gssub-v13-exact-prefix",
        "official_commit": OFFICIAL_COMMIT,
        "acsolverx_commit": ACSOLVERX_COMMIT,
        "challenge_id": args.target_id,
        "live_status": live_row.get("status"),
        "live_best": live_best,
        "live_k_teams": live_row.get("kTeams"),
        "initial_total": initial_total,
        "quotient_total_cap": qcap,
        "prefix_depth": args.prefix_depth,
        "overhead_weight": args.overhead_weight,
        "prefix_search": pmeta,
        "prefixes": [],
        "verified": False,
        "candidate_length": None,
    }

    reverse_paths, reverse_hist = v2.build_reverse(core, args.reverse_depth, args.reverse_cap)
    report["reverse_states"] = len(reverse_paths)
    report["reverse_hist"] = reverse_hist

    best_any = None
    best_strict = None
    for rank, pref in enumerate(prefixes, 1):
        suffix_path, suffix_nodes, suffix_seconds = complete_suffix(
            ns, pref["qkey"], max_nodes=args.suffix_max_nodes, max_len=qcap
        )
        pm = {
            "rank": rank,
            "prefix_cost": pref["cost"],
            "prefix_excess": pref["excess"],
            "prefix_total": pref["total"],
            "suffix_found": suffix_path is not None,
            "suffix_nodes": suffix_nodes,
            "suffix_seconds": suffix_seconds,
            "verified": False,
            "candidate_length": None,
        }
        if suffix_path is None:
            report["prefixes"].append(pm)
            continue
        if v2.path_state_key(ns, suffix_path[0]) != pref["qkey"]:
            raise RuntimeError(("suffix_initial_key_mismatch", args.target_id, rank))

        suffix_steps = len(suffix_path) - 1
        total_qsteps = args.prefix_depth + suffix_steps
        pm["suffix_steps"] = suffix_steps
        pm["quotient_steps"] = total_qsteps
        pm["optimistic_strict_lb"] = pref["cost"] + suffix_steps

        strict = None
        strict_meta = {"code": "optimistic_bound_impossible"}
        if pref["cost"] + suffix_steps < live_best:
            strict, strict_meta = compile_seeded_suffix(
                core, ns, pref["state"], pref["path"], pref["cost"],
                suffix_path, reverse_paths, limits["max_total_relator_length"],
                ceiling_exclusive=live_best,
                beam_width=args.strict_beam,
                seconds=args.compile_seconds,
                label=f"strict-prefix-{rank}",
            )
        pm["strict_compile"] = strict_meta

        cand = strict
        mode = "strict" if strict is not None else None
        near_meta = None
        if cand is None and pref["cost"] + suffix_steps < near_exclusive:
            near, near_meta = compile_seeded_suffix(
                core, ns, pref["state"], pref["path"], pref["cost"],
                suffix_path, reverse_paths, limits["max_total_relator_length"],
                ceiling_exclusive=near_exclusive,
                beam_width=args.near_beam,
                seconds=args.near_compile_seconds,
                label=f"near-prefix-{rank}",
            )
            if near is not None:
                cand, mode = near, "near"
        pm["near_compile"] = near_meta

        if cand is not None:
            verdict = core.verify(c, list(cand), c["move_spec_version"], limits)
            pm["verdict"] = verdict
            pm["candidate_length"] = len(cand)
            pm["verified"] = bool(verdict.get("ok"))
            pm["mode"] = mode
            if verdict.get("ok"):
                if best_any is None or len(cand) < len(best_any):
                    best_any = tuple(cand)
                if len(cand) < live_best and (best_strict is None or len(cand) < len(best_strict)):
                    best_strict = tuple(cand)
        report["prefixes"].append(pm)

    if best_any is not None:
        report["verified"] = True
        report["candidate_length"] = len(best_any)
        (out / "candidate_any.txt").write_text(
            f"{args.target_id}: {json.dumps(list(best_any), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    else:
        (out / "candidate_any.txt").write_text("", encoding="utf-8")

    if best_strict is not None:
        (out / "submission_v13.txt").write_text(
            f"{args.target_id}: {json.dumps(list(best_strict), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    else:
        (out / "submission_v13.txt").write_text("", encoding="utf-8")

    save_json(out / "report.json", report)
    print("EXACT_PREFIX", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
