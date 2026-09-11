#!/usr/bin/env python3
"""
Andrews-Curtis Development V1

Prospective, verifier-gated search:
  1. Learn only reusable move macros from the published 424 training certificates.
  2. Freeze those macros.
  3. Build an exact reverse neighbourhood of the target under the official AC moves.
  4. Search scored presentations without using scored labels/origins.
  5. Verify every retained certificate with the official verifier.
  6. Convert every verified AC certificate into a Stable-AC certificate by appending
     the official [16, 15] destabilization suffix and verify again.

The scored pool is consumed only after the learned macro vocabulary is frozen.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import heapq
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--out-dir", default="andrews_curtis/out_v1")
    p.add_argument("--reverse-depth", type=int, default=8)
    p.add_argument("--reverse-cap", type=int, default=450000)
    p.add_argument("--reverse-max-total", type=int, default=34)
    p.add_argument("--macro-count", type=int, default=12)
    p.add_argument("--search-count", type=int, default=1800)
    p.add_argument("--nodes-per-problem", type=int, default=1400)
    p.add_argument("--max-search-seconds", type=int, default=1500)
    p.add_argument("--holdout-count", type=int, default=32)
    return p.parse_args()


def state_key(relators):
    return tuple(tuple(w) for w in relators)


def total_len(s):
    return sum(len(w) for w in s)


def cyclic_len(w):
    if len(w) < 2:
        return len(w)
    a, b = 0, len(w)
    while b - a >= 2 and w[a] == -w[b - 1]:
        a += 1
        b -= 1
    return b - a


def heuristic(s):
    # A cheap consequence-facing heuristic: prefer small cyclic cores, but
    # retain a weaker preference for small explicit representatives.
    cyc = sum(cyclic_len(w) for w in s)
    tot = total_len(s)
    singleton = sum(1 for w in s if len(w) == 1)
    return cyc + 0.16 * tot - 0.20 * singleton


def mine_macros(instances, macro_count, inverse_move):
    # Deterministic prospective split: even-numbered training rows develop the
    # macro vocabulary; odd-numbered rows remain untouched for diagnostics.
    dev = instances[0::2]
    holdout = instances[1::2]
    counts = collections.Counter()
    support = collections.Counter()

    for row in dev:
        moves = tuple(row["moves"])
        seen_here = set()
        for n in range(2, 7):
            for i in range(0, len(moves) - n + 1):
                gram = moves[i : i + n]
                # Exclude immediate undo pairs: they are not useful retained
                # continuation structure.
                bad = any(inverse_move[a] == b for a, b in zip(gram, gram[1:]))
                if bad:
                    continue
                counts[gram] += 1
                seen_here.add(gram)
        for gram in seen_here:
            support[gram] += 1

    ranked = []
    for gram, c in counts.items():
        s = support[gram]
        if s < 2:
            continue
        # Reward recurrence across independent certificates and primitive
        # compression, not raw frequency within one path.
        score = s * (len(gram) - 1) * math.log2(2 + c)
        ranked.append((score, s, c, gram))
    ranked.sort(key=lambda x: (-x[0], -len(x[3]), x[3]))
    chosen = [x[3] for x in ranked[:macro_count]]
    meta = [
        {"moves": list(g), "support": s, "occurrences": c, "score": score}
        for score, s, c, g in ranked[:macro_count]
    ]
    return chosen, meta, holdout


def build_reverse(core, depth_limit, cap, max_total):
    target = ((1,), (2,))
    # state -> shortest primitive path from state to target
    paths = {target: ()}
    depth = {target: 0}
    q = collections.deque([target])
    by_depth = collections.Counter({0: 1})

    while q and len(paths) < cap:
        s = q.popleft()
        d = depth[s]
        if d >= depth_limit:
            continue
        for m in range(core.NUM_MOVES):
            n = core.apply_move(s, m)
            if total_len(n) > max_total or n in paths:
                continue
            # s --m--> n, so n --inverse(m)--> s --> target
            paths[n] = (core.INVERSE_MOVE[m],) + paths[s]
            depth[n] = d + 1
            by_depth[d + 1] += 1
            q.append(n)
            if len(paths) >= cap:
                break
    return paths, dict(sorted(by_depth.items()))


def apply_sequence(core, s, seq, length_cap):
    cur = s
    for m in seq:
        cur = core.apply_move(cur, m)
        if total_len(cur) > length_cap:
            return None
    return cur


def solve_best_first(
    core,
    initial,
    reverse_paths,
    macros,
    max_expansions,
    length_cap,
):
    target = ((1,), (2,))
    if initial == target:
        return (), 0
    if initial in reverse_paths:
        return reverse_paths[initial], 0

    actions = [(m,) for m in range(core.NUM_MOVES)] + list(macros)
    heap = []
    seqno = 0
    heapq.heappush(heap, (heuristic(initial), 0, seqno, initial, (), None))
    seen_g = {initial: 0}
    expansions = 0

    while heap and expansions < max_expansions:
        _f, g, _k, s, path, last = heapq.heappop(heap)
        if g != seen_g.get(s):
            continue
        expansions += 1

        for act in actions:
            if last is not None and len(act) == 1 and core.INVERSE_MOVE[last] == act[0]:
                continue
            ng = g + len(act)
            if ng >= 100000:
                continue
            n = apply_sequence(core, s, act, length_cap)
            if n is None:
                continue

            prev = seen_g.get(n)
            if prev is not None and prev <= ng:
                continue
            npath = path + act

            if n == target:
                return npath, expansions
            suffix = reverse_paths.get(n)
            if suffix is not None:
                return npath + suffix, expansions

            seen_g[n] = ng
            seqno += 1
            # Small path-cost term keeps the search from exploding into
            # gratuitously long macro chains while still permitting growth.
            f = heuristic(n) + 0.025 * ng
            heapq.heappush(heap, (f, ng, seqno, n, npath, act[-1]))
    return None, expansions


def verify_ac(core, challenge, path, limits):
    return core.verify(challenge, list(path), challenge["move_spec_version"], limits)


def verify_stable(stable_core, challenge, path, limits):
    return stable_core.verify(challenge, list(path), challenge["move_spec_version"], limits)


def shard_lines(lines, out_dir, stem, max_lines=500):
    files = []
    for i in range(0, len(lines), max_lines):
        part = lines[i : i + max_lines]
        fn = out_dir / f"{stem}_{i // max_lines + 1:02d}.txt"
        fn.write_text("\n".join(part) + "\n", encoding="utf-8")
        files.append(str(fn))
    return files


def main():
    args = parse_args()
    acc_root = Path(args.acc_root).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(acc_root / "competition" / "tools"))
    from verifier import core, stable_core  # noqa: E402

    training = json.loads(
        (acc_root / "competition" / "examples" / "training_424.json").read_text()
    )
    manifest = json.loads(
        (acc_root / "competition" / "tools" / "verifier" / "data" / "manifest.json").read_text()
    )
    limits = manifest["limits"]
    challenges = manifest["challenges"]
    ac_rows = [c for c in challenges if c["challenge_id"].startswith("ac-")]
    stable_by_suffix = {
        c["challenge_id"][4:]: c
        for c in challenges
        if c["challenge_id"].startswith("sac-")
    }

    known_lengths = [r["length"] for r in training["instances"]]
    print(
        "TRAINING",
        json.dumps(
            {
                "n": len(known_lengths),
                "min": min(known_lengths),
                "median": statistics.median(known_lengths),
                "mean": round(statistics.mean(known_lengths), 3),
                "max": max(known_lengths),
            },
            sort_keys=True,
        ),
        flush=True,
    )

    macros, macro_meta, holdout = mine_macros(
        training["instances"], args.macro_count, core.INVERSE_MOVE
    )
    print("FROZEN_MACROS", json.dumps(macro_meta, sort_keys=True), flush=True)

    t0 = time.time()
    reverse_paths, reverse_hist = build_reverse(
        core,
        args.reverse_depth,
        args.reverse_cap,
        args.reverse_max_total,
    )
    print(
        "REVERSE",
        json.dumps(
            {
                "states": len(reverse_paths),
                "depth_hist": reverse_hist,
                "seconds": round(time.time() - t0, 3),
            },
            sort_keys=True,
        ),
        flush=True,
    )

    # Prospective diagnostic: the macros are frozen from dev rows before these
    # odd-index holdout rows are searched.
    holdout_results = []
    for row in holdout[: args.holdout_count]:
        s = state_key(row["initial_relators"])
        cap = max(total_len(s) + 18, 36)
        p_atomic, e_atomic = solve_best_first(
            core, s, reverse_paths, (), min(700, args.nodes_per_problem), cap
        )
        p_macro, e_macro = solve_best_first(
            core, s, reverse_paths, macros, min(700, args.nodes_per_problem), cap
        )
        holdout_results.append(
            {
                "training_id": row["training_id"],
                "known_length": row["length"],
                "atomic_found": p_atomic is not None,
                "atomic_length": None if p_atomic is None else len(p_atomic),
                "atomic_expansions": e_atomic,
                "macro_found": p_macro is not None,
                "macro_length": None if p_macro is None else len(p_macro),
                "macro_expansions": e_macro,
            }
        )
    print(
        "HOLDOUT",
        json.dumps(
            {
                "n": len(holdout_results),
                "atomic_solved": sum(r["atomic_found"] for r in holdout_results),
                "macro_solved": sum(r["macro_found"] for r in holdout_results),
                "macro_only": sum(
                    r["macro_found"] and not r["atomic_found"] for r in holdout_results
                ),
            },
            sort_keys=True,
        ),
        flush=True,
    )

    # Scored search. The scored rows are never used to alter the macro set.
    # Easy-first ordering is based only on exposed input complexity.
    ac_rows.sort(
        key=lambda c: (
            sum(len(w) for w in c["initial_relators"]),
            c["challenge_id"],
        )
    )

    solved = {}
    direct_reverse = 0
    search_started = time.time()
    searched = 0
    expansions_total = 0

    # Exact low-depth census over the whole pool first.
    for c in ac_rows:
        s = state_key(c["initial_relators"])
        p = reverse_paths.get(s)
        if p is None:
            continue
        v = verify_ac(core, c, p, limits)
        if v["ok"]:
            solved[c["challenge_id"]] = {
                "path": p,
                "verdict": v,
                "method": "reverse_exact",
                "expansions": 0,
            }
            direct_reverse += 1

    for c in ac_rows:
        if len(solved) >= len(ac_rows):
            break
        if searched >= args.search_count:
            break
        if time.time() - search_started > args.max_search_seconds:
            print("SEARCH_TIME_CAP", round(time.time() - search_started, 3), flush=True)
            break
        if c["challenge_id"] in solved:
            continue

        searched += 1
        s = state_key(c["initial_relators"])
        initial_total = total_len(s)
        cap = min(90, max(38, initial_total + 20))
        p, ex = solve_best_first(
            core,
            s,
            reverse_paths,
            macros,
            args.nodes_per_problem,
            cap,
        )
        expansions_total += ex
        if p is None:
            if searched % 100 == 0:
                print(
                    "PROGRESS",
                    json.dumps(
                        {
                            "searched": searched,
                            "solved": len(solved),
                            "expansions": expansions_total,
                            "elapsed_s": round(time.time() - search_started, 2),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            continue
        v = verify_ac(core, c, p, limits)
        if not v["ok"]:
            raise RuntimeError((c["challenge_id"], "internal path failed verifier", v))
        solved[c["challenge_id"]] = {
            "path": p,
            "verdict": v,
            "method": "macro_best_first",
            "expansions": ex,
        }

    # Stable AC gets an independently verified certificate for every AC solve.
    stable_solved = {}
    for cid, row in solved.items():
        suffix = cid[3:]
        sc = stable_by_suffix[suffix]
        sp = tuple(row["path"]) + (16, 15)
        sv = verify_stable(stable_core, sc, sp, limits)
        if not sv["ok"]:
            raise RuntimeError((sc["challenge_id"], "AC->Stable conversion failed", sv))
        stable_solved[sc["challenge_id"]] = {
            "path": sp,
            "verdict": sv,
            "method": row["method"] + "+destabilize",
        }

    # Submission lines: pair AC + stable for each presentation, shortest AC
    # certificate first. 500-line shards obey the official structural limit.
    ordered = sorted(
        solved.items(),
        key=lambda kv: (
            len(kv[1]["path"]),
            kv[0],
        ),
    )
    lines = []
    solution_index = []
    for cid, row in ordered:
        suffix = cid[3:]
        sid = "sac-" + suffix
        ap = list(row["path"])
        sp = list(stable_solved[sid]["path"])
        lines.append(f"{cid}: {json.dumps(ap, separators=(',', ':'))}")
        lines.append(f"{sid}: {json.dumps(sp, separators=(',', ':'))}")
        solution_index.append(
            {
                "ac_id": cid,
                "stable_id": sid,
                "ac_length": len(ap),
                "stable_length": len(sp),
                "method": row["method"],
                "ac_certificate_hash": row["verdict"]["certificate_hash"],
                "stable_certificate_hash": stable_solved[sid]["verdict"]["certificate_hash"],
            }
        )

    submission_files = shard_lines(lines, out_dir, "submission_v1")

    report = {
        "experiment": "andrews-curtis-development-v1",
        "official_commit": "99a65377c5c4f412cd9af7b8d31c41464a855736",
        "training": {
            "count": len(training["instances"]),
            "known_length_stats": {
                "min": min(known_lengths),
                "median": statistics.median(known_lengths),
                "mean": statistics.mean(known_lengths),
                "max": max(known_lengths),
            },
            "development_rows": len(training["instances"][0::2]),
            "holdout_rows": len(training["instances"][1::2]),
            "frozen_macros": macro_meta,
            "holdout_results": holdout_results,
        },
        "reverse": {
            "depth_limit": args.reverse_depth,
            "state_cap": args.reverse_cap,
            "states": len(reverse_paths),
            "depth_hist": reverse_hist,
            "max_total": args.reverse_max_total,
        },
        "scored": {
            "presentations": len(ac_rows),
            "direct_reverse_solved": direct_reverse,
            "searched_nonreverse": searched,
            "expansions_total": expansions_total,
            "ac_solved": len(solved),
            "stable_solved_via_ac": len(stable_solved),
            "solution_lines": len(lines),
        },
        "solutions": solution_index,
        "submission_files": submission_files,
    }
    report_bytes = json.dumps(report, indent=2, sort_keys=True).encode()
    (out_dir / "report_v1.json").write_bytes(report_bytes)
    (out_dir / "report_v1.sha256").write_text(
        hashlib.sha256(report_bytes).hexdigest() + "  report_v1.json\n"
    )
    (out_dir / "macros_v1.json").write_text(
        json.dumps(macro_meta, indent=2, sort_keys=True) + "\n"
    )

    print(
        "FINAL",
        json.dumps(
            {
                "ac_solved": len(solved),
                "stable_solved": len(stable_solved),
                "submission_files": submission_files,
                "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
