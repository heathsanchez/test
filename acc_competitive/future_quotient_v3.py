#!/usr/bin/env python3
"""
ACC Future Quotient V3.

V1 discovered that one-step future signatures strongly predict verified Atlas
continuation but do not produce exact joins off-Atlas.
V2 showed that treating those contacts as nearby exact states is wrong:
bounded exact bridges fail.

V3 follows the newly isolated residual instead of widening search:
  * keep V1/V2 future classes as guidance only;
  * refine a contact lazily by one additional official future step;
  * only when an off-Atlas state and an exact Atlas representative still agree
    under that two-step protected-future signature, execute the class's learned
    official next-move policy exactly;
  * at every rollout step require the same lazy refined match again;
  * warrant nothing until the rollout reaches the exact Atlas or the target and
    the complete reconstructed certificate passes the pinned official verifier.

Thus a failed rollout is a separator, not a proof failure or a reason to widen
the search radius.
"""

from __future__ import annotations

import argparse
import collections
import heapq
import json
import sqlite3
import sys
import time
from pathlib import Path

from future_quotient_v2 import (
    OFFICIAL_PIN,
    TARGET,
    atlas_suffix,
    base_signature,
    decode_state,
    digest_parts,
    future_signature,
    key_state,
    load_index,
    reconstruct_prefix,
    snapshot_rows,
)


def refined_signature2(core, state, total_cap):
    """One further lawful-future refinement beyond the V1 future signature."""
    first, _ = future_signature(core, state, total_cap)
    children = []
    for m in range(core.NUM_MOVES):
        nxt = core.apply_move(state, m)
        if sum(map(len, nxt)) > total_cap:
            children.append(b"X")
        else:
            sig, _ = future_signature(core, nxt, total_cap)
            children.append(sig)
    return digest_parts((first, *children))


def load_representative_cache(core, representatives, total_cap):
    cache = {}

    def rep_sig2(rep_key):
        got = cache.get(rep_key)
        if got is None:
            got = refined_signature2(core, decode_state(rep_key), total_cap)
            cache[rep_key] = got
        return got

    return rep_sig2


def policy_rollout(
    core,
    adb,
    start,
    start_depth,
    bound_exclusive,
    total_cap,
    future_idx,
    representatives,
    rep_sig2,
    query_sig2_cache,
    min_policy_purity,
    max_steps,
):
    """Execute the learned policy only while a lazy two-step class match survives."""
    state = start
    moves = []
    seen = {state}
    trace = []

    def qsig2(s):
        k = key_state(s)
        got = query_sig2_cache.get(k)
        if got is None:
            got = refined_signature2(core, s, total_cap)
            query_sig2_cache[k] = got
        return got

    for _ in range(max_steps + 1):
        k = key_state(state)

        row = adb.execute(
            "SELECT distance,next_move FROM atlas WHERE state=?", (k,)
        ).fetchone()
        if row is not None:
            ad = int(row[0])
            if start_depth + len(moves) + ad < bound_exclusive:
                suffix = atlas_suffix(
                    core,
                    adb,
                    state,
                    bound_exclusive - start_depth - len(moves) + 8,
                )
                if suffix is not None:
                    return moves + suffix, {
                        "reason": "exact_atlas_join",
                        "rollout_steps": len(moves),
                        "atlas_distance": ad,
                        "atlas_suffix": len(suffix),
                        "trace": trace,
                    }
            return None, {
                "reason": "atlas_join_outside_bound",
                "rollout_steps": len(moves),
                "atlas_distance": ad,
                "trace": trace,
            }

        if state == TARGET:
            if start_depth + len(moves) < bound_exclusive:
                return moves, {
                    "reason": "exact_target",
                    "rollout_steps": len(moves),
                    "trace": trace,
                }
            return None, {
                "reason": "target_outside_bound",
                "rollout_steps": len(moves),
                "trace": trace,
            }

        fs, _ = future_signature(core, state, total_cap)
        finfo = future_idx.get(fs)
        if finfo is None:
            return None, {
                "reason": "future_class_miss",
                "rollout_steps": len(moves),
                "trace": trace,
            }

        q2 = qsig2(state)
        matching = [
            rep
            for rep in representatives.get(fs, ())
            if rep_sig2(rep[0]) == q2
        ]
        if not matching:
            return None, {
                "reason": "two_step_separator",
                "rollout_steps": len(moves),
                "future_sig": fs.hex(),
                "trace": trace,
            }

        policy_move = finfo[5]
        policy_purity = float(finfo[6])
        if policy_move is None:
            return None, {
                "reason": "no_policy",
                "rollout_steps": len(moves),
                "future_sig": fs.hex(),
                "trace": trace,
            }
        if policy_purity < min_policy_purity:
            return None, {
                "reason": "policy_purity_below_gate",
                "rollout_steps": len(moves),
                "future_sig": fs.hex(),
                "policy_purity": policy_purity,
                "trace": trace,
            }

        matching_moves = {
            rep[2] for rep in matching if rep[2] is not None
        }
        if matching_moves and policy_move not in matching_moves:
            return None, {
                "reason": "refined_policy_disagreement",
                "rollout_steps": len(moves),
                "future_sig": fs.hex(),
                "policy_move": policy_move,
                "matching_rep_moves": sorted(matching_moves),
                "trace": trace,
            }

        trace.append(
            {
                "future_sig": fs.hex(),
                "min_distance": int(finfo[1]),
                "policy_move": int(policy_move),
                "policy_purity": policy_purity,
                "matching_representatives": len(matching),
            }
        )

        nxt = core.apply_move(state, int(policy_move))
        if sum(map(len, nxt)) > total_cap:
            return None, {
                "reason": "length_limit",
                "rollout_steps": len(moves),
                "trace": trace,
            }

        moves.append(int(policy_move))
        if start_depth + len(moves) >= bound_exclusive:
            return None, {
                "reason": "live_bound_exhausted",
                "rollout_steps": len(moves),
                "trace": trace,
            }
        if nxt in seen:
            return None, {
                "reason": "policy_cycle",
                "rollout_steps": len(moves),
                "trace": trace,
            }
        seen.add(nxt)
        state = nxt

    return None, {
        "reason": "rollout_cap",
        "rollout_steps": len(moves),
        "trace": trace,
    }


def search_target(
    core,
    challenge,
    atlas_path,
    index_path,
    bound_exclusive,
    total_cap,
    node_cap,
    time_cap,
    rollout_attempt_cap,
    min_policy_purity,
):
    base_idx, future_idx, policies, representatives = load_index(index_path)
    adb = sqlite3.connect(atlas_path)
    initial = tuple(tuple(w) for w in challenge["initial_relators"])

    parent = {key_state(initial): (None, None)}
    states = {key_state(initial): initial}
    best_g = {key_state(initial): 0}
    serial = 0

    def base_h(s):
        info = base_idx.get(base_signature(s))
        if info is None:
            return 256.0
        return float(info[1])

    pq = [(base_h(initial), 0, sum(map(len, initial)), serial, key_state(initial), None)]
    serial += 1

    popped = generated = exact_hits = future_hits = policy_hits = 0
    refined_contacts = rollout_attempts = rollout_successes = 0
    best_seen_future = None
    t0 = time.time()
    candidate = None
    candidate_meta = None

    rep_sig2 = load_representative_cache(core, representatives, total_cap)
    query_sig2_cache = {}
    rollout_seen = set()
    failure_hist = collections.Counter()
    separators = []

    while pq and popped < node_cap and time.time() - t0 < time_cap:
        _, g, _, _, k, last = heapq.heappop(pq)
        if g != best_g.get(k):
            continue
        state = states[k]
        if g >= bound_exclusive:
            continue
        popped += 1

        row = adb.execute(
            "SELECT distance,next_move FROM atlas WHERE state=?", (k,)
        ).fetchone()
        if row is not None:
            exact_hits += 1
            ad = int(row[0])
            if g + ad < bound_exclusive:
                prefix = reconstruct_prefix(parent, k)
                suffix = atlas_suffix(
                    core, adb, state, bound_exclusive - len(prefix) + 8
                )
                if suffix is not None:
                    candidate = prefix + suffix
                    candidate_meta = {
                        "join_kind": "exact_atlas_join",
                        "join_depth": g,
                        "atlas_distance": ad,
                        "atlas_suffix": len(suffix),
                    }
                    break

        fs, children_base = future_signature(core, state, total_cap)
        finfo = future_idx.get(fs)
        move_order = list(range(core.NUM_MOVES))

        if finfo is not None:
            future_hits += 1
            best_seen_future = (
                int(finfo[1])
                if best_seen_future is None
                else min(best_seen_future, int(finfo[1]))
            )

            q2 = query_sig2_cache.get(k)
            if q2 is None:
                q2 = refined_signature2(core, state, total_cap)
                query_sig2_cache[k] = q2

            matching = [
                rep
                for rep in representatives.get(fs, ())
                if rep_sig2(rep[0]) == q2
            ]
            if matching:
                refined_contacts += 1

                if (
                    rollout_attempts < rollout_attempt_cap
                    and k not in rollout_seen
                ):
                    rollout_seen.add(k)
                    rollout_attempts += 1
                    max_steps = bound_exclusive - 1 - g
                    tail, meta = policy_rollout(
                        core,
                        adb,
                        state,
                        g,
                        bound_exclusive,
                        total_cap,
                        future_idx,
                        representatives,
                        rep_sig2,
                        query_sig2_cache,
                        min_policy_purity,
                        max_steps,
                    )
                    if tail is not None:
                        prefix = reconstruct_prefix(parent, k)
                        cand = prefix + tail
                        if len(cand) >= bound_exclusive:
                            raise RuntimeError(
                                ("policy rollout violates frozen bound", len(cand), bound_exclusive)
                            )
                        rollout_successes += 1
                        candidate = cand
                        candidate_meta = {
                            "join_kind": "two_step_refined_policy_rollout",
                            "join_depth": g,
                            "initial_future_sig": fs.hex(),
                            "matching_representatives": len(matching),
                            **meta,
                        }
                        break

                    reason = str(meta.get("reason"))
                    failure_hist[reason] += 1
                    if len(separators) < 64:
                        separators.append(
                            {
                                "query_state": k.hex(),
                                "query_depth": g,
                                "future_sig": fs.hex(),
                                "matching_representatives": len(matching),
                                "rollout_failure": {
                                    k: v
                                    for k, v in meta.items()
                                    if k != "trace"
                                },
                                "trace_prefix": meta.get("trace", [])[:8],
                            }
                        )

            pol = policies.get(fs, [])
            if pol:
                policy_hits += 1
                ranked = [m for m, _ in pol]
                ranked_set = set(ranked)
                move_order = ranked + [m for m in move_order if m not in ranked_set]

        for m in move_order:
            if last is not None and core.INVERSE_MOVE[last] == m:
                continue
            nxt = core.apply_move(state, m)
            generated += 1
            if sum(map(len, nxt)) > total_cap:
                continue
            ng = g + 1
            if ng >= bound_exclusive:
                continue
            nk = key_state(nxt)
            if ng >= best_g.get(nk, 10**18):
                continue
            best_g[nk] = ng
            parent[nk] = (k, m)
            states[nk] = nxt
            binfo = base_idx.get(children_base[m])
            qh = float(binfo[1]) if binfo is not None else 256.0
            heapq.heappush(
                pq,
                (ng + qh, ng, sum(map(len, nxt)), serial, nk, m),
            )
            serial += 1

    status = (
        "FOUND_VERIFIER_CANDIDATE"
        if candidate is not None
        else "UNKNOWN_NODE_CAP"
        if popped >= node_cap
        else "UNKNOWN_TIME_CAP"
        if time.time() - t0 >= time_cap
        else "NO_CANDIDATE_IN_EXPLORED_SCOPE"
    )

    meta = {
        "status": status,
        "found": candidate is not None,
        "nodes_popped": popped,
        "generated": generated,
        "visited": len(best_g),
        "frontier": len(pq),
        "exact_atlas_hits": exact_hits,
        "future_class_hits": future_hits,
        "policy_class_hits": policy_hits,
        "refined_two_step_contacts": refined_contacts,
        "rollout_attempts": rollout_attempts,
        "rollout_successes": rollout_successes,
        "rollout_failure_histogram": dict(sorted(failure_hist.items())),
        "separator_examples": separators,
        "best_seen_future_min_distance": best_seen_future,
        "seconds": round(time.time() - t0, 3),
        "bound_exclusive": bound_exclusive,
        "node_cap": node_cap,
        "time_cap": time_cap,
        "min_policy_purity": min_policy_purity,
    }
    if candidate_meta is not None:
        meta.update(candidate_meta)
    adb.close()
    return candidate, meta


def cmd_search(a):
    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads(
        (acc / "competition/tools/verifier/data/manifest.json").read_text()
    )
    byid = {c["challenge_id"]: c for c in manifest["challenges"]}
    limits = manifest["limits"]
    ac = snapshot_rows(a.snapshot_ac)
    stable = snapshot_rows(a.snapshot_stable)
    ids = json.loads(Path(a.targets).read_text())
    ids = [x["challenge_id"] if isinstance(x, dict) else str(x) for x in ids]

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    lines = []

    for cid in ids:
        sid = "sac-" + cid[3:]
        c = byid.get(cid)
        sc = byid.get(sid)
        ar = ac.get(cid, {})
        sr = stable.get(sid, {})
        if c is None or sc is None:
            continue

        ab = ar.get("currentBestLength")
        sb = sr.get("currentBestLength")
        if not isinstance(ab, int) or not isinstance(sb, int):
            continue

        bound = max(ab, sb - 2)
        path, meta = search_target(
            core,
            c,
            a.atlas,
            a.index,
            bound,
            int(limits["max_total_relator_length"]),
            a.node_cap,
            a.time_cap,
            a.rollout_attempt_cap,
            a.min_policy_purity,
        )

        rec = {
            "challenge_id": cid,
            "stable_challenge_id": sid,
            "ac_best": ab,
            "stable_best": sb,
            "source_bound_exclusive": bound,
            "stable_slack_vs_ac_best": sb - (ab + 2),
            **meta,
        }

        if path is not None:
            verdict = core.verify(
                c, path, c["move_spec_version"], limits
            )
            if not verdict.get("ok"):
                raise RuntimeError(
                    f"V3 policy candidate failed pinned AC verifier {cid}: {verdict}"
                )

            stable_path = list(path) + [16, 15]
            sverdict = stable_core.verify(
                sc, stable_path, sc["move_spec_version"], limits
            )
            if not sverdict.get("ok"):
                raise RuntimeError(
                    f"V3 policy candidate failed pinned Stable verifier {sid}: {sverdict}"
                )

            ac_win = len(path) < ab
            stable_win = len(stable_path) < sb
            rec.update(
                {
                    "source_length": len(path),
                    "stable_length": len(stable_path),
                    "ac_strict_win": ac_win,
                    "stable_strict_win": stable_win,
                    "strict_win": ac_win or stable_win,
                    "certificate_hash": verdict.get("certificate_hash"),
                    "stable_certificate_hash": sverdict.get("certificate_hash"),
                }
            )
            if ac_win:
                lines.append(
                    f"{cid}: {json.dumps(path,separators=(',',':'))}"
                )
            if stable_win:
                lines.append(
                    f"{sid}: {json.dumps(stable_path,separators=(',',':'))}"
                )
        else:
            rec.update(
                {
                    "ac_strict_win": False,
                    "stable_strict_win": False,
                    "strict_win": False,
                }
            )

        rows.append(rec)
        print(
            "ACC_FUTURE_QUOTIENT_V3_CASE",
            json.dumps(rec, sort_keys=True),
            flush=True,
        )

    (out / "results.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n"
    )
    (out / "candidate_batch.txt").write_text(
        "\n".join(lines) + ("\n" if lines else "")
    )

    failure_hist = collections.Counter()
    for row in rows:
        failure_hist.update(row.get("rollout_failure_histogram", {}))

    report = {
        "version": "acc-future-quotient-v3",
        "official_pin": OFFICIAL_PIN,
        "targets": len(rows),
        "strict_winning_targets": sum(bool(r.get("strict_win")) for r in rows),
        "ac_wins": sum(bool(r.get("ac_strict_win")) for r in rows),
        "stable_wins": sum(bool(r.get("stable_strict_win")) for r in rows),
        "candidate_rows": len(lines),
        "nodes_popped": sum(int(r.get("nodes_popped", 0)) for r in rows),
        "future_class_hits": sum(int(r.get("future_class_hits", 0)) for r in rows),
        "refined_two_step_contacts": sum(
            int(r.get("refined_two_step_contacts", 0)) for r in rows
        ),
        "rollout_attempts": sum(int(r.get("rollout_attempts", 0)) for r in rows),
        "rollout_successes": sum(int(r.get("rollout_successes", 0)) for r in rows),
        "rollout_failure_histogram": dict(sorted(failure_hist.items())),
        "claim_boundary": (
            "Two-step signatures are lazy search refinements only. "
            "Policy moves are exact official AC moves. A candidate is emitted "
            "only after exact target/Atlas completion and pinned official replay."
        ),
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        "ACC_FUTURE_QUOTIENT_V3_SUMMARY",
        json.dumps(report, sort_keys=True),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--atlas", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--snapshot-ac", required=True)
    ap.add_argument("--snapshot-stable", required=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--node-cap", type=int, default=120000)
    ap.add_argument("--time-cap", type=float, default=1200.0)
    ap.add_argument("--rollout-attempt-cap", type=int, default=2000)
    ap.add_argument("--min-policy-purity", type=float, default=0.75)
    a = ap.parse_args()
    cmd_search(a)


if __name__ == "__main__":
    main()
