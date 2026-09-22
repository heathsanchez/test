#!/usr/bin/env python3
import argparse, json, random
from pathlib import Path
from collections import Counter

def C(g): return tuple(tuple(r) for r in g)
def sh(g): return len(g),len(g[0])
def flat(g): return [x for r in g for x in r]
def arc_bg(g): return 0 if 0 in set(flat(g)) else Counter(flat(g)).most_common(1)[0][0]
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

def macro_fit(task):
    allowed=None; dims=None
    order=list(D8)+['BG']
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if ho%hi or wo%wi:return None
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
            allowed=[[set(s) for s in row] for row in cur]; dims=(nr,nc)
        else:
            if dims!=(nr,nc):return None
            for i in range(nr):
                for j in range(nc):
                    allowed[i][j] &= cur[i][j]
                    if not allowed[i][j]:return None
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
    templ=[[c if x==b else b for x in row] for row in g]
    out=[]
    for srcrow in g:
        for rr in range(h):
            row=[]
            for x in srcrow: row += templ[rr] if x!=b else [b]*w
            out.append(row)
    return out

def mask_kron_fit(task):
    try:
        if all(C(mask_kron_apply(p['input']))==C(p['output']) for p in task['train']):return mask_kron_apply
    except Exception:pass
    return None

def scale_fit(task):
    k=None
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if ho%hi or wo%wi or ho//hi!=wo//wi:return None
        q=ho//hi
        z=[[v for v in row for _ in range(q)] for row in x for _ in range(q)]
        if C(z)!=C(y):return None
        if k is None:k=q
        elif k!=q:return None
    return lambda g:[[v for v in row for _ in range(k)] for row in g for _ in range(k)]

def tile_fit(task):
    par=None
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if ho%hi or wo%wi:return None
        kr,kc=ho//hi,wo//wi
        z=[[v for _ in range(kc) for v in row] for _ in range(kr) for row in x]
        if C(z)!=C(y):return None
        if par is None:par=(kr,kc)
        elif par!=(kr,kc):return None
    kr,kc=par
    return lambda g:[[v for _ in range(kc) for v in row] for _ in range(kr) for row in g]

F={
 'identity':fixed_fit(lambda g:[r[:] for r in g]),
 'recolor':recolor_fit,
 'rot90':fixed_fit(r90),'rot180':fixed_fit(r180),'rot270':fixed_fit(r270),
 'flip_h':fixed_fit(H),'flip_v':fixed_fit(V),'transpose':fixed_fit(T),
 'scale':scale_fit,'tile':tile_fit,
 'macroblock_transform':macro_fit,
 'mask_kronecker_complement':mask_kron_fit,
}
BASE=['identity','recolor']

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

def load(root):
    d=root/'data'/'evaluation'
    if not d.exists():d=root/'evaluation'
    return {p.stem:json.loads(p.read_text()) for p in sorted(d.glob('*.json'))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arc-root',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--n',type=int,default=50);ap.add_argument('--seed',type=int,default=1729)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True);tasks=load(a.arc_root)
    smoke=[]
    for tid,fam in [('00576224','macroblock_transform'),('0692e18c','mask_kronecker_complement')]:
        fn=F[fam](tasks[tid]); tr=fn is not None
        te=tr and score(tasks[tid],tuple(C(fn(p['input'])) for p in tasks[tid]['test']))=='exact'
        smoke.append({'task':tid,'family':fam,'train_exact':tr,'test_exact':bool(te),'pass':bool(tr and te)})
    print(json.dumps({'smoke':smoke}),flush=True)
    if not all(x['pass'] for x in smoke):
        (a.out_dir/'summary.json').write_text(json.dumps({'status':'SMOKE_FAIL','smoke':smoke},indent=2));raise SystemExit(2)

    ids=sorted(tasks);random.Random(a.seed).shuffle(ids);ids=ids[:a.n]
    active=list(BASE);installed={x:0 for x in BASE};records=[];constructions=[];transfers=[]
    for i,tid in enumerate(ids,1):
        t=tasks[tid]
        fo,fm,_=select(t,BASE); frozen=score(t,fo)
        do,dm,_=select(t,active); dev=score(t,do)
        before=list(active); built=None; diag=None
        if dev!='exact':
            dormant=[n for n in F if n not in active]
            cd=classes(t,dormant)
            diag={'dormant_consequence_classes':len(cd)}
            if len(cd)==1:
                _,members=next(iter(cd.items()))
                built=min(members,key=list(F).index)
                active.append(built);installed[built]=i
                constructions.append({'i':i,'task':tid,'family':built,'certificate':'exact_train_unique_test_input_consequence'})
                do,dm,_=select(t,active);dev=score(t,do)
        reused=[n for n in dm if n not in BASE and installed.get(n,10**9)<i]
        causal=False;abl=None
        if dev=='exact' and frozen!='exact' and reused:
            ao,_,_=select(t,[n for n in active if n not in reused]);abl=score(t,ao);causal=abl!='exact'
            if causal:transfers.append({'i':i,'task':tid,'families':reused,'ablation':abl})
        r={'i':i,'task':tid,'frozen':frozen,'developmental':dev,'active_before':before,'constructed':built,'diag':diag,'reused_prior':reused,'causal_transfer':causal,'ablation':abl,'active_after':list(active)}
        records.append(r);print(json.dumps(r),flush=True)
    summary={'status':'ARC50_DEV_V3','smoke':smoke,'seed':a.seed,'n':len(ids),'base':BASE,'final_active':active,'constructions':constructions,'causal_transfers':transfers,'frozen_exact':sum(r['frozen']=='exact' for r in records),'developmental_exact':sum(r['developmental']=='exact' for r in records),'frozen_false':sum(r['frozen']=='false' for r in records),'developmental_false':sum(r['developmental']=='false' for r in records),'strong_gate':bool(transfers),'contract':'construction uses train outputs + test inputs only; test outputs final scoring only'}
    (a.out_dir/'records.json').write_text(json.dumps(records,indent=2));(a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
