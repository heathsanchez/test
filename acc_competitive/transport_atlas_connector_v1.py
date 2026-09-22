#!/usr/bin/env python3
import argparse, collections, json, sqlite3, sys
from pathlib import Path

TARGET = ((1,), (2,))
MAP = {-2: 1, -1: 2, 1: 3, 2: 4}
TRANSPORT = [16, 15]


def key_state(state):
    return bytes([MAP[x] for x in state[0]] + [0] + [MAP[x] for x in state[1]])


def snapshot_rows(path):
    snap = json.loads(Path(path).read_text())
    data = snap.get("data", snap)
    out = {}
    for row in data["items"]:
        cid = row.get("problemId") or row.get("challengeId")
        if cid:
            out[str(cid)] = row
    return out


def load_atlas(path):
    db = sqlite3.connect(path)
    dist = {bytes(k): int(d) for k, d in db.execute("SELECT state,distance FROM atlas")}
    return db, dist


def atlas_suffix(core, db, state, limit):
    s = state
    out = []
    seen = {s}
    for _ in range(max(0, limit)):
        if s == TARGET:
            return out
        row = db.execute("SELECT next_move FROM atlas WHERE state=?", (key_state(s),)).fetchone()
        if row is None or row[0] is None:
            return None
        move = int(row[0])
        out.append(move)
        s = core.apply_move(s, move)
        if s in seen:
            return None
        seen.add(s)
    return out if s == TARGET else None


def connect(core, initial, atlas_dist, db, ceiling, depth_limit, total_cap, node_cap):
    initial = tuple(tuple(w) for w in initial)
    q = collections.deque([(initial, 0, None)])
    parent = {initial: (None, None)}
    best = None
    nodes = 0

    while q and nodes < node_cap:
        state, depth, last = q.popleft()
        nodes += 1
        atlas_d = atlas_dist.get(key_state(state))
        if atlas_d is not None:
            total = depth + atlas_d
            if total < ceiling and (best is None or total < best[0]):
                best = (total, state, depth)

        if depth >= depth_limit:
            continue
        if best is not None and depth + 1 >= best[0]:
            continue

        for move in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last] == move:
                continue
            nxt = core.apply_move(state, move)
            if sum(map(len, nxt)) > total_cap or nxt in parent:
                continue
            parent[nxt] = (state, move)
            q.append((nxt, depth + 1, move))

    meta = {
        "nodes": nodes,
        "node_cap_hit": bool(q and nodes >= node_cap),
        "frontier": len(q),
        "radius_complete": not q,
        "connector_depth": depth_limit,
    }
    if best is None:
        return None, meta

    _, hit, prefix_len = best
    prefix = []
    state = hit
    while parent[state][0] is not None:
        prev, move = parent[state]
        prefix.append(move)
        state = prev
    prefix.reverse()

    suffix = atlas_suffix(core, db, hit, ceiling - len(prefix) + 1)
    if suffix is None:
        meta.update({"hit": True, "suffix_fail": True})
        return None, meta
    meta.update({
        "prefix": len(prefix),
        "suffix": len(suffix),
        "atlas_distance": len(suffix),
    })
    return prefix + suffix, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--atlas", required=True)
    ap.add_argument("--snapshot-ac", required=True)
    ap.add_argument("--snapshot-stable", required=True)
    ap.add_argument("--target-ids-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--connector-depth", type=int, default=4)
    ap.add_argument("--node-cap", type=int, default=250000)
    args = ap.parse_args()

    acc = Path(args.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    byid = {c["challenge_id"]: c for c in manifest["challenges"]}
    live_ac = snapshot_rows(args.snapshot_ac)
    live_stable = snapshot_rows(args.snapshot_stable)
    targets = json.loads(Path(args.target_ids_file).read_text())
    targets = [x["challenge_id"] if isinstance(x, dict) else str(x) for x in targets]

    db, atlas_dist = load_atlas(args.atlas)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    pending = []

    for cid in targets:
        if not cid.startswith("ac-") or cid not in byid:
            continue
        sid = "sac-" + cid[3:]
        if sid not in byid:
            continue
        ac_row = live_ac.get(cid, {})
        stable_row = live_stable.get(sid, {})
        ac_best = ac_row.get("currentBestLength")
        stable_best = stable_row.get("currentBestLength")
        if not isinstance(ac_best, int) or not isinstance(stable_best, int):
            continue
        if ac_row.get("status") != "solved" or stable_row.get("status") != "solved":
            continue

        # Source length L can publish to AC iff L < ac_best and to Stable-AC
        # iff L + 2 < stable_best. Search the union of those strict-win sets.
        source_bound_exclusive = max(ac_best, stable_best - len(TRANSPORT))
        if source_bound_exclusive <= 0:
            continue

        challenge = byid[cid]
        path, meta = connect(
            core,
            challenge["initial_relators"],
            atlas_dist,
            db,
            source_bound_exclusive,
            args.connector_depth,
            int(limits["max_total_relator_length"]),
            args.node_cap,
        )
        rec = {
            "challenge_id": cid,
            "stable_challenge_id": sid,
            "ac_incumbent": ac_best,
            "stable_incumbent": stable_best,
            "transport_cost": len(TRANSPORT),
            "transport_slack": stable_best - ac_best - len(TRANSPORT),
            "source_bound_exclusive": source_bound_exclusive,
            **meta,
        }

        if path is None:
            rec.update({
                "found": False,
                "ac_strict_win": False,
                "stable_strict_win": False,
                "strict_win": False,
                "obstruction": "node_cap" if meta["node_cap_hit"] else "exact_radius_exhausted",
            })
        else:
            verified = core.verify(challenge, path, challenge["move_spec_version"], limits)
            if not verified.get("ok"):
                raise RuntimeError(f"pinned AC verifier failed {cid}: {verified}")
            ac_win = len(path) < ac_best
            stable_path = path + TRANSPORT
            stable_win = len(stable_path) < stable_best
            stable_hash = None
            if stable_win:
                stable_challenge = byid[sid]
                stable_verified = stable_core.verify(
                    stable_challenge,
                    stable_path,
                    stable_challenge["move_spec_version"],
                    limits,
                )
                if not stable_verified.get("ok"):
                    raise RuntimeError(f"pinned Stable verifier failed {sid}: {stable_verified}")
                stable_hash = stable_verified.get("certificate_hash")

            rec.update({
                "found": True,
                "source_length": len(path),
                "stable_length": len(stable_path),
                "ac_strict_win": ac_win,
                "stable_strict_win": stable_win,
                "strict_win": ac_win or stable_win,
                "certificate_hash": verified.get("certificate_hash"),
                "stable_certificate_hash": stable_hash,
            })
            if ac_win:
                pending.append(f"{cid}: {json.dumps(path, separators=(',', ':'))}")
            if stable_win:
                pending.append(f"{sid}: {json.dumps(stable_path, separators=(',', ':'))}")

        rows.append(rec)
        print("TRANSPORT_CONNECTOR_CASE", json.dumps(rec, sort_keys=True))

    (out / "results.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    (out / "pending_submission.txt").write_text("\n".join(pending) + ("\n" if pending else ""))
    summary = {
        "targets": len(rows),
        "winning_targets": sum(bool(r.get("strict_win")) for r in rows),
        "ac_wins": sum(bool(r.get("ac_strict_win")) for r in rows),
        "stable_wins": sum(bool(r.get("stable_strict_win")) for r in rows),
        "exact_radius_exhausted": sum(r.get("obstruction") == "exact_radius_exhausted" for r in rows),
        "node_cap_hits": sum(r.get("obstruction") == "node_cap" for r in rows),
        "atlas_states": len(atlas_dist),
        "pending_rows": len(pending),
        "connector_depth": args.connector_depth,
        "node_cap": args.node_cap,
    }
    (out / "report.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("TRANSPORT_CONNECTOR_SUMMARY", json.dumps(summary, sort_keys=True))
    db.close()


if __name__ == "__main__":
    main()
