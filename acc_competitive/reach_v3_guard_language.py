#!/usr/bin/env python3
"""
ACC Reach V3: exhaust the smallest anonymous one-site Boolean edit language
over the existing GS-Sub proposal-admission guard.

The current proposal generator admits a rotated product only when the boundary
letters are inverse.  Let b be that one Boolean observation.  The complete
Boolean transducer language b -> admit has exactly four functions:

  never:       0,0
  boundary:    0,1   (current behavior)
  nonboundary: 1,0
  all:         1,1

No target features, fitted weights, ACC motifs, family labels, or extra state
are introduced.  Search priority remains the current total relator length.
"""
from __future__ import annotations

import argparse
import heapq
import itertools
import json
import sys
from pathlib import Path


GUARDS = {
    "never": (0, 0),
    "boundary": (0, 1),
    "nonboundary": (1, 0),
    "all": (1, 1),
}


def save(p, o):
    Path(p).write_text(json.dumps(o, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--snapshot-ac", required=True)
    ap.add_argument("--snapshot-stable", required=True)
    ap.add_argument("--target-id", required=True)
    ap.add_argument("--role", choices=["prospective", "protected_replay"], required=True)
    ap.add_argument("--guard", choices=sorted(GUARDS), required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-nodes", type=int, default=150000)
    ap.add_argument("--max-quotient-total", type=int, default=100)
    ap.add_argument("--reverse-depth", type=int, default=7)
    ap.add_argument("--reverse-cap", type=int, default=250000)
    ap.add_argument("--compiler-beam", type=int, default=16)
    return ap.parse_args()


def guarded_neighbors(ns, r1, r2, table):
    np = ns["np"]
    inv = ns["inverse_relator_nj"]
    is_inverse = ns["is_inverse_nj"]
    results = []
    for c in (r2, inv(r2)):
        for i in range(len(r1)):
            rot1 = np.roll(r1, 2 * i)
            for j in range(len(c)):
                rot2 = np.roll(c, 2 * j)
                if len(rot1) == 0 or len(rot2) == 0:
                    continue
                b = 1 if is_inverse(rot1[-1], rot2[0]) else 0
                if not table[b]:
                    continue
                neighbour = np.concatenate((rot1, rot2))
                results.append((neighbour, r2))
                results.append((r1, neighbour))
    return results


def solve_guarded(ns, r0, r1, max_nodes, max_len, table):
    reduce_relator = ns["reduce_relator_nj"]
    canonical_pair = ns["canonical_pair_nj"]
    state_to_key = ns["state_to_key"]
    str_to_arr = ns["str_to_arr"]

    initial = canonical_pair(
        reduce_relator(str_to_arr(r0)),
        reduce_relator(str_to_arr(r1)),
    )
    ikey = state_to_key(initial)
    counter = itertools.count()
    pq = [(len(initial[0]) + len(initial[1]), next(counter), 0, ikey)]
    prev = {ikey: None}
    best_depth = {ikey: 0}
    nodes = 0

    def key_to_state(key):
        return (str_to_arr(key[0]), str_to_arr(key[1]))

    while pq and nodes < max_nodes:
        _, _, depth, key = heapq.heappop(pq)
        if depth != best_depth.get(key):
            continue
        nodes += 1
        a, b = key_to_state(key)
        if len(a) == 1 and len(b) == 1:
            path = []
            cur = key
            while cur is not None:
                path.append(key_to_state(cur))
                cur = prev[cur]
            path.reverse()
            return path, nodes

        nd = depth + 1
        for nr1, nr2 in guarded_neighbors(ns, a, b, table):
            nr1r = reduce_relator(nr1)
            nr2r = reduce_relator(nr2)
            if len(nr1r) + len(nr2r) >= max_len:
                continue
            c1, c2 = canonical_pair(nr1r, nr2r)
            knew = state_to_key((c1, c2))
            if nd >= best_depth.get(knew, 10**18):
                continue
            best_depth[knew] = nd
            prev[knew] = key
            heapq.heappush(
                pq,
                (len(c1) + len(c2), next(counter), nd, knew),
            )
    return None, nodes


def compile_general_candidates(core, ns, state, desired, total_cap):
    # Same exact compiler substrate as V2, but without assuming a boundary
    # cancellation.  Exact replay through official moves remains authority.
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        gssub_key,
        orientation_options,
        orientation_options_no_invert,
        total_len,
    )

    best_exact = {}
    for i in (0, 1):
        j = 1 - i
        target_opts = orientation_options(core, state[i], i)
        source_opts = orientation_options_no_invert(core, state[j], j)
        mul_pos = 2 if i == 0 else 4
        mul_neg = 3 if i == 0 else 5
        for tw, tseq in target_opts:
            if not tw:
                continue
            for sw, sseq in source_opts:
                if not sw:
                    continue
                undo_source = tuple(core.INVERSE_MOVE[m] for m in reversed(sseq))
                for source_word, mul in ((sw, mul_pos), (core.invert(sw), mul_neg)):
                    new_word = core.free_reduce(tw + source_word)
                    nxt = (new_word, state[1]) if i == 0 else (state[0], new_word)
                    if total_len(nxt) > total_cap:
                        continue
                    if gssub_key(ns, nxt) != desired:
                        continue
                    atomics = tuple(tseq) + tuple(sseq) + (mul,) + undo_source
                    chk = state
                    for m in atomics:
                        chk = core.apply_move(chk, m)
                    if chk != nxt:
                        raise RuntimeError("generalized exact compiler mismatch")
                    old = best_exact.get(nxt)
                    if old is None or len(atomics) < len(old):
                        best_exact[nxt] = atomics
    return [(n, e) for n, e in best_exact.items()]


def compile_general_path(core, ns, exact_initial, quotient_path, reverse_paths, total_cap, beam_width):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import exact_terminal_suffix, gssub_key, path_state_key, total_len

    if not quotient_path:
        return None, {"code": "empty_quotient_path"}
    if gssub_key(ns, exact_initial) != path_state_key(ns, quotient_path[0]):
        return None, {"code": "initial_key_mismatch"}

    beam = [(exact_initial, (), 0)]
    for step_index, qstate in enumerate(quotient_path[1:], 1):
        desired = path_state_key(ns, qstate)
        by_exact = {}
        for state, path, cost in beam:
            for nxt, edge in compile_general_candidates(core, ns, state, desired, total_cap):
                nc = cost + len(edge)
                old = by_exact.get(nxt)
                if old is None or nc < old[0]:
                    by_exact[nxt] = (nc, path, tuple(edge))
        if not by_exact:
            return None, {"code": "uncompiled_transition", "step": step_index}
        ranked = sorted(
            ((c, n, p, e) for n, (c, p, e) in by_exact.items()),
            key=lambda x: x[0],
        )[:max(1, int(beam_width))]
        beam = [(n, p + e, c) for c, n, p, e in ranked]

    finals = []
    for state, path, cost in beam:
        suffix = exact_terminal_suffix(core, state, reverse_paths)
        if suffix is not None:
            finals.append((cost + len(suffix), path + tuple(suffix)))
    if not finals:
        return None, {"code": "no_exact_terminal_bridge"}
    _, atomics = min(finals, key=lambda x: x[0])

    end = exact_initial
    peak = total_len(end)
    for m in atomics:
        end = core.apply_move(end, m)
        peak = max(peak, total_len(end))
    if end != ((1,), (2,)):
        return None, {"code": "compiled_path_not_target"}
    return atomics, {
        "code": "ok",
        "compiler": "generalized-guard-exact-beam-v1",
        "quotient_steps": len(quotient_path) - 1,
        "atomic_cost": len(atomics),
        "peak": peak,
    }


def main():
    a = parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse,
        challenge_maps,
        int_word_to_str,
        load_gssub,
        snapshot_file_map,
        total_len,
    )

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    ac_by_id, sac_by_id = challenge_maps(manifest)
    _, ac_live = snapshot_file_map(a.snapshot_ac)
    _, st_live = snapshot_file_map(a.snapshot_stable)

    c = ac_by_id[a.target_id]
    exact = tuple(tuple(w) for w in c["initial_relators"])
    initial_total = total_len(exact)
    qcap = min(a.max_quotient_total, max(initial_total + 36, 48))

    ns = load_gssub(Path(a.acsolverx_root))
    reverse_paths, reverse_hist = build_reverse(core, a.reverse_depth, a.reverse_cap)

    table = GUARDS[a.guard]
    qpath, nodes = solve_guarded(
        ns,
        int_word_to_str(exact[0]),
        int_word_to_str(exact[1]),
        a.max_nodes,
        qcap,
        table,
    )

    cid = a.target_id
    sid = "sac-" + cid[3:]
    row = {
        "experiment": "ACC_REACH_V3_BOOLEAN_GUARD",
        "challenge_id": cid,
        "stable_id": sid,
        "role": a.role,
        "guard": a.guard,
        "guard_truth_table_false_true": list(table),
        "max_nodes": a.max_nodes,
        "nodes": int(nodes),
        "initial_total": initial_total,
        "quotient_cap": qcap,
        "quotient_found": qpath is not None,
        "frozen_ac_best": ac_live.get(cid, {}).get("currentBestLength"),
        "frozen_stable_best": st_live.get(sid, {}).get("currentBestLength"),
        "reverse_states": len(reverse_paths),
        "reverse_hist": reverse_hist,
    }

    if qpath is not None:
        atomics, comp = compile_general_path(
            core, ns, exact, qpath, reverse_paths,
            limits["max_total_relator_length"], a.compiler_beam,
        )
        row["compile"] = comp
        if atomics is not None:
            v = core.verify(c, list(atomics), c["move_spec_version"], limits)
            row["ac_verdict"] = v
            row["atomic_length"] = len(atomics)
            if v.get("ok"):
                sc = sac_by_id[sid]
                sp = tuple(atomics) + (16, 15)
                sv = stable_core.verify(sc, list(sp), sc["move_spec_version"], limits)
                row["stable_verdict"] = sv
                row["stable_length"] = len(sp)
                if sv.get("ok"):
                    (out / "candidate_ac.txt").write_text(
                        f"{cid}: {json.dumps(list(atomics),separators=(',',':'))}\n",
                        encoding="utf-8",
                    )

    alen = row.get("atomic_length")
    slen = row.get("stable_length")
    abest = row.get("frozen_ac_best")
    sbest = row.get("frozen_stable_best")
    row["strict_ac_frozen"] = (
        a.role == "prospective"
        and isinstance(alen, int) and isinstance(abest, int) and alen < abest
        and (row.get("ac_verdict") or {}).get("ok") is True
    )
    row["strict_stable_frozen"] = (
        a.role == "prospective"
        and isinstance(slen, int) and isinstance(sbest, int) and slen < sbest
        and (row.get("stable_verdict") or {}).get("ok") is True
    )

    save(out / "result.json", row)
    print("REACH_V3_CASE", json.dumps({
        "guard": a.guard,
        "cid": cid,
        "role": a.role,
        "nodes": row["nodes"],
        "quotient": row["quotient_found"],
        "atomic": row.get("atomic_length"),
        "replay_ok": (
            (row.get("ac_verdict") or {}).get("ok") is True
            and (row.get("stable_verdict") or {}).get("ok") is True
        ) if a.role == "protected_replay" else None,
        "strict_ac": row["strict_ac_frozen"],
        "strict_stable": row["strict_stable_frozen"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
