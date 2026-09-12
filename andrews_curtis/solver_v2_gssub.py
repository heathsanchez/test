#!/usr/bin/env python3
"""
Andrews-Curtis Development V2: GS-Sub quotient search with exact atomic compilation.

Authority:
- Search language: public Math-AI-Caltech/ACSolverX GS-Sub canonical quotient.
- Admission language: frozen SAIR ACC atomic moves 0..13 only.
- Every quotient transition is compiled into an explicit sequence of official
  atomic moves and replayed by the pinned official verifier.
- Live API status is checked again immediately before any submission.

The quotient search is therefore proposal machinery only. It has no authority.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import heapq
import json
import os
import sys
import time
from pathlib import Path
from urllib import request, error


BASE = "https://api.sair.foundation/api/public/v1"
TARGET = ((1,), (2,))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--acsolverx-root", required=True)
    p.add_argument("--out-dir", default="andrews_curtis/out_v2")
    p.add_argument("--max-targets", type=int, default=180)
    p.add_argument("--target-ids-file", default=None)
    p.add_argument("--include-solved", action="store_true")
    p.add_argument("--snapshot-ac-file", default=None)
    p.add_argument("--snapshot-stable-file", default=None)
    p.add_argument("--defer-live-filter", action="store_true")
    p.add_argument("--max-nodes", type=int, default=10000)
    p.add_argument("--max-quotient-total", type=int, default=100)
    p.add_argument("--reverse-depth", type=int, default=7)
    p.add_argument("--reverse-cap", type=int, default=250000)
    p.add_argument("--compiler-beam", type=int, default=4)
    p.add_argument("--depth-weight", type=float, default=0.0)
    p.add_argument("--search-seconds", type=int, default=1100)
    p.add_argument("--submit", action="store_true")
    return p.parse_args()


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def api(method, path, body=None):
    key = os.environ.get("SAIR_API_KEY", "")
    if not key:
        raise RuntimeError("SAIR_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": "curl/8.5.0",
    }
    data = None
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    req = request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, dict(resp.headers.items()), json.loads(raw) if raw else {}
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            obj = json.loads(raw)
        except Exception:
            obj = {"raw": raw}
        return e.code, dict(e.headers.items()), obj


def api_get(path):
    status, headers, obj = api("GET", path)
    if not (200 <= status < 300):
        raise RuntimeError(f"GET {path} HTTP {status}: {obj}")
    return headers, obj


def data_obj(obj):
    return obj.get("data", obj) if isinstance(obj, dict) else obj


def snapshot_map(problem):
    _, obj = api_get(f"/competitions/acc/discoveries/snapshot?problem={problem}")
    d = data_obj(obj)
    items = d["items"]
    return obj, {x["challengeId"]: x for x in items}



def snapshot_file_map(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    d = data_obj(obj)
    items = d["items"]
    return obj, {x["challengeId"]: x for x in items}


def int_word_to_str(w):
    chars = {1: "x", -1: "X", 2: "y", -2: "Y"}
    return "".join(chars[a] for a in w)


def load_gssub(acsolverx_root: Path):
    nb = json.loads((acsolverx_root / "greedy_search.ipynb").read_text(encoding="utf-8"))
    sources = []
    found = False
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        sources.append(src)
        if "class ACRelatorSolver" in src:
            found = True
            break
    if not found:
        raise RuntimeError("ACSolverX greedy_search.ipynb missing ACRelatorSolver")
    ns = {}
    exec("\n\n".join(sources), ns)
    return ns



def solve_depth_weighted_gssub(ns, r0, r1, max_nodes, max_len, depth_weight):
    """
    Best-first GS-Sub search with an explicit path-depth penalty.

    ACSolverX's public greedy search prioritizes only the current total relator
    length. For a shortest-certificate competition that can prefer very deep
    quotient trajectories. This keeps the same public neighbor language and
    canonicalization, but ranks a state by:

        total_relator_length + depth_weight * quotient_depth

    and allows a quotient state to be reopened if reached at lower depth.
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
    pq = [(len(initial[0]) + len(initial[1]), 0, ikey)]
    prev = {ikey: None}
    best_depth = {ikey: 0}
    nodes = 0
    seen = {ikey}

    def key_to_state(key):
        return (str_to_arr(key[0]), str_to_arr(key[1]))

    while pq and nodes < max_nodes:
        _, depth, key = heapq.heappop(pq)
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
            priority = len(c1) + len(c2) + float(depth_weight) * nd
            heapq.heappush(pq, (priority, nd, knew))
    return None, nodes, seen

def total_len(s):
    return len(s[0]) + len(s[1])


def build_reverse(core, depth_limit, cap, max_total=34):
    paths = {TARGET: ()}
    depth = {TARGET: 0}
    q = collections.deque([TARGET])
    hist = collections.Counter({0: 1})
    while q and len(paths) < cap:
        s = q.popleft()
        d = depth[s]
        if d >= depth_limit:
            continue
        for m in range(core.NUM_MOVES):
            n = core.apply_move(s, m)
            if total_len(n) > max_total or n in paths:
                continue
            paths[n] = (core.INVERSE_MOVE[m],) + paths[s]
            depth[n] = d + 1
            hist[d + 1] += 1
            q.append(n)
            if len(paths) >= cap:
                break
    return paths, dict(sorted(hist.items()))


def conjugation_move(relator_index, g):
    offset = 6 if relator_index == 0 else 10
    order = {1: 0, -1: 1, 2: 2, -2: 3}
    return offset + order[g]


def word_conjugate(core, w, g):
    return core.free_reduce((g,) + tuple(w) + (-g,))


def orientation_options(core, w, relator_index):
    """All inversion/cyclic-conjugation representatives with exact atomic paths."""
    best = {}
    w = tuple(w)
    for invflag in (False, True):
        cur = core.invert(w) if invflag else w
        seq = (relator_index,) if invflag else ()
        local = set()
        # Once a representative repeats, the orbit is closed. +2 permits
        # cyclic shortening before entering the reduced orbit.
        for _ in range(max(2, len(w) + 2)):
            if cur in local:
                break
            local.add(cur)
            old = best.get(cur)
            if old is None or len(seq) < len(old):
                best[cur] = seq
            if not cur:
                break
            g = -cur[0]  # g r g^-1 left-rotates when g is first-letter inverse
            m = conjugation_move(relator_index, g)
            cur = word_conjugate(core, cur, g)
            seq = seq + (m,)
    return list(best.items())



def orientation_options_no_invert(core, w, relator_index):
    """Cyclic-conjugation representatives only; no physical relator inversion."""
    best = {}
    cur = tuple(w)
    seq = ()
    local = set()
    for _ in range(max(2, len(w) + 2)):
        if cur in local:
            break
        local.add(cur)
        old = best.get(cur)
        if old is None or len(seq) < len(old):
            best[cur] = seq
        if not cur:
            break
        g = -cur[0]
        m = conjugation_move(relator_index, g)
        cur = word_conjugate(core, cur, g)
        seq = seq + (m,)
    return list(best.items())


def compiled_superneighbor_candidates(core, ns, state, desired, total_cap):
    """
    All economical exact representatives of one desired GS-Sub neighbor.

    Source inversion is compiled through the official direct multiply-by-inverse
    move (3 or 5), rather than physically inverting the untouched source and
    then undoing that inversion. This preserves the exact source byte-for-byte
    while removing two atomic moves whenever the quotient proposal uses the
    inverted source orientation.
    """
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
                    if tw[-1] != -source_word[0]:
                        continue
                    new_word = core.free_reduce(tw + source_word)
                    n = (new_word, state[1]) if i == 0 else (state[0], new_word)
                    if total_len(n) > total_cap:
                        continue
                    if gssub_key(ns, n) != desired:
                        continue
                    atomics = tuple(tseq) + tuple(sseq) + (mul,) + undo_source

                    chk = state
                    for m in atomics:
                        chk = core.apply_move(chk, m)
                    if chk != n:
                        raise RuntimeError("optimized compiled supermove mismatch")

                    prev = best_exact.get(n)
                    if prev is None or len(atomics) < len(prev):
                        best_exact[n] = atomics
    return [(n, edge) for n, edge in best_exact.items()]


def exact_terminal_suffix(core, state, reverse_paths):
    suffix = reverse_paths.get(state)
    if suffix is not None:
        return tuple(suffix)
    q = collections.deque([(state, ())])
    seen = {state}
    while q:
        s, p = q.popleft()
        if len(p) >= 8:
            continue
        for m in range(core.NUM_MOVES):
            n = core.apply_move(s, m)
            if n in seen or total_len(n) > 20:
                continue
            np = p + (m,)
            if n == TARGET:
                return np
            seen.add(n)
            q.append((n, np))
    return None


def compile_quotient_path_optimized(
    core, ns, exact_initial, quotient_path, reverse_paths, total_cap, beam_width=4
):
    """
    Dynamic exact-representative compiler for a fixed quotient path.

    The legacy compiler greedily picks one locally cheapest representative at
    each quotient step. Here we retain a small beam of exact representatives
    and minimize accumulated official atomic cost. Admission remains an exact
    replay through the official transition function.
    """
    if not quotient_path:
        return None, {"code": "empty_quotient_path"}

    initial_key = gssub_key(ns, exact_initial)
    q0 = path_state_key(ns, quotient_path[0])
    if initial_key != q0:
        return None, {"code": "initial_key_mismatch", "exact": initial_key, "quotient": q0}

    beam_width = max(1, int(beam_width))
    beam = [(exact_initial, (), 0)]
    layer_meta = []

    for step_index, qstate in enumerate(quotient_path[1:], 1):
        desired = path_state_key(ns, qstate)
        by_exact = {}
        raw_candidates = 0

        for state, path, cost in beam:
            cands = compiled_superneighbor_candidates(core, ns, state, desired, total_cap)
            # Coverage fallback: if the optimized signed compiler misses a
            # transition, preserve the legacy compiler's proven behavior.
            if not cands:
                hit = compiled_superneighbors(core, ns, state, total_cap).get(desired)
                if hit is not None:
                    cands = [hit]
            raw_candidates += len(cands)
            for nxt, edge in cands:
                nc = cost + len(edge)
                prev = by_exact.get(nxt)
                if prev is None or nc < prev[0]:
                    by_exact[nxt] = (nc, path, tuple(edge))

        if not by_exact:
            return None, {
                "code": "uncompiled_transition",
                "step": step_index,
                "from_beam": len(beam),
                "to_key": desired,
            }

        ranked = sorted(
            ((nc, nxt, parent_path, edge) for nxt, (nc, parent_path, edge) in by_exact.items()),
            key=lambda x: x[0],
        )[:beam_width]
        beam = [(nxt, parent_path + edge, nc) for nc, nxt, parent_path, edge in ranked]
        layer_meta.append({
            "quotient_step": step_index,
            "raw_candidates": raw_candidates,
            "distinct_exact": len(by_exact),
            "beam": len(beam),
            "best_cost": beam[0][2],
        })

    finals = []
    for state, path, cost in beam:
        suffix = exact_terminal_suffix(core, state, reverse_paths)
        if suffix is not None:
            finals.append((cost + len(suffix), path + tuple(suffix), state, len(suffix)))
    if not finals:
        return None, {"code": "no_exact_terminal_bridge", "beam": len(beam)}

    total_cost, atomics, final_state, suffix_len = min(finals, key=lambda x: x[0])
    end = exact_initial
    peak = total_len(end)
    for m in atomics:
        end = core.apply_move(end, m)
        peak = max(peak, total_len(end))
    if end != TARGET:
        return None, {"code": "optimized_compiled_path_not_exact_target", "final": end}

    return atomics, {
        "code": "ok",
        "compiler": "signed-exact-beam-v1",
        "beam_width": beam_width,
        "quotient_steps": len(quotient_path) - 1,
        "atomic_cost": total_cost,
        "suffix_len": suffix_len,
        "peak": peak,
        "layers": layer_meta,
    }


def gssub_key(ns, state):
    return ns["canonical_pair_str"](
        int_word_to_str(state[0]),
        int_word_to_str(state[1]),
    )


def path_state_key(ns, state_arrays):
    return (
        ns["arr_to_str"](state_arrays[0]),
        ns["arr_to_str"](state_arrays[1]),
    )


def compiled_superneighbors(core, ns, state, total_cap):
    """
    Compile quotient substitution proposals into exact official move sequences.

    For each target relator:
      target symmetry; source symmetry; multiply target by source;
      undo source symmetry exactly.
    The untouched source therefore returns byte-for-byte to its original word.
    """
    out = {}
    for i in (0, 1):
        j = 1 - i
        target_opts = orientation_options(core, state[i], i)
        source_opts = orientation_options(core, state[j], j)
        mul = 2 if i == 0 else 4

        for tw, tseq in target_opts:
            if not tw:
                continue
            for sw, sseq in source_opts:
                if not sw:
                    continue
                # GS-Sub keeps only products with an immediate boundary
                # cancellation; this is its exploration-efficiency primitive.
                if tw[-1] != -sw[0]:
                    continue
                new_word = core.free_reduce(tw + sw)
                n = (new_word, state[1]) if i == 0 else (state[0], new_word)
                if total_len(n) > total_cap:
                    continue
                undo_source = tuple(core.INVERSE_MOVE[m] for m in reversed(sseq))
                atomics = tuple(tseq) + tuple(sseq) + (mul,) + undo_source

                # Recompute through the official transition function. This is a
                # local compiler proof, not an assumption about the formula.
                chk = state
                for m in atomics:
                    chk = core.apply_move(chk, m)
                if chk != n:
                    raise RuntimeError("compiled supermove mismatch")

                key = gssub_key(ns, n)
                prev = out.get(key)
                if prev is None or len(atomics) < len(prev[1]):
                    out[key] = (n, atomics)
    return out


def compile_quotient_path(core, ns, exact_initial, quotient_path, reverse_paths, total_cap):
    if not quotient_path:
        return None, {"code": "empty_quotient_path"}

    initial_key = gssub_key(ns, exact_initial)
    q0 = path_state_key(ns, quotient_path[0])
    if initial_key != q0:
        return None, {"code": "initial_key_mismatch", "exact": initial_key, "quotient": q0}

    cur = exact_initial
    atomics = ()
    step_meta = []

    for step_index, qstate in enumerate(quotient_path[1:], 1):
        desired = path_state_key(ns, qstate)
        nbrs = compiled_superneighbors(core, ns, cur, total_cap)
        hit = nbrs.get(desired)
        if hit is None:
            return None, {
                "code": "uncompiled_transition",
                "step": step_index,
                "from_key": gssub_key(ns, cur),
                "to_key": desired,
                "available_neighbors": len(nbrs),
            }
        nxt, edge = hit
        step_meta.append({
            "quotient_step": step_index,
            "atomic_length": len(edge),
            "before_total": total_len(cur),
            "after_total": total_len(nxt),
        })
        atomics += edge
        cur = nxt

    suffix = reverse_paths.get(cur)
    if suffix is None:
        # Terminal quotient should be a singleton pair. Search a tiny exact
        # bridge locally in case the reverse census cap missed its representative.
        q = collections.deque([(cur, ())])
        seen = {cur}
        suffix = None
        while q:
            s, p = q.popleft()
            if len(p) >= 8:
                continue
            for m in range(core.NUM_MOVES):
                n = core.apply_move(s, m)
                if n in seen or total_len(n) > 20:
                    continue
                np = p + (m,)
                if n == TARGET:
                    suffix = np
                    q.clear()
                    break
                seen.add(n)
                q.append((n, np))
    if suffix is None:
        return None, {"code": "no_exact_terminal_bridge", "final_key": gssub_key(ns, cur)}

    atomics += tuple(suffix)
    end = exact_initial
    peak = total_len(end)
    for m in atomics:
        end = core.apply_move(end, m)
        peak = max(peak, total_len(end))
    if end != TARGET:
        return None, {"code": "compiled_path_not_exact_target", "final": end}
    return atomics, {"code": "ok", "quotient_steps": len(quotient_path) - 1, "steps": step_meta, "peak": peak}


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


def current_competitive(row, candidate_len):
    if row["status"] == "unsolved":
        return True, "currently_unsolved"
    best = row.get("currentBestLength")
    if isinstance(best, int) and candidate_len <= best:
        return True, "tie_or_improve"
    return False, "longer_than_live_best"


def submit_batch(text):
    payload = {
        "payload": {"text": text},
        "meta": {"description": "MathGraph ACC V2 GS-Sub quotient search; exact atomic compilation; verifier-gated"},
    }
    status, headers, obj = api("POST", "/competitions/acc/submissions", payload)
    if status != 202:
        raise RuntimeError(f"submission HTTP {status}: {obj}")
    sid = data_obj(obj).get("submissionId")
    if not sid:
        raise RuntimeError(f"202 response missing submissionId: {obj}")

    polls = []
    final = None
    for attempt in range(1, 61):
        st, hdr, got = api("GET", f"/competitions/acc/submissions/{sid}")
        polls.append({"attempt": attempt, "http_status": st, "body": got})
        retry = hdr.get("Retry-After") or hdr.get("retry-after")
        try:
            delay = max(2, min(30, int(retry))) if retry else 5
        except Exception:
            delay = 5
        # Polling is read-only and SAIR's independent verifier can transiently
        # return 429/5xx after the POST has already been accepted. Never turn
        # that into a duplicate re-submission; wait and poll the same sid.
        if st == 429 or st in (500, 502, 503, 504):
            time.sleep(delay)
            continue
        if not (200 <= st < 300):
            raise RuntimeError(f"poll HTTP {st}: {got}")
        state = str(data_obj(got).get("status", "")).lower()
        if state in ("complete", "completed", "failed", "error", "rejected"):
            final = got
            break
        time.sleep(delay)
    if final is None:
        raise RuntimeError("submission did not reach terminal state")
    return sid, obj, polls, final


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

    # Use the scout's frozen frontier inside parallel search shards whenever
    # available. Only the aggregate/submission job needs a fresh live read.
    if args.snapshot_ac_file and args.snapshot_stable_file:
        ac_snapshot_before, ac_live = snapshot_file_map(args.snapshot_ac_file)
        sac_snapshot_before, sac_live = snapshot_file_map(args.snapshot_stable_file)
    else:
        ac_snapshot_before, ac_live = snapshot_map("ac")
        sac_snapshot_before, sac_live = snapshot_map("stable_ac")
    save_json(out / "snapshot_ac_before.json", ac_snapshot_before)
    save_json(out / "snapshot_stable_ac_before.json", sac_snapshot_before)

    unsolved = [
        ac_by_id[cid] for cid, row in ac_live.items()
        if row["status"] == "unsolved" and cid in ac_by_id
    ]
    unsolved.sort(key=lambda c: (
        sum(len(w) for w in c["initial_relators"]),
        max(len(w) for w in c["initial_relators"]),
        c["challenge_id"],
    ))
    if args.target_ids_file:
        raw = json.loads(Path(args.target_ids_file).read_text())
        requested = [x["challenge_id"] if isinstance(x, dict) else str(x) for x in raw]
        targets = [
            ac_by_id[cid] for cid in requested
            if cid in ac_by_id
            and (
                args.include_solved
                or ac_live.get(cid, {}).get("status") == "unsolved"
            )
        ][: args.max_targets]
    else:
        targets = unsolved[: args.max_targets]

    ns = load_gssub(acsolverx_root)

    t0 = time.time()
    reverse_paths, reverse_hist = build_reverse(
        core, args.reverse_depth, args.reverse_cap
    )
    print("REVERSE", json.dumps({
        "states": len(reverse_paths),
        "hist": reverse_hist,
        "seconds": round(time.time() - t0, 3),
    }, sort_keys=True), flush=True)

    results = []
    verified = {}
    start = time.time()

    for idx, c in enumerate(targets, 1):
        if time.time() - start > args.search_seconds:
            print("SEARCH_TIME_CAP", round(time.time() - start, 2), flush=True)
            break

        cid = c["challenge_id"]
        exact = tuple(tuple(w) for w in c["initial_relators"])
        r0 = int_word_to_str(exact[0])
        r1 = int_word_to_str(exact[1])
        initial_total = total_len(exact)
        qcap = min(args.max_quotient_total, max(initial_total + 36, 48))

        if args.depth_weight > 0:
            quotient_path, nodes, _seen = solve_depth_weighted_gssub(
                ns, r0, r1,
                max_nodes=args.max_nodes,
                max_len=qcap,
                depth_weight=args.depth_weight,
            )
        else:
            solver = ns["ACRelatorSolver"](
                r0, r1,
                max_nodes=args.max_nodes,
                max_len=qcap,
                verbose=False,
                stop_early=False,
            )
            found = solver.solve()
            if len(found) == 3:
                quotient_path, nodes, _seen = found
            else:
                quotient_path, nodes = found[:2]

        live_row = ac_live.get(cid, {})
        rec = {
            "challenge_id": cid,
            "live_status": live_row.get("status"),
            "live_best": live_row.get("currentBestLength"),
            "live_k_teams": live_row.get("kTeams"),
            "initial_total": initial_total,
            "max_nodes": args.max_nodes,
            "compiler_beam": args.compiler_beam,
            "depth_weight": args.depth_weight,
            "quotient_total_cap": qcap,
            "nodes": int(nodes),
            "quotient_found": quotient_path is not None,
        }

        if quotient_path is not None:
            atomics, comp = compile_quotient_path_optimized(
                core, ns, exact, quotient_path, reverse_paths,
                total_cap=limits["max_total_relator_length"],
                beam_width=args.compiler_beam,
            )
            rec["compile"] = comp
            if atomics is not None:
                verdict = core.verify(
                    c, list(atomics), c["move_spec_version"], limits
                )
                rec["ac_verdict"] = verdict
                rec["atomic_length"] = len(atomics)
                if verdict["ok"]:
                    sid = "sac-" + cid[3:]
                    sc = sac_by_id[sid]
                    stable_path = tuple(atomics) + (16, 15)
                    sv = stable_core.verify(
                        sc, list(stable_path), sc["move_spec_version"], limits
                    )
                    rec["stable_verdict"] = sv
                    if sv["ok"]:
                        verified[cid] = {
                            "path": tuple(atomics),
                            "verdict": verdict,
                            "stable_id": sid,
                            "stable_path": stable_path,
                            "stable_verdict": sv,
                            "nodes": int(nodes),
                            "quotient_steps": comp.get("quotient_steps"),
                        }
        results.append(rec)

        if idx % 10 == 0 or cid in verified:
            print("PROGRESS", json.dumps({
                "targets_processed": idx,
                "verified_ac": len(verified),
                "last": cid,
                "last_nodes": int(nodes),
                "elapsed_s": round(time.time() - start, 2),
            }, sort_keys=True), flush=True)

    save_json(out / "search_results.json", results)

    # Parallel shards can defer all live competitiveness checks to the single
    # aggregate job. This avoids an API thundering herd while preserving the
    # final live recheck immediately before submission.
    if args.defer_live_filter:
        ac_now = ac_live
        sac_now = sac_live
        ac_snapshot_pre_submit = ac_snapshot_before
        sac_snapshot_pre_submit = sac_snapshot_before
    else:
        ac_snapshot_pre_submit, ac_now = snapshot_map("ac")
        sac_snapshot_pre_submit, sac_now = snapshot_map("stable_ac")
    save_json(out / "snapshot_ac_pre_submit.json", ac_snapshot_pre_submit)
    save_json(out / "snapshot_stable_ac_pre_submit.json", sac_snapshot_pre_submit)

    lines = []
    selection = []
    for cid, v in sorted(verified.items(), key=lambda kv: (len(kv[1]["path"]), kv[0])):
        if args.defer_live_filter:
            ok, reason = True, "deferred_to_aggregate"
        else:
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
        if args.defer_live_filter:
            sok, sreason = True, "deferred_to_aggregate"
        else:
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
    submission_text = "\n".join(lines) + ("\n" if lines else "")
    (out / "submission_v2.txt").write_text(submission_text, encoding="utf-8")

    submit_info = None
    if args.submit and lines:
        if len(lines) > 500:
            raise RuntimeError(f"refusing >500-line single V2 batch: {len(lines)}")
        sid, response, polls, final = submit_batch(submission_text)
        submit_info = {
            "submission_id": sid,
            "response": response,
            "polls": polls,
            "final": final,
        }
        save_json(out / "submission_receipt.json", submit_info)

        # Evidence after platform verification.
        ac_after, _ = snapshot_map("ac")
        sac_after, _ = snapshot_map("stable_ac")
        save_json(out / "snapshot_ac_after.json", ac_after)
        save_json(out / "snapshot_stable_ac_after.json", sac_after)

    report = {
        "experiment": "andrews-curtis-development-v2-gssub-atomic-compile",
        "official_commit": "99a65377c5c4f412cd9af7b8d31c41464a855736",
        "acsolverx_commit": "6a12515fe1d95178a483b76d5553266e61122417",
        "live_unsolved_at_start": len(unsolved),
        "target_count_requested": args.max_targets,
        "target_count_processed": len(results),
        "verified_ac": len(verified),
        "competitive_submission_rows": len(lines),
        "submission_id": None if submit_info is None else submit_info["submission_id"],
        "search_seconds": round(time.time() - start, 3),
        "solutions": [
            {
                "ac_id": cid,
                "ac_length": len(v["path"]),
                "ac_hash": v["verdict"]["certificate_hash"],
                "stable_id": v["stable_id"],
                "stable_length": len(v["stable_path"]),
                "stable_hash": v["stable_verdict"]["certificate_hash"],
                "nodes": v["nodes"],
                "quotient_steps": v["quotient_steps"],
            }
            for cid, v in sorted(verified.items())
        ],
    }
    report_bytes = json.dumps(report, indent=2, sort_keys=True).encode()
    (out / "report_v2.json").write_bytes(report_bytes)
    (out / "report_v2.sha256").write_text(
        hashlib.sha256(report_bytes).hexdigest() + "  report_v2.json\n",
        encoding="utf-8",
    )
    print("FINAL", json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
