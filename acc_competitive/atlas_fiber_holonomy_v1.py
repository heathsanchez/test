#!/usr/bin/env python3
import argparse, collections, json, sqlite3, sys
from pathlib import Path

from atlas_product_guided_bridge_v1 import (
    TARGET, atlas_suffix, decode_state, move, quotient_contexts, qproject, qstep,
)


def quotient_witness(fg, start, sources, ctxs, max_depth):
    if start in sources:
        return (), 1
    q = collections.deque([(start, ())])
    seen = {start}
    nodes = 0
    while q:
        s, path = q.popleft()
        nodes += 1
        if len(path) >= max_depth:
            continue
        for m in range(14):
            z = qstep(fg, s, m, ctxs)
            if z in seen:
                continue
            np = path + (m,)
            if z in sources:
                return np, nodes
            seen.add(z)
            q.append((z, np))
    return None, nodes


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


def fiber_alternatives(fg, exact_start, q_start, ctxs, radius, cap):
    """Find distinct exact lifts in the same refined quotient fiber via short loops."""
    q = collections.deque([(exact_start, q_start, ())])
    seen_exact = {exact_start}
    alts = []
    nodes = 0
    while q:
        s, qs, path = q.popleft()
        nodes += 1
        if len(path) >= radius:
            continue
        for m in range(14):
            z = move(s, m)
            if z in seen_exact:
                continue
            qz = qstep(fg, qs, m, ctxs)
            np = path + (m,)
            seen_exact.add(z)
            if qz == q_start and z != exact_start:
                alts.append((z, np))
            q.append((z, qz, np))
    # Prefer shorter holonomy, then smaller exact relator footprint.
    alts.sort(key=lambda t: (len(t[1]), len(t[0][0]) + len(t[0][1]), max(len(t[0][0]), len(t[0][1])), t[1]))
    return alts[:cap], nodes, len(alts)


def apply_path(state, moves):
    s = state
    for m in moves:
        s = move(s, int(m))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--acc-root', required=True)
    ap.add_argument('--atlas', required=True)
    ap.add_argument('--targets-json', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--quotient-depth', type=int, default=5)
    ap.add_argument('--holonomy-radius', type=int, default=4)
    ap.add_argument('--alts-per-checkpoint', type=int, default=12)
    ap.add_argument('--tail-depth', type=int, default=2)
    a = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from acc_competitive import finite_group_pdb_v1 as fg

    manifest = json.loads((Path(a.acc_root) / 'competition/tools/verifier/data/manifest.json').read_text())
    byid = {c['challenge_id']: c for c in manifest['challenges']}
    target_obj = json.loads(Path(a.targets_json).read_text())
    if isinstance(target_obj, dict):
        target_ids = target_obj.get('challenge_ids') or target_obj.get('target_ids') or target_obj.get('exact_depth5_residual_ids') or []
    else:
        target_ids = target_obj
    target_ids = [str(x) for x in target_ids]

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

    ctxs = quotient_contexts(fg)
    q_sources = {qproject(fg, s, ctxs) for s in meta}
    print('HOLONOMY_QUOTIENT', json.dumps({
        'contexts': [x[0] for x in ctxs], 'atlas_states': len(meta), 'atlas_signatures': len(q_sources)
    }, sort_keys=True))

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    candidates = []
    rows = []
    total_q_nodes = total_h_nodes = total_tail_nodes = 0
    total_alt_lifts = total_alt_raw = 0
    checkpoints_with_alt = 0

    for ti, cid in enumerate(target_ids, 1):
        ch = byid[cid]
        initial = (tuple(ch['initial_relators'][0]), tuple(ch['initial_relators'][1]))
        q0 = qproject(fg, initial, ctxs)
        witness, qnodes = quotient_witness(fg, q0, q_sources, ctxs, a.quotient_depth)
        total_q_nodes += qnodes
        rec = {'challenge_id': cid, 'quotient_nodes': qnodes, 'quotient_witness': None if witness is None else list(witness)}
        if witness is None:
            rec['phase'] = 'no_refined_quotient_hit'
            rows.append(rec)
            continue

        checkpoint_exact = initial
        checkpoint_q = q0
        alt_kept = alt_raw = hnodes_row = tails_row = 0
        candidate = None

        # Include every checkpoint before/after witness moves. The baseline lift is already exhausted;
        # only nontrivial same-fiber alternatives are tested.
        for i in range(len(witness) + 1):
            alts, hnodes, raw = fiber_alternatives(
                fg, checkpoint_exact, checkpoint_q, ctxs,
                a.holonomy_radius, a.alts_per_checkpoint,
            )
            hnodes_row += hnodes
            alt_raw += raw
            alt_kept += len(alts)
            if alts:
                checkpoints_with_alt += 1
            suffix_witness = witness[i:]
            for alt_state, hol in alts:
                endpoint = apply_path(alt_state, suffix_witness)
                tail, hit, tnodes = tail_search(endpoint, meta, a.tail_depth)
                tails_row += tnodes
                if tail is None:
                    continue
                prefix = list(witness[:i]) + list(hol) + list(suffix_witness) + list(tail)
                suffix = atlas_suffix(hit, meta)
                moves = prefix + suffix
                candidate = {
                    'challenge_id': cid,
                    'checkpoint': i,
                    'quotient_witness': list(witness),
                    'holonomy_moves': list(hol),
                    'tail_moves': list(tail),
                    'prefix_moves': prefix,
                    'atlas_hit_distance': meta[hit][0],
                    'atlas_source': meta[hit][2],
                    'suffix_moves': suffix,
                    'moves': moves,
                    'length': len(moves),
                }
                candidates.append(candidate)
                print('HOLONOMY_CANDIDATE', json.dumps(candidate, sort_keys=True))
                break
            if candidate is not None:
                break
            if i < len(witness):
                m = witness[i]
                checkpoint_exact = move(checkpoint_exact, m)
                checkpoint_q = qstep(fg, checkpoint_q, m, ctxs)

        total_h_nodes += hnodes_row
        total_tail_nodes += tails_row
        total_alt_lifts += alt_kept
        total_alt_raw += alt_raw
        rec.update({
            'phase': 'candidate' if candidate else ('fiber_holonomy_present' if alt_raw else 'locally_fiber_rigid'),
            'holonomy_nodes': hnodes_row,
            'raw_same_fiber_alternatives': alt_raw,
            'kept_same_fiber_alternatives': alt_kept,
            'tail_nodes': tails_row,
            'candidate': candidate,
        })
        rows.append(rec)
        print('HOLONOMY_ROW', json.dumps({k: rec[k] for k in (
            'challenge_id','phase','holonomy_nodes','raw_same_fiber_alternatives','kept_same_fiber_alternatives','tail_nodes'
        )}, sort_keys=True))
        if ti % 5 == 0 or ti == len(target_ids):
            print('HOLONOMY_PROGRESS', json.dumps({
                'done': ti, 'targets': len(target_ids), 'candidates': len(candidates),
                'holonomy_nodes': total_h_nodes, 'same_fiber_alternatives': total_alt_raw,
            }, sort_keys=True))

    (out / 'candidates.txt').write_text(''.join(
        f"{x['challenge_id']}: {json.dumps(x['moves'], separators=(',', ':'))}\n" for x in candidates
    ))
    report = {
        'version': 'atlas-fiber-holonomy-v1',
        'read_only': True,
        'atlas_states': len(meta),
        'atlas_signatures': len(q_sources),
        'contexts': [x[0] for x in ctxs],
        'targets': len(target_ids),
        'quotient_depth': a.quotient_depth,
        'holonomy_radius': a.holonomy_radius,
        'alts_per_checkpoint': a.alts_per_checkpoint,
        'tail_depth': a.tail_depth,
        'quotient_nodes': total_q_nodes,
        'holonomy_nodes': total_h_nodes,
        'tail_nodes': total_tail_nodes,
        'same_fiber_alternatives_raw': total_alt_raw,
        'same_fiber_alternatives_kept': total_alt_lifts,
        'checkpoints_with_alternative': checkpoints_with_alt,
        'candidates': len(candidates),
        'candidate_rows': candidates,
        'rows': rows,
        'claim_boundary': 'This is a bounded constructive fiber-holonomy search, not an exact distance lower bound. It is distinct from the exhausted single quotient-witness lift: short official-move loops that are null in the six-context quotient are used to generate multiple exact lifts before resuming the quotient witness.',
    }
    (out / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('HOLONOMY_SUMMARY', json.dumps({k: report[k] for k in (
        'targets','atlas_states','atlas_signatures','quotient_nodes','holonomy_nodes','tail_nodes',
        'same_fiber_alternatives_raw','same_fiber_alternatives_kept','checkpoints_with_alternative','candidates'
    )}, sort_keys=True))


if __name__ == '__main__':
    main()
