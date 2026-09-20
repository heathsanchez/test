#!/usr/bin/env python3
import argparse, collections, json, sqlite3
from pathlib import Path

from atlas_product_guided_bridge_v1 import TARGET, atlas_suffix, decode_state, move


def tail_search(start, atlas, max_depth):
    if start in atlas:
        return (), start, 1
    q = collections.deque([(start, ())])
    seen = {start}
    nodes = 0
    while q:
        s, path = q.popleft()
        nodes += 1
        if len(path) >= max_depth:
            continue
        for m in range(14):
            z = move(s, m)
            if z in seen:
                continue
            np = path + (m,)
            if z in atlas:
                return np, z, nodes
            seen.add(z)
            q.append((z, np))
    return None, None, nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--acc-root', required=True)
    ap.add_argument('--atlas', required=True)
    ap.add_argument('--fiber-rows', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--max-total-depth', type=int, default=7)
    ap.add_argument('--prior-exact-depth', type=int, default=5)
    a = ap.parse_args()

    manifest = json.loads((Path(a.acc_root) / 'competition/tools/verifier/data/manifest.json').read_text())
    byid = {c['challenge_id']: c for c in manifest['challenges']}
    rows = json.loads(Path(a.fiber_rows).read_text())

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

    for i, r in enumerate(rows, 1):
        cid = r['challenge_id']
        witness = tuple(int(x) for x in (r.get('witness_moves') or []))
        if not witness:
            continue
        if len(witness) > a.max_total_depth:
            continue
        ch = byid[cid]
        initial = (tuple(ch['initial_relators'][0]), tuple(ch['initial_relators'][1]))
        endpoint = initial
        for m in witness:
            endpoint = move(endpoint, m)

        tail_cap = a.max_total_depth - len(witness)
        tail, hit, nodes = tail_search(endpoint, meta, tail_cap)
        total_nodes += nodes
        rec = {
            'challenge_id': cid,
            'refined_product_distance': r.get('refined_product_distance'),
            'witness_moves': list(witness),
            'tail_cap': tail_cap,
            'tail_nodes': nodes,
            'fiber_repair_bridge': tail is not None,
        }
        if tail is not None:
            prefix = list(witness) + list(tail)
            if len(prefix) <= a.prior_exact_depth:
                raise RuntimeError(f'prior exact-depth contradiction on {cid}: bridge at {len(prefix)}')
            suffix = atlas_suffix(hit, meta)
            moves = prefix + suffix
            rec.update({
                'tail_moves': list(tail),
                'prefix_length': len(prefix),
                'atlas_hit_distance': meta[hit][0],
                'atlas_source': meta[hit][2],
                'suffix_moves': suffix,
                'moves': moves,
                'length': len(moves),
            })
            candidates.append(rec)
            print('FIBER_REPAIR_CANDIDATE', json.dumps(rec, sort_keys=True))
        results.append(rec)
        if i % 5 == 0 or i == len(rows):
            print('FIBER_REPAIR_PROGRESS', json.dumps({
                'done': i, 'targets': len(rows), 'tail_nodes': total_nodes,
                'candidates': len(candidates),
            }, sort_keys=True))

    (out / 'candidates.txt').write_text(''.join(
        f"{x['challenge_id']}: {json.dumps(x['moves'], separators=(',', ':'))}\n"
        for x in candidates
    ))
    report = {
        'version': 'atlas-fiber-witness-tail-v1',
        'read_only': True,
        'atlas_states': len(meta),
        'max_total_depth': a.max_total_depth,
        'prior_exact_depth': a.prior_exact_depth,
        'targets': len(results),
        'tail_nodes': total_nodes,
        'candidates': len(candidates),
        'candidate_rows': candidates,
        'rows': results,
        'note': 'New mechanism after certified exact depth-5 exhaustion: follow each refined quotient witness exactly, then search only the short residual fiber tail needed to reach total prefix depth at most 7. This does not repeat global exact depth<=5 BFS.',
    }
    (out / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('FIBER_REPAIR_SUMMARY', json.dumps({
        k: report[k] for k in ('atlas_states','max_total_depth','prior_exact_depth','targets','tail_nodes','candidates')
    }, sort_keys=True))


if __name__ == '__main__':
    main()
