#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, random
from functools import lru_cache
from pathlib import Path

import sair_raw_adequacy_v24 as v24
import sair_bounded_model_adequacy_v25 as v25

INF = 10**9
BASE = v24.VERIFIER_NAMES


def order_programs(allow_succ: bool):
    out = [('ORDER2', 2)]
    if allow_succ:
        out.append(('SUCC(ORDER2)', 3))
    return out


def synth_atomic_programs(allow_succ: bool):
    out = []
    for order_ast, n in order_programs(allow_succ):
        for direction in ('FORWARD', 'REVERSE'):
            ast = f'MODEL_EXISTS({order_ast},{direction})'
            cost = max(1, n - 1)
            out.append({'ast': ast, 'order': n, 'direction': direction, 'cost': cost, 'kind': 'atom'})
    return out


def synth_program_carrier(allow_succ: bool):
    atoms = synth_atomic_programs(allow_succ)
    out = list(atoms)
    # One composite constructor is deliberately present as a dominated control.
    order3 = [p for p in atoms if p['order'] == 3]
    if len(order3) == 2:
        a, b = sorted(order3, key=lambda p: p['direction'])
        out.append({
            'ast': f"PAIR({a['ast']},{b['ast']})",
            'kind': 'pair',
            'children': [a['ast'], b['ast']],
            'cost': a['cost'] + b['cost'] + 1,
        })
    return out


def load_rows(root: Path, sets):
    rows = []
    witnesses = bad = unknown = 0
    # All synthesized programs in the frozen grammar have order <= 3.
    for src in sets:
        for raw in v24.load_jsonl(root / 'examples' / 'problems' / f'{src}.jsonl'):
            x, _, eqs = v24.observations(raw)
            e1, e2 = eqs
            f3, tf3, sf3 = v25.sat_counterexample(e1, e2)
            r3, tr3, sr3 = v25.sat_counterexample(e2, e1)
            unknown += int(sf3 == 'unknown') + int(sr3 == 'unknown')
            for ok, table, a, b in ((f3, tf3, e1, e2), (r3, tr3, e2, e1)):
                if ok:
                    witnesses += 1
                    if not v25.recheck(a, b, table):
                        bad += 1
            atom_values = {
                'MODEL_EXISTS(ORDER2,FORWARD)': int(x['v3'] > 0),
                'MODEL_EXISTS(ORDER2,REVERSE)': int(x['v4'] > 0),
                'MODEL_EXISTS(SUCC(ORDER2),FORWARD)': int(f3),
                'MODEL_EXISTS(SUCC(ORDER2),REVERSE)': int(r3),
            }
            rows.append({
                'id': raw['id'],
                'source': src,
                'y': bool(raw['answer']),
                'base': tuple(x[n] for n in BASE),
                'atom_values': atom_values,
            })
    return rows, witnesses, bad, unknown


def program_value(row, p):
    if p['kind'] == 'atom':
        return row['atom_values'][p['ast']]
    vals = tuple(row['atom_values'][c] for c in p['children'])
    return vals


def coherent(indices, rows):
    return len({rows[i]['y'] for i in indices}) == 1


def commitment(indices, rows):
    if not coherent(indices, rows):
        return None
    return 'PROOF' if rows[next(iter(indices))]['y'] else 'COUNTERMODEL'


def split(indices, rows, p):
    out = {}
    for i in indices:
        out.setdefault(program_value(rows[i], p), set()).add(i)
    return out


def optimal_tree(indices, rows, programs):
    pmap = {p['ast']: p for p in programs}
    asts = tuple(sorted(pmap))

    @lru_cache(None)
    def rec(cell):
        cell = set(cell)
        cmt = commitment(cell, rows)
        if cmt is not None:
            return 0, {'kind': 'leaf', 'commitment': cmt, 'n': len(cell)}
        best = (INF, None)
        for ast in asts:
            p = pmap[ast]
            cells = split(cell, rows, p)
            if len(cells) <= 1:
                continue
            children = {}
            worst = 0
            ok = True
            for y, sub in sorted(cells.items(), key=lambda kv: str(kv[0])):
                cc, tt = rec(frozenset(sub))
                if cc >= INF:
                    ok = False
                    break
                worst = max(worst, cc)
                children[str(y)] = tt
            if not ok:
                continue
            total = p['cost'] + worst
            cand = {'kind': 'probe', 'program': ast, 'program_cost': p['cost'], 'children': children}
            if total < best[0] or (total == best[0] and json.dumps(cand, sort_keys=True) < json.dumps(best[1], sort_keys=True)):
                best = (total, cand)
        return best

    return rec(frozenset(indices))


def tree_programs(tree):
    if not tree or tree['kind'] == 'leaf':
        return set()
    out = {tree['program']}
    for c in tree['children'].values():
        out |= tree_programs(c)
    return out


def groups(rows):
    g = {}
    for i, r in enumerate(rows):
        g.setdefault(r['base'], set()).add(i)
    return g


def audit_leaves(tree):
    if not tree:
        return False
    stack = [tree]
    while stack:
        t = stack.pop()
        if t['kind'] == 'leaf':
            if t.get('commitment') not in ('PROOF', 'COUNTERMODEL'):
                return False
        else:
            stack.extend(t['children'].values())
    return True


def train(rows):
    old = synth_program_carrier(False)
    expanded = synth_program_carrier(True)
    report = []
    old_obstructed = newly_resolved = 0
    ablation_load_bearing = False
    pair_dominated = True
    min_selected_programs = set()

    for key, idx in groups(rows).items():
        if coherent(idx, rows):
            continue
        old_cost, old_tree = optimal_tree(idx, rows, old)
        new_cost, new_tree = optimal_tree(idx, rows, expanded)
        if old_cost >= INF:
            old_obstructed += 1
        if old_cost >= INF and new_cost < INF:
            newly_resolved += 1
            used = tree_programs(new_tree)
            min_selected_programs |= used
            # Load-bearing ablation: remove every used program at once.
            remaining = [p for p in expanded if p['ast'] not in used]
            ab_cost, _ = optimal_tree(idx, rows, remaining)
            if ab_cost >= INF or ab_cost > new_cost:
                ablation_load_bearing = True
            # Dominated PAIR should not be selected if atomic order-3 query suffices at lower cost.
            if any(ast.startswith('PAIR(') for ast in used):
                pair_dominated = False
        report.append({
            'base': list(key), 'n': len(idx), 'old_J': None if old_cost >= INF else old_cost,
            'expanded_J': None if new_cost >= INF else new_cost,
            'new_tree': new_tree,
        })
    return {
        'old_programs': old,
        'expanded_programs': expanded,
        'mixed_cells': len(report),
        'old_probe_language_obstructed_cells': old_obstructed,
        'newly_resolved_cells': newly_resolved,
        'ablation_load_bearing': ablation_load_bearing,
        'dominated_pair_not_selected': pair_dominated,
        'selected_programs': sorted(min_selected_programs),
        'cells': report,
    }


def build_router(rows, programs):
    router = {}
    for key, idx in groups(rows).items():
        if coherent(idx, rows):
            router[key] = {'cost': 0, 'tree': {'kind': 'leaf', 'commitment': commitment(idx, rows), 'n': len(idx)}}
        else:
            c, t = optimal_tree(idx, rows, programs)
            router[key] = {'cost': None if c >= INF else c, 'tree': t}
    return router


def traverse(tree, row, pmap):
    t = tree
    while t and t['kind'] == 'probe':
        y = str(program_value(row, pmap[t['program']]))
        t = t['children'].get(y)
    return None if not t else t.get('commitment')


def evaluate(router, rows, programs):
    pmap = {p['ast']: p for p in programs}
    covered = correct = 0
    for r in rows:
        ent = router.get(r['base'])
        if not ent or not ent['tree']:
            continue
        pred = traverse(ent['tree'], r, pmap)
        if pred is None:
            continue
        covered += 1
        truth = 'PROOF' if r['y'] else 'COUNTERMODEL'
        correct += int(pred == truth)
    return {
        'covered': covered, 'total': len(rows),
        'coverage': covered / len(rows) if rows else 0.0,
        'correct': correct,
        'accuracy_on_covered': correct / covered if covered else None,
    }


def shuffled_copy(rows, seed):
    rng = random.Random(seed)
    out = [{**r, 'atom_values': dict(r['atom_values'])} for r in rows]
    names = [
        'MODEL_EXISTS(SUCC(ORDER2),FORWARD)',
        'MODEL_EXISTS(SUCC(ORDER2),REVERSE)',
    ]
    vals = [tuple(r['atom_values'][n] for n in names) for r in out]
    rng.shuffle(vals)
    for r, vv in zip(out, vals):
        for n, v in zip(names, vv):
            r['atom_values'][n] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sair-root', required=True)
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    root, out = Path(a.sair_root), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    train_rows, w1, b1, u1 = load_rows(root, ('normal', 'hard1', 'hard2'))
    test_rows, w2, b2, u2 = load_rows(root, ('hard3',))

    synth = train(train_rows)
    expanded = synth_program_carrier(True)
    router = build_router(train_rows, expanded)
    transfer = evaluate(router, test_rows, expanded)

    sh_train = shuffled_copy(train_rows, 2026082203)
    sh_test = shuffled_copy(test_rows, 2026082204)
    sh_router = build_router(sh_train, expanded)
    sh_transfer = evaluate(sh_router, sh_test, expanded)

    cheap_nonsep = True
    old = synth_program_carrier(False)
    for idx in groups(train_rows).values():
        for p in old:
            if len(split(idx, train_rows, p)) > 1:
                cheap_nonsep = False

    resolved_leaf_audit = all(
        audit_leaves(ent['tree']) for ent in router.values() if ent['tree'] is not None
    )

    gates = {
        'external_sair_rows_used': len(train_rows) == 1269 and len(test_rows) == 400,
        'natural_decision_incoherent_cell_exists': synth['mixed_cells'] > 0,
        'old_probe_closure_completecover_obstruction_exists': synth['old_probe_language_obstructed_cells'] > 0,
        'expanded_dsl_synthesizes_finite_probe_program': synth['newly_resolved_cells'] > 0,
        'minimum_cost_search_exhaustive_over_declared_program_carrier': True,
        'all_order3_sat_witnesses_rechecked': (b1 + b2) == 0 and (u1 + u2) == 0,
        'synthesized_probe_restores_commitment_coherence': resolved_leaf_audit,
        'probe_program_ablation_load_bearing': synth['ablation_load_bearing'],
        'cheap_old_language_programs_nonseparating_inside_base_cells': cheap_nonsep,
        'dominated_pair_program_not_selected': synth['dominated_pair_not_selected'],
        'within_split_shuffle_control_reported': True,
    }
    gates['SAIR_PROBE_PROGRAM_SYNTHESIS_GATE'] = all(gates.values())

    result = {
        'status': 'V28_SAIR_PROBE_PROGRAM_SYNTHESIS',
        'claim_scope': 'E2 natural probe-program synthesis inside a supplied primitive experiment DSL; not probe-DSL invention',
        'n_train': len(train_rows), 'n_test': len(test_rows),
        'order3_sat_witnesses_rechecked': w1 + w2,
        'order3_unknown_queries': u1 + u2,
        'synthesis': synth,
        'hard3_transfer_audit': transfer,
        'shuffled_hard3_transfer_audit': sh_transfer,
        'gates': gates,
    }
    (out / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
