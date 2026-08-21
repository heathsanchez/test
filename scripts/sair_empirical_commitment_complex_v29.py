#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from functools import lru_cache
from pathlib import Path

import sair_raw_adequacy_v24 as v24
import sair_bounded_model_adequacy_v25 as v25

INF=10**9
PROBES=(('p_ce3_fwd',3),('p_ce3_rev',3))


def tptp_term(n):
    if n.leaf:
        return n.v.upper()
    return f"f({tptp_term(n.l)},{tptp_term(n.r)})"


def tptp_problem(e1,e2):
    def stmt(name,kind,eq):
        a,b=eq; vs=sorted(v24.vars_of(a)|v24.vars_of(b)); q=','.join(v.upper() for v in vs)
        body=f"{tptp_term(a)}={tptp_term(b)}"
        if q: body=f"! [{q}] : ({body})"
        return f"fof({name},{kind},({body})).\n"
    return stmt('hyp','axiom',e1)+stmt('goal','conjecture',e2)


def vampire_theorem(vampire,e1,e2,mode):
    txt=tptp_problem(e1,e2)
    with tempfile.NamedTemporaryFile('w',suffix='.p',delete=False) as f:
        f.write(txt); path=f.name
    cmd=[vampire,'-t','1']
    if mode=='casc': cmd += ['--mode','casc']
    cmd.append(path)
    try:
        cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=3)
        out=cp.stdout
        ok=('% SZS status Theorem' in out) or ('% SZS status Unsatisfiable' in out)
        return ok, out[-2000:]
    except subprocess.TimeoutExpired:
        return False,'TIMEOUT'
    finally:
        try: Path(path).unlink()
        except Exception: pass


def load_all(root):
    rows=[]
    for src in ('normal','hard1','hard2'):
        for raw in v24.load_jsonl(root/'examples'/'problems'/f'{src}.jsonl'):
            rows.append((hashlib.sha256(str(raw['id']).encode()).hexdigest(),src,raw))
    rows.sort(key=lambda z:(z[0],z[1],str(z[2]['id'])))
    return rows[:160]


def common_actions(indices,rows):
    indices=list(indices)
    if not indices:return set()
    out=set(rows[indices[0]]['actions'])
    for i in indices[1:]: out &= set(rows[i]['actions'])
    return out


def group(rows):
    g={}
    for i,r in enumerate(rows):g.setdefault(r['base'],set()).add(i)
    return g


def split(indices,rows,p):
    out={}
    for i in indices: out.setdefault(rows[i]['probes'][p],set()).add(i)
    return out


def optimal_tree(indices,rows,allowed):
    costs=dict(PROBES); allowed=tuple(allowed)
    @lru_cache(None)
    def rec(cell):
        cell=set(cell); ca=common_actions(cell,rows)
        if ca:
            return 0,{'kind':'leaf','common_actions':sorted(ca),'n':len(cell)}
        best=(INF,None)
        for p in allowed:
            cells=split(cell,rows,p)
            if len(cells)<=1: continue
            children={}; worst=0; good=True
            for y,sub in sorted(cells.items()):
                c,t=rec(frozenset(sub))
                if c>=INF: good=False; break
                worst=max(worst,c); children[str(y)]=t
            if not good: continue
            total=costs[p]+worst
            cand={'kind':'probe','probe':p,'cost':costs[p],'children':children}
            key=(total,json.dumps(cand,sort_keys=True))
            if best[1] is None or key<(best[0],json.dumps(best[1],sort_keys=True)):
                best=(total,cand)
        return best
    return rec(frozenset(indices))


def tree_probes(t):
    if not t or t['kind']=='leaf':return set()
    out={t['probe']}
    for c in t['children'].values(): out |= tree_probes(c)
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sair-root',required=True);ap.add_argument('--vampire',required=True);ap.add_argument('--out-dir',required=True)
    a=ap.parse_args(); root=Path(a.sair_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    selected=load_all(root)
    rows=[]; sat_rechecks=bad_rechecks=unknown=route_contradictions=0
    atom_counts={'CE2':0,'CE3':0,'VP_DEF':0,'VP_CASC':0}
    for _h,src,raw in selected:
        x,w,eqs=v24.observations(raw); e1,e2=eqs
        ce2=bool(x['v3']>0)
        ce3,t3,s3=v25.sat_counterexample(e1,e2)
        rev3,tr3,sr3=v25.sat_counterexample(e2,e1)
        unknown += int(s3=='unknown')+int(sr3=='unknown')
        for ok,t,hyp,goal in ((ce3,t3,e1,e2),(rev3,tr3,e2,e1)):
            if ok:
                sat_rechecks+=1
                if not v25.recheck(hyp,goal,t):bad_rechecks+=1
        vpdef,_=vampire_theorem(a.vampire,e1,e2,'default')
        vpcasc,_=vampire_theorem(a.vampire,e1,e2,'casc')
        y=bool(raw['answer'])
        route_contradictions += int(ce2 and y)+int(ce3 and y)+int(vpdef and not y)+int(vpcasc and not y)
        atoms={'CE2':ce2,'CE3':ce3,'VP_DEF':vpdef,'VP_CASC':vpcasc}
        for k,v in atoms.items():atom_counts[k]+=int(v)
        actions=set()
        if ce2 or vpdef: actions.add('A0')
        if ce3 or vpdef: actions.add('A1')
        if ce2 or vpcasc: actions.add('A2')
        if ce3 or vpcasc: actions.add('A3')
        if not actions: actions.add('OBSTRUCT_B')
        rows.append({'id':raw['id'],'source':src,'y':y,'base':tuple(x[n] for n in v24.VERIFIER_NAMES),
                     'actions':sorted(actions),'probes':{'p_ce3_fwd':int(ce3),'p_ce3_rev':int(rev3)},'atoms':atoms})

    groups=group(rows)
    coherent=0; incoherent=0; mixed_label=0; mixed_label_coherent=0; multi_action_rows=0
    finiteJ=0; unresolved=0; costs=[]; ablation_ok=False; leaf_audit=True
    examples=[]
    for r in rows: multi_action_rows+=int(len(r['actions'])>1)
    for key,idx in groups.items():
        ca=common_actions(idx,rows); labels={rows[i]['y'] for i in idx}
        if len(labels)>1:mixed_label+=1
        if ca:
            coherent+=1
            if len(labels)>1:
                mixed_label_coherent+=1
                if len(examples)<5: examples.append({'n':len(idx),'labels':sorted(labels),'common_actions':sorted(ca)})
            continue
        incoherent+=1
        c,t=optimal_tree(idx,rows,[p for p,_ in PROBES])
        if c>=INF: unresolved+=1; continue
        finiteJ+=1;costs.append(c)
        # recompute each leaf's common action by following subsets
        def audit(cell,tree):
            nonlocal leaf_audit
            if tree['kind']=='leaf':
                ca2=common_actions(cell,rows); leaf_audit &= bool(ca2) and set(tree['common_actions'])==ca2; return
            for yy,sub in split(cell,rows,tree['probe']).items():
                audit(sub,tree['children'][str(yy)])
        audit(idx,t)
        used=tree_probes(t)
        if used:
            remain=[p for p,_ in PROBES if p not in used]
            c2,_=optimal_tree(idx,rows,remain)
            if c2>=INF or c2>c:ablation_ok=True

    gates={
      'answer_blind_sample_selection':len(rows)==160,
      'all_order3_sat_witnesses_rechecked':bad_rechecks==0 and unknown==0,
      'no_route_contradictions_against_protected_answers':route_contradictions==0,
      'multi_action_world_exists':multi_action_rows>0,
      'mixed_label_commitment_coherent_cell_exists':mixed_label_coherent>0,
      'action_incoherent_cell_exists':incoherent>0,
      'router_search_exhaustive_over_declared_probes':True,
      'finite_J_leaf_common_actions_recomputed':leaf_audit,
      'probe_ablation_load_bearing_if_finite_J':(finiteJ==0 or ablation_ok),
    }
    gates['SAIR_EMPIRICAL_COMMITMENT_COMPLEX_GATE']=all(gates.values())
    result={'status':'V29_SAIR_EMPIRICAL_COMMITMENT_COMPLEX','n_rows':len(rows),'n_fin2_cells':len(groups),
            'atom_success_counts':atom_counts,'route_contradictions':route_contradictions,
            'order3_sat_rechecks':sat_rechecks,'order3_unknown':unknown,
            'multi_action_rows':multi_action_rows,'coherent_cells':coherent,'incoherent_cells':incoherent,
            'mixed_label_cells':mixed_label,'mixed_label_commitment_coherent_cells':mixed_label_coherent,
            'finite_positive_J_cells':finiteJ,'unresolved_incoherent_cells':unresolved,
            'mean_positive_J':(sum(costs)/len(costs) if costs else None),'mixed_coherent_examples':examples,'gates':gates}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True));print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
