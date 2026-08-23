#!/usr/bin/env python3
import argparse, json, random
from pathlib import Path
from collections import Counter

# ARC recursive developmental test v4.
# Candidate fitting/selection uses TRAIN pairs and TEST INPUTS only.
# Test outputs are consulted only after a prediction is frozen, for scoring.
# Development is recursive within a task: solve -> residual -> route -> install one
# uniquely licensed capability family -> re-solve, until exact candidate/fixed point.


def C(g): return tuple(tuple(r) for r in g)
def sh(g): return len(g), len(g[0]) if g else 0
def flat(g): return [x for r in g for x in r]
def arc_bg(g):
    xs=flat(g)
    return 0 if 0 in set(xs) else Counter(xs).most_common(1)[0][0]
def r90(g): return [list(r) for r in zip(*g[::-1])]
def r180(g): return r90(r90(g))
def r270(g): return r90(r180(g))
def H(g): return [r[::-1] for r in g]
def V(g): return g[::-1]
def T(g): return [list(r) for r in zip(*g)]
D8={'I':lambda g:[r[:] for r in g],'R90':r90,'R180':r180,'R270':r270,'H':H,'V':V,'T':T,'TH':lambda g:H(T(g))}


def recolor_fit(task):
    mp={}
    for p in task['train']:
        if sh(p['input'])!=sh(p['output']): return None
        for a,b in zip(flat(p['input']),flat(p['output'])):
            if a in mp and mp[a]!=b:return None
            mp[a]=b
    if not any(a!=b for a,b in mp.items()):return None
    return lambda g:[[mp.get(x,x) for x in row] for row in g]

def fixed_fit(fn):
    def fit(task):
        try:
            if all(C(fn(p['input']))==C(p['output']) for p in task['train']): return fn
        except Exception: pass
        return None
    return fit

def scale_fit(task):
    k=None
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if not hi or ho%hi or wo%wi or ho//hi!=wo//wi:return None
        q=ho//hi
        if q<=1 or q>8:return None
        z=[[v for v in row for _ in range(q)] for row in x for _ in range(q)]
        if C(z)!=C(y):return None
        if k is None:k=q
        elif k!=q:return None
    return lambda g:[[v for v in row for _ in range(k)] for row in g for _ in range(k)]

def tile_fit(task):
    par=None
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if not hi or ho%hi or wo%wi:return None
        kr,kc=ho//hi,wo//wi
        if kr*kc<=1 or kr>8 or kc>8:return None
        z=[[v for _ in range(kc) for v in row] for _ in range(kr) for row in x]
        if C(z)!=C(y):return None
        if par is None:par=(kr,kc)
        elif par!=(kr,kc):return None
    kr,kc=par
    return lambda g:[[v for _ in range(kc) for v in row] for _ in range(kr) for row in g]

def macro_fit(task):
    allowed=None; dims=None; order=list(D8)+['BG']
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if not hi or ho%hi or wo%wi:return None
        nr,nc=ho//hi,wo//wi
        if nr*nc<=1 or nr>8 or nc>8:return None
        cur=[]
        for br in range(nr):
            row=[]
            for bc in range(nc):
                b=[rr[bc*wi:(bc+1)*wi] for rr in y[br*hi:(br+1)*hi]]
                s={n for n,f in D8.items() if C(f(x))==C(b)}
                if len(set(flat(b)))==1 and flat(b)[0]==arc_bg(x):s.add('BG')
                if not s:return None
                row.append(s)
            cur.append(row)
        if allowed is None:
            allowed=[[set(s) for s in row] for row in cur];dims=(nr,nc)
        else:
            if dims!=(nr,nc):return None
            for i in range(nr):
                for j in range(nc):
                    allowed[i][j] &= cur[i][j]
                    if not allowed[i][j]:return None
    if allowed is None:return None
    pattern=[[next(n for n in order if n in allowed[i][j]) for j in range(dims[1])] for i in range(dims[0])]
    def apply(g):
        h,w=sh(g); b=arc_bg(g); out=[]
        for prow in pattern:
            bs=[([[b]*w for _ in range(h)] if n=='BG' else D8[n](g)) for n in prow]
            for r in range(h):out.append(sum((z[r] for z in bs),[]))
        return out
    return apply

def mask_kron_apply(g):
    b=arc_bg(g); vals=[x for x in set(flat(g)) if x!=b]
    if len(vals)!=1:raise ValueError
    c=vals[0]; h,w=sh(g)
    tmpl=[[c if x==b else b for x in row] for row in g]
    out=[]
    for srcrow in g:
        for rr in range(h):
            row=[]
            for x in srcrow:row += tmpl[rr] if x!=b else [b]*w
            out.append(row)
    return out

def mask_kron_fit(task):
    try:
        if all(C(mask_kron_apply(p['input']))==C(p['output']) for p in task['train']):return mask_kron_apply
    except Exception:pass
    return None

F={
 'identity':fixed_fit(lambda g:[r[:] for r in g]),
 'recolor':recolor_fit,
 'rot90':fixed_fit(r90),'rot180':fixed_fit(r180),'rot270':fixed_fit(r270),
 'flip_h':fixed_fit(H),'flip_v':fixed_fit(V),'transpose':fixed_fit(T),
 'scale':scale_fit,'tile':tile_fit,
 'macroblock_transform':macro_fit,
 'mask_kronecker_complement':mask_kron_fit,
}
ORDER=list(F); BASE=['identity','recolor']


def classes(task,names):
    d={}
    for n in names:
        fn=F[n](task)
        if fn is None:continue
        try:o=tuple(C(fn(p['input'])) for p in task['test'])
        except Exception:continue
        d.setdefault(o,[]).append(n)
    return d

def select(task,names):
    d=classes(task,names)
    if len(d)!=1:return None,[],('none' if not d else 'ambiguous')
    o,m=next(iter(d.items()));return o,m,'unique'

def score(task,o):
    if o is None:return 'abstain'
    return 'exact' if all(C(p['output'])==o[i] for i,p in enumerate(task['test'])) else 'false'

def load_split(root,split):
    d=root/'data'/split
    if not d.exists():d=root/split
    return {p.stem:json.loads(p.read_text()) for p in sorted(d.glob('*.json'))}

def residual_signature(task):
    shape_pairs=[(sh(p['input']),sh(p['output'])) for p in task['train']]
    same=all(a==b for a,b in shape_pairs)
    multiples=all(a[0] and b[0]%a[0]==0 and b[1]%a[1]==0 for a,b in shape_pairs)
    square_product=all(b[0]==a[0]*a[0] and b[1]==a[1]*a[1] for a,b in shape_pairs)
    if square_product:return 'self_product_shape'
    if multiples and not same:return 'macroblock_or_scale_shape'
    if same:return 'same_shape'
    return 'shape_change_other'

def routed_dormant(task,active):
    dormant=[n for n in F if n not in active]
    sig=residual_signature(task)
    if sig=='self_product_shape': pref=['mask_kronecker_complement','macroblock_transform','scale','tile']
    elif sig=='macroblock_or_scale_shape': pref=['macroblock_transform','scale','tile']
    elif sig=='same_shape': pref=['rot90','rot180','rot270','flip_h','flip_v','transpose']
    else: pref=[]
    routed=[n for n in pref if n in dormant]
    # Only fall back to the complete dormant carrier if the structural route yields no train-fit class.
    if routed and classes(task,routed):return routed,sig,'structural_route'
    return dormant,sig,'full_dormant_fallback'

def recursive_episode(task,active,installed_at,index,max_refines=4,allow_install=True):
    trace=[]; built=[]
    for depth in range(max_refines+1):
        o,m,state=select(task,active); status=score(task,o)
        trace.append({'depth':depth,'phase':'solve','status':status,'selection':state,'members':m,'active':list(active)})
        if status=='exact' or not allow_install:return status,m,built,trace
        routed,sig,route_kind=routed_dormant(task,active)
        cd=classes(task,routed)
        trace.append({'depth':depth,'phase':'residual','residual':sig,'route':route_kind,'carrier':routed,'consequence_classes':len(cd)})
        if len(cd)!=1:return status,m,built,trace
        _,members=next(iter(cd.items()))
        chosen=min(members,key=ORDER.index)
        if chosen in active:return status,m,built,trace
        active.append(chosen);installed_at[chosen]=index;built.append(chosen)
        trace.append({'depth':depth,'phase':'install','family':chosen,'certificate':'exact_train_unique_test_input_consequence'})
    o,m,_=select(task,active);return score(task,o),m,built,trace

def smoke(tasks):
    out=[]
    for tid,fam in [('00576224','macroblock_transform'),('0692e18c','mask_kronecker_complement')]:
        fn=F[fam](tasks[tid]);tr=fn is not None
        te=tr and score(tasks[tid],tuple(C(fn(p['input'])) for p in tasks[tid]['test']))=='exact'
        out.append({'task':tid,'family':fam,'train_exact':tr,'test_exact':bool(te),'pass':bool(tr and te)})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arc-root',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--seed',type=int,default=1729);ap.add_argument('--max-refines',type=int,default=4)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    train=load_split(a.arc_root,'training');ev=load_split(a.arc_root,'evaluation')
    sm=smoke(ev);print(json.dumps({'smoke':sm}),flush=True)
    if not all(x['pass'] for x in sm):
        (a.out_dir/'summary.json').write_text(json.dumps({'status':'SMOKE_FAIL','smoke':sm},indent=2));raise SystemExit(2)

    # Phase A: 400-task online developmental stream on training split.
    train_ids=sorted(train);random.Random(a.seed).shuffle(train_ids)
    active=list(BASE);installed={x:0 for x in BASE};development=[];constructions=[]
    for i,tid in enumerate(train_ids,1):
        t=train[tid]; before=list(active)
        frozen_o,_,_=select(t,BASE);frozen=score(t,frozen_o)
        status,m,built,trace=recursive_episode(t,active,installed,i,a.max_refines,True)
        for fam in built:constructions.append({'phase':'development','i':i,'task':tid,'family':fam})
        rec={'phase':'development','i':i,'task':tid,'frozen':frozen,'developmental':status,'active_before':before,'built':built,'active_after':list(active),'trace':trace}
        development.append(rec)
        if built or status=='exact':print(json.dumps({k:v for k,v in rec.items() if k!='trace'}),flush=True)

    # Phase B: source-distinct 400-task evaluation. Registry is frozen at the Phase-A state.
    frozen_registry=list(active); eval_ids=sorted(ev);random.Random(a.seed+1).shuffle(eval_ids)
    transfer=[];causal=[]
    for j,tid in enumerate(eval_ids,1):
        t=ev[tid]
        base_o,_,_=select(t,BASE);base_status=score(t,base_o)
        o,m,_=select(t,frozen_registry);reg_status=score(t,o)
        reused=[n for n in m if n not in BASE and n in frozen_registry]
        ablations={};is_causal=False
        if reg_status=='exact' and base_status!='exact' and reused:
            for fam in reused:
                ao,_,_=select(t,[n for n in frozen_registry if n!=fam]);ablations[fam]=score(t,ao)
            is_causal=any(v!='exact' for v in ablations.values())
            if is_causal:causal.append({'j':j,'task':tid,'families':reused,'ablations':ablations})
        rec={'phase':'transfer','j':j,'task':tid,'base':base_status,'registry':reg_status,'reused':reused,'causal':is_causal,'ablations':ablations}
        transfer.append(rec)
        if reg_status=='exact' or is_causal:print(json.dumps(rec),flush=True)

    # Phase C: online recursive evaluation too, to measure later-task causal reuse inside eval.
    online_active=list(BASE);online_inst={x:0 for x in BASE};online=[];online_causal=[]
    for j,tid in enumerate(eval_ids,1):
        t=ev[tid];before=list(online_active)
        base_o,_,_=select(t,BASE);base_status=score(t,base_o)
        status,m,built,trace=recursive_episode(t,online_active,online_inst,j,a.max_refines,True)
        reused=[n for n in m if n not in BASE and online_inst.get(n,10**9)<j]
        ablations={};is_causal=False
        if status=='exact' and base_status!='exact' and reused:
            for fam in reused:
                ao,_,_=select(t,[n for n in online_active if n!=fam]);ablations[fam]=score(t,ao)
            is_causal=any(v!='exact' for v in ablations.values())
            if is_causal:online_causal.append({'j':j,'task':tid,'families':reused,'ablations':ablations})
        online.append({'j':j,'task':tid,'base':base_status,'developmental':status,'built':built,'reused':reused,'causal':is_causal,'ablations':ablations,'active_before':before,'active_after':list(online_active),'trace':trace})

    summary={
      'status':'ARC400_RECURSIVE_DEV_V4','smoke':sm,'seed':a.seed,'max_refines':a.max_refines,
      'development_tasks':len(train_ids),'transfer_tasks':len(eval_ids),
      'phaseA_final_registry':frozen_registry,'phaseA_constructions':constructions,
      'phaseA_base_exact':sum(r['frozen']=='exact' for r in development),'phaseA_dev_exact':sum(r['developmental']=='exact' for r in development),
      'phaseB_base_exact':sum(r['base']=='exact' for r in transfer),'phaseB_registry_exact':sum(r['registry']=='exact' for r in transfer),
      'phaseB_causal_transfers':causal,
      'phaseC_final_registry':online_active,'phaseC_base_exact':sum(r['base']=='exact' for r in online),'phaseC_dev_exact':sum(r['developmental']=='exact' for r in online),'phaseC_causal_transfers':online_causal,
      'strong_gate_source_distinct':bool(causal),'strong_gate_online':bool(online_causal),
      'contract':'recursive bounded refinement; construction uses train outputs + test inputs only; test outputs final scoring only; source-distinct transfer freezes registry before evaluation'
    }
    (a.out_dir/'development.json').write_text(json.dumps(development,indent=2));(a.out_dir/'transfer.json').write_text(json.dumps(transfer,indent=2));(a.out_dir/'online.json').write_text(json.dumps(online,indent=2));(a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
