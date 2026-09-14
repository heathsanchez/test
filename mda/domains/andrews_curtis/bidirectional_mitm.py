#!/usr/bin/env python3
"""
Hard-bound bidirectional ACC search with developmental state identities.

This search asks one question only: is there an officially valid ac-04359
certificate strictly shorter than the frozen live record?

Both sides use exact official atomic transitions. Search-state retention is the
only abstraction:

  baseline: Q
  refined:  (Q, rot)
  exact:    exact presentation

where Q is the retained GS-Sub quotient and rot is the prospectively learned
S2-invariant rotation-orbit distinction.

The forward and reverse searches are breadth-first to a fixed half-bound.
Whenever representation buckets meet, exact representatives are reconciled:
first by exact equality, then (within remaining budget) by a bounded exact
bridge. Every candidate is replayed by the pinned official verifier.

Thus representation affects search geometry only; certificate semantics remain
fully exact.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path


def save(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--challenge-id", required=True)
    ap.add_argument("--live-best", type=int, required=True)
    ap.add_argument("--identity", choices=["baseline", "refined", "exact"], required=True)
    ap.add_argument("--reps-per-key", type=int, default=1)
    ap.add_argument("--half-depth", type=int, default=8)
    ap.add_argument("--bridge-max", type=int, default=4)
    ap.add_argument("--reverse-label-cap", type=int, default=400000)
    ap.add_argument("--forward-label-cap", type=int, default=400000)
    ap.add_argument("--match-cap", type=int, default=50000)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    strict_bound = a.live_best - 1
    if strict_bound < 0:
        raise SystemExit("invalid frozen live best")

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        gssub_key,
        int_word_to_str,
        load_gssub,
        orientation_options,
        total_len,
    )
    sys.path.insert(0, str(root / "acc_competitive"))
    from peephole_superopt_v1 import shorter_path

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    byid = {c["challenge_id"]: c for c in manifest["challenges"]}
    limits = manifest["limits"]
    c = byid[a.challenge_id]
    initial = tuple(tuple(w) for w in c["initial_relators"])
    target = ((1,), (2,))
    total_cap = limits["max_total_relator_length"]

    ns = None if a.identity == "exact" else load_gssub(Path(a.acsolverx_root))

    # Cache identity because the same exact presentations appear repeatedly.
    id_cache = {}

    def rot_code(st, qkey):
        opts = []
        for i in (0, 1):
            z = []
            for w, seq in orientation_options(core, st[i], i):
                s = int_word_to_str(w)
                inv = bool(seq and seq[0] == i)
                rot = len(seq) - (1 if inv else 0)
                z.append((s, int(rot), len(seq)))
            opts.append(z)
        assignments = []
        for slot0 in (0, 1):
            slot1 = 1 - slot0
            for x0 in [x for x in opts[0] if x[0] == qkey[slot0]]:
                for x1 in [x for x in opts[1] if x[0] == qkey[slot1]]:
                    assignments.append((
                        x0[2] + x1[2],
                        tuple(sorted((x0[1], x1[1]))),
                    ))
        if not assignments:
            raise RuntimeError("cannot recover learned rot coordinate")
        assignments.sort()
        return assignments[0][1]

    def ident(st):
        got = id_cache.get(st)
        if got is not None:
            return got
        if a.identity == "exact":
            got = ("E", st)
        else:
            q = gssub_key(ns, st)
            if a.identity == "baseline":
                got = ("Q", q)
            else:
                got = ("QR", q, rot_code(st, q))
        id_cache[st] = got
        return got

    reps = max(1, int(a.reps_per_key))

    # Labels are small immutable tuples:
    # reverse: (state, depth, suffix)
    # forward: (state, depth, prefix)
    #
    # A representation bucket retains up to reps exact representatives.
    # Exact duplicate states are never retained twice.

    def admit(bucket_map, exact_seen, st, depth, path):
        if st in exact_seen:
            return False
        k = ident(st)
        b = bucket_map.get(k)
        if b is None:
            bucket_map[k] = [(st, depth, path)]
            exact_seen.add(st)
            return True
        if len(b) >= reps:
            return False
        b.append((st, depth, path))
        exact_seen.add(st)
        return True

    # -------- reverse half --------
    reverse = {}
    reverse_exact = set()
    rq = collections.deque()
    admit(reverse, reverse_exact, target, 0, ())
    rq.append((target, 0, ()))
    reverse_expanded = 0
    reverse_generated = 0
    reverse_cap_hit = False
    t0 = time.time()

    while rq:
        if len(reverse_exact) >= a.reverse_label_cap:
            reverse_cap_hit = True
            break
        st, d, suffix = rq.popleft()
        reverse_expanded += 1
        if d >= a.half_depth:
            continue
        for m in range(core.NUM_MOVES):
            reverse_generated += 1
            inv = core.INVERSE_MOVE[m]
            pred = core.apply_move(st, inv)
            if total_len(pred) > total_cap:
                continue
            nsuf = (m,) + suffix
            if admit(reverse, reverse_exact, pred, d + 1, nsuf):
                rq.append((pred, d + 1, nsuf))

    reverse_s = time.time() - t0

    # Fast exact-state lookup as well as representation buckets.
    reverse_by_exact = {}
    for b in reverse.values():
        for st, d, suffix in b:
            old = reverse_by_exact.get(st)
            if old is None or d < old[0]:
                reverse_by_exact[st] = (d, suffix)

    # -------- exact meeting logic --------
    bridge_cache = {}
    match_attempts = 0
    exact_meets = 0
    representation_meets = 0
    bridge_attempts = 0
    bridge_successes = 0

    def verify_candidate(prefix, bridge, suffix, meta):
        cand = tuple(prefix) + tuple(bridge) + tuple(suffix)
        if len(cand) > strict_bound:
            return None
        vv = core.verify(c, list(cand), c["move_spec_version"], limits)
        if not vv.get("ok"):
            raise RuntimeError(("MITM reconstruction failed official verifier", meta, vv))
        return cand, vv

    def try_meet(st, d, prefix):
        nonlocal match_attempts, exact_meets, representation_meets
        nonlocal bridge_attempts, bridge_successes

        # Exact intersection first.
        ex = reverse_by_exact.get(st)
        if ex is not None:
            dr, suffix = ex
            if d + dr <= strict_bound:
                exact_meets += 1
                hit = verify_candidate(prefix, (), suffix, {
                    "kind": "exact", "forward_depth": d, "reverse_depth": dr
                })
                if hit is not None:
                    cand, vv = hit
                    return cand, vv, {
                        "kind": "exact",
                        "forward_depth": d,
                        "reverse_depth": dr,
                        "bridge_length": 0,
                    }

        k = ident(st)
        rb = reverse.get(k)
        if not rb:
            return None
        representation_meets += 1

        # Cheapest reverse representatives first.
        for rst, dr, suffix in sorted(rb, key=lambda x: x[1]):
            if match_attempts >= a.match_cap:
                return None
            match_attempts += 1
            remaining = strict_bound - d - dr
            if remaining < 0:
                continue
            if st == rst:
                continue  # exact case already checked
            lim = min(a.bridge_max, remaining)
            if lim <= 0:
                continue
            bridge_attempts += 1
            ck = (st, rst, lim)
            if ck in bridge_cache:
                bridge = bridge_cache[ck]
            else:
                bridge = shorter_path(core, st, rst, lim, total_cap)
                bridge_cache[ck] = None if bridge is None else tuple(bridge)
            if bridge is None:
                continue
            bridge_successes += 1
            hit = verify_candidate(prefix, bridge, suffix, {
                "kind": "representation_bridge",
                "forward_depth": d,
                "reverse_depth": dr,
                "bridge_limit": lim,
            })
            if hit is not None:
                cand, vv = hit
                return cand, vv, {
                    "kind": "representation_bridge",
                    "forward_depth": d,
                    "reverse_depth": dr,
                    "bridge_length": len(bridge),
                }
        return None

    # -------- forward half --------
    forward = {}
    forward_exact = set()
    fq = collections.deque()
    admit(forward, forward_exact, initial, 0, ())
    fq.append((initial, 0, ()))
    forward_expanded = 0
    forward_generated = 0
    forward_cap_hit = False
    match_cap_hit = False
    result = None
    t1 = time.time()

    while fq and result is None:
        if len(forward_exact) >= a.forward_label_cap:
            forward_cap_hit = True
            break
        st, d, prefix = fq.popleft()
        forward_expanded += 1

        result = try_meet(st, d, prefix)
        if result is not None:
            break
        if match_attempts >= a.match_cap:
            match_cap_hit = True
            break
        if d >= a.half_depth:
            continue

        for m in range(core.NUM_MOVES):
            forward_generated += 1
            nxt = core.apply_move(st, m)
            if total_len(nxt) > total_cap:
                continue
            np = prefix + (m,)
            if admit(forward, forward_exact, nxt, d + 1, np):
                fq.append((nxt, d + 1, np))

    forward_s = time.time() - t1

    if result is not None:
        cand, verdict, meet_meta = result
        status = "VERIFIED_STRICT_BIDIRECTIONAL_RECORD_CANDIDATE"
    elif match_cap_hit:
        cand = verdict = meet_meta = None
        status = "UNKNOWN_MATCH_BUDGET"
    elif forward_cap_hit or reverse_cap_hit:
        cand = verdict = meet_meta = None
        status = "UNKNOWN_SEARCH_LABEL_CAP"
    else:
        cand = verdict = meet_meta = None
        status = "NO_STRICT_PATH_IN_REPRESENTATION_BOUNDED_SEARCH"

    out = {
        "experiment": "ACC_MDA_BIDIRECTIONAL_MITM_V1",
        "challenge_id": a.challenge_id,
        "identity": a.identity,
        "reps_per_key": reps,
        "live_best_frozen": a.live_best,
        "strict_bound": strict_bound,
        "half_depth": a.half_depth,
        "bridge_max": a.bridge_max,
        "status": status,
        "found": cand is not None,
        "length": None if cand is None else len(cand),
        "certificate": None if cand is None else list(cand),
        "certificate_hash": None if verdict is None else verdict.get("certificate_hash"),
        "meeting": meet_meta,
        "reverse_keys": len(reverse),
        "reverse_exact_reps": len(reverse_exact),
        "reverse_expanded": reverse_expanded,
        "reverse_generated": reverse_generated,
        "reverse_cap_hit": reverse_cap_hit,
        "reverse_s": round(reverse_s, 3),
        "forward_keys": len(forward),
        "forward_exact_reps": len(forward_exact),
        "forward_expanded": forward_expanded,
        "forward_generated": forward_generated,
        "forward_cap_hit": forward_cap_hit,
        "forward_s": round(forward_s, 3),
        "representation_meets": representation_meets,
        "exact_meets": exact_meets,
        "match_attempts": match_attempts,
        "match_cap_hit": match_cap_hit,
        "bridge_attempts": bridge_attempts,
        "bridge_successes": bridge_successes,
        "identity_cache": len(id_cache),
        "claim_boundary": (
            "Both halves use exact official atomic transitions. Representation affects only "
            "which exact representatives survive per search-state key. Same-key meetings are "
            "reconciled by exact equality or bounded exact bridges, and every candidate is "
            "replayed through the pinned official verifier. A negative result is scoped to "
            "the declared depth, representative, bridge, and label budgets."
        ),
    }

    outdir = Path(a.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    save(outdir / "result.json", out)
    if cand is not None:
        (outdir / "candidate.txt").write_text(
            f"{a.challenge_id}: {json.dumps(list(cand), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    else:
        (outdir / "candidate.txt").write_text("", encoding="utf-8")

    print("MDA_BIDIRECTIONAL_MITM", json.dumps({
        "identity": a.identity,
        "reps_per_key": reps,
        "status": status,
        "found": cand is not None,
        "length": None if cand is None else len(cand),
        "meeting": meet_meta,
        "reverse_keys": len(reverse),
        "reverse_reps": len(reverse_exact),
        "forward_keys": len(forward),
        "forward_reps": len(forward_exact),
        "matches": match_attempts,
        "bridges": bridge_attempts,
        "reverse_s": round(reverse_s, 3),
        "forward_s": round(forward_s, 3),
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
