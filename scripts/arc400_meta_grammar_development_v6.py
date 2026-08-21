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
BASE_GRAMMAR={'U'}
META_RULES=('INTEGER_SCALE_RESIDUAL=>S','INPUT_BLOCK_FACTORIZATION_RESIDUAL=>B')

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
                zz=[[b]*w for _ in range(h)] if z=='BG' else D8[z](g)
                if sh(zz)!=(h,w): raise ValueError('shape-changing tile')
                bs.append(zz)
            for r in range(h): out.append(sum((x[r] for x in bs),[]))
        return out
    raise ValueError(ast)

def synth_U(task):
    out=[]
    for n,f in D8.items():
        try:
            if all(C(f(p['input']))==C(p['output']) for p in task['train']): out.append(('U',n))
        except Exception: pass
    return out

def synth_S(task):
    k=None
    for p in task['train']:
        hi,wi=sh(p['input']);ho,wo=sh(p['output'])
        if ho%hi or wo%wi or ho//hi!=wo//wi:return []
        q=ho//hi
        if q<2 or q>6:return []
        z=[[x for x in row for _ in range(q)] for row in p['input'] for _ in range(q)]
        if C(z)!=C(p['output']):return []
        if k is None:k=q
        elif k!=q:return []
    return [('S',k)] if k else []

def synth_B(task):
    allowed=None;dims=None
    for p in task['train']:
        x,y=p['input'],p['output'];hi,wi=sh(x);ho,wo=sh(y)
        if ho%hi or wo%wi:return []
        nr,nc=ho//hi,wo//wi
        if nr*nc<=1 or nr>8 or nc>8:return []
        cur=[]
        for br in range(nr):
            row=[]
            for bc in range(nc):
                block=[rr[bc*wi:(bc+1)*wi] for rr in y[br*hi:(br+1)*wi]] if False else [rr[bc*wi:(bc+1)*wi] for rr in y[br*hi:(br+1)*hi]]
                s=set()
                for n,f in D8.items():
                    try:
                        z=f(x)
                        if sh(z)==sh(x) and C(z)==C(block):s.add(n)
                    except Exception:pass
                if len(set(flat(block)))==1 and flat(block)[0]==bg(x):s.add('BG')
                if not s:return []
                row.append(s)
            cur.append(row)
        if allowed is None:allowed=[[set(s) for s in r] for r in cur];dims=(nr,nc)
        else:
            if dims!=(nr,nc):return []
            for i in range(nr):
                for j in range(nc):
                    allowed[i][j]&=cur[i][j]
                    if not allowed[i][j]:return []
    labels=[]
    for i in range(dims[0]):
        for j in range(dims[1]):labels.append(next(n for n in ORDER if n in allowed[i][j]))
    return [('B',dims[0],dims[1],tuple(labels))]

def synth(task,grammar):
    xs=[]
    if 'U' in grammar:xs+=synth_U(task)
    if 'S' in grammar:xs+=synth_S(task)
    if 'B' in grammar:xs+=synth_B(task)
    good=[]
    for a in xs:
        try:
            if all(C(apply_ast(a,p['input']))==C(p['output']) for p in task['train']):good.append(a)
        except Exception:pass
    return sorted(set(good),key=repr)

def residual(task,grammar):
    # Mechanical residual signatures only; no test-output access.
    scale=synth_S(task) if 'S' not in grammar else []
    block=synth_B(task) if 'B' not in grammar else []
    return {'integer_scale_factorization':bool(scale),'input_block_factorization':bool(block),
            'scale_witness':repr(scale[0]) if scale else None,'block_witness':repr(block[0]) if block else None}

def refine_grammar(r,grammar):
    proposals=[]
    if r['integer_scale_factorization'] and 'S' not in grammar:proposals.append('S')
    if r['input_block_factorization'] and 'B' not in grammar:proposals.append('B')
    # deterministic minimum meta-rule; each proposal has an explicit residual witness.
    return proposals[0] if proposals else None

def consequences(task,asts):
    d={}
    for a in asts:
        try:o=tuple(C(apply_ast(a,p['input'])) for p in task['test'])
        except Exception:continue
        d.setdefault(o,[]).append(a)
    return d

def score_output(task,o):return o is not None and all(o[i]==C(p['output']) for i,p in enumerate(task['test']))
def load(root,split):
    d=root/'data'/split
    return {p.stem:json.loads(p.read_text()) for p in sorted(d.glob('*.json'))}

def solve_with_grammar(task,grammar):
    asts=synth(task,grammar);cl=consequences(task,asts)
    if len(cl)!=1:return None,None,asts
    o,m=next(iter(cl.items()));return o,min(m,key=repr),asts

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arc-root',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--seed',type=int,default=1729);ap.add_argument('--max-refines',type=int,default=3)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    tr=load(a.arc_root,'training');ev=load(a.arc_root,'evaluation')
    ids=list(tr);random.Random(a.seed).shuffle(ids)
    grammar=set(BASE_GRAMMAR);grammar_events=[];program_registry=[];program_sources={};dev=[]
    for i,tid in enumerate(ids,1):
        t=tr[tid];before=sorted(grammar);built=[];o,ast,_=solve_with_grammar(t,grammar)
        steps=0
        while o is None and steps<a.max_refines:
            r=residual(t,grammar);k=refine_grammar(r,grammar)
            if k is None:break
            grammar.add(k);grammar_events.append({'i':i,'task':tid,'constructor':k,'residual':r,'meta_rule':META_RULES[0] if k=='S' else META_RULES[1]});built.append(k);steps+=1
            o,ast,_=solve_with_grammar(t,grammar)
        exact=score_output(t,o)
        if exact and ast is not None and ast not in program_registry:
            program_registry.append(ast);program_sources[repr(ast)]=tid
        dev.append({'i':i,'task':tid,'grammar_before':before,'grammar_after':sorted(grammar),'constructors_added':built,'ast':repr(ast) if ast else None,'exact':exact})
    learned_grammar=set(grammar)
    # Source-distinct evaluation: base U grammar vs learned grammar. New ASTs may be synthesized per task.
    eids=list(ev);random.Random(a.seed+1).shuffle(eids);transfers=[];base_exact=learned_exact=0;composite_transfers=0
    for j,tid in enumerate(eids,1):
        t=ev[tid]
        bo,bast,_=solve_with_grammar(t,set(BASE_GRAMMAR));be=score_output(t,bo);base_exact+=int(be)
        lo,last,_=solve_with_grammar(t,learned_grammar);le=score_output(t,lo);learned_exact+=int(le)
        if not le or be or last is None:continue
        ctor=last[0]
        if ctor in BASE_GRAMMAR:continue
        ablgrammar=set(learned_grammar);ablgrammar.discard(ctor)
        ao,_,_=solve_with_grammar(t,ablgrammar);abl=score_output(t,ao)
        causal=not abl
        if causal:
            is_composite=(ctor=='B' and len(last[3])>1)
            composite_transfers+=int(is_composite)
            transfers.append({'j':j,'task':tid,'ast':repr(last),'constructor':ctor,'composite':is_composite,'constructor_ablation':'lost_exact','source_constructor_event':next((x for x in grammar_events if x['constructor']==ctor),None)})
    summary={'status':'ARC400_META_GRAMMAR_DEV_V6','claim':'bounded residual-driven expansion of active AST grammar from U-only to synthesized S/B constructors, followed by source-distinct per-task program synthesis and constructor ablation','meta_rules':META_RULES,'development_tasks':len(tr),'evaluation_tasks':len(ev),'base_grammar':sorted(BASE_GRAMMAR),'learned_grammar':sorted(learned_grammar),'grammar_events':grammar_events,'retained_training_programs':len(program_registry),'base_exact':base_exact,'learned_grammar_exact':learned_exact,'causal_grammar_transfers':transfers,'causal_composite_transfers':composite_transfers,'strong_gate':bool(transfers),'full_gate':composite_transfers>0}
    (a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2));(a.out_dir/'development.json').write_text(json.dumps(dev,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
