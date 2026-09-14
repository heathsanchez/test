#!/usr/bin/env python3
"""
ACC V5 matched frontier separator.

This is a diagnostic experiment, not a mechanism promotion.

For one frozen challenge it holds apparatus, target, verifier, search cap,
quotient cap and compiler family fixed, and varies only the already-warranted
pre-quotient search policy:

  current  : retained ACSolverX ordering
  mask3    : replay-clean V2 short+long ordering

For the quotient path each policy actually reaches, the exact compiler is then
run at frozen beam widths 1, 16 and 64.  This separates, within the declared
scope, search reachability, quotient-route choice, compiler-choice cost and
terminal-bridge cost.  Every produced certificate is independently replayed by
the pinned official verifier.

No failure here is promoted to unrestricted inadequacy.  The live leaderboard
is an OPEN consequence horizon.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--target-id", required=True)
    ap.add_argument("--role", required=True, choices=["protected_scoring", "responsive_loss"])
    ap.add_argument("--policy", required=True, choices=["current", "mask3"])
    ap.add_argument("--snapshot-ac", required=True)
    ap.add_argument("--snapshot-stable", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-nodes", type=int, default=200000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    ap.add_argument("--reverse-depth", type=int, default=7)
    ap.add_argument("--reverse-cap", type=int, default=250000)
    ap.add_argument("--beams", default="1,16,64", help="comma-separated frozen compiler beams")
    a = ap.parse_args()
    beams = tuple(dict.fromkeys(int(x) for x in a.beams.split(",") if x.strip()))
    if not beams or any(x < 1 for x in beams):
        raise ValueError(("bad_beams", a.beams))

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse,
        challenge_maps,
        compile_quotient_path_optimized,
        int_word_to_str,
        load_gssub,
        path_state_key,
        snapshot_file_map,
        total_len,
    )
    sys.path.insert(0, str(root / "acc_competitive"))
    from reach_v2_priority_language import solve_subset_priority

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    ac_by, sac_by = challenge_maps(manifest)
    _, ac_live = snapshot_file_map(a.snapshot_ac)
    _, st_live = snapshot_file_map(a.snapshot_stable)

    cid = a.target_id
    sid = "sac-" + cid[3:]
    c = ac_by[cid]
    sc = sac_by[sid]
    exact = tuple(tuple(w) for w in c["initial_relators"])
    r0, r1 = int_word_to_str(exact[0]), int_word_to_str(exact[1])
    initial_total = total_len(exact)
    qcap = min(a.max_quotient_total, max(initial_total + 36, 48))

    ns = load_gssub(Path(a.acsolverx_root))
    t0 = time.time()
    reverse_paths, reverse_hist = build_reverse(core, a.reverse_depth, a.reverse_cap)
    reverse_seconds = time.time() - t0

    search_start = time.time()
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
        qpath, nodes, _ = solve_subset_priority(
            ns, r0, r1, a.max_nodes, qcap, 3
        )
    search_seconds = time.time() - search_start

    row = {
        "experiment": "ACC_V5_MATCHED_FRONTIER_SEPARATOR_V1",
        "challenge_id": cid,
        "stable_id": sid,
        "role": a.role,
        "policy": a.policy,
        "warrant_status": "retained_current" if a.policy == "current" else "v2_replay_clean_frontier",
        "authority_scope": "frozen official verifier + frozen public leaderboard snapshot",
        "warrant_horizon": "OPEN",
        "max_nodes": a.max_nodes,
        "quotient_cap": qcap,
        "initial_total": initial_total,
        "nodes": int(nodes),
        "search_seconds": search_seconds,
        "quotient_found": qpath is not None,
        "frozen_ac_status": ac_live.get(cid, {}).get("status"),
        "frozen_ac_best": ac_live.get(cid, {}).get("currentBestLength"),
        "frozen_ac_kTeams": ac_live.get(cid, {}).get("kTeams"),
        "frozen_stable_status": st_live.get(sid, {}).get("status"),
        "frozen_stable_best": st_live.get(sid, {}).get("currentBestLength"),
        "frozen_stable_kTeams": st_live.get(sid, {}).get("kTeams"),
        "reverse_states": len(reverse_paths),
        "reverse_hist": reverse_hist,
        "reverse_seconds": reverse_seconds,
        "compiler_trials": [],
        "declared_beams": list(beams),
    }

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    best = None
    if qpath is not None:
        sig = [path_state_key(ns, q) for q in qpath]
        raw = json.dumps(sig, separators=(",", ":"), sort_keys=False).encode()
        row["quotient_steps"] = len(qpath) - 1
        row["quotient_path_sha256"] = hashlib.sha256(raw).hexdigest()

        for beam in beams:
            ct0 = time.time()
            atomics, comp = compile_quotient_path_optimized(
                core, ns, exact, qpath, reverse_paths,
                total_cap=limits["max_total_relator_length"],
                beam_width=beam,
            )
            trial = {
                "beam": beam,
                "compile_seconds": time.time() - ct0,
                "compile_code": comp.get("code"),
                "compiler": comp.get("compiler"),
                "quotient_steps": comp.get("quotient_steps"),
                "compiler_atomic_cost": comp.get("atomic_cost"),
                "terminal_suffix_len": comp.get("suffix_len"),
                "peak": comp.get("peak"),
            }
            if atomics is not None:
                v = core.verify(c, list(atomics), c["move_spec_version"], limits)
                stable = tuple(atomics) + (16, 15)
                sv = stable_core.verify(sc, list(stable), sc["move_spec_version"], limits)
                trial.update({
                    "ac_verdict": v,
                    "stable_verdict": sv,
                    "atomic_length": len(atomics),
                    "stable_length": len(stable),
                    "gap_ac_frozen": (
                        len(atomics) - row["frozen_ac_best"]
                        if isinstance(row["frozen_ac_best"], int) else None
                    ),
                    "gap_stable_frozen": (
                        len(stable) - row["frozen_stable_best"]
                        if isinstance(row["frozen_stable_best"], int) else None
                    ),
                })
                if v.get("ok") and sv.get("ok"):
                    if best is None or len(atomics) < len(best[0]):
                        best = (tuple(atomics), beam, trial)
            row["compiler_trials"].append(trial)

    if best is not None:
        atomics, beam, trial = best
        row["best_verified_beam"] = beam
        row["best_atomic_length"] = len(atomics)
        row["best_stable_length"] = len(atomics) + 2
        row["best_gap_ac_frozen"] = trial.get("gap_ac_frozen")
        row["best_gap_stable_frozen"] = trial.get("gap_stable_frozen")
        row["best_is_scoring_ac_frozen"] = (
            isinstance(row["frozen_ac_best"], int)
            and len(atomics) <= row["frozen_ac_best"]
        )
        row["best_is_scoring_stable_frozen"] = (
            isinstance(row["frozen_stable_best"], int)
            and len(atomics) + 2 <= row["frozen_stable_best"]
        )
        (out / "candidate_ac.txt").write_text(
            f"{cid}: {json.dumps(list(atomics), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    else:
        row["best_is_scoring_ac_frozen"] = False
        row["best_is_scoring_stable_frozen"] = False

    save(out / "result.json", row)
    print("V5_FRONTIER_SEPARATOR", json.dumps({
        "cid": cid,
        "role": a.role,
        "policy": a.policy,
        "nodes": int(nodes),
        "quotient": qpath is not None,
        "qsteps": row.get("quotient_steps"),
        "best_atomic": row.get("best_atomic_length"),
        "gap_ac": row.get("best_gap_ac_frozen"),
        "gap_stable": row.get("best_gap_stable_frozen"),
        "beam": row.get("best_verified_beam"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
