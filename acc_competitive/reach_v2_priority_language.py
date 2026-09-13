#!/usr/bin/env python3
"""
ACC Reach V2: finite anonymous pre-quotient priority language.

Authority comes from the certified Reach V1 obstruction.  The change support is
restricted to the pre-quotient priority rule.  No ACC motifs, family labels,
target-specific features, fitted weights, or post-hoc parameter tuning appear
in the candidate language.

Primitive observables are the complete symmetric raw size information already
present at a quotient state plus path depth:

    s = min(len(r1), len(r2))
    l = max(len(r1), len(r2))
    d = quotient depth

The developmental language is the complete set of non-empty subset sums of
(s,l,d), all coefficients exactly 1.  Hence there are exactly 2^3-1 = 7
anonymous candidates.  Existing current and depth_weight=0.25 policies are
evaluated as controls, not members of the new language.
"""
from __future__ import annotations

import argparse
import heapq
import itertools
import json
import sys
from pathlib import Path


CONTROL_IDS = ["ac-08551", "ac-04629", "ac-00761"]


def save(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--targets", required=True)
    p.add_argument("--snapshot-ac", required=True)
    p.add_argument("--snapshot-stable", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--policy", required=True,
                   help="current | depth025 | mask1 ... mask7")
    p.add_argument("--max-nodes", type=int, default=150000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--compiler-beam", type=int, default=16)
    return p.parse_args()


def mask_name(mask: int) -> str:
    names = ["short", "long", "depth"]
    return "+".join(names[i] for i in range(3) if mask & (1 << i))


def solve_subset_priority(ns, r0, r1, max_nodes, max_len, mask):
    """
    Best-first GS-Sub with exactly one developmental degree of freedom:
    which non-empty subset of (shorter length, longer length, depth) is summed.

    Equal-priority states use insertion order only.  No hidden state feature is
    used as a tie-breaker.  Reopening at lower depth is the already-admitted
    depth-aware execution semantics from Reach V1.
    """
    reduce_relator = ns["reduce_relator_nj"]
    canonical_pair = ns["canonical_pair_nj"]
    state_to_key = ns["state_to_key"]
    str_to_arr = ns["str_to_arr"]
    get_neighbors = ns["get_neighbors_nj"]

    initial = canonical_pair(
        reduce_relator(str_to_arr(r0)),
        reduce_relator(str_to_arr(r1)),
    )
    ikey = state_to_key(initial)
    counter = itertools.count()

    def key_to_state(key):
        return (str_to_arr(key[0]), str_to_arr(key[1]))

    def priority_pair(a, b, depth):
        x, y = sorted((len(a), len(b)))
        vals = (x, y, depth)
        return sum(vals[i] for i in range(3) if mask & (1 << i))

    pq = [(priority_pair(initial[0], initial[1], 0), next(counter), 0, ikey)]
    prev = {ikey: None}
    best_depth = {ikey: 0}
    nodes = 0
    seen = {ikey}

    while pq and nodes < max_nodes:
        _, _, depth, key = heapq.heappop(pq)
        if depth != best_depth.get(key):
            continue
        nodes += 1
        r1a, r2a = key_to_state(key)
        if len(r1a) == 1 and len(r2a) == 1:
            path = []
            cur = key
            while cur is not None:
                path.append(key_to_state(cur))
                cur = prev[cur]
            path.reverse()
            return path, nodes, seen

        nd = depth + 1
        for nr1, nr2 in get_neighbors(r1a, r2a):
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
            seen.add(knew)
            pri = priority_pair(c1, c2, nd)
            heapq.heappush(pq, (pri, next(counter), nd, knew))
    return None, nodes, seen


def main():
    a = parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse,
        challenge_maps,
        compile_quotient_path_optimized,
        int_word_to_str,
        load_gssub,
        snapshot_file_map,
        solve_depth_weighted_gssub,
        total_len,
    )

    acc = Path(a.acc_root)
    acsolverx = Path(a.acsolverx_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    ac_by_id, sac_by_id = challenge_maps(manifest)

    ac_snap, ac_live = snapshot_file_map(a.snapshot_ac)
    st_snap, st_live = snapshot_file_map(a.snapshot_stable)
    prospectives = json.loads(Path(a.targets).read_text())
    prospectives = [x["challenge_id"] if isinstance(x, dict) else str(x) for x in prospectives]
    prospectives = list(dict.fromkeys(prospectives))
    controls = [x for x in CONTROL_IDS if x not in set(prospectives)]
    work = [(x, "prospective") for x in prospectives] + [(x, "protected_replay") for x in controls]

    policy = a.policy
    if policy == "current":
        policy_kind = "existing_current"
        mask = None
    elif policy == "depth025":
        policy_kind = "existing_depth025"
        mask = None
    elif policy.startswith("mask"):
        mask = int(policy[4:])
        if mask not in range(1, 8):
            raise ValueError(policy)
        policy_kind = "reach_v2_anonymous_subset_sum"
    else:
        raise ValueError(policy)

    ns = load_gssub(acsolverx)
    reverse_paths, reverse_hist = build_reverse(core, a.reverse_depth, a.reverse_cap)

    rows = []
    paths = {}
    for cid, role in work:
        c = ac_by_id[cid]
        exact = tuple(tuple(w) for w in c["initial_relators"])
        r0 = int_word_to_str(exact[0])
        r1 = int_word_to_str(exact[1])
        initial_total = total_len(exact)
        qcap = min(a.max_quotient_total, max(initial_total + 36, 48))

        if policy == "current":
            solver = ns["ACRelatorSolver"](
                r0, r1, max_nodes=a.max_nodes, max_len=qcap,
                verbose=False, stop_early=False,
            )
            found = solver.solve()
            if len(found) == 3:
                qpath, nodes, _ = found
            else:
                qpath, nodes = found[:2]
        elif policy == "depth025":
            qpath, nodes, _ = solve_depth_weighted_gssub(
                ns, r0, r1, a.max_nodes, qcap, 0.25
            )
        else:
            qpath, nodes, _ = solve_subset_priority(
                ns, r0, r1, a.max_nodes, qcap, mask
            )

        acrow = ac_live.get(cid, {})
        sid = "sac-" + cid[3:]
        strow = st_live.get(sid, {})
        rec = {
            "challenge_id": cid,
            "stable_id": sid,
            "role": role,
            "policy": policy,
            "policy_kind": policy_kind,
            "policy_mask": mask,
            "policy_expression": None if mask is None else mask_name(mask),
            "max_nodes": a.max_nodes,
            "initial_total": initial_total,
            "quotient_cap": qcap,
            "nodes": int(nodes),
            "quotient_found": qpath is not None,
            "frozen_ac_best": acrow.get("currentBestLength"),
            "frozen_stable_best": strow.get("currentBestLength"),
        }

        if qpath is not None:
            atomics, comp = compile_quotient_path_optimized(
                core, ns, exact, qpath, reverse_paths,
                total_cap=limits["max_total_relator_length"],
                beam_width=a.compiler_beam,
            )
            rec["compile"] = comp
            if atomics is not None:
                verdict = core.verify(c, list(atomics), c["move_spec_version"], limits)
                rec["ac_verdict"] = verdict
                rec["atomic_length"] = len(atomics)
                if verdict.get("ok"):
                    sc = sac_by_id[sid]
                    stable_path = tuple(atomics) + (16, 15)
                    sv = stable_core.verify(sc, list(stable_path), sc["move_spec_version"], limits)
                    rec["stable_verdict"] = sv
                    rec["stable_length"] = len(stable_path)
                    if sv.get("ok"):
                        paths[cid] = list(atomics)

        alen = rec.get("atomic_length")
        slen = rec.get("stable_length")
        abest = rec.get("frozen_ac_best")
        sbest = rec.get("frozen_stable_best")
        rec["strict_ac_frozen"] = (
            role == "prospective" and isinstance(alen, int) and isinstance(abest, int) and alen < abest
        )
        rec["strict_stable_frozen"] = (
            role == "prospective" and isinstance(slen, int) and isinstance(sbest, int) and slen < sbest
        )
        rows.append(rec)
        print("REACH_V2_TARGET", json.dumps({
            "policy": policy, "cid": cid, "role": role, "nodes": int(nodes),
            "quotient": qpath is not None, "atomic": rec.get("atomic_length"),
            "strict_ac": rec["strict_ac_frozen"],
            "strict_stable": rec["strict_stable_frozen"],
        }, sort_keys=True), flush=True)

    control_rows = [r for r in rows if r["role"] == "protected_replay"]
    prospective_rows = [r for r in rows if r["role"] == "prospective"]
    replay_ok = all(
        (r.get("ac_verdict") or {}).get("ok") is True
        and (r.get("stable_verdict") or {}).get("ok") is True
        for r in control_rows
    )
    strict_ac = sum(r["strict_ac_frozen"] for r in prospective_rows)
    strict_stable = sum(r["strict_stable_frozen"] for r in prospective_rows)
    verified_p = sum((r.get("ac_verdict") or {}).get("ok") is True for r in prospective_rows)
    quotient_p = sum(r["quotient_found"] for r in prospective_rows)

    report = {
        "experiment": "ACC_REACH_V2_ANONYMOUS_SUBSET_PRIORITY",
        "policy": policy,
        "policy_kind": policy_kind,
        "policy_mask": mask,
        "policy_expression": None if mask is None else mask_name(mask),
        "language_statement": (
            "Complete non-empty subset-sum closure of symmetric primitive "
            "(shorter_relator_length,longer_relator_length,quotient_depth), "
            "unit coefficients only; 7 candidates exactly."
        ),
        "prospective_targets": len(prospective_rows),
        "protected_controls": [r["challenge_id"] for r in control_rows],
        "protected_replay_ok": replay_ok,
        "quotient_hits_prospective": quotient_p,
        "verified_prospective": verified_p,
        "strict_ac_frozen": strict_ac,
        "strict_stable_frozen": strict_stable,
        "strict_rows_frozen": strict_ac + strict_stable,
        "total_nodes": sum(r["nodes"] for r in rows),
        "total_atomic_length_prospective": sum(
            r.get("atomic_length", 0) for r in prospective_rows
            if (r.get("ac_verdict") or {}).get("ok") is True
        ),
        "all_targets_processed": len(rows) == len(work),
        "reverse_states": len(reverse_paths),
        "reverse_hist": reverse_hist,
    }

    save(out / "results.json", rows)
    save(out / "report.json", report)
    save(out / "paths.json", paths)
    text = "".join(
        f"{cid}: {json.dumps(m,separators=(',',':'))}\n"
        for cid, m in sorted(paths.items())
        if cid in set(prospectives)
    )
    (out / "prospective_ac.txt").write_text(text, encoding="utf-8")
    print("REACH_V2_POLICY", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
