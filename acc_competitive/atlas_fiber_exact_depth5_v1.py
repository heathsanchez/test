#!/usr/bin/env python3
import argparse, json, sqlite3
from collections import Counter
from pathlib import Path

from atlas_product_guided_bridge_v1 import (
    TARGET, atlas_suffix, decode_state, move, search,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--acc-root', required=True)
    ap.add_argument('--atlas', required=True)
    ap.add_argument('--fiber-rows', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--max-depth', type=int, default=5)
    a = ap.parse_args()

    manifest = json.loads((Path(a.acc_root) / 'competition/tools/verifier/data/manifest.json').read_text())
    byid = {c['challenge_id']: c for c in manifest['challenges']}
    rows = json.loads(Path(a.fiber_rows).read_text())
    targets = [
        r for r in rows
        if isinstance(r.get('refined_product_distance'), int)
        and r['refined_product_distance'] <= a.max_depth
    ]

    db = sqlite3.connect(a.atlas)
    meta = {}
    for state, d, nm, source in db.execute('select state,distance,next_move,source from atlas'):
        meta[decode_state(state)] = (int(d), None if nm is None else int(nm), source)
    db.close()
    if TARGET not in meta or meta[TARGET][0] != 0:
        raise RuntimeError('Atlas target/root invariant failed')

    checked = 0
    for s, (d, nm, _) in meta.items():
        if d <= 0:
            continue
        if nm is None:
            raise RuntimeError('non-root Atlas state missing next_move')
        z = move(s, nm)
        if z not in meta or meta[z][0] >= d:
            raise RuntimeError('Atlas descent semantics failed')
        checked += 1
        if checked >= 10000:
            break
    print('ATLAS_DESCENT_VALIDATED', json.dumps({'checked': checked, 'states': len(meta)}, sort_keys=True))

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results, candidates = [], []
    total_nodes = 0
    direct_witness_lifts = 0

    for i, r in enumerate(targets, 1):
        cid = r['challenge_id']
        ch = byid[cid]
        initial = (tuple(ch['initial_relators'][0]), tuple(ch['initial_relators'][1]))

        witness = tuple(int(x) for x in (r.get('witness_moves') or []))
        ws = initial
        for m in witness:
            ws = move(ws, m)
        direct = bool(witness) and ws in meta
        if direct:
            direct_witness_lifts += 1
            prefix, hit, nodes = witness, ws, 0
        else:
            prefix, hit, nodes = search(initial, meta, a.max_depth)
        total_nodes += nodes

        rec = {
            'challenge_id': cid,
            'refined_product_distance': r.get('refined_product_distance'),
            'old_product_distance': r.get('old_product_distance'),
            'quotient_witness_moves': list(witness),
            'direct_quotient_witness_lift': direct,
            'exact_nodes': nodes,
            'exact_bridge': prefix is not None,
        }
        if prefix is not None:
            suffix = atlas_suffix(hit, meta)
            moves = list(prefix) + suffix
            rec.update({
                'prefix_moves': list(prefix),
                'atlas_hit_distance': meta[hit][0],
                'atlas_source': meta[hit][2],
                'suffix_moves': suffix,
                'moves': moves,
                'length': len(moves),
            })
            candidates.append(rec)
            print('FIBER_EXACT_CANDIDATE', json.dumps(rec, sort_keys=True))
        results.append(rec)
        if i % 5 == 0 or i == len(targets):
            print('FIBER_EXACT_PROGRESS', json.dumps({
                'done': i, 'targets': len(targets), 'nodes': total_nodes,
                'direct_witness_lifts': direct_witness_lifts,
                'candidates': len(candidates),
            }, sort_keys=True))

    (out / 'candidates.txt').write_text(''.join(
        f"{x['challenge_id']}: {json.dumps(x['moves'], separators=(',', ':'))}\n"
        for x in candidates
    ))
    hist = Counter(str(r.get('refined_product_distance')) for r in targets)
    report = {
        'version': 'atlas-fiber-exact-depth5-v1',
        'read_only': True,
        'atlas_states': len(meta),
        'max_depth': a.max_depth,
        'targets': len(targets),
        'target_histogram': dict(sorted(hist.items())),
        'exact_nodes': total_nodes,
        'direct_quotient_witness_lifts': direct_witness_lifts,
        'candidates': len(candidates),
        'candidate_rows': candidates,
        'rows': results,
        'claim_if_zero_candidates': 'For every searched row, exhaustive exact official-move BFS has no Proof-Atlas intersection through depth 5; combined with the certified radius-4 cohort evidence, these rows are exact-Atlas-distance at least 6 against this Atlas snapshot.',
    }
    (out / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('FIBER_EXACT_SUMMARY', json.dumps({
        k: report[k] for k in ('atlas_states', 'max_depth', 'targets', 'target_histogram', 'exact_nodes', 'direct_quotient_witness_lifts', 'candidates')
    }, sort_keys=True))


if __name__ == '__main__':
    main()
