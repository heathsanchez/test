#!/usr/bin/env python3
"""
ACC Future Quotient V4.

Residual carried from V3:
- one-step future classes were highly predictive on the Proof Atlas;
- exact within-class bridges failed;
- lazy two-step continuation still produced 56 false portals;
- the already-qualified six-context finite-group projection separates all
  56/56 V3 false portals.

V4 therefore adds no new mathematical primitive.  It composes two previously
qualified, independent views:

    FutureSignatureV1(state)
    x
    SixContextFiniteGroupProjection(state)

The product is search guidance only.  It is useful because the finite-group
projection is an exact homomorphic image of the official AC moves: equal
projected states remain equal after the same official move sequence.

At a guarded class contact V4 may execute the class's learned official next
move.  It rechecks the guarded class after every exact move and stops on the
first separator.  A candidate is emitted only after reaching the exact Proof
Atlas or exact target and then passing the pinned official verifier.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from acc_competitive import finite_group_pdb_v1 as fg
from acc_competitive.atlas_fiber_refinement_v1 import contexts as fg_contexts
from acc_competitive.atlas_fiber_refinement_v1 import project as fg_project


def guard_signature(state, ctxs):
    """Stable digest of the already-qualified synchronized finite-group image."""
    return digest_parts((fg_project(fg, state, ctxs),))


def init_guard_db(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA temp_store=MEMORY")
    db.executescript(
        """
        DROP TABLE IF EXISTS guarded_observations;
        DROP TABLE IF EXISTS guarded_classes;
        DROP TABLE IF EXISTS guarded_policy;

        CREATE TABLE guarded_observations(
          state BLOB NOT NULL,
          future_sig BLOB NOT NULL,
          guard_sig BLOB NOT NULL,
          distance INTEGER NOT NULL,
          distance_band INTEGER NOT NULL,
          next_move INTEGER
        );

        CREATE TABLE guarded_policy(
          future_sig BLOB NOT NULL,
          guard_sig BLOB NOT NULL,
          move INTEGER NOT NULL,
          n INTEGER NOT NULL,
          PRIMARY KEY(future_sig,guard_sig,move)
        );

        CREATE TABLE guarded_classes(
          future_sig BLOB NOT NULL,
          guard_sig BLOB NOT NULL,
          n INTEGER NOT NULL,
          min_distance INTEGER NOT NULL,
          max_distance INTEGER NOT NULL,
          mean_distance REAL NOT NULL,
          band_count INTEGER NOT NULL,
          policy_move INTEGER,
          policy_purity REAL NOT NULL,
          PRIMARY KEY(future_sig,guard_sig)
        );
        """
    )
    db.commit()
    return db


def build_guard_index(v2_index, out_db, progress_every=10000):
    src = sqlite3.connect(v2_index)
    dst = init_guard_db(out_db)
    ctxs = fg_contexts(fg)

    batch = []
    n = 0
    t0 = time.time()
    for state, fs, distance, band, next_move in src.execute(
        "SELECT state,future_sig,distance,distance_band,next_move FROM observations ORDER BY distance,state"
    ):
        s = decode_state(state)
        gs = guard_signature(s, ctxs)
        batch.append(
            (
                bytes(state),
                bytes(fs),
                gs,
                int(distance),
                int(band),
                None if next_move is None else int(next_move),
            )
        )
        n += 1
        if len(batch) >= 2000:
            dst.executemany(
                "INSERT INTO guarded_observations VALUES(?,?,?,?,?,?)", batch
            )
            dst.commit()
            batch.clear()
        if progress_every and n % progress_every == 0:
            print(
                "FQ4_GUARD_BUILD_PROGRESS",
                json.dumps(
                    {"states": n, "seconds": round(time.time() - t0, 3)},
                    sort_keys=True,
                ),
                flush=True,
            )
    if batch:
        dst.executemany(
            "INSERT INTO guarded_observations VALUES(?,?,?,?,?,?)", batch
        )
        dst.commit()

    dst.executescript(
        """
        CREATE INDEX guard_obs_key
          ON guarded_observations(future_sig,guard_sig);
        CREATE INDEX guard_obs_distance
          ON guarded_observations(future_sig,guard_sig,distance);

        INSERT INTO guarded_policy
        SELECT future_sig,guard_sig,next_move,COUNT(*)
        FROM guarded_observations
        WHERE next_move IS NOT NULL
        GROUP BY future_sig,guard_sig,next_move;

        CREATE TEMP TABLE guarded_policy_mode AS
        SELECT future_sig,guard_sig,move,n,total FROM (
          SELECT future_sig,guard_sig,move,n,
                 SUM(n) OVER (PARTITION BY future_sig,guard_sig) AS total,
                 ROW_NUMBER() OVER (
                   PARTITION BY future_sig,guard_sig
                   ORDER BY n DESC,move ASC
                 ) AS rn
          FROM guarded_policy
        ) WHERE rn=1;

        INSERT INTO guarded_classes
        SELECT o.future_sig,
               o.guard_sig,
               COUNT(*),
               MIN(o.distance),
               MAX(o.distance),
               AVG(o.distance),
               COUNT(DISTINCT o.distance_band),
               pm.move,
               COALESCE(1.0*pm.n/pm.total,0.0)
        FROM guarded_observations o
        LEFT JOIN guarded_policy_mode pm
          ON pm.future_sig=o.future_sig AND pm.guard_sig=o.guard_sig
        GROUP BY o.future_sig,o.guard_sig;
        """
    )
    dst.commit()

    classes = dst.execute("SELECT COUNT(*) FROM guarded_classes").fetchone()[0]
    singleton_classes = dst.execute(
        "SELECT COUNT(*) FROM guarded_classes WHERE n=1"
    ).fetchone()[0]
    singleton_states = dst.execute(
        "SELECT COALESCE(SUM(n),0) FROM guarded_classes WHERE n=1"
    ).fetchone()[0]
    pure_states = dst.execute(
        "SELECT COALESCE(SUM(n),0) FROM guarded_classes WHERE band_count=1"
    ).fetchone()[0]
    policy_rows = dst.execute(
        "SELECT n,policy_purity FROM guarded_classes WHERE policy_move IS NOT NULL"
    ).fetchall()
    policy_weight = sum(x[0] for x in policy_rows)
    weighted_policy_purity = (
        sum(nc * pp for nc, pp in policy_rows) / policy_weight
        if policy_weight
        else 0.0
    )
    strong_policy_states = sum(nc for nc, pp in policy_rows if pp >= 0.75)

    report = {
        "version": "acc-future-quotient-v4-guard",
        "official_pin": OFFICIAL_PIN,
        "atlas_states": n,
        "guarded_classes": classes,
        "singleton_classes": singleton_classes,
        "singleton_state_fraction": singleton_states / n if n else 0.0,
        "distance_band_pure_state_fraction": pure_states / n if n else 0.0,
        "weighted_policy_purity": weighted_policy_purity,
        "strong_policy_state_fraction": strong_policy_states / n if n else 0.0,
        "contexts": [x[0] for x in ctxs],
        "build_seconds": round(time.time() - t0, 3),
        "claim_boundary": (
            "The guard is the already-qualified six-context synchronized "
            "finite-group projection. Equality is a necessary compatibility "
            "test only; no exact state equality is inferred."
        ),
    }
    src.close()
    dst.close()
    return report


def load_guard_classes(path):
    db = sqlite3.connect(path)
    out = {
        (bytes(fs), bytes(gs)): (
            int(n),
            int(mind),
            int(maxd),
            float(avgd),
            int(bands),
            None if pm is None else int(pm),
            float(pp),
        )
        for fs, gs, n, mind, maxd, avgd, bands, pm, pp in db.execute(
            """
            SELECT future_sig,guard_sig,n,min_distance,max_distance,
                   mean_distance,band_count,policy_move,policy_purity
            FROM guarded_classes
            """
        )
    }
    db.close()
    return out


def audit_v3_separators(v2_index, v3_dir, total_cap):
    """Reproduce the exact V3 false-contact boundary and test the guard."""
    from future_quotient_v3 import refined_signature2

    ctxs = fg_contexts(fg)
    db = sqlite3.connect(v2_index)
    rows = []
    total = separated = 0

    for p in sorted(Path(v3_dir).rglob("results.json")):
        obj = json.loads(p.read_text())
        cases = obj if isinstance(obj, list) else [obj]
        for case in cases:
            for ex in case.get("separator_examples", []):
                qkey = bytes.fromhex(ex["query_state"])
                query = decode_state(qkey)
                fs = bytes.fromhex(ex["future_sig"])
                q2 = refined_signature2_for_audit(query, total_cap)
                qg = guard_signature(query, ctxs)

                matching = []
                for rk, distance, next_move, rep_rank in db.execute(
                    """
                    SELECT state,distance,next_move,rep_rank
                    FROM future_representatives
                    WHERE signature=?
                    ORDER BY rep_rank
                    """,
                    (fs,),
                ):
                    rep = decode_state(rk)
                    if refined_signature2_for_audit(rep, total_cap) == q2:
                        matching.append(
                            {
                                "state": bytes(rk),
                                "distance": int(distance),
                                "next_move": None
                                if next_move is None
                                else int(next_move),
                                "rank": int(rep_rank),
                                "guard": guard_signature(rep, ctxs),
                            }
                        )

                if not matching:
                    raise RuntimeError(
                        f"cannot reproduce V3 refined contact {case.get('challenge_id')} {fs.hex()}"
                    )

                same_guard = [r for r in matching if r["guard"] == qg]
                total += 1
                if not same_guard:
                    separated += 1
                rows.append(
                    {
                        "challenge_id": case.get("challenge_id"),
                        "query_depth": ex.get("query_depth"),
                        "future_sig": fs.hex(),
                        "matching_v3_representatives": len(matching),
                        "same_six_context_guard": len(same_guard),
                        "v3_failure_reason": (
                            ex.get("rollout_failure") or {}
                        ).get("reason"),
                    }
                )

    db.close()
    return {
        "v3_false_contacts": total,
        "separated_by_six_context_guard": separated,
        "separation_fraction": separated / total if total else None,
        "rows": rows,
    }


# Keep the audit self-contained and source-identical to V3's refinement.
def refined_signature2_for_audit(state, total_cap):
    first, _ = future_signature_for_audit(state, total_cap)
    children = []
    for m in range(14):
        nxt = apply_move_for_audit(state, m)
        if sum(map(len, nxt)) > total_cap:
            children.append(b"X")
        else:
            sig, _ = future_signature_for_audit(nxt, total_cap)
            children.append(sig)
    return digest_parts((first, *children))


def apply_move_for_audit(state, m):
    # Imported official semantics are unavailable in the build-only audit
    # process until runtime; use the same frozen formulas as ac-r2-v1.
    r0, r1 = state

    def inv_word(w):
        return tuple(-a for a in reversed(w))

    def reduce_word(w):
        out = []
        for a in w:
            if out and out[-1] == -a:
                out.pop()
            else:
                out.append(a)
        return tuple(out)

    if m == 0:
        return inv_word(r0), r1
    if m == 1:
        return r0, inv_word(r1)
    if m == 2:
        return reduce_word(r0 + r1), r1
    if m == 3:
        return reduce_word(r0 + inv_word(r1)), r1
    if m == 4:
        return r0, reduce_word(r1 + r0)
    if m == 5:
        return r0, reduce_word(r1 + inv_word(r0))
    gens = (1, -1, 2, -2)
    if 6 <= m <= 9:
        g = gens[m - 6]
        return reduce_word((g,) + r0 + (-g,)), r1
    if 10 <= m <= 13:
        g = gens[m - 10]
        return r0, reduce_word((g,) + r1 + (-g,))
    raise ValueError(m)


def future_signature_for_audit(state, total_cap):
    b = base_signature(state)
    children = []
    for m in range(14):
        nxt = apply_move_for_audit(state, m)
        if sum(map(len, nxt)) > total_cap:
            children.append(b"X")
        else:
            children.append(base_signature(nxt))
    return digest_parts((b, *children)), children


def guarded_rollout(
    core,
    adb,
    start,
    start_depth,
    bound_exclusive,
    total_cap,
    future_idx,
    guarded_classes,
    ctxs,
    min_policy_purity,
    max_steps,
):
    state = start
    moves = []
    seen = {state}
    trace = []

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
        gs = guard_signature(state, ctxs)
        info = guarded_classes.get((fs, gs))
        if info is None:
            return None, {
                "reason": "guarded_class_miss",
                "rollout_steps": len(moves),
                "trace": trace,
            }

        n, mind, maxd, avgd, bands, policy_move, policy_purity = info
        if policy_move is None:
            return None, {
                "reason": "no_policy",
                "rollout_steps": len(moves),
                "trace": trace,
            }
        if policy_purity < min_policy_purity:
            return None, {
                "reason": "policy_purity_below_gate",
                "rollout_steps": len(moves),
                "policy_purity": policy_purity,
                "trace": trace,
            }

        trace.append(
            {
                "future_sig": fs.hex(),
                "guard_sig": gs.hex(),
                "class_size": n,
                "min_distance": mind,
                "policy_move": policy_move,
                "policy_purity": policy_purity,
            }
        )

        nxt = core.apply_move(state, policy_move)
        if sum(map(len, nxt)) > total_cap:
            return None, {
                "reason": "length_limit",
                "rollout_steps": len(moves),
                "trace": trace,
            }
        moves.append(policy_move)
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
    v2_index,
    guard_index,
    bound_exclusive,
    total_cap,
    node_cap,
    time_cap,
    rollout_attempt_cap,
    min_policy_purity,
):
    base_idx, future_idx, _, _ = load_index(v2_index)
    guarded_classes = load_guard_classes(guard_index)
    ctxs = fg_contexts(fg)
    adb = sqlite3.connect(atlas_path)

    initial = tuple(tuple(w) for w in challenge["initial_relators"])
    ik = key_state(initial)
    parent = {ik: (None, None)}
    states = {ik: initial}
    best_g = {ik: 0}
    serial = 0

    def heuristic(s):
        fs, _ = future_signature(core, s, total_cap)
        gs = guard_signature(s, ctxs)
        info = guarded_classes.get((fs, gs))
        if info is not None:
            return float(info[1])
        binfo = base_idx.get(base_signature(s))
        return float(binfo[1]) if binfo is not None else 256.0

    pq = [(heuristic(initial), 0, sum(map(len, initial)), serial, ik, None)]
    serial += 1

    popped = generated = exact_hits = future_hits = guarded_hits = 0
    rollout_attempts = rollout_successes = 0
    best_guarded_distance = None
    t0 = time.time()
    candidate = None
    candidate_meta = None
    failure_hist = collections.Counter()
    separator_examples = []
    rollout_seen = set()

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

        fs, child_base = future_signature(core, state, total_cap)
        finfo = future_idx.get(fs)
        move_order = list(range(core.NUM_MOVES))
        if finfo is not None:
            future_hits += 1

        gs = guard_signature(state, ctxs)
        ginfo = guarded_classes.get((fs, gs))
        if ginfo is not None:
            guarded_hits += 1
            best_guarded_distance = (
                ginfo[1]
                if best_guarded_distance is None
                else min(best_guarded_distance, ginfo[1])
            )
            policy_move = ginfo[5]
            policy_purity = ginfo[6]

            # Only spend a rollout when the class's best known continuation
            # could still fit under the frozen live bound.
            viable = g + ginfo[1] < bound_exclusive
            if (
                viable
                and rollout_attempts < rollout_attempt_cap
                and k not in rollout_seen
            ):
                rollout_seen.add(k)
                rollout_attempts += 1
                tail, meta = guarded_rollout(
                    core,
                    adb,
                    state,
                    g,
                    bound_exclusive,
                    total_cap,
                    future_idx,
                    guarded_classes,
                    ctxs,
                    min_policy_purity,
                    bound_exclusive - 1 - g,
                )
                if tail is not None:
                    prefix = reconstruct_prefix(parent, k)
                    cand = prefix + tail
                    if len(cand) >= bound_exclusive:
                        raise RuntimeError(
                            ("guarded rollout violates live bound", len(cand), bound_exclusive)
                        )
                    rollout_successes += 1
                    candidate = cand
                    candidate_meta = {
                        "join_kind": "future_x_sixctx_guarded_rollout",
                        "join_depth": g,
                        "guarded_class_size": ginfo[0],
                        "guarded_min_distance": ginfo[1],
                        **meta,
                    }
                    break

                reason = str(meta.get("reason"))
                failure_hist[reason] += 1
                if len(separator_examples) < 64:
                    separator_examples.append(
                        {
                            "query_state": k.hex(),
                            "query_depth": g,
                            "future_sig": fs.hex(),
                            "guard_sig": gs.hex(),
                            "guarded_class_size": ginfo[0],
                            "guarded_min_distance": ginfo[1],
                            "rollout_failure": {
                                kk: vv
                                for kk, vv in meta.items()
                                if kk != "trace"
                            },
                            "trace_prefix": meta.get("trace", [])[:8],
                        }
                    )

            if policy_move is not None:
                move_order = [policy_move] + [
                    m for m in move_order if m != policy_move
                ]

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

            # Keep the cheap V1 base heuristic for frontier ordering.
            # The finite-group product is a portal/continuation guard only;
            # evaluating it on every generated child would add cost without
            # changing any pruning or authority boundary.
            binfo = base_idx.get(child_base[m])
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
        "guarded_class_hits": guarded_hits,
        "best_guarded_min_distance": best_guarded_distance,
        "rollout_attempts": rollout_attempts,
        "rollout_successes": rollout_successes,
        "rollout_failure_histogram": dict(sorted(failure_hist.items())),
        "separator_examples": separator_examples,
        "seconds": round(time.time() - t0, 3),
        "bound_exclusive": bound_exclusive,
        "node_cap": node_cap,
        "time_cap": time_cap,
    }
    if candidate_meta:
        meta.update(candidate_meta)
    adb.close()
    return candidate, meta


def cmd_build(a):
    report = build_guard_index(
        a.v2_index, a.out_guard_index, a.progress_every
    )
    Path(a.out_report).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print("ACC_FUTURE_QUOTIENT_V4_BUILD", json.dumps(report, sort_keys=True))

    if a.v3_dir:
        audit = audit_v3_separators(a.v2_index, a.v3_dir, a.total_cap)
        Path(a.out_audit).write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n"
        )
        print(
            "ACC_FUTURE_QUOTIENT_V4_SEPARATOR_AUDIT",
            json.dumps(
                {
                    k: v
                    for k, v in audit.items()
                    if k != "rows"
                },
                sort_keys=True,
            ),
        )


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
            a.v2_index,
            a.guard_index,
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
            v = core.verify(c, path, c["move_spec_version"], limits)
            if not v.get("ok"):
                raise RuntimeError(
                    f"V4 candidate failed pinned AC verifier {cid}: {v}"
                )
            sp = list(path) + [16, 15]
            sv = stable_core.verify(
                sc, sp, sc["move_spec_version"], limits
            )
            if not sv.get("ok"):
                raise RuntimeError(
                    f"V4 derivative failed pinned Stable verifier {sid}: {sv}"
                )

            ac_win = len(path) < ab
            stable_win = len(sp) < sb
            rec.update(
                {
                    "source_length": len(path),
                    "stable_length": len(sp),
                    "ac_strict_win": ac_win,
                    "stable_strict_win": stable_win,
                    "strict_win": ac_win or stable_win,
                    "certificate_hash": v.get("certificate_hash"),
                    "stable_certificate_hash": sv.get("certificate_hash"),
                }
            )
            if ac_win:
                lines.append(
                    f"{cid}: {json.dumps(path,separators=(',',':'))}"
                )
            if stable_win:
                lines.append(
                    f"{sid}: {json.dumps(sp,separators=(',',':'))}"
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
            "ACC_FUTURE_QUOTIENT_V4_CASE",
            json.dumps(rec, sort_keys=True),
            flush=True,
        )

    (out / "results.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n"
    )
    (out / "candidate_batch.txt").write_text(
        "\n".join(lines) + ("\n" if lines else "")
    )

    failures = collections.Counter()
    for r in rows:
        failures.update(r.get("rollout_failure_histogram", {}))

    report = {
        "version": "acc-future-quotient-v4",
        "official_pin": OFFICIAL_PIN,
        "targets": len(rows),
        "strict_winning_targets": sum(bool(r.get("strict_win")) for r in rows),
        "candidate_rows": len(lines),
        "nodes_popped": sum(int(r.get("nodes_popped", 0)) for r in rows),
        "future_class_hits": sum(int(r.get("future_class_hits", 0)) for r in rows),
        "guarded_class_hits": sum(int(r.get("guarded_class_hits", 0)) for r in rows),
        "rollout_attempts": sum(int(r.get("rollout_attempts", 0)) for r in rows),
        "rollout_successes": sum(int(r.get("rollout_successes", 0)) for r in rows),
        "rollout_failure_histogram": dict(sorted(failures.items())),
        "claim_boundary": (
            "V4 composes V1 future signatures with the previously-qualified "
            "six-context finite-group projection. The product is search guidance "
            "only; policy steps are exact official moves and every emitted path "
            "requires exact Atlas/target completion plus pinned verifier replay."
        ),
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        "ACC_FUTURE_QUOTIENT_V4_SUMMARY",
        json.dumps(report, sort_keys=True),
    )


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--v2-index", required=True)
    b.add_argument("--out-guard-index", required=True)
    b.add_argument("--out-report", required=True)
    b.add_argument("--v3-dir")
    b.add_argument("--out-audit", default="fq4_separator_audit.json")
    b.add_argument("--progress-every", type=int, default=10000)
    b.add_argument("--total-cap", type=int, default=10000)
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("search")
    s.add_argument("--acc-root", required=True)
    s.add_argument("--atlas", required=True)
    s.add_argument("--v2-index", required=True)
    s.add_argument("--guard-index", required=True)
    s.add_argument("--snapshot-ac", required=True)
    s.add_argument("--snapshot-stable", required=True)
    s.add_argument("--targets", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--node-cap", type=int, default=120000)
    s.add_argument("--time-cap", type=float, default=1200.0)
    s.add_argument("--rollout-attempt-cap", type=int, default=2000)
    s.add_argument("--min-policy-purity", type=float, default=0.75)
    s.set_defaults(func=cmd_search)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
