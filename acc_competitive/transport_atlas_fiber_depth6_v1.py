#!/usr/bin/env python3
import argparse, json, sqlite3, sys
from pathlib import Path

from atlas_product_guided_bridge_v1 import TARGET, atlas_suffix, decode_state, move
from atlas_fiber_shortest_dag_v1 import contexts, qproject, exact_lift
from atlas_fiber_slack6_v1 import layered_dag

TRANSPORT = [16, 15]
ATLAS_STATES = 433272
OFFICIAL_PIN = "99a65377c5c4f412cd9af7b8d31c41464a855736"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc-root", required=True)
    ap.add_argument("--atlas", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--target-ids-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--depth", type=int, default=6)
    a = ap.parse_args()
    if a.depth != 6:
        raise RuntimeError("V1 is qualified only for exact depth 6")

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from acc_competitive import finite_group_pdb_v1 as fg

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    byid = {c["challenge_id"]: c for c in manifest["challenges"]}

    rows = json.loads(Path(a.rows).read_text())
    if not isinstance(rows, list):
        raise RuntimeError("rows must be a JSON list")
    row_by_id = {str(r.get("challenge_id")): r for r in rows if r.get("challenge_id")}
    ids_raw = json.loads(Path(a.target_ids_file).read_text())
    ids = [str(x.get("challenge_id")) if isinstance(x, dict) else str(x) for x in ids_raw]
    if not ids or any(cid not in row_by_id for cid in ids):
        raise RuntimeError("target shard is not a subset of frozen transport rows")

    db = sqlite3.connect(a.atlas)
    meta = {}
    for state, d, nm, source in db.execute("select state,distance,next_move,source from atlas"):
        meta[decode_state(state)] = (int(d), None if nm is None else int(nm), source)
    db.close()
    if len(meta) != ATLAS_STATES or TARGET not in meta or meta[TARGET][0] != 0:
        raise RuntimeError(f"Atlas invariant failed: {len(meta)} states")
    checked = 0
    for s, (d, nm, _) in meta.items():
        if d <= 0:
            continue
        if nm is None:
            raise RuntimeError("non-root Atlas state missing next_move")
        z = move(s, nm)
        if z not in meta or meta[z][0] >= d:
            raise RuntimeError("Atlas next_move is not descending")
        checked += 1
        if checked >= 10000:
            break
    print("ATLAS_DESCENT_VALIDATED", json.dumps({"checked": checked, "states": len(meta)}, sort_keys=True))

    ctxs = contexts(fg)
    sources = {qproject(fg, s, ctxs) for s in meta}
    print("TRANSPORT_FIBER_ATLAS", json.dumps({
        "atlas_states": len(meta),
        "projected_signatures": len(sources),
        "contexts": [x[0] for x in ctxs],
        "depth": a.depth,
    }, sort_keys=True))

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    pending = []

    for i, cid in enumerate(ids, 1):
        r = row_by_id[cid]
        sid = str(r.get("stable_challenge_id") or ("sac-" + cid[3:]))
        if cid not in byid or sid not in byid:
            raise RuntimeError(f"manifest missing target pair {cid}/{sid}")
        ac_best = int(r["ac_best"])
        stable_best = int(r["stable_best"])
        source_bound_exclusive = max(ac_best, stable_best - len(TRANSPORT))

        ch = byid[cid]
        initial = (tuple(ch["initial_relators"][0]), tuple(ch["initial_relators"][1]))
        start = qproject(fg, initial, ctxs)
        layers, viable, expanded, reverse_checks = layered_dag(fg, start, sources, ctxs, a.depth)
        terminal = len(viable[-1])
        if terminal:
            hits, exact_counts = exact_lift(initial, fg, ctxs, viable, meta)
        else:
            hits, exact_counts = [], [1]

        completed = []
        for hit, prefix in hits:
            suffix = atlas_suffix(hit, meta)
            moves = list(prefix) + suffix
            completed.append((len(moves), moves, hit, prefix, suffix))
        completed.sort(key=lambda x: x[0])

        rec = {
            "challenge_id": cid,
            "stable_challenge_id": sid,
            "ac_incumbent": ac_best,
            "stable_incumbent": stable_best,
            "transport_cost": len(TRANSPORT),
            "transport_slack": stable_best - ac_best - len(TRANSPORT),
            "source_bound_exclusive": source_bound_exclusive,
            "depth": a.depth,
            "quotient_exact_length_layer_sizes": [len(x) for x in layers],
            "quotient_slack_dag_sizes": [len(x) for x in viable],
            "quotient_terminal_atlas_signatures": terminal,
            "quotient_expanded": expanded,
            "quotient_reverse_checks": reverse_checks,
            "exact_lift_layer_sizes": exact_counts,
            "exact_atlas_hits": len(hits),
            "found": bool(completed),
            "strict_win": False,
            "ac_strict_win": False,
            "stable_strict_win": False,
        }

        if not completed:
            rec["obstruction"] = "fiber_depth6_exhausted"
            print("TRANSPORT_FIBER_DEPTH6_EXHAUSTED", json.dumps({
                "challenge_id": cid,
                "terminal_quotient_signatures": terminal,
                "exact_lift_layer_sizes": exact_counts,
            }, sort_keys=True))
        else:
            length, moves, hit, prefix, suffix = completed[0]
            verified = core.verify(ch, moves, ch["move_spec_version"], limits)
            if not verified.get("ok"):
                raise RuntimeError(f"pinned AC verifier failed {cid}: {verified}")
            ac_win = length < ac_best
            stable_moves = moves + TRANSPORT
            stable_win = len(stable_moves) < stable_best
            stable_hash = None
            if stable_win:
                sch = byid[sid]
                sv = stable_core.verify(sch, stable_moves, sch["move_spec_version"], limits)
                if not sv.get("ok"):
                    raise RuntimeError(f"pinned Stable verifier failed {sid}: {sv}")
                stable_hash = sv.get("certificate_hash")
            rec.update({
                "source_length": length,
                "stable_length": len(stable_moves),
                "prefix_moves": list(prefix),
                "prefix_length": len(prefix),
                "atlas_hit_distance": meta[hit][0],
                "atlas_source": meta[hit][2],
                "suffix_moves": suffix,
                "moves": moves,
                "certificate_hash": verified.get("certificate_hash"),
                "stable_certificate_hash": stable_hash,
                "ac_strict_win": ac_win,
                "stable_strict_win": stable_win,
                "strict_win": ac_win or stable_win,
            })
            if ac_win:
                pending.append(f"{cid}: {json.dumps(moves, separators=(',', ':'))}")
            if stable_win:
                pending.append(f"{sid}: {json.dumps(stable_moves, separators=(',', ':'))}")
            if not (ac_win or stable_win):
                rec["obstruction"] = "noncompetitive_depth6_hit"
            print("TRANSPORT_FIBER_EXACT_HIT", json.dumps({
                "challenge_id": cid,
                "source_length": length,
                "ac_strict_win": ac_win,
                "stable_strict_win": stable_win,
                "atlas_source": meta[hit][2],
            }, sort_keys=True))

        results.append(rec)
        print("TRANSPORT_FIBER_PROGRESS", json.dumps({"done": i, "targets": len(ids), "pending_rows": len(pending)}, sort_keys=True))

    (out / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (out / "pending_submission.txt").write_text("\n".join(pending) + ("\n" if pending else ""))
    report = {
        "version": "transport-atlas-fiber-depth6-v1",
        "read_only": True,
        "official_pin": OFFICIAL_PIN,
        "atlas_states": len(meta),
        "contexts": [x[0] for x in ctxs],
        "depth": a.depth,
        "targets": len(results),
        "candidates": sum(bool(r.get("found")) for r in results),
        "winning_targets": sum(bool(r.get("strict_win")) for r in results),
        "ac_wins": sum(bool(r.get("ac_strict_win")) for r in results),
        "stable_wins": sum(bool(r.get("stable_strict_win")) for r in results),
        "fiber_depth6_exhausted": sum(r.get("obstruction") == "fiber_depth6_exhausted" for r in results),
        "pending_rows": len(pending),
        "rows": results,
        "claim": "For each frozen positive-transport-slack target, every exact six-move bridge into the Proof Atlas must project to an exact-length six-context quotient path ending in an Atlas signature. The layered quotient DAG retains revisits and detours and every exact lift of its Atlas-reaching portion is exhausted.",
        "reuse_rule": "Do not repeat this exact depth-6 six-context fiber mechanism for rows certified exhausted against the same 433272-state Atlas."
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("TRANSPORT_FIBER_SUMMARY", json.dumps({k: report[k] for k in (
        "targets", "candidates", "winning_targets", "ac_wins", "stable_wins", "fiber_depth6_exhausted", "pending_rows"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
