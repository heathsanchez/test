#!/usr/bin/env python3
"""
Exact corridor-splice search for ACC ac-04359.

Goal: turn our verified 18-move certificate into a <=16 move strict record
without using any competitor certificate.

Method:
  1. Replay our certificate and treat every intermediate exact state as a
     permitted rejoin point.
  2. Build a shallow exact reverse atlas around those corridor states. Each
     atlas entry stores an official atomic suffix to the target through our
     known proof.
  3. Search forward from the true initial state using the retained compiled
     GS-Sub transition language.
  4. Compare two state identities under identical transitions/budget:
       baseline = current GS-Sub quotient
       refined  = (GS-Sub quotient, learned S2-invariant rotation orbit)
     plus an exact-identity atomic safety-net arm.
  5. Check corridor-atlas intersections not only at compiled endpoints but at
     every atomic state traversed inside a compiled edge.
  6. Accept only a path <= frozen_live_best-1 and replay it with the official
     verifier.

The reverse corridor atlas is exact; the representation only affects forward
state merging/search geometry.
"""
from __future__ import annotations

import argparse
import heapq
import json
import re
import sys
import time
from pathlib import Path


def parse_candidate(path: str, cid: str):
    for line in Path(path).read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$", line.strip())
        if m and m.group(1) == cid:
            return list(json.loads(m.group(2)))
    raise KeyError(cid)


def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--acsolverx-root", required=True)
    ap.add_argument("--candidate-file", required=True)
    ap.add_argument("--challenge-id", required=True)
    ap.add_argument("--live-best", type=int, required=True)
    ap.add_argument("--identity", choices=["baseline", "refined", "exact"], required=True)
    ap.add_argument("--transition", choices=["compiled", "atomic"], required=True)
    ap.add_argument("--corridor-depth", type=int, default=4)
    ap.add_argument("--corridor-label-cap", type=int, default=350000)
    ap.add_argument("--node-cap", type=int, default=120000)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    strict_bound = a.live_best - 1
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "andrews_curtis"))
    from solver_v2_gssub import (
        challenge_maps,
        compiled_superneighbor_candidates,
        compiled_superneighbors,
        gssub_key,
        int_word_to_str,
        load_gssub,
        orientation_options,
        total_len,
    )
    sys.path.insert(0, str(root / "acc_competitive"))
    from proof_atlas_fortify_v1 import mod_state, modular_pdb

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition" / "tools"))
    from verifier import core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    byid = {c["challenge_id"]: c for c in manifest["challenges"]}
    c = byid[a.challenge_id]
    initial = tuple(tuple(w) for w in c["initial_relators"])
    seed = parse_candidate(a.candidate_file, a.challenge_id)
    v0 = core.verify(c, seed, c["move_spec_version"], limits)
    if not v0.get("ok"):
        raise RuntimeError(("seed fails official verifier", v0))

    # Replay exact 18-move corridor.
    corridor = [initial]
    s = initial
    for m in seed:
        s = core.apply_move(s, m)
        corridor.append(s)
    target = corridor[-1]

    ns = None
    if a.identity != "exact" or a.transition == "compiled":
        ns = load_gssub(Path(a.acsolverx_root))

    def rot_code(st, qkey):
        opts = []
        for i in (0, 1):
            z = []
            for w, seq in orientation_options(core, st[i], i):
                ss = int_word_to_str(w)
                inv = bool(seq and seq[0] == i)
                rot = len(seq) - (1 if inv else 0)
                z.append((ss, int(rot), len(seq)))
            opts.append(z)
        cand = []
        for slot0 in (0, 1):
            slot1 = 1 - slot0
            m0 = [x for x in opts[0] if x[0] == qkey[slot0]]
            m1 = [x for x in opts[1] if x[0] == qkey[slot1]]
            for x in m0:
                for y in m1:
                    cand.append((x[2] + y[2], tuple(sorted((x[1], y[1])))))
        if not cand:
            raise RuntimeError("rotation orbit coordinate unavailable")
        cand.sort()
        return cand[0][1]

    def ident(st):
        if a.identity == "exact":
            return ("E", st)
        q = gssub_key(ns, st)
        if a.identity == "baseline":
            return ("Q", q)
        return ("QR", q, rot_code(st, q))

    # Certified lower bound to target from modular abelianized quotients.
    primes = (2, 3, 5, 7, 11, 13)
    pdb = {p: modular_pdb(p) for p in primes}

    def lb(st):
        best = 0
        for p in primes:
            d = pdb[p].get(mod_state(st, p))
            if d is not None:
                best = max(best, d)
        return best

    # ---- exact reverse corridor atlas ----
    # Each label is (tail_cost, extra_depth, tail_tuple, source_index).
    # We maintain a small Pareto frontier per exact state because a lower-cost
    # route reached at greater reverse depth must not suppress a shallower label
    # that can still be expanded.
    labels = {}
    heap = []
    serial = 0

    def dominated(front, cost, dep):
        return any(c0 <= cost and d0 <= dep for c0, d0, _, _ in front)

    def add_label(st, cost, dep, tail, src):
        nonlocal serial
        if cost > strict_bound or dep > a.corridor_depth:
            return False
        front = labels.setdefault(st, [])
        if dominated(front, cost, dep):
            return False
        front[:] = [x for x in front if not (cost <= x[0] and dep <= x[1])]
        front.append((cost, dep, tail, src))
        heapq.heappush(heap, (cost, dep, serial, st, tail, src))
        serial += 1
        return True

    # Every corridor state is a source with the already-verified remaining tail.
    for j, st in enumerate(corridor):
        tail = tuple(seed[j:])
        add_label(st, len(tail), 0, tail, j)

    expanded_labels = 0
    t_atlas = time.time()
    while heap and expanded_labels < a.corridor_label_cap:
        cost, dep, _, st, tail, src = heapq.heappop(heap)
        if not any(x[0] == cost and x[1] == dep and x[2] == tail and x[3] == src
                   for x in labels.get(st, [])):
            continue
        expanded_labels += 1
        if dep >= a.corridor_depth:
            continue
        for m in range(core.NUM_MOVES):
            # predecessor p such that p --m--> st
            inv = core.INVERSE_MOVE[m]
            p = core.apply_move(st, inv)
            if total_len(p) > limits["max_total_relator_length"]:
                continue
            # avoid immediate m;inv(m) cancellation at start of tail
            if tail and tail[0] == inv:
                continue
            add_label(p, cost + 1, dep + 1, (m,) + tail, src)

    atlas_best = {}
    for st, front in labels.items():
        best = min(front, key=lambda x: (x[0], x[1], x[2]))
        atlas_best[st] = best
    atlas_s = time.time() - t_atlas
    atlas_capped = expanded_labels >= a.corridor_label_cap and bool(heap)

    # ---- forward search ----
    # Parent pointers are on representation keys; exact state is the currently
    # retained representative for that key.
    k0 = ident(initial)
    best_g = {k0: 0}
    states = {k0: initial}
    parent = {k0: None}
    pedge = {}
    pq = [(lb(initial), 0, 0, k0)]
    serial = 1
    popped = generated = pruned_bound = pruned_seen = 0
    found = None
    found_meta = None
    t_search = time.time()

    def reconstruct(k):
        edges = []
        cur = k
        while parent[cur] is not None:
            edges.append(pedge[cur])
            cur = parent[cur]
        edges.reverse()
        return tuple(m for e in edges for m in e)

    def test_hit(prefix, st, where, parent_key=None, edge_prefix=()):
        nonlocal found, found_meta
        hit = atlas_best.get(st)
        if hit is None:
            return False
        tail_cost, dep, tail, src = hit
        total = len(prefix) + tail_cost
        if total > strict_bound:
            return False
        cand = tuple(prefix) + tuple(tail)
        vv = core.verify(c, list(cand), c["move_spec_version"], limits)
        if not vv.get("ok"):
            raise RuntimeError(("corridor splice failed verifier", where, vv))
        found = cand
        found_meta = {
            "where": where,
            "corridor_source_index": src,
            "corridor_extra_reverse_depth": dep,
            "prefix_length": len(prefix),
            "tail_length": tail_cost,
            "total_length": len(cand),
            "certificate_hash": vv.get("certificate_hash"),
        }
        return True

    if test_hit((), initial, "initial"):
        pass
    else:
        while pq and popped < a.node_cap and found is None:
            f, g, _, k = heapq.heappop(pq)
            if g != best_g.get(k):
                continue
            st = states[k]
            if g + lb(st) > strict_bound:
                pruned_bound += 1
                continue
            popped += 1
            prefix = reconstruct(k)
            if test_hit(prefix, st, "popped_state", parent_key=k):
                break

            if a.transition == "atomic":
                movesets = []
                for m in range(core.NUM_MOVES):
                    n = core.apply_move(st, m)
                    if total_len(n) > limits["max_total_relator_length"]:
                        continue
                    movesets.append((n, (m,)))
            else:
                legacy = compiled_superneighbors(
                    core, ns, st, limits["max_total_relator_length"]
                )
                by_state = {}
                for desired, fallback in legacy.items():
                    xs = compiled_superneighbor_candidates(
                        core, ns, st, desired, limits["max_total_relator_length"]
                    )
                    if not xs:
                        xs = [fallback]
                    for n, e in xs:
                        e = tuple(e)
                        old = by_state.get(n)
                        if old is None or len(e) < len(old):
                            by_state[n] = e
                movesets = list(by_state.items())

            for n, edge in movesets:
                generated += 1
                # Check every exact intermediate state inside compiled edges.
                inter = st
                for z, m in enumerate(edge, start=1):
                    inter = core.apply_move(inter, m)
                    partial_g = g + z
                    if partial_g > strict_bound:
                        break
                    if test_hit(prefix + tuple(edge[:z]), inter, "edge_intermediate",
                                parent_key=k, edge_prefix=edge[:z]):
                        break
                if found is not None:
                    break

                ng = g + len(edge)
                if ng + lb(n) > strict_bound:
                    pruned_bound += 1
                    continue
                nk = ident(n)
                if ng >= best_g.get(nk, 10**18):
                    pruned_seen += 1
                    continue
                best_g[nk] = ng
                states[nk] = n
                parent[nk] = k
                pedge[nk] = tuple(edge)
                heapq.heappush(pq, (ng + lb(n), ng, serial, nk))
                serial += 1

    search_s = time.time() - t_search

    if found is not None:
        status = "VERIFIED_STRICT_CORRIDOR_SPLICE"
    elif popped >= a.node_cap:
        status = "UNKNOWN_SEARCH_NODE_CAP"
    elif atlas_capped:
        status = "UNKNOWN_CORRIDOR_ATLAS_CAP"
    else:
        status = "NO_STRICT_SPLICE_IN_EXPLORED_SCOPE"

    out = {
        "experiment": "ACC_MDA_CORRIDOR_SPLICE_V1",
        "challenge_id": a.challenge_id,
        "identity": a.identity,
        "transition": a.transition,
        "live_best_frozen": a.live_best,
        "strict_bound": strict_bound,
        "seed_length": len(seed),
        "status": status,
        "found": found is not None,
        "length": None if found is None else len(found),
        "certificate": None if found is None else list(found),
        "found_meta": found_meta,
        "corridor_depth": a.corridor_depth,
        "corridor_exact_states": len(atlas_best),
        "corridor_labels_expanded": expanded_labels,
        "corridor_label_cap": a.corridor_label_cap,
        "corridor_atlas_capped": atlas_capped,
        "corridor_build_s": round(atlas_s, 3),
        "nodes_popped": popped,
        "neighbors_generated": generated,
        "identity_states": len(best_g),
        "pruned_bound": pruned_bound,
        "pruned_seen": pruned_seen,
        "node_cap": a.node_cap,
        "search_s": round(search_s, 3),
        "claim_boundary": (
            "All reverse-atlas suffixes are exact official move sequences ending through our "
            "own verified 18-move path. Forward baseline/refined arms use identical compiled "
            "transitions and bounds; only state identity differs. Exact atomic arm is a "
            "competitive safety-net, not part of the causal comparison."
        ),
    }

    outdir = Path(a.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    save(outdir / "result.json", out)
    if found is not None:
        (outdir / "candidate.txt").write_text(
            f"{a.challenge_id}: {json.dumps(list(found), separators=(',', ':'))}\n",
            encoding="utf-8",
        )
    else:
        (outdir / "candidate.txt").write_text("", encoding="utf-8")
    print("MDA_CORRIDOR_SPLICE", json.dumps({
        "identity": a.identity,
        "transition": a.transition,
        "status": status,
        "found": found is not None,
        "length": None if found is None else len(found),
        "atlas_states": len(atlas_best),
        "atlas_labels": expanded_labels,
        "nodes": popped,
        "generated": generated,
        "search_s": round(search_s, 3),
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
