#!/usr/bin/env python3
"""Exact finite source-cap coverage and P35/P37 falsification, not global closure.

Run from the repository root. Parent: 3ae1c9023b7883977132655ba771c9239828b9b0.
No published convergence computation or unbounded origin estimate is replayed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collatz_live_origin_bridge_v1 import language_counts, first_crossing


def sweep(depth: int) -> dict:
    """Depth-indexed exact scan. Only possible first-crossing types are retained."""
    if not 2 <= depth <= 300000:
        raise ValueError('depth must be in [2,300000]')
    p2, p3, q, count, best = 1, 1, 0, 0, 0
    digest = hashlib.sha256()
    records = []
    for j in range(1, depth + 1):
        p2 *= 2
        while 3 * p3 < p2:
            p3 *= 3
            q += 1
        assert p3 < p2 < 3 * p3
        if 2 * p3 < p2:
            continue
        count += 1
        D = p2 - p3
        numerator = q * (p3 // 3) if q else 0
        cap = numerator // D
        # Integer form of n <= q*3^(q-1)/(2^j-3^q).
        assert cap * D <= numerator < (cap + 1) * D
        digest.update(f'{j},{q},{cap}\n'.encode())
        if cap > best:
            best = cap
            records.append({'j': j, 'q': q, 'cap': cap})
    return {'depth': depth, 'possible_first_crossing_types': count,
            'max_nondescending_source_cap': best,
            'maximizing_record': records[-1], 'record_count': len(records),
            'records': records, 'type_rows_sha256': digest.hexdigest(),
            'minimal_required_published_floor': best + 1,
            'convenient_floor': 2 ** 33, 'below_convenient_floor': best < 2 ** 33}


def p37_audit() -> dict:
    qmin, _, _ = language_counts(1024)
    minima = {}
    for n in range(1, 2 ** 20, 2):
        crossing = first_crossing(n, qmin)
        assert crossing is not None
        j, y, q = crossing
        minima.setdefault(j, (n, y, q))
    rows = {}
    for j, (R, Y, q) in sorted(minima.items()):
        if j == 2:
            continue
        Bstar = 0
        for k in range(1, j):
            if qmin[k] > qmin[k - 1]:
                Bstar = 3 * Bstar + 2 ** (k - 1)
        D = 2 ** j - 3 ** q
        M0 = 2 ** j * (Y - R)
        assert D > 0 and M0 < 0
        rows[j] = {'j': j, 'R': R, 'Y': Y, 'q': q,
                   'old_cap': (Bstar - M0 - 1) // D,
                   'lattice_cap': (Bstar - M0 - 2 ** j) // D}
    counts = {'old_competitors': 0, 'lattice_competitors': 0,
              'lattice_base_exits': 0, 'lattice_same_type_comparisons': 0,
              'lattice_distinct_type_edges': 0}
    depth_witnesses, cap_witnesses = [], []
    for j, row in rows.items():
        R = row['R']
        counts['old_competitors'] += len(range(R + 2, row['old_cap'] + 1, 2))
        for n in range(R + 2, row['lattice_cap'] + 1, 2):
            counts['lattice_competitors'] += 1
            crossing = first_crossing(n, qmin)
            assert crossing is not None
            k, y, _ = crossing
            if k == 2:
                counts['lattice_base_exits'] += 1
                continue
            if k == j:
                counts['lattice_same_type_comparisons'] += 1
                # A same-type candidate is compared, not turned into a self-loop.
                assert y - n <= row['Y'] - R
                continue
            assert k in rows, 'child type lacks an independently found incumbent'
            counts['lattice_distinct_type_edges'] += 1
            child = rows[k]
            witness = {'parent_j': j, 'child_j': k, 'source': n,
                       'parent_incumbent': R, 'parent_endpoint': row['Y'],
                       'competitor_endpoint': y,
                       'parent_old_cap': row['old_cap'],
                       'parent_lattice_cap': row['lattice_cap'],
                       'child_lattice_cap': child['lattice_cap']}
            if k > j:
                depth_witnesses.append(witness)
            if child['lattice_cap'] >= row['lattice_cap']:
                cap_witnesses.append(witness)
    assert len(rows) == 104
    assert counts == {'old_competitors': 4174, 'lattice_competitors': 3785,
                      'lattice_base_exits': 1918, 'lattice_same_type_comparisons': 1,
                      'lattice_distinct_type_edges': 1866}
    assert [(w['parent_j'], w['child_j'], w['source']) for w in depth_witnesses] == [(111, 129, 45127)]
    assert [(w['parent_j'], w['child_j'], w['source']) for w in cap_witnesses] == [(40, 21, 159), (54, 42, 103)]
    return {'source_scan': 2 ** 19, 'nontrivial_observed_types': len(rows),
            'counts': counts, 'depth_rank_counterexamples': depth_witnesses,
            'lattice_cap_rank_counterexamples': cap_witnesses,
            'disposition': 'Depth rank and lattice-cap rank rejected; P37 as a whole remains UNKNOWN.'}


def independent_small_word_audit(depth: int = 18) -> dict:
    qmin, _, _ = language_counts(depth)
    states = [(0, 0, 0, 0)]  # q, R, Y, B
    checked = 0
    for j in range(1, depth + 1):
        nxt = []
        for q, R, Y, B in states:
            for lift in (0, 1):
                Rp = R + lift * 2 ** (j - 1)
                z = Y + 3 ** q * lift
                b = z % 2
                qp = q + b
                Yp = (3 * z + 1) // 2 if b else z // 2
                Bp = 3 * B + 2 ** (j - 1) if b else B
                assert 2 ** j * Yp == 3 ** qp * Rp + Bp
                assert 3 * Bp <= qp * 3 ** qp
                checked += 1
                if qp >= qmin[j]:
                    nxt.append((qp, Rp, Yp, Bp))
                else:
                    assert j == (3 ** qp).bit_length()
                    if Rp <= Yp:
                        assert 3 * (2 ** j - 3 ** qp) * Rp <= qp * 3 ** qp
        states = nxt
    return {'depth': depth, 'affine_and_elementary_bias_checks': checked}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depth', type=int, default=271782)
    args = parser.parse_args()
    cap = sweep(args.depth)
    if args.depth == 271782:
        assert cap['possible_first_crossing_types'] == 171476
        assert cap['maximizing_record'] == {'j': 125743, 'q': 79335, 'cap': 7216089270}
    result = {'schema': 'COLLATZ_SOURCE_FLOOR_GAP_V1',
              'parent_head': '3ae1c9023b7883977132655ba771c9239828b9b0',
              'global_collatz': 'UNKNOWN', 'finite_caps': cap,
              'elementary_bound': '3*B <= q*3^q; non-descent implies 3*D*n <= q*3^q',
              'small_word_audit': independent_small_word_audit(),
              'p35_p37': p37_audit(),
              'external_boundary': 'Published convergence below 2^33 is sufficient but not recomputed here.',
              'onset_boundary': 'Finite minimal-counterexample gap removed only through the explicit scanned depth.',
              'not_proved': ['universal live-origin estimate and its onset',
                             'universal canonical M>=0 cylinder exclusion',
                             'a universal P37 residual-preserving decreasing rank'],
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
