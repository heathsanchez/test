#!/usr/bin/env python3
"""ACC GS-Sub V9: fixed-skeleton, live-bound, lookahead exact compiler.

V8 closed the global exact-state ordering hypothesis: millions of exact states
and compiled edges still popped only depth ~10, while the ordinary GS-Sub
quotient search reaches the two competitive targets at depths 392 and 438 in
only tens of thousands of quotient nodes.  The remaining high-yield boundary
is therefore exact compilation of an already-good quotient skeleton.

This solver keeps the public ACSolverX quotient search, the V3 carry-symmetry
exact compiler language, the pinned official transition semantics, and the
pinned official verifier.  It changes only fixed-skeleton compilation:

* use the current live record as an admissible terminal-cost bound;
* at quotient layer i, prune a representative when
      atomic_cost + remaining_required_multiplications >= bound;
  because every remaining GS-Sub step needs at least one official
  multiplication;
* rank the surviving exact representatives with one-step exact lookahead so a
  locally cheap representative is not retained when its next required quotient
  transition is expensive or unavailable;
* run a strict-record pass first; only if that yields no verified steal, run a
  verifier-gated <=10% near-miss pass for downstream atlas/peephole salvage.

The quotient search and compiler are proposal machinery only.  Every emitted
candidate is replayed and accepted by the pinned official verifier; publication
remains the responsibility of the strict fresh-live aggregator.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import solver_v2_gssub as v2
import solver_v3_gssub_carry as v3


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--snapshot-ac-file", required=True)
    p.add_argument("--max-nodes", type=int, default=250000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--strict-beam", type=int, default=512)
    p.add_argument("--near-beam", type=int, default=128)
    p.add_argument("--strict-seconds", type=int, default=1700)
    p.add_argument("--near-seconds", type=int, default=700)
    p.add_argument("--near-miss-frac", type=float, default=0.10)
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def candidate_edges(core, ns, state, desired, total_cap):
    """V3 carry candidates plus V2's proven coverage fallback."""
    cands = v3.compiled_superneighbor_candidates_carry(core, ns, state, desired, total_cap)
    if cands:
        return cands
    hit = v2.compiled_superneighbors(core, ns, state, total_cap).get(desired)
    return [] if hit is None else [hit]


def compile_fixed_skeleton(
    core,
    ns,
    exact_initial,
    quotient_path,
    reverse_paths,
    total_cap,
    *,
    ceiling_exclusive,
    beam_width,
    seconds,
    label,
):
    """Compile one quotient skeleton under an admissible final-cost ceiling.

    The ceiling is exclusive.  Thus strict mode uses ceiling=live_best; near
    mode uses ceiling=floor(live_best*(1+margin))+1.
    """
    start = time.time()
    if not quotient_path:
        return None, {"code": "empty_quotient_path", "label": label}
    if v2.gssub_key(ns, exact_initial) != v2.path_state_key(ns, quotient_path[0]):
        return None, {"code": "initial_key_mismatch", "label": label}

    qsteps = len(quotient_path) - 1
    # state, accumulated official moves, atomic cost
    beam = [(exact_initial, (), 0)]
    layers = []
    total_bound_prunes = 0
    total_dead_next = 0
    widest_raw = 1

    for step_index, qstate in enumerate(quotient_path[1:], 1):
        if time.time() - start >= seconds:
            return None, {
                "code": "time_cap",
                "label": label,
                "step": step_index,
                "quotient_steps": qsteps,
                "beam": len(beam),
                "seconds": round(time.time() - start, 3),
                "bound_prunes": total_bound_prunes,
                "dead_next": total_dead_next,
            }

        desired = v2.path_state_key(ns, qstate)
        remaining = qsteps - step_index
        by_exact = {}
        raw = 0
        bound_prunes = 0
        min_raw_lower_bound = None

        for state, path, cost in beam:
            for nxt, edge in candidate_edges(core, ns, state, desired, total_cap):
                raw += 1
                nc = cost + len(edge)
                # Every remaining quotient transition needs at least one
                # official multiplication.  Ignore terminal suffix cost here,
                # making this a safe optimistic lower bound.
                lower_bound = nc + remaining
                if min_raw_lower_bound is None or lower_bound < min_raw_lower_bound:
                    min_raw_lower_bound = lower_bound
                if lower_bound >= ceiling_exclusive:
                    bound_prunes += 1
                    continue
                prev = by_exact.get(nxt)
                if prev is None or nc < prev[0]:
                    by_exact[nxt] = (nc, path, tuple(edge))

        total_bound_prunes += bound_prunes
        widest_raw = max(widest_raw, raw)
        if not by_exact:
            return None, {
                "code": "live_bound_frontier_exhausted",
                "label": label,
                "step": step_index,
                "quotient_steps": qsteps,
                "input_beam": len(beam),
                "raw_candidates": raw,
                "min_raw_lower_bound": min_raw_lower_bound,
                "ceiling_exclusive": ceiling_exclusive,
                "seconds": round(time.time() - start, 3),
                "bound_prunes": total_bound_prunes,
                "dead_next": total_dead_next,
            }

        ranked = []
        dead_next = 0
        next_desired = (
            v2.path_state_key(ns, quotient_path[step_index + 1])
            if step_index < qsteps else None
        )
        for nxt, (nc, parent_path, edge) in by_exact.items():
            # One-step exact lookahead changes only beam ranking.  A state with
            # no currently compiled next edge is not declared impossible; it is
            # merely ranked behind states with an economical continuation.
            next_min = 0
            next_count = 0
            if next_desired is not None:
                next_min = 10**9
                next_remaining = remaining - 1
                for _n2, e2 in candidate_edges(core, ns, nxt, next_desired, total_cap):
                    projected = nc + len(e2) + next_remaining
                    if projected < ceiling_exclusive:
                        next_count += 1
                        if len(e2) < next_min:
                            next_min = len(e2)
                if next_count == 0:
                    dead_next += 1
                    next_min = 10**6
            score = (
                nc + next_min,
                nc,
                -next_count,
                v2.total_len(nxt),
            )
            ranked.append((score, nxt, parent_path, edge, nc, next_min, next_count))

        total_dead_next += dead_next
        ranked.sort(key=lambda x: x[0])
        kept = ranked[: max(1, int(beam_width))]
        beam = [
            (nxt, parent_path + edge, nc)
            for _score, nxt, parent_path, edge, nc, _nm, _ncount in kept
        ]

        layer = {
            "step": step_index,
            "input_raw": raw,
            "distinct_exact": len(by_exact),
            "bound_prunes": bound_prunes,
            "dead_next": dead_next,
            "beam": len(beam),
            "best_cost": min(x[2] for x in beam),
            "best_optimistic_final": min(x[2] for x in beam) + remaining,
        }
        # Keep diagnostics compact while preserving early death/frontier shape.
        if step_index <= 8 or step_index == qsteps or step_index % 25 == 0:
            layers.append(layer)

    finals = []
    for state, path, cost in beam:
        suffix = v2.exact_terminal_suffix(core, state, reverse_paths)
        if suffix is None:
            continue
        total_cost = cost + len(suffix)
        if total_cost >= ceiling_exclusive:
            continue
        atomics = path + tuple(suffix)
        cur = exact_initial
        peak = v2.total_len(cur)
        for m in atomics:
            cur = core.apply_move(cur, m)
            peak = max(peak, v2.total_len(cur))
        if cur == v2.TARGET:
            finals.append((total_cost, atomics, len(suffix), peak))

    if not finals:
        return None, {
            "code": "no_exact_terminal_under_bound",
            "label": label,
            "quotient_steps": qsteps,
            "beam": len(beam),
            "ceiling_exclusive": ceiling_exclusive,
            "best_prefix_cost": min((x[2] for x in beam), default=None),
            "seconds": round(time.time() - start, 3),
            "bound_prunes": total_bound_prunes,
            "dead_next": total_dead_next,
            "widest_raw": widest_raw,
            "layers": layers,
        }

    total_cost, atomics, suffix_len, peak = min(finals, key=lambda x: x[0])
    return atomics, {
        "code": "ok",
        "label": label,
        "compiler": "fixed-skeleton-live-bound-lookahead-v1",
        "quotient_steps": qsteps,
        "atomic_cost": total_cost,
        "suffix_len": suffix_len,
        "peak": peak,
        "ceiling_exclusive": ceiling_exclusive,
        "beam_width": beam_width,
        "seconds": round(time.time() - start, 3),
        "bound_prunes": total_bound_prunes,
        "dead_next": total_dead_next,
        "widest_raw": widest_raw,
        "layers": layers,
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
        c["challenge_id"]: c
        for c in manifest["challenges"]
        if c["challenge_id"].startswith("ac-")
    }
    c = ac_by_id[args.target_id]

    snapshot_obj, live = v2.snapshot_file_map(args.snapshot_ac_file)
    save_json(out / "snapshot_ac_start.json", snapshot_obj)
    live_row = live[args.target_id]
    live_best = live_row.get("currentBestLength")
    if not isinstance(live_best, int):
        report = {
            "experiment": "acc-gssub-v9-fixed-skeleton-live-bound-lookahead",
            "challenge_id": args.target_id,
            "code": "target_not_currently_solved",
            "live_status": live_row.get("status"),
            "live_best": live_best,
        }
        save_json(out / "report.json", report)
        print("SKELETON_LOOKAHEAD", json.dumps(report, sort_keys=True), flush=True)
        return

    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = v2.total_len(exact)
    qcap = min(args.max_quotient_total, max(initial_total + 36, 48))
    ns = v2.load_gssub(acsolverx_root)

    r0 = v2.int_word_to_str(exact[0])
    r1 = v2.int_word_to_str(exact[1])
    solver = ns["ACRelatorSolver"](
        r0, r1,
        max_nodes=args.max_nodes,
        max_len=qcap,
        verbose=False,
        stop_early=False,
    )
    t0 = time.time()
    found = solver.solve()
    if len(found) == 3:
        quotient_path, quotient_nodes, _seen = found
    else:
        quotient_path, quotient_nodes = found[:2]
    quotient_seconds = round(time.time() - t0, 3)

    if quotient_path is None:
        report = {
            "experiment": "acc-gssub-v9-fixed-skeleton-live-bound-lookahead",
            "challenge_id": args.target_id,
            "code": "quotient_not_found",
            "live_best": live_best,
            "quotient_nodes": int(quotient_nodes),
            "quotient_seconds": quotient_seconds,
        }
        save_json(out / "report.json", report)
        print("SKELETON_LOOKAHEAD", json.dumps(report, sort_keys=True), flush=True)
        return

    reverse_paths, reverse_hist = v2.build_reverse(core, args.reverse_depth, args.reverse_cap)
    qsteps = len(quotient_path) - 1
    print("QUOTIENT_SKELETON", json.dumps({
        "challenge_id": args.target_id,
        "nodes": int(quotient_nodes),
        "steps": qsteps,
        "seconds": quotient_seconds,
        "live_best": live_best,
        "strict_overhead_budget_before_suffix": live_best - 1 - qsteps,
    }, sort_keys=True), flush=True)

    strict, strict_meta = compile_fixed_skeleton(
        core, ns, exact, quotient_path, reverse_paths,
        limits["max_total_relator_length"],
        ceiling_exclusive=live_best,
        beam_width=args.strict_beam,
        seconds=args.strict_seconds,
        label="strict",
    )

    atomics = strict
    selected_meta = strict_meta
    near_meta = None
    if atomics is None:
        near_ceiling = int(math.floor(live_best * (1.0 + args.near_miss_frac)))
        atomics, near_meta = compile_fixed_skeleton(
            core, ns, exact, quotient_path, reverse_paths,
            limits["max_total_relator_length"],
            ceiling_exclusive=near_ceiling + 1,
            beam_width=args.near_beam,
            seconds=args.near_seconds,
            label="near",
        )
        selected_meta = near_meta

    report = {
        "experiment": "acc-gssub-v9-fixed-skeleton-live-bound-lookahead",
        "official_commit": "99a65377c5c4f412cd9af7b8d31c41464a855736",
        "acsolverx_commit": "6a12515fe1d95178a483b76d5553266e61122417",
        "challenge_id": args.target_id,
        "live_status": live_row.get("status"),
        "live_best": live_best,
        "live_k_teams": live_row.get("kTeams"),
        "initial_total": initial_total,
        "quotient_total_cap": qcap,
        "quotient_nodes": int(quotient_nodes),
        "quotient_steps": qsteps,
        "quotient_seconds": quotient_seconds,
        "reverse_states": len(reverse_paths),
        "reverse_hist": reverse_hist,
        "strict_overhead_budget_before_suffix": live_best - 1 - qsteps,
        "strict_compile": strict_meta,
        "near_compile": near_meta,
        "verified": False,
        "candidate_length": None,
    }

    any_text = ""
    strict_text = ""
    if atomics is not None:
        verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
        if not verdict.get("ok"):
            raise RuntimeError(("pinned_verifier_failure", args.target_id, verdict, selected_meta))
        report["verified"] = True
        report["verdict"] = verdict
        report["candidate_length"] = len(atomics)
        report["strict_vs_frozen_live"] = len(atomics) < live_best
        report["near_miss_vs_frozen_live"] = (
            live_best <= len(atomics) <= int(math.floor(live_best * (1.0 + args.near_miss_frac)))
        )
        any_text = f"{args.target_id}: {json.dumps(list(atomics), separators=(',', ':'))}\n"
        if len(atomics) < live_best:
            strict_text = any_text

    (out / "candidate_any.txt").write_text(any_text, encoding="utf-8")
    (out / "submission_v9.txt").write_text(strict_text, encoding="utf-8")
    save_json(out / "report.json", report)
    print("SKELETON_LOOKAHEAD", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
