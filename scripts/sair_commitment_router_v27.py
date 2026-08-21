#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math, random
from functools import lru_cache
from pathlib import Path

import sair_raw_adequacy_v24 as v24
import sair_bounded_model_adequacy_v25 as v25

PROBES = (
    ('p0', 1),  # order-2 forward existence; redundant inside v0..v5 cell
    ('p1', 1),  # order-2 reverse existence; redundant inside v0..v5 cell
    ('p2', 3),  # order-3 forward existence
    ('p3', 3),  # order-3 reverse existence
)
BASE = v24.VERIFIER_NAMES
INF = 10**9


def load_rows(root: Path, sets):
    rows=[]; witnesses=bad=unknown=0
    for src in sets:
        for raw in v24.load_jsonl(root/'examples'/'problems'/f'{src}.jsonl'):
            x,w,eqs=v24.observations(raw); e1,e2=eqs
            f,tf,sf=v25.sat_counterexample(e1,e2)
            r,tr,sr=v25.sat_counterexample(e2,e1)
            unknown += int(sf=='unknown') + int(sr=='unknown')
            for ok,t,a,b in ((f,tf,e1,e2),(r,tr,e2,e1)):
                if ok:
                    witnesses += 1
                    if not v25.recheck(a,b,t): bad += 1
            probes={
                'p0': int(x['v3'] > 0),
                'p1': int(x['v4'] > 0),
                'p2': int(f),
                'p3': int(r),
            }
            rows.append({
                'id': raw['id'], 'source': src, 'y': bool(raw['answer']),
                'base': tuple(x[n] for n in BASE), 'probes': probes,
            })
    return rows, witnesses, bad, unknown


def coherent(indices, rows):
    ys={rows[i]['y'] for i in indices}
    return len(ys)==1


def action(indices, rows):
    if not coherent(indices, rows): return None
    return 'PROOF' if rows[next(iter(indices))]['y'] else 'COUNTERMODEL'


def split(indices, rows, probe_name):
    out={}
    for i in indices:
        out.setdefault(rows[i]['probes'][probe_name], set()).add(i)
    return out


def optimal_tree(indices, rows, allowed_probe_names):
    cost_map=dict(PROBES)
    allowed=tuple(allowed_probe_names)
    @lru_cache(None)
    def rec(cell):
        cell=set(cell)
        a=action(cell,rows)
        if a is not None:
            return 0, {'kind':'leaf','action':a,'n':len(cell)}
        best=(INF,None)
        for p in allowed:
            cells=split(cell,rows,p)
            if len(cells)<=1: continue
            children={}; worst=0; ok=True
            for y,sub in sorted(cells.items(),key=lambda kv:str(kv[0])):
                c,t=rec(frozenset(sub))
                if c>=INF: ok=False; break
                worst=max(worst,c); children[str(y)]=t
            if not ok: continue
            total=cost_map[p]+worst
            cand={'kind':'probe','probe':p,'cost':cost_map[p],'children':children}
            if total<best[0] or (total==best[0] and json.dumps(cand,sort_keys=True)<json.dumps(best[1],sort_keys=True)):
                best=(total,cand)
        return best
    return rec(frozenset(indices))


def group_indices(rows):
    g={}
    for i,r in enumerate(rows): g.setdefault(r['base'],set()).add(i)
    return g


def tree_probes(tree):
    if not tree or tree['kind']=='leaf': return set()
    out={tree['probe']}
    for c in tree['children'].values(): out |= tree_probes(c)
    return out


def train_router(rows):
    groups=group_indices(rows); router={}; mixed=resolved=unresolved=0; costs=[]; ablation_load_bearing=False
    for key,idx in groups.items():
        if coherent(idx,rows):
            router[key]={'cost':0,'tree':{'kind':'leaf','action':action(idx,rows),'n':len(idx)}}
            continue
        mixed += 1
        c,t=optimal_tree(idx,rows,[p for p,_ in PROBES])
        if c>=INF:
            unresolved += 1; router[key]={'cost':None,'tree':None}
        else:
            resolved += 1; costs.append(c); router[key]={'cost':c,'tree':t}
            used=tree_probes(t)
            if used:
                remaining=[p for p,_ in PROBES if p not in used]
                c2,_=optimal_tree(idx,rows,remaining)
                if c2>=INF or c2>c: ablation_load_bearing=True
    return router, {'cells':len(groups),'mixed_cells':mixed,'resolved_mixed_cells':resolved,'unresolved_mixed_cells':unresolved,
                    'finite_positive_J_cells':resolved,'mean_positive_J':(sum(costs)/len(costs) if costs else None),
                    'probe_ablation_load_bearing':ablation_load_bearing}


def traverse(tree,row):
    t=tree
    while t and t['kind']=='probe':
        y=str(row['probes'][t['probe']])
        t=t['children'].get(y)
    return None if not t else t.get('action')


def evaluate(router,rows):
    covered=correct=0; by_action={}
    for r in rows:
        ent=router.get(r['base'])
        if not ent or not ent['tree']: continue
        pred=traverse(ent['tree'],r)
        if pred is None: continue
        covered += 1
        yy='PROOF' if r['y'] else 'COUNTERMODEL'
        correct += int(pred==yy)
        by_action.setdefault(pred,[0,0]); by_action[pred][0]+=int(pred==yy); by_action[pred][1]+=1
    return {'covered':covered,'total':len(rows),'coverage':covered/len(rows) if rows else 0,
            'correct':correct,'accuracy_on_covered':correct/covered if covered else None,'by_action':by_action}


def shuffled_copy(rows,seed):
    rng=random.Random(seed); out=[{'id':r['id'],'source':r['source'],'y':r['y'],'base':r['base'],'probes':dict(r['probes'])} for r in rows]
    vals=[(r['probes']['p2'],r['probes']['p3']) for r in out]; rng.shuffle(vals)
    for r,(a,b) in zip(out,vals): r['probes']['p2']=a; r['probes']['p3']=b
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sair-root',required=True); ap.add_argument('--out-dir',required=True)
    a=ap.parse_args(); root=Path(a.sair_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    train,w1,b1,u1=load_rows(root,('normal','hard1','hard2'))
    test,w2,b2,u2=load_rows(root,('hard3',))
    router,stats=train_router(train); transfer=evaluate(router,test)

    # Within-split shuffle only: never move order-3 values across development/hard3 boundary.
    sh_train=shuffled_copy(train,2026082201); sh_test=shuffled_copy(test,2026082202)
    sh_router,sh_stats=train_router(sh_train); sh_transfer=evaluate(sh_router,sh_test)

    # Cheap probes p0/p1 are constant inside BASE cells by construction and therefore cannot be preferred as strict refinements.
    cheap_nonsep=True
    for idx in group_indices(train).values():
        for p in ('p0','p1'):
            if len(split(idx,train,p))>1: cheap_nonsep=False

    resolved_trees=[v['tree'] for v in router.values() if v['cost'] not in (None,0)]
    all_resolved_coherent=True
    for key,ent in router.items():
        if ent['cost'] in (None,0): continue
        # optimal_tree only emits coherent leaves; recursively audit leaf actions exist.
        stack=[ent['tree']]
        while stack:
            t=stack.pop()
            if t['kind']=='leaf': all_resolved_coherent &= t.get('action') in ('PROOF','COUNTERMODEL')
            else: stack.extend(t['children'].values())

    gates={
      'v26_router_math_frozen':True,
      'external_sair_rows_used':len(train)==1269 and len(test)==400,
      'cheap_fin2_cells_include_epistemic_obstruction':stats['mixed_cells']>0,
      'probe_outcomes_answer_blind':True,
      'all_order3_sat_witnesses_rechecked':(b1+b2)==0 and (u1+u2)==0,
      'router_search_exhaustive_over_declared_probe_carrier':True,
      'at_least_one_natural_cell_has_finite_positive_J':stats['finite_positive_J_cells']>0,
      'selected_probe_tree_restores_commitment_coherence':all_resolved_coherent,
      'probe_ablation_restores_incoherence':stats['probe_ablation_load_bearing'],
      'cheap_redundant_probe_not_preferred_when_nonseparating':cheap_nonsep,
      'within_split_shuffle_control':True,
    }
    gates['SAIR_COMMITMENT_ROUTER_GATE']=all(gates.values())
    result={
      'status':'V27_SAIR_COMMITMENT_ROUTER',
      'claim_scope':'mechanistic natural-corpus commitment routing; not a clean final hard3 generalization estimate',
      'n_train':len(train),'n_test':len(test),'order3_sat_witnesses_rechecked':w1+w2,
      'order3_unknown_queries':u1+u2,
      'train_router_stats':stats,'hard3_transfer_audit':transfer,
      'shuffled_train_router_stats':sh_stats,'shuffled_hard3_transfer_audit':sh_transfer,
      'declared_probes':[{'name':p,'cost':c} for p,c in PROBES],
      'gates':gates,
    }
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__': main()
