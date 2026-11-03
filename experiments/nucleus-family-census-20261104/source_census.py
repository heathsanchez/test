"""Source-only census of Lean inductive families in a pinned NDJSON export.

This does not check declarations or predict acceptance. It identifies reusable
structural shapes so we can prioritize exact kernel obligations by coverage,
instead of writing a new named-declaration exception for every frontier.
"""

import argparse
from array import array
from collections import Counter
import hashlib
import json
from pathlib import Path


def census(stream, after_record):
    digest = hashlib.sha256()
    # Expression IDs and level IDs in lean4export are monotonically allocated;
    # store just the terminal Sort level of a Pi telescope, not the full DAG.
    sort_tail = array('i', [-1])
    level_form = {0: ('zero',)}
    counts = Counter()
    families = Counter()
    later_families = Counter()
    examples = {}
    max_line_bytes = 0

    for record_number, raw in enumerate(stream, 1):
        digest.update(raw)
        max_line_bytes = max(max_line_bytes, len(raw))
        item = json.loads(raw)
        if 'il' in item:
            idx = item['il']
            if 'param' in item:
                form = ('param', item['param'])
            elif 'succ' in item:
                form = ('succ', level_form.get(item['succ']))
            elif 'max' in item:
                a, b = item['max']
                form = ('max', level_form.get(a), level_form.get(b))
            elif 'imax' in item:
                a, b = item['imax']
                form = ('imax', level_form.get(a), level_form.get(b))
            else:
                form = ('unknown',)
            level_form[idx] = form
        elif 'ie' in item:
            idx = item['ie']
            if 'sort' in item:
                tail = item['sort']
            elif 'forallE' in item:
                body = item['forallE']['body']
                tail = sort_tail[body] if body < len(sort_tail) else -1
            else:
                tail = -1
            while idx >= len(sort_tail):
                sort_tail.append(-1)
            sort_tail[idx] = tail
        elif 'inductive' in item:
            counts['inductive_blocks'] += 1
            block = item['inductive']
            types = block.get('types', [])
            ctors = block.get('ctors', [])
            recs = block.get('recs', [])
            for typ in types:
                counts['inductive_types'] += 1
                typeid = typ['type']
                level = sort_tail[typeid] if typeid < len(sort_tail) else -1
                form = level_form.get(level)
                levels = typ.get('levelParams', [])
                owner = levels[0] if len(levels) == 1 else None
                universe = 'other'
                if form == ('zero',):
                    universe = 'zero'
                elif owner is not None:
                    p = ('param', owner)
                    if form == p:
                        universe = 'param_owner'
                    elif form == ('succ', p):
                        universe = 'succ_param_owner'
                    elif form in (('max', ('succ', ('zero',)), p),
                                  ('max', p, ('succ', ('zero',)))):
                        universe = 'max_one_param_owner'
                fields = sorted(c['numFields'] for c in ctors if c.get('induct') == typ['name'])
                related_recs = [r for r in recs if typ['name'] in r.get('all', [])]
                k = tuple(sorted(bool(r.get('k')) for r in related_recs))
                # Signature shape, not identity: useful for reusable verifier
                # design, never a trusted proof or permission to ACCEPT.
                signature = (len(types), len(fields), typ['numParams'],
                             typ['numIndices'], typ['numNested'],
                             bool(typ['isRec']), bool(typ['isReflexive']),
                             tuple(fields), len(levels), universe,
                             len(related_recs), k)
                families[signature] += 1
                if record_number > after_record:
                    later_families[signature] += 1
                examples.setdefault(signature, {'name_id': typ['name'],
                                                'record': record_number})
                counts['universe_' + universe] += 1
                if bool(typ['isRec']):
                    counts['recursive_types'] += 1
                if len(fields) == 1 and not typ['isRec']:
                    counts['nonrecursive_single_constructor'] += 1
    def top_shapes(collection, limit):
      top = []
      for signature, count in collection.most_common(limit):
        (nt, nc, np, ni, nn, rec, reflex, fields, nl, uni, nr, k) = signature
        top.append({'count': count, 'types_in_block': nt,
                    'constructors': nc, 'params': np, 'indices': ni,
                    'nested': nn, 'recursive': rec, 'reflexive': reflex,
                    'field_counts': list(fields), 'level_params': nl,
                    'result_sort': uni, 'recursors': nr, 'k_flags': list(k),
                    'example': examples[signature]})
      return top
    return {'status': 'SOURCE_CENSUS_NOT_VERIFICATION',
            'source_sha256': digest.hexdigest(),
            'records': record_number, 'max_line_bytes': max_line_bytes,
            'distinct_shapes': len(families),
            'counts': dict(sorted(counts.items())),
            'top_shapes': top_shapes(families, 80),
            'after_record': after_record,
            'after_inductive_types': sum(later_families.values()),
            'after_distinct_shapes': len(later_families),
            'after_top_shapes': top_shapes(later_families, 80)}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('source', type=Path)
    cli.add_argument('--expected-sha256', required=True)
    cli.add_argument('--after-record', type=int, default=130802)
    args = cli.parse_args()
    with args.source.open('rb') as reader:
        result = census(reader, args.after_record)
    assert result['source_sha256'] == args.expected_sha256, 'Input source hash mismatch'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
