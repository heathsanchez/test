#!/usr/bin/env python3
"""
ACC V2 checkpoint transfer.

Extract public substitution paths from Math-AI-Caltech/ACSolverX's released
610-solve checkpoint, map their Miller-Schupp presentations into the scored ACC
pool by presentation equivalence, compile every substitution step into the
official SAIR atomic move language, replay with the pinned official verifier,
then live-filter before any submission.

The checkpoint is proposal/history. The SAIR verifier is authority.
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from solver_v2_gssub import (
    api,
    data_obj,
    snapshot_map,
    total_len,
    build_reverse,
    orientation_options,
    current_competitive,
    submit_batch,
)


TARGET = ((1,), (2,))
RANK = {-2: 0, 2: 1, -1: 2, 1: 3}  # Y < y < X < x, ACSolverX GS-Sub order


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", default="andrews_curtis/out_v2_checkpoint")
    p.add_argument("--checkpoint-name", default="610model")
    p.add_argument("--checkpoint-step", type=int, default=1000)
    p.add_argument("--ms-prefix", type=int, default=634)
    p.add_argument("--max-compile", type=int, default=180)
    p.add_argument("--compile-seconds", type=int, default=900)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--submit", action="store_true")
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def invert(w):
    return tuple(-a for a in reversed(w))


def cyclic_reduce(w):
    w = tuple(w)
    a, b = 0, len(w)
    while b - a >= 2 and w[a] == -w[b - 1]:
        a += 1
        b -= 1
    return w[a:b]


def rank_key(w):
    return tuple(RANK[a] for a in w)


def min_rotation(w, numeric=False):
    w = tuple(w)
    if not w:
        return ()
    if numeric:
        return min(w[i:] + w[:i] for i in range(len(w)))
    return min(
        (w[i:] + w[:i] for i in range(len(w))),
        key=rank_key,
    )


def canon_word(w):
    w = cyclic_reduce(w)
    if not w:
        return ()
    a = min_rotation(w)
    b = min_rotation(invert(w))
    return a if rank_key(a) <= rank_key(b) else b


def pair_sort_key(w):
    return (len(w), rank_key(w))


def canon_pair(state):
    a = canon_word(state[0])
    b = canon_word(state[1])
    return tuple(sorted((a, b), key=pair_sort_key))


def parse_padded_presentation(row, max_length=24):
    if len(row) != 2 * max_length:
        raise ValueError(f"expected {2*max_length} entries, got {len(row)}")
    a = tuple(int(x) for x in row[:max_length] if int(x) != 0)
    b = tuple(int(x) for x in row[max_length:] if int(x) != 0)
    return (a, b)


def rotate_left(w, k):
    w = tuple(w)
    if not w:
        return ()
    k %= len(w)
    return w[k:] + w[:k]


def free_reduce(w):
    out = []
    for a in w:
        if out and out[-1] == -a:
            out.pop()
        else:
            out.append(a)
    return tuple(out)


def min_numeric_rotation_index(w):
    w = tuple(w)
    if not w:
        return 0
    best_i = 0
    best = w
    for i in range(1, len(w)):
        r = w[i:] + w[:i]
        if r < best:
            best = r
            best_i = i
    return best_i


def checkpoint_s_move(state, action, max_length=24):
    """
    Pure-Python replay of ACSolverX envs/ac_moves.py::s_move at the word level.
    Used only to determine the next quotient class of a published checkpoint
    action; final certificates never rely on this implementation.
    """
    i, inv_second, k1, k2 = map(int, action)
    r0, r1 = state
    comp1 = invert(r1) if inv_second == 1 else r1
    rot0 = rotate_left(r0, k1)
    rot1 = rotate_left(comp1, k2)

    prod = free_reduce(rot0 + rot1)
    if len(prod) > max_length:
        new_rel = cyclic_reduce(rot0)
    else:
        new_rel = cyclic_reduce(prod)

    # JAX implementation skips the whole update if the computed relator equals
    # the rotated first relator.
    if new_rel == rot0:
        return state

    if len(new_rel) > max_length:
        return state
    booth = min_numeric_rotation_index(new_rel)
    new_rel = rotate_left(new_rel, booth)

    return (new_rel, r1) if i == 0 else (r0, new_rel)


def decode_action(sample, max_length=24):
    L = max_length
    a = int(sample)
    k1 = (a // (4 * L)) + 1
    rem = a % (4 * L)
    k2_tmp = rem // 4
    ij = rem % 4
    i = ij // 2
    j = ij % 2
    k2 = k2_tmp * ((-1) ** j) - j
    return [int(i), int(j), int(k1), int(k2)]


def pair_from_desired_and_source(desired_pair, source_class):
    vals = list(desired_pair)
    for idx, w in enumerate(vals):
        if w == source_class:
            vals.pop(idx)
            if len(vals) == 1:
                return vals[0]
    return None


def compile_checkpoint_transition(core, current, target_index, desired_pair, total_cap):
    """
    Find the shortest official atomic macro whose quotient result is the desired
    checkpoint class, while modifying the same target relator.

    We enumerate all inversion/cyclic-conjugation representatives. Source
    symmetries are undone after multiplication, so the source relator is exact.
    """
    i = int(target_index)
    j = 1 - i
    source_class = canon_word(current[j])
    desired_target = pair_from_desired_and_source(desired_pair, source_class)

    target_opts = orientation_options(core, current[i], i)
    source_opts = orientation_options(core, current[j], j)
    mul = 2 if i == 0 else 4

    best = None
    for tw, tseq in target_opts:
        if not tw:
            continue
        for sw, sseq in source_opts:
            if not sw:
                continue
            nw = core.free_reduce(tw + sw)
            n = (nw, current[1]) if i == 0 else (current[0], nw)
            if total_len(n) > total_cap:
                continue

            # Cheap single-word filter when the untouched source class is
            # identifiable in the desired pair.
            if desired_target is not None and canon_word(nw) != desired_target:
                continue
            if canon_pair(n) != desired_pair:
                continue

            undo = tuple(core.INVERSE_MOVE[m] for m in reversed(sseq))
            path = tuple(tseq) + tuple(sseq) + (mul,) + undo
            if best is None or len(path) < len(best[1]):
                # Exact local replay under official semantics.
                chk = current
                for m in path:
                    chk = core.apply_move(chk, m)
                if chk != n:
                    raise RuntimeError("checkpoint compiler local replay mismatch")
                best = (n, path)

    return best


def bridge_to_target(core, start, reverse_paths):
    p = reverse_paths.get(start)
    if p is not None:
        return tuple(p)

    # Terminal checkpoint states have two total letters. Tiny exact BFS is
    # enough even if the reverse census was capped.
    q = collections.deque([(start, ())])
    seen = {start}
    while q:
        s, path = q.popleft()
        if len(path) >= 10:
            continue
        for m in range(core.NUM_MOVES):
            n = core.apply_move(s, m)
            if n in seen or total_len(n) > 24:
                continue
            npth = path + (m,)
            if n == TARGET:
                return npth
            seen.add(n)
            q.append((n, npth))
    return None


def restore_solve_data(acsolverx_root: Path, checkpoint_name: str, step: int):
    import jax.numpy as jnp
    import orbax.checkpoint as ocp

    ckpt_abs = acsolverx_root / "ppo_checkpoints" / checkpoint_name
    manager = ocp.CheckpointManager(
        str(ckpt_abs), item_names=("params", "solve_data", "config")
    )
    actual_step = manager.latest_step() if step < 0 else step
    if actual_step is None:
        raise RuntimeError("checkpoint has no step")

    # Restore at the checkpoint's native solve-table shape. The public
    # repository's current AC19_extended.txt can differ in total row count from
    # the historical training snapshot; the first 634 MS rows are the stable
    # prefix we actually consume below.
    md_path = ckpt_abs / str(actual_step) / "solve_data" / "_METADATA"
    md = json.loads(md_path.read_text())
    shapes = []
    for entry in md.get("tree_metadata", {}).values():
        shape = entry.get("value_metadata", {}).get("write_shape")
        if shape:
            shapes.append(shape)
    row_counts = {int(s[0]) for s in shapes if len(s) >= 1}
    if len(row_counts) != 1:
        raise RuntimeError(f"cannot infer checkpoint solve-data rows: {row_counts}")
    num_states = row_counts.pop()

    cfg = manager.restore(
        actual_step,
        args=ocp.args.Composite(config=ocp.args.JsonRestore({})),
    )
    width = int(cfg.config["NUM_STEPS"])
    dummy = {
        "solved_idx": jnp.zeros(num_states, dtype=jnp.bool_),
        "path_lengths": jnp.zeros(num_states, dtype=jnp.int32),
        "best_paths": jnp.zeros((num_states, width), dtype=jnp.int32),
    }
    restored = manager.restore(
        actual_step,
        args=ocp.args.Composite(
            solve_data=ocp.args.StandardRestore(dummy)
        ),
    )
    sd = restored.solve_data
    return {
        "step": int(actual_step),
        "solved_idx": np.asarray(sd["solved_idx"]),
        "path_lengths": np.asarray(sd["path_lengths"]),
        "best_paths": np.asarray(sd["best_paths"]),
        "width": width,
    }


def load_dataset_prefix(path: Path, n):
    rows = []
    with path.open() as f:
        for idx, line in enumerate(f):
            if idx >= n:
                break
            rows.append(parse_padded_presentation(ast.literal_eval(line.strip())))
    return rows


def challenge_maps(manifest):
    ac = {}
    sac = {}
    for c in manifest["challenges"]:
        cid = c["challenge_id"]
        if cid.startswith("ac-"):
            ac[cid] = c
        elif cid.startswith("sac-"):
            sac[cid] = c
    return ac, sac


def main():
    args = parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    acc_root = Path(args.acc_root).resolve()
    acsolverx_root = Path(args.acsolverx_root).resolve()

    sys.path.insert(0, str(acc_root / "competition" / "tools"))
    from verifier import core, stable_core  # noqa

    manifest = json.loads(
        (acc_root / "competition" / "tools" / "verifier" / "data" / "manifest.json").read_text()
    )
    limits = manifest["limits"]
    ac_by_id, sac_by_id = challenge_maps(manifest)

    ac_snapshot, ac_live = snapshot_map("ac")
    sac_snapshot, sac_live = snapshot_map("stable_ac")
    save_json(out / "snapshot_ac_before.json", ac_snapshot)
    save_json(out / "snapshot_stable_ac_before.json", sac_snapshot)

    # Map each scored presentation quotient class to its challenge id.
    scored_key_to_id = {}
    for cid, c in ac_by_id.items():
        k = canon_pair(tuple(tuple(w) for w in c["initial_relators"]))
        if k in scored_key_to_id:
            raise RuntimeError("scored quotient collision")
        scored_key_to_id[k] = cid

    dataset_states = load_dataset_prefix(
        acsolverx_root / "data" / "AC19_extended.txt",
        args.ms_prefix,
    )

    print("RESTORE_CHECKPOINT", flush=True)
    sd = restore_solve_data(
        acsolverx_root, args.checkpoint_name, args.checkpoint_step
    )
    solved_prefix = [
        i for i in range(min(args.ms_prefix, len(sd["solved_idx"])))
        if bool(sd["solved_idx"][i])
    ]
    print("CHECKPOINT", json.dumps({
        "step": sd["step"],
        "width": sd["width"],
        "solved_first_prefix": len(solved_prefix),
        "prefix": args.ms_prefix,
    }, sort_keys=True), flush=True)

    mapped = []
    for idx in solved_prefix:
        state = dataset_states[idx]
        cid = scored_key_to_id.get(canon_pair(state))
        if cid is None:
            continue
        mapped.append({
            "dataset_index": idx,
            "challenge_id": cid,
            "live_status": ac_live[cid]["status"],
            "live_best": ac_live[cid].get("currentBestLength"),
            "checkpoint_steps": int(sd["path_lengths"][idx]),
            "initial_total": total_len(state),
        })

    # First priority: still-unsolved scored presentations. Then solved rows only
    # as a diagnostic for path quality if compile budget remains.
    mapped.sort(key=lambda r: (
        0 if r["live_status"] == "unsolved" else 1,
        r["checkpoint_steps"],
        r["dataset_index"],
    ))
    save_json(out / "mapped_checkpoint_rows.json", mapped)

    reverse_paths, reverse_hist = build_reverse(
        core, args.reverse_depth, args.reverse_cap
    )

    compiled = {}
    attempts = []
    t0 = time.time()
    for rec in mapped[: args.max_compile]:
        if time.time() - t0 > args.compile_seconds:
            print("COMPILE_TIME_CAP", round(time.time() - t0, 2), flush=True)
            break

        idx = rec["dataset_index"]
        cid = rec["challenge_id"]
        c = ac_by_id[cid]
        current = tuple(tuple(w) for w in c["initial_relators"])
        checkpoint_state = dataset_states[idx]

        if canon_pair(current) != canon_pair(checkpoint_state):
            raise RuntimeError("mapping invariant failed")

        nsteps = int(sd["path_lengths"][idx])
        packed = sd["best_paths"][idx][:nsteps]
        atomics = ()
        fail = None

        for step_i, packed_action in enumerate(packed):
            action = decode_action(int(packed_action), max_length=24)
            checkpoint_state = checkpoint_s_move(
                checkpoint_state, action, max_length=24
            )
            desired = canon_pair(checkpoint_state)

            if canon_pair(current) == desired:
                # Published action was quotient-noop from this representative.
                continue

            hit = compile_checkpoint_transition(
                core, current, action[0], desired,
                total_cap=limits["max_total_relator_length"],
            )
            if hit is None:
                fail = {
                    "code": "uncompiled_checkpoint_transition",
                    "step": step_i,
                    "action": action,
                    "packed": int(packed_action),
                    "current_pair": [list(w) for w in canon_pair(current)],
                    "desired_pair": [list(w) for w in desired],
                }
                break
            current, edge = hit
            atomics += tuple(edge)

        if fail is None:
            bridge = bridge_to_target(core, current, reverse_paths)
            if bridge is None:
                fail = {
                    "code": "no_terminal_bridge",
                    "final_pair": [list(w) for w in canon_pair(current)],
                    "checkpoint_final_pair": [list(w) for w in canon_pair(checkpoint_state)],
                }
            else:
                atomics += bridge

        attempt = dict(rec)
        attempt["compile_ok"] = fail is None
        attempt["failure"] = fail

        if fail is None:
            verdict = core.verify(
                c, list(atomics), c["move_spec_version"], limits
            )
            attempt["atomic_length"] = len(atomics)
            attempt["ac_verdict"] = verdict
            if verdict["ok"]:
                sid = "sac-" + cid[3:]
                sc = sac_by_id[sid]
                sp = tuple(atomics) + (16, 15)
                sv = stable_core.verify(
                    sc, list(sp), sc["move_spec_version"], limits
                )
                attempt["stable_verdict"] = sv
                if sv["ok"]:
                    compiled[cid] = {
                        "path": tuple(atomics),
                        "verdict": verdict,
                        "stable_id": sid,
                        "stable_path": sp,
                        "stable_verdict": sv,
                        "dataset_index": idx,
                        "checkpoint_steps": nsteps,
                    }
        attempts.append(attempt)

        if len(attempts) % 10 == 0 or cid in compiled:
            print("PROGRESS", json.dumps({
                "attempts": len(attempts),
                "verified": len(compiled),
                "last": cid,
                "last_live_status": rec["live_status"],
                "elapsed_s": round(time.time() - t0, 2),
            }, sort_keys=True), flush=True)

    save_json(out / "compile_attempts.json", attempts)

    # Live filter again immediately before submitting.
    ac_pre, ac_now = snapshot_map("ac")
    sac_pre, sac_now = snapshot_map("stable_ac")
    save_json(out / "snapshot_ac_pre_submit.json", ac_pre)
    save_json(out / "snapshot_stable_ac_pre_submit.json", sac_pre)

    lines = []
    selection = []
    for cid, v in sorted(compiled.items(), key=lambda kv: (len(kv[1]["path"]), kv[0])):
        ok, reason = current_competitive(ac_now[cid], len(v["path"]))
        selection.append({
            "challenge_id": cid,
            "problem": "ac",
            "length": len(v["path"]),
            "live_status": ac_now[cid]["status"],
            "live_best": ac_now[cid].get("currentBestLength"),
            "selected": ok,
            "reason": reason,
        })
        if ok:
            lines.append(f"{cid}: {json.dumps(list(v['path']), separators=(',', ':'))}")

        sid = v["stable_id"]
        sok, sreason = current_competitive(sac_now[sid], len(v["stable_path"]))
        selection.append({
            "challenge_id": sid,
            "problem": "stable_ac",
            "length": len(v["stable_path"]),
            "live_status": sac_now[sid]["status"],
            "live_best": sac_now[sid].get("currentBestLength"),
            "selected": sok,
            "reason": sreason,
        })
        if sok:
            lines.append(f"{sid}: {json.dumps(list(v['stable_path']), separators=(',', ':'))}")

    save_json(out / "selection.json", selection)
    text = "\n".join(lines) + ("\n" if lines else "")
    (out / "submission_checkpoint_v2.txt").write_text(text, encoding="utf-8")

    submit_info = None
    if args.submit and lines:
        if len(lines) > 500:
            # Prioritize AC first-solve rows if the public checkpoint yields a
            # very large batch; never silently consume multiple quotas.
            lines = lines[:500]
            text = "\n".join(lines) + "\n"
        sid, response, polls, final = submit_batch(text)
        submit_info = {
            "submission_id": sid,
            "response": response,
            "polls": polls,
            "final": final,
        }
        save_json(out / "submission_receipt.json", submit_info)
        ac_after, _ = snapshot_map("ac")
        sac_after, _ = snapshot_map("stable_ac")
        save_json(out / "snapshot_ac_after.json", ac_after)
        save_json(out / "snapshot_stable_ac_after.json", sac_after)

    report = {
        "experiment": "andrews-curtis-v2-public-checkpoint-transfer",
        "official_commit": "99a65377c5c4f412cd9af7b8d31c41464a855736",
        "acsolverx_commit": "6a12515fe1d95178a483b76d5553266e61122417",
        "checkpoint_step": sd["step"],
        "checkpoint_prefix": args.ms_prefix,
        "checkpoint_solved_prefix": len(solved_prefix),
        "mapped_to_scored_pool": len(mapped),
        "mapped_unsolved_at_start": sum(r["live_status"] == "unsolved" for r in mapped),
        "compile_attempts": len(attempts),
        "verified_ac": len(compiled),
        "competitive_rows": len(lines),
        "submission_id": None if submit_info is None else submit_info["submission_id"],
        "compile_seconds": round(time.time() - t0, 3),
        "reverse_hist": reverse_hist,
        "solutions": [
            {
                "ac_id": cid,
                "dataset_index": v["dataset_index"],
                "checkpoint_steps": v["checkpoint_steps"],
                "ac_length": len(v["path"]),
                "ac_hash": v["verdict"]["certificate_hash"],
                "stable_id": v["stable_id"],
                "stable_length": len(v["stable_path"]),
                "stable_hash": v["stable_verdict"]["certificate_hash"],
            }
            for cid, v in sorted(compiled.items())
        ],
    }
    b = json.dumps(report, indent=2, sort_keys=True).encode()
    (out / "report_checkpoint_v2.json").write_bytes(b)
    (out / "report_checkpoint_v2.sha256").write_text(
        hashlib.sha256(b).hexdigest() + "  report_checkpoint_v2.json\n"
    )
    print("FINAL", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
