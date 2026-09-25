#!/usr/bin/env python3
"""
ACC Future Quotient V2.

Purpose
-------
Compile the existing verified Proof Atlas into a consequence-relative search
heuristic without enlarging the trusted certificate boundary.

The quotient is deliberately *not* an equality theory.  States are grouped by
observable structural consequences plus the same observations after each
official AC move.  Atlas distance and Atlas next-move data are used only as
labels on those groups.  Search may use the labels for ordering, but a
certificate is accepted only after an exact state joins the Proof Atlas and the
entire reconstructed path passes the pinned official verifier.

This gives a clean epistemic boundary:

  future quotient       -> search guidance only
  bounded exact bridge   -> reconciliation candidate
  exact Atlas suffix     -> executable continuation
  pinned verifier        -> warrant
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import sqlite3
import sys
import time
from pathlib import Path

from peephole_superopt_v1 import shorter_path

TARGET = ((1,), (2,))
MAP = {-2: 1, -1: 2, 1: 3, 2: 4}
UNMAP = {1: -2, 2: -1, 3: 1, 4: 2}
OFFICIAL_PIN = "99a65377c5c4f412cd9af7b8d31c41464a855736"


def key_state(s):
    return bytes([MAP[x] for x in s[0]] + [0] + [MAP[x] for x in s[1]])


def decode_state(k):
    b = bytes(k)
    j = b.index(0)
    return (
        tuple(UNMAP[x] for x in b[:j]),
        tuple(UNMAP[x] for x in b[j + 1 :]),
    )


def bucket(n):
    # Consequence-relative coarse scale.  These are representation buckets,
    # never proof claims.
    cuts = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32, 48, 64, 96, 128, 192)
    for i, c in enumerate(cuts):
        if n <= c:
            return i
    return len(cuts)


def distance_band(d):
    cuts = (0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048)
    for i, c in enumerate(cuts):
        if d <= c:
            return i
    return len(cuts)


def word_stats(w):
    ex = sum(1 if x == 1 else -1 if x == -1 else 0 for x in w)
    ey = sum(1 if x == 2 else -1 if x == -2 else 0 for x in w)
    turns = sum(1 for a, b in zip(w, w[1:]) if abs(a) != abs(b))
    signs = sum(1 for a, b in zip(w, w[1:]) if (a > 0) != (b > 0))
    return len(w), ex, ey, turns, signs


def free_face_profile(s):
    # Structural shadow of the separately-qualified recursive free-face law.
    # Record only occurrence geometry; this function does not claim the macro
    # is executable from the rank-2 AC state.
    out = []
    for g in (1, 2):
        for i in (0, 1):
            here = sum(abs(x) == g for x in s[i])
            other = sum(abs(x) == g for x in s[1 - i])
            if here == 1:
                out.append((g, i, bucket(other)))
    return tuple(out)


def singleton_profile(s):
    out = []
    for i, w in enumerate(s):
        if len(w) == 1:
            g = abs(w[0])
            other = sum(abs(x) == g for x in s[1 - i])
            out.append((i, g, 1 if w[0] > 0 else -1, bucket(other)))
    return tuple(out)


def terminal_class(s):
    if len(s) != 2 or any(len(w) != 1 for w in s):
        return 0
    vals = [w[0] for w in s]
    if sorted(abs(v) for v in vals) != [1, 2]:
        return 0
    # Signed-permutation terminal basin already qualified by the Stable
    # terminal compiler.  Keep orientation/sign as search information.
    return 1 + (0 if abs(vals[0]) == 1 else 4) + (1 if vals[0] < 0 else 0) + (2 if vals[1] < 0 else 0)


def base_tuple(s):
    a = word_stats(s[0])
    b = word_stats(s[1])
    total = a[0] + b[0]
    det = abs(a[1] * b[2] - a[2] * b[1])
    exp_l1 = abs(a[1]) + abs(a[2]) + abs(b[1]) + abs(b[2])
    ff = free_face_profile(s)
    sg = singleton_profile(s)

    # The tuple intentionally contains only cheap, exact observables already
    # meaningful under the qualified ACC/Stable experiments.
    vals = [
        bucket(total),
        bucket(a[0]),
        bucket(b[0]),
        bucket(abs(a[0] - b[0])),
        bucket(a[3] + b[3]),
        bucket(a[4] + b[4]),
        bucket(det),
        bucket(exp_l1),
        terminal_class(s),
        len(ff),
        len(sg),
    ]
    for rec in ff[:4]:
        vals.extend(rec)
    vals.append(255)
    for rec in sg[:2]:
        vals.extend(rec)
    return tuple(int(x) for x in vals)


def digest_parts(parts):
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, bytes):
            h.update(len(p).to_bytes(2, "little"))
            h.update(p)
        else:
            b = repr(p).encode()
            h.update(len(b).to_bytes(2, "little"))
            h.update(b)
    return h.digest()


def base_signature(s):
    return digest_parts((base_tuple(s),))


def future_signature(core, s, total_cap):
    b = base_signature(s)
    children = []
    for m in range(core.NUM_MOVES):
        n = core.apply_move(s, m)
        if sum(map(len, n)) > total_cap:
            children.append(b"X")
        else:
            children.append(base_signature(n))
    return digest_parts((b, *children)), children


def atlas_suffix(core, db, state, limit):
    s = state
    out = []
    seen = {s}
    for _ in range(max(0, limit)):
        if s == TARGET:
            return out
        row = db.execute(
            "SELECT next_move FROM atlas WHERE state=?", (key_state(s),)
        ).fetchone()
        if row is None or row[0] is None:
            return None
        m = int(row[0])
        out.append(m)
        s = core.apply_move(s, m)
        if s in seen:
            return None
        seen.add(s)
    return out if s == TARGET else None


def init_index(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA temp_store=MEMORY")
    db.executescript(
        """
        DROP TABLE IF EXISTS observations;
        DROP TABLE IF EXISTS base_classes;
        DROP TABLE IF EXISTS future_classes;
        DROP TABLE IF EXISTS future_policy;
        DROP TABLE IF EXISTS future_representatives;

        CREATE TABLE observations(
          state BLOB NOT NULL,
          base_sig BLOB NOT NULL,
          future_sig BLOB NOT NULL,
          distance INTEGER NOT NULL,
          distance_band INTEGER NOT NULL,
          next_move INTEGER
        );

        CREATE TABLE base_classes(
          signature BLOB PRIMARY KEY,
          n INTEGER NOT NULL,
          min_distance INTEGER NOT NULL,
          max_distance INTEGER NOT NULL,
          mean_distance REAL NOT NULL,
          band_count INTEGER NOT NULL
        );

        CREATE TABLE future_classes(
          signature BLOB PRIMARY KEY,
          n INTEGER NOT NULL,
          min_distance INTEGER NOT NULL,
          max_distance INTEGER NOT NULL,
          mean_distance REAL NOT NULL,
          band_count INTEGER NOT NULL,
          policy_move INTEGER,
          policy_purity REAL NOT NULL
        );

        CREATE TABLE future_policy(
          signature BLOB NOT NULL,
          move INTEGER NOT NULL,
          n INTEGER NOT NULL,
          PRIMARY KEY(signature,move)
        );

        CREATE TABLE future_representatives(
          signature BLOB NOT NULL,
          state BLOB NOT NULL,
          distance INTEGER NOT NULL,
          next_move INTEGER,
          rep_rank INTEGER NOT NULL,
          PRIMARY KEY(signature,rep_rank)
        );
        """
    )
    db.commit()
    return db


def build_index(core, atlas_path, out_db, total_cap, progress_every=10000):
    adb = sqlite3.connect(atlas_path)
    qdb = init_index(out_db)
    rows = adb.execute("SELECT state,distance,next_move FROM atlas ORDER BY distance,state")
    batch = []
    n = 0
    t0 = time.time()

    for k, d, nm in rows:
        s = decode_state(k)
        bs = base_signature(s)
        fs, _ = future_signature(core, s, total_cap)
        batch.append((bytes(k), bs, fs, int(d), distance_band(int(d)), None if nm is None else int(nm)))
        n += 1
        if len(batch) >= 2000:
            qdb.executemany("INSERT INTO observations VALUES(?,?,?,?,?,?)", batch)
            qdb.commit()
            batch.clear()
        if progress_every and n % progress_every == 0:
            print(
                "FQ_BUILD_PROGRESS",
                json.dumps({"states": n, "seconds": round(time.time() - t0, 2)}, sort_keys=True),
                flush=True,
            )
    if batch:
        qdb.executemany("INSERT INTO observations VALUES(?,?,?,?,?,?)", batch)
        qdb.commit()

    qdb.executescript(
        """
        CREATE INDEX obs_base ON observations(base_sig);
        CREATE INDEX obs_future ON observations(future_sig);
        CREATE INDEX obs_future_distance ON observations(future_sig,distance);

        INSERT INTO base_classes
        SELECT base_sig,COUNT(*),MIN(distance),MAX(distance),AVG(distance),COUNT(DISTINCT distance_band)
        FROM observations GROUP BY base_sig;

        INSERT INTO future_policy
        SELECT future_sig,next_move,COUNT(*)
        FROM observations
        WHERE next_move IS NOT NULL
        GROUP BY future_sig,next_move;

        CREATE TEMP TABLE policy_mode AS
        SELECT signature,move,n,total FROM (
          SELECT signature,move,n,
                 SUM(n) OVER (PARTITION BY signature) AS total,
                 ROW_NUMBER() OVER (PARTITION BY signature ORDER BY n DESC,move ASC) AS rn
          FROM future_policy
        ) WHERE rn=1;

        INSERT INTO future_classes
        SELECT o.future_sig,
               COUNT(*),
               MIN(o.distance),
               MAX(o.distance),
               AVG(o.distance),
               COUNT(DISTINCT o.distance_band),
               pm.move,
               COALESCE(1.0*pm.n/pm.total,0.0)
        FROM observations o
        LEFT JOIN policy_mode pm ON pm.signature=o.future_sig
        GROUP BY o.future_sig;

        INSERT INTO future_representatives
        SELECT future_sig,state,distance,next_move,rn FROM (
          SELECT future_sig,state,distance,next_move,
                 ROW_NUMBER() OVER (
                   PARTITION BY future_sig
                   ORDER BY distance ASC,state ASC
                 ) AS rn
          FROM observations
        ) WHERE rn<=8;
        """
    )
    qdb.commit()

    base_classes = qdb.execute("SELECT COUNT(*) FROM base_classes").fetchone()[0]
    future_classes = qdb.execute("SELECT COUNT(*) FROM future_classes").fetchone()[0]
    base_pure_states = qdb.execute(
        "SELECT COALESCE(SUM(n),0) FROM base_classes WHERE band_count=1"
    ).fetchone()[0]
    future_pure_states = qdb.execute(
        "SELECT COALESCE(SUM(n),0) FROM future_classes WHERE band_count=1"
    ).fetchone()[0]
    policy_rows = qdb.execute(
        "SELECT n,policy_purity FROM future_classes WHERE policy_move IS NOT NULL"
    ).fetchall()
    policy_weight = sum(n for n, _ in policy_rows)
    policy_purity = (
        sum(n * p for n, p in policy_rows) / policy_weight if policy_weight else 0.0
    )
    strong_policy_states = sum(n for n, p in policy_rows if p >= 0.75)
    split_base_classes = qdb.execute(
        """
        SELECT COUNT(*) FROM (
          SELECT base_sig,COUNT(DISTINCT future_sig) c
          FROM observations GROUP BY base_sig HAVING c>1
        )
        """
    ).fetchone()[0]

    report = {
        "version": "acc-future-quotient-v2",
        "status": "CANDIDATE_REPRESENTATION",
        "trusted_boundary": "future classes guide search only; bounded bridges are exact official moves; exact Atlas suffix plus pinned verifier remain authoritative",
        "official_pin": OFFICIAL_PIN,
        "atlas_states": n,
        "base_classes": base_classes,
        "future_classes": future_classes,
        "base_classes_split_by_future": split_base_classes,
        "base_distance_band_pure_state_fraction": base_pure_states / n if n else 0.0,
        "future_distance_band_pure_state_fraction": future_pure_states / n if n else 0.0,
        "distance_band_purity_gain": (future_pure_states - base_pure_states) / n if n else 0.0,
        "weighted_policy_purity": policy_purity,
        "strong_policy_state_fraction": strong_policy_states / n if n else 0.0,
        "build_seconds": round(time.time() - t0, 3),
    }
    adb.close()
    qdb.close()
    return report


def load_index(index_path):
    db = sqlite3.connect(index_path)
    base = {
        bytes(sig): (int(n), int(mind), int(maxd), float(avgd), int(bands))
        for sig, n, mind, maxd, avgd, bands in db.execute(
            "SELECT signature,n,min_distance,max_distance,mean_distance,band_count FROM base_classes"
        )
    }
    future = {
        bytes(sig): (
            int(n),
            int(mind),
            int(maxd),
            float(avgd),
            int(bands),
            None if pm is None else int(pm),
            float(pp),
        )
        for sig, n, mind, maxd, avgd, bands, pm, pp in db.execute(
            "SELECT signature,n,min_distance,max_distance,mean_distance,band_count,policy_move,policy_purity FROM future_classes"
        )
    }
    policies = {}
    for sig, move, n in db.execute(
        "SELECT signature,move,n FROM future_policy ORDER BY signature,n DESC,move ASC"
    ):
        policies.setdefault(bytes(sig), []).append((int(move), int(n)))
    reps = {}
    for sig, state, distance, next_move, rep_rank in db.execute(
        "SELECT signature,state,distance,next_move,rep_rank FROM future_representatives ORDER BY signature,rep_rank"
    ):
        reps.setdefault(bytes(sig), []).append(
            (bytes(state), int(distance), None if next_move is None else int(next_move), int(rep_rank))
        )
    db.close()
    return base, future, policies, reps


def reconstruct_prefix(parent, goal_key):
    out = []
    k = goal_key
    while parent[k][0] is not None:
        prev, m = parent[k]
        out.append(m)
        k = prev
    out.reverse()
    return out


def search_target(
    core,
    challenge,
    atlas_path,
    index_path,
    bound_exclusive,
    total_cap,
    node_cap,
    time_cap,
    max_bridge,
    reps_per_class,
    bridge_attempt_cap,
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
            # Unknown future region: not forbidden, merely lower priority.
            return 256.0, 0
        return float(info[1]), info[0]

    h0, _ = base_h(initial)
    pq = [(h0, 0, sum(map(len, initial)), serial, key_state(initial), None)]
    serial += 1

    popped = generated = exact_hits = future_hits = policy_hits = 0
    bridge_eligible = bridge_attempts = bridge_successes = 0
    best_seen_future = None
    separator_examples = []
    bridge_cache = {}
    t0 = time.time()
    candidate = None
    candidate_meta = None

    while pq and popped < node_cap and time.time() - t0 < time_cap:
        _, g, _, _, k, last = heapq.heappop(pq)
        if g != best_g.get(k):
            continue
        s = states[k]
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
                suffix = atlas_suffix(core, adb, s, bound_exclusive - len(prefix) + 8)
                if suffix is not None:
                    candidate = prefix + suffix
                    candidate_meta = {
                        "join_depth": g,
                        "atlas_suffix": len(suffix),
                        "atlas_distance": ad,
                        "exact_join_state": k.hex(),
                    }
                    break

        fs, children_base = future_signature(core, s, total_cap)
        finfo = future_idx.get(fs)
        move_order = list(range(core.NUM_MOVES))
        if finfo is not None:
            future_hits += 1
            best_seen_future = finfo[1] if best_seen_future is None else min(best_seen_future, finfo[1])

            # V2 residual: exact reconciliation inside a future class.
            # Quotient membership itself is never treated as equality.
            if bridge_attempts < bridge_attempt_cap:
                for rep_key, rep_distance, _, rep_rank in representatives.get(fs, ())[:reps_per_class]:
                    max_fit = bound_exclusive - 1 - g - rep_distance
                    if max_fit <= 0:
                        continue
                    bridge_limit = min(max_bridge, max_fit)
                    if bridge_limit <= 0:
                        continue
                    bridge_eligible += 1
                    ck = (k, rep_key, bridge_limit)
                    if ck in bridge_cache:
                        bridge = bridge_cache[ck]
                    else:
                        bridge_attempts += 1
                        rep_state = decode_state(rep_key)
                        bridge = shorter_path(core, s, rep_state, bridge_limit, total_cap)
                        bridge_cache[ck] = bridge
                    if bridge is None:
                        if len(separator_examples) < 64:
                            separator_examples.append({
                                "future_sig": fs.hex(),
                                "query_state": k.hex(),
                                "query_depth": g,
                                "representative_state": rep_key.hex(),
                                "representative_distance": rep_distance,
                                "representative_rank": rep_rank,
                                "bridge_limit": bridge_limit,
                            })
                        if bridge_attempts >= bridge_attempt_cap:
                            break
                        continue

                    bridge_successes += 1
                    rep_state = decode_state(rep_key)
                    suffix = atlas_suffix(core, adb, rep_state, rep_distance + 8)
                    if suffix is None:
                        raise RuntimeError("future representative lacks executable Atlas suffix")
                    prefix = reconstruct_prefix(parent, k)
                    cand = prefix + list(bridge) + suffix
                    if len(cand) >= bound_exclusive:
                        raise RuntimeError(("bridge candidate violates frozen bound", len(cand), bound_exclusive))
                    candidate = cand
                    candidate_meta = {
                        "join_kind": "future_class_exact_bridge",
                        "future_sig": fs.hex(),
                        "join_depth": g,
                        "bridge_length": len(bridge),
                        "bridge": list(bridge),
                        "atlas_representative_state": rep_key.hex(),
                        "atlas_representative_rank": rep_rank,
                        "atlas_suffix": len(suffix),
                        "atlas_distance": rep_distance,
                    }
                    break
                if candidate is not None:
                    break

            pol = policies.get(fs, [])
            if pol:
                policy_hits += 1
                ranked = [m for m, _ in pol]
                move_order = ranked + [m for m in move_order if m not in set(ranked)]

        for m in move_order:
            if last is not None and core.INVERSE_MOVE[last] == m:
                continue
            n = core.apply_move(s, m)
            generated += 1
            if sum(map(len, n)) > total_cap:
                continue
            ng = g + 1
            if ng >= bound_exclusive:
                continue
            nk = key_state(n)
            if ng >= best_g.get(nk, 10**18):
                continue
            best_g[nk] = ng
            parent[nk] = (k, m)
            states[nk] = n
            binfo = base_idx.get(children_base[m])
            qh = float(binfo[1]) if binfo is not None else 256.0
            # Heuristic is ordering only; no pruning depends on qh.
            pri = ng + qh
            heapq.heappush(
                pq, (pri, ng, sum(map(len, n)), serial, nk, m)
            )
            serial += 1

    status = (
        "FOUND_EXACT_ATLAS_JOIN"
        if candidate is not None
        else "UNKNOWN_NODE_CAP"
        if popped >= node_cap
        else "UNKNOWN_TIME_CAP"
        if time.time() - t0 >= time_cap
        else "NO_JOIN_IN_EXPLORED_SCOPE"
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
        "bridge_eligible_contacts": bridge_eligible,
        "bridge_attempts": bridge_attempts,
        "bridge_successes": bridge_successes,
        "separator_examples": separator_examples,
        "best_seen_future_min_distance": best_seen_future,
        "seconds": round(time.time() - t0, 3),
        "bound_exclusive": bound_exclusive,
        "node_cap": node_cap,
        "time_cap": time_cap,
    }
    if candidate_meta:
        meta.update(candidate_meta)
    adb.close()
    return candidate, meta


def snapshot_rows(path):
    obj = json.loads(Path(path).read_text())
    d = obj.get("data", obj)
    return {
        str(x.get("problemId") or x.get("challengeId")): x
        for x in d["items"]
        if x.get("problemId") or x.get("challengeId")
    }


def cmd_build(a):
    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core

    manifest = json.loads(
        (acc / "competition/tools/verifier/data/manifest.json").read_text()
    )
    limits = manifest["limits"]
    report = build_index(
        core,
        a.atlas,
        a.out_index,
        int(limits["max_total_relator_length"]),
        a.progress_every,
    )
    Path(a.out_report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("ACC_FUTURE_QUOTIENT_BUILD", json.dumps(report, sort_keys=True))


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

        # Strict source bound: L < max(AC_best, Stable_best-2).
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
            a.max_bridge,
            a.reps_per_class,
            a.bridge_attempt_cap,
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
                raise RuntimeError(f"Future quotient reconstruction failed AC verifier {cid}: {v}")
            stable_path = list(path) + [16, 15]
            sv = stable_core.verify(sc, stable_path, sc["move_spec_version"], limits)
            if not sv.get("ok"):
                raise RuntimeError(f"Future quotient lift failed Stable verifier {sid}: {sv}")

            ac_win = len(path) < ab
            stable_win = len(stable_path) < sb
            rec.update(
                {
                    "source_length": len(path),
                    "stable_length": len(stable_path),
                    "ac_strict_win": ac_win,
                    "stable_strict_win": stable_win,
                    "strict_win": ac_win or stable_win,
                    "certificate_hash": v.get("certificate_hash"),
                    "stable_certificate_hash": sv.get("certificate_hash"),
                }
            )
            if ac_win:
                lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
            if stable_win:
                lines.append(f"{sid}: {json.dumps(stable_path,separators=(',',':'))}")
        else:
            rec.update(
                {
                    "ac_strict_win": False,
                    "stable_strict_win": False,
                    "strict_win": False,
                }
            )
        rows.append(rec)
        print("ACC_FUTURE_QUOTIENT_CASE", json.dumps(rec, sort_keys=True), flush=True)

    (out / "results.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    (out / "candidate_batch.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
    report = {
        "version": "acc-future-quotient-v2",
        "official_pin": OFFICIAL_PIN,
        "targets": len(rows),
        "found_exact_joins": sum(bool(r.get("found")) for r in rows),
        "strict_winning_targets": sum(bool(r.get("strict_win")) for r in rows),
        "ac_wins": sum(bool(r.get("ac_strict_win")) for r in rows),
        "stable_wins": sum(bool(r.get("stable_strict_win")) for r in rows),
        "candidate_rows": len(lines),
        "nodes_popped": sum(int(r.get("nodes_popped", 0)) for r in rows),
        "future_class_hits": sum(int(r.get("future_class_hits", 0)) for r in rows),
        "policy_class_hits": sum(int(r.get("policy_class_hits", 0)) for r in rows),
        "bridge_eligible_contacts": sum(int(r.get("bridge_eligible_contacts", 0)) for r in rows),
        "bridge_attempts": sum(int(r.get("bridge_attempts", 0)) for r in rows),
        "bridge_successes": sum(int(r.get("bridge_successes", 0)) for r in rows),
        "claim_boundary": "Future quotient and learned policy are search-order heuristics only. V2 reconciles class contacts only through bounded exact official-move bridges to exact Atlas representatives; every emitted row is replayed by the pinned official verifier.",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("ACC_FUTURE_QUOTIENT_SUMMARY", json.dumps(report, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--acc-root", required=True)
    b.add_argument("--atlas", required=True)
    b.add_argument("--out-index", required=True)
    b.add_argument("--out-report", required=True)
    b.add_argument("--progress-every", type=int, default=10000)
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("search")
    s.add_argument("--acc-root", required=True)
    s.add_argument("--atlas", required=True)
    s.add_argument("--index", required=True)
    s.add_argument("--snapshot-ac", required=True)
    s.add_argument("--snapshot-stable", required=True)
    s.add_argument("--targets", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--node-cap", type=int, default=120000)
    s.add_argument("--time-cap", type=float, default=1200.0)
    s.add_argument("--max-bridge", type=int, default=4)
    s.add_argument("--reps-per-class", type=int, default=4)
    s.add_argument("--bridge-attempt-cap", type=int, default=2000)
    s.set_defaults(func=cmd_search)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
