#!/usr/bin/env python3
import argparse,json,random
from pathlib import Path
from collections import Counter

def C(g): return tuple(tuple(r) for r in g)
def sh(g): return len(g),len(g[0])
def flat(g): return [x for r in g for x in r]
def bg(g): return 0 if 0 in set(flat(g)) else Counter(flat(g)).most_common(1)[0][0]
def r90(g): return [list(r) for r in zip(*g[::-1])]
def r180(g): return r90(r90(g))
def r270(g): return r90(r180(g))
def H(g): return [r[::-1] for r in g]
def V(g): return g[::-1]
def T(g): return [list(r) for r in zip(*g)]
D8={'I':lambda g:[r[:] for r in g],'R90':r90,'R180':r180,'R270':r270,'H':H,'V':V,'T':T,'TH':lambda g:H(T(g))}
ORDER=list(D8)+['BG']

def apply_ast(ast,g):
    typ=ast[0]
    if typ=='U': return D8[ast[1]](g)
    if typ=='S':
        k=ast[1]; return [[x for x in row for _ in range(k)] for row in g for _ in range(k)]
    if typ=='B':
        _,nr,nc,labels=ast; h,w=sh(g); b=bg(g); out=[]; q=iter(labels)
        grid=[[next(q) for _ in range(nc)] for _ in range(nr)]
        for prow in grid:
            bs=[]
            for z in prow:
                block=[[b]*w for _ in range(h)] if z=='BG' else D8[z](g)
                if sh(block)!=(h,w): raise ValueError('block transform changes cell shape')
                bs.append(block)
            for r in range(h): out.append(sum((x[r] for x in bs),[]))
        return out
    raise ValueError(ast)

def synth_unary(task):
    out=[]
    for n,f in D8.items():
        if n=='I': continue
        try:
            if all(C(f(p['input']))==C(p['output']) for p in task['train']): out.append(('U',n))
        except Exception: pass
    return out

def synth_scale(task):
    k=None
    for p in task['train']:
        hi,wi=sh(p['input']); ho,wo=sh(p['output'])
        if ho%hi or wo%wi or ho//hi!=wo//wi:return []
        q=ho//hi
        if q<2 or q>6:return []
        z=[[x for x in row for _ in range(q)] for row in p['input'] for _ in range(q)]
        if C(z)!=C(p['output']):return []
        if k is None:k=q
        elif k!=q:return []
    return [('S',k)] if k else []

def synth_block(task):
    allowed=None; dims=None
    for p in task['train']:
        x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
        if ho%hi or wo%wi:return []
        nr,nc=ho//hi,wo//wi
        if nr*nc<=1 or nr>8 or nc>8:return []
        cur=[]
        for br in range(nr):
            row=[]
            for bc in range(nc):
                block=[rr[bc*wi:(bc+1)*wi] for rr in y[br*hi:(br+1)*hi]]
                s=set()
                for n,f in D8.items():
                    try:
                        if sh(f(x))==(hi,wi) and C(f(x))==C(block): s.add(n)
                    except Exception: pass
                if len(set(flat(block)))==1 and flat(block)[0]==bg(x): s.add('BG')
                if not s:return []
                row.append(s)
            cur.append(row)
        if allowed is None: allowed=[[set(s) for s in r] for r in cur]; dims=(nr,nc)
        else:
            if dims!=(nr,nc):return []
            for i in range(nr):
                for j in range(nc):
                    allowed[i][j]&=cur[i][j]
                    if not allowed[i][j]:return []
    labels=[]
    for i in range(dims[0]):
        for j in range(dims[1]): labels.append(next(n for n in ORDER if n in allowed[i][j]))
    return [('B',dims[0],dims[1],tuple(labels))]

def synth(task):
    xs=synth_unary(task)+synth_scale(task)+synth_block(task); good=[]
    for a in xs:
        try:
            if all(C(apply_ast(a,p['input']))==C(p['output']) for p in task['train']):good.append(a)
        except Exception: pass
    return sorted(set(good),key=repr)

def fits_train(ast,task):
    try:return all(C(apply_ast(ast,p['input']))==C(p['output']) for p in task['train'])
    except Exception:return False

def score(ast,task):
    try:return all(C(apply_ast(ast,p['input']))==C(p['output']) for p in task['test'])
    except Exception:return False

def load(root,split):
    d=root/'data'/split
    return {p.stem:json.loads(p.read_text()) for p in sorted(d.glob('*.json'))}

def base_exact(task):
    if all(C(p['input'])==C(p['output']) for p in task['train']): return all(C(p['input'])==C(p['output']) for p in task['test'])
    mp={}
    for p in task['train']:
        if sh(p['input'])!=sh(p['output']):return False
        for a,b in zip(flat(p['input']),flat(p['output'])):
            if a in mp and mp[a]!=b:return False
            mp[a]=b
    if not mp:return False
    return all(C([[mp.get(x,x) for x in r] for r in p['input']])==C(p['output']) for p in task['test'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arc-root',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--seed',type=int,default=1729)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    tr=load(a.arc_root,'training');ev=load(a.arc_root,'evaluation')
    ids=list(tr);random.Random(a.seed).shuffle(ids)
    registry=[];sources={};development=[]
    for i,tid in enumerate(ids,1):
        t=tr[tid];cands=synth(t);classes={}
        for ast in cands:
            try:o=tuple(C(apply_ast(ast,p['input'])) for p in t['test'])
            except Exception:continue
            classes.setdefault(o,[]).append(ast)
        built=None
        if len(classes)==1:
            _,asts=next(iter(classes.items()));built=min(asts,key=repr)
            if built not in registry:registry.append(built);sources[repr(built)]=tid
        development.append({'i':i,'task':tid,'candidates':len(cands),'built':repr(built) if built else None})
    transfers=[];reg_exact=0;base=0
    eids=list(ev);random.Random(a.seed+1).shuffle(eids)
    for j,tid in enumerate(eids,1):
        t=ev[tid];b=base_exact(t);base+=int(b)
        fitting=[ast for ast in registry if fits_train(ast,t)];classes={}
        for ast in fitting:
            try:o=tuple(C(apply_ast(ast,p['input'])) for p in t['test'])
            except Exception:continue
            classes.setdefault(o,[]).append(ast)
        if len(classes)!=1:continue
        _,asts=next(iter(classes.items()));chosen=min(asts,key=repr)
        if score(chosen,t):
            reg_exact+=1
            if not b:
                rem=[x for x in registry if x!=chosen and fits_train(x,t)]
                causal=not any(score(x,t) for x in rem)
                if causal:transfers.append({'j':j,'task':tid,'ast':repr(chosen),'source_task':sources.get(repr(chosen)),'ablation':'lost_exact'})
    summary={'status':'ARC400_PROGRAM_SYNTHESIS_V5','claim':'bounded AST synthesis from D8/BG/block-assembly/scale primitives; no dormant named operator families','development_tasks':len(tr),'evaluation_tasks':len(ev),'registry_size':len(registry),'registry':[repr(x) for x in registry],'base_exact':base,'registry_exact':reg_exact,'causal_source_distinct_transfers':transfers,'strong_gate':bool(transfers)}
    (a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2));(a.out_dir/'development.json').write_text(json.dumps(development,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
