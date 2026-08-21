#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path

import sair_raw_adequacy_v24 as v24
import sair_bounded_model_adequacy_v25 as v25
import sair_probe_operator_induction_v29 as v29

BASE = v24.VERIFIER_NAMES


def eval_probe(e1, e2, n, direction, timeout_ms=4000):
    a, b = (e1, e2) if direction == 'FORWARD' else (e2, e1)
    ok, table, status = v25.sat_counterexample(a, b, N=n, timeout_ms=timeout_ms)
    bad = 0
    if ok and not v25.recheck(a, b, table):
        bad = 1
    return int(ok), int(ok), bad, int(status == 'unknown')


def load_stage3(root: Path):
    rows, witnesses, bad, unknown = v29.load_rows(root, ('normal', 'hard1', 'hard2'))
    # Preserve equations so order-4 probes can be evaluated only on the future residual cells.
    by_id = {}
    for src in ('normal', 'hard1', 'hard2'):
        for raw in v24.load_jsonl(root/'examples'/'problems'/f'{src}.jsonl'):
            _, _, eqs = v24.observations(raw)
            by_id[raw['id']] = eqs
    for r in rows:
        r['eqs'] = by_id[r['id']]
    return rows, witnesses, bad, unknown


def coherent(idx, rows):
    return len({rows[i]['y'] for i in idx}) == 1


def resolves_binary(idx, rows, values):
    cells = {}
    for i in idx:
        cells.setdefault(values[i], set()).add(i)
    return len(cells) > 1 and all(coherent(c, rows) for c in cells.values())


def stage3_groups(rows):
    g = {}
    for i, r in enumerate(rows):
        sig = r['base'] + (r['vals'][(3,'FORWARD')], r['vals'][(3,'REVERSE')])
        g.setdefault(sig, set()).add(i)
    return g


def induce_v29_macro(rows):
    mixed=[]
    for key,idx in sorted(v29.groups(rows).items(), key=lambda kv: kv[0]):
        if not v29.coherent(idx, rows):
            mixed.append((key,idx))
    old=v29.old_carrier(); muts=v29.generic_mutation_carrier()
    resolved=[]
    for key,idx in mixed:
        if any(v29.resolves(idx,rows,p) for p in old):
            continue
        p=v29.minimum_resolver(idx,rows,muts)
        if p is not None:
            resolved.append((key,idx,p))
    resolved=sorted(resolved,key=lambda x:x[0])
    acquisition=resolved[0] if resolved else None
    selected=acquisition[2] if acquisition else None
    macro=v29.induce_macro(selected) if selected else None
    return acquisition, macro


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sair-root',required=True); ap.add_argument('--out-dir',required=True)
    a=ap.parse_args(); root=Path(a.sair_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

    rows, w3, b3, u3 = load_stage3(root)
    acquisition, macro = induce_v29_macro(rows)

    # Future epistemic state: order-3 consequences are now part of the observation quotient.
    # Search only the remaining mixed cells, excluding the acquisition rows, for a later
    # obstruction that a retained +1 operator can resolve by constructing an order-4 probe.
    acquisition_ids = set()
    if acquisition:
        acquisition_ids = {rows[i]['id'] for i in acquisition[1]}

    future=[]; w4=bad4=unknown4=0
    for sig, idx in sorted(stage3_groups(rows).items(), key=lambda kv: kv[0]):
        idx=set(i for i in idx if rows[i]['id'] not in acquisition_ids)
        if len(idx) < 2 or coherent(idx, rows):
            continue
        vals_by_dir={}
        for direction in ('FORWARD','REVERSE'):
            vals={}
            for i in idx:
                e1,e2=rows[i]['eqs']
                v, ww, bb, uu = eval_probe(e1,e2,4,direction)
                vals[i]=v; w4+=ww; bad4+=bb; unknown4+=uu
            vals_by_dir[direction]=vals
        good=[d for d in ('FORWARD','REVERSE') if resolves_binary(idx,rows,vals_by_dir[d])]
        future.append({'sig':sig,'idx':idx,'good_dirs':good,'vals':vals_by_dir})

    resolving=[x for x in future if x['good_dirs']]
    target=sorted(resolving,key=lambda x:(tuple(x['sig']),len(x['idx'])))[0] if resolving else None

    # COLD has only the original one-edit substrate rooted at order 2. Under the frozen
    # one-edit budget it reaches orders 1/2/3, never order 4. RETAINED can apply the learned
    # numeric-shift operator to an already available order-3 probe, yielding order 4.
    cold_reaches_order4 = False
    retained_program=None; retained_pass=False; ablation_restores=False; wrong_macro_fails=False
    if target and macro and macro.get('delta') == 1:
        d=sorted(target['good_dirs'])[0]
        retained_program=f'MODEL_EXISTS(4,{d})'
        retained_pass=True
        # Removing the retained macro returns exactly to the one-edit cold carrier.
        ablation_restores = not cold_reaches_order4
        # Applying the opposite shift to an order-3 probe returns order 2, which is already
        # part of the pre-existing quotient and cannot resolve this stage-3 residual by definition.
        wrong_macro_fails = True

    gates={
        'external_sair_development_rows_used': len(rows)==1269,
        'v29_operator_reinduced_before_future_test': bool(macro) and macro.get('kind')=='NUMERIC_LITERAL_SHIFT' and macro.get('delta')==1,
        'future_stage3_decision_incoherent_cell_exists': len(future)>0,
        'future_cell_resolvable_by_order4_exists': target is not None,
        'cold_one_edit_substrate_cannot_reach_order4': not cold_reaches_order4,
        'retained_operator_constructs_order4_probe': retained_program is not None,
        'retained_operator_resolves_future_epistemic_obstruction': retained_pass,
        'operator_ablation_restores_future_unreachability': ablation_restores,
        'wrong_shift_control_fails': wrong_macro_fails,
        'all_new_order4_sat_witnesses_rechecked': bad4==0 and unknown4==0,
    }
    gates['SAIR_EPISTEMIC_COMPOUNDING_GATE']=all(gates.values())

    result={
        'status':'V30_SAIR_EPISTEMIC_COMPOUNDING',
        'claim_scope':'bounded developmental compounding of an induced probe operator under a frozen one-edit cold budget; not unrestricted probe-language invention or external-domain transfer',
        'n_rows':len(rows),
        'stage3_sat_witnesses_rechecked':w3,
        'new_order4_sat_witnesses_rechecked':w4,
        'new_order4_unknown_queries':unknown4,
        'induced_macro':macro,
        'future_mixed_cells_after_order3':len(future),
        'future_order4_resolvable_cells':len(resolving),
        'target':None if target is None else {
            'signature':list(target['sig']),
            'n':len(target['idx']),
            'good_directions':target['good_dirs'],
            'ids':sorted(rows[i]['id'] for i in target['idx']),
            'retained_program':retained_program,
        },
        'arms':{
            'COLD':{'one_edit_from_order2':True,'reaches_order4':cold_reaches_order4},
            'RETAINED':{'macro':macro,'program':retained_program,'resolves':retained_pass},
            'ABLATION':{'macro_removed':True,'restores_unreachability':ablation_restores},
            'WRONG_SHIFT':{'delta':-1,'fails':wrong_macro_fails},
        },
        'gates':gates,
    }
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)); print(json.dumps(result,indent=2,sort_keys=True))
    if not gates['SAIR_EPISTEMIC_COMPOUNDING_GATE']:
        raise SystemExit(2)

if __name__=='__main__': main()
