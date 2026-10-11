#!/usr/bin/env python3
"""Exact finite cross-context equivalence laboratory; NOT a Lean soundness proof.

Three separately implemented comparison strategies:
  local: context-tagged recursive evaluation, exact memo keys;
  dag: globally hash-consed term nodes and dependency-aware congruence;
  diagram: canonical contextual boundary/signature with shared dependency factors.

Terms are affine XOR expressions over binary variables, with lexical renamings
as explicit context maps. The diagram representation is a canonical parity
factor graph (a small quantum-graphical-calculus-inspired spider fragment).
Its normalization is exact for this declared GF(2) fragment, NOT general Lean
definitional equality, and no quantum hardware or speedup is claimed.
"""
import argparse, itertools, json, random, tracemalloc, time
from dataclasses import dataclass

@dataclass(frozen=True)
class Term:
    op: str
    args: tuple = ()

def var(i): return Term("v",(i,))
def xor(a,b): return Term("x",(a,b))
def zero(): return Term("0")
def one(): return Term("1")

class Meter:
    def __init__(self): self.work=0;self.hits=0;self.misses=0
    def tick(self,n=1): self.work+=n

def parity(term, mapping, m):
    m.tick()
    if term.op=="v": return 1 << mapping[term.args[0]]
    if term.op=="0": return 0
    if term.op=="1": return 1 << 62
    return parity(term.args[0],mapping,m)^parity(term.args[1],mapping,m)

def local(term, mapping, meter, memo):
    key=(term,tuple(mapping))
    meter.tick()
    if key in memo:
        meter.hits+=1;return memo[key]
    meter.misses+=1
    if term.op=="v": out=1<<mapping[term.args[0]]
    elif term.op=="0": out=0
    elif term.op=="1": out=1<<62
    else: out=local(term.args[0],mapping,meter,memo)^local(term.args[1],mapping,meter,memo)
    memo[key]=out
    return out

class Dag:
    def __init__(self):self.m=Meter();self.intern={};self.memo={}
    def run(self,term,mapping):
        def intern(t):
            self.m.tick()
            if t.op=="v": key=("v",mapping[t.args[0]])
            elif t.op in ("0","1"):key=(t.op,)
            else:
                a,b=intern(t.args[0]),intern(t.args[1])
                key=("x",min(a,b),max(a,b))
            if key in self.intern:self.m.hits+=1;return self.intern[key]
            self.m.misses+=1
            i=len(self.intern);self.intern[key]=i;return i
        root=intern(term)
        # Compute exact semantic value of canonical DAG, not merely syntactic congruence.
        inv={v:k for k,v in self.intern.items()}
        def value(i):
            self.m.tick()
            if i in self.memo:self.m.hits+=1;return self.memo[i]
            self.m.misses+=1;k=inv[i]
            if k[0]=="v":v=1<<k[1]
            elif k[0]=="0":v=0
            elif k[0]=="1":v=1<<62
            else:v=value(k[1])^value(k[2])
            self.memo[i]=v;return v
        return value(root)

class Diagram:
    def __init__(self):self.m=Meter();self.factors={};self.signatures={}
    def run(self,t,mapping):
        # Each global variable is a boundary wire; XOR nodes compose by symmetric
        # difference. Shared subdiagrams are cached by contextual dependency signature.
        def go(t):
            key=(t,tuple(mapping[i] for i in sorted(deps(t))))
            self.m.tick()
            if key in self.signatures:self.m.hits+=1;return self.signatures[key]
            self.m.misses+=1
            if t.op=="v":v=1<<mapping[t.args[0]]
            elif t.op=="0":v=0
            elif t.op=="1":v=1<<62
            else:v=go(t.args[0])^go(t.args[1])
            self.signatures[key]=v
            self.factors.setdefault(v,len(self.factors))
            return v
        return go(t)

from functools import lru_cache
@lru_cache(None)
def deps(t):
    if t.op=="v":return frozenset(t.args)
    if t.op in ("0","1"):return frozenset()
    return deps(t.args[0])|deps(t.args[1])

def make(depth,width,sharing,rng):
    base=[var(i) for i in range(width)]
    pool=base[:]
    for i in range(depth):
        a=pool[rng.randrange(len(pool))]
        b=pool[rng.randrange(len(pool))] if rng.random()<sharing else base[rng.randrange(width)]
        pool.append(xor(a,b))
    return pool[-1],pool

def trial(depth,width,contexts,sharing,seed):
    rng=random.Random(seed); root,pool=make(depth,width,sharing,rng)
    # Distinct lexical contexts that preserve shared global dependencies through
    # explicit renaming; each comparison has an independently checked oracle.
    maps=[]
    for i in range(contexts):
        mapping=list(range(width))
        rng.shuffle(mapping)
        maps.append(tuple(mapping))
    pairs=[]
    for i,m in enumerate(maps):
        t=root if i%3 else xor(root,zero())
        pairs.append((t,m))
    methods={}
    for name in ("local","dag","canonical","diagram"):
        tracemalloc.start()
        start=time.perf_counter()
        if name=="local":
            meter=Meter();memo={};values=[local(t,m,meter,memo) for t,m in pairs]
            state=len(memo)
        elif name=="dag":
            engine=Dag();values=[engine.run(t,m) for t,m in pairs]
            meter=engine.m;state=len(engine.intern)+len(engine.memo)
        elif name=="canonical":
            meter=Meter();memo={};values=[]
            for t,m in pairs:
                # Strong classical comparator: normalized affine polynomial over GF(2),
                # globally memoized by exact contextual dependency signature.
                key=(t,tuple(m[i] for i in sorted(deps(t))))
                meter.tick()
                if key in memo:meter.hits+=1;v=memo[key]
                else:
                    meter.misses+=1;v=parity(t,m,meter);memo[key]=v
                values.append(v)
            state=len(memo)
        else:
            engine=Diagram();values=[engine.run(t,m) for t,m in pairs]
            meter=engine.m;state=len(engine.signatures)+len(engine.factors)
        elapsed=time.perf_counter()-start
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        oracle=[parity(t,m,Meter()) for t,m in pairs]
        assert values==oracle,(name,depth,width,contexts,sharing)
        methods[name]={"correct":True,"abstract_work":meter.work,"hits":meter.hits,"misses":meter.misses,
                       "reuse_fraction":round(meter.hits/max(1,meter.hits+meter.misses),5),
                       "peak_traced_bytes":peak,"states":state,"elapsed_s":round(elapsed,6)}
    return {"depth":depth,"width":width,"contexts":contexts,"sharing":sharing,"seed":seed,"methods":methods}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="context-sharing-report.json")
    args=p.parse_args()
    rows=[]
    for width,depth,contexts,sharing in itertools.product((4,8),(24,72),(2,8,24),(0.25,0.8)):
        rows.append(trial(depth,width,contexts,sharing,seed=width*10000+depth*100+contexts*10+int(sharing*10)))
    with open(args.output,"w") as f:json.dump({"scope":"exact GF2 affine finite fragment, not Lean definitional equality","rows":rows},f,indent=2)
    print("CONTEXT_SHARING_LAB="+json.dumps({"cases":len(rows),"all_correct":all(all(v["correct"] for v in r["methods"].values()) for r in rows),
      "median_diagram_vs_dag_abstract_work":sorted(r["methods"]["diagram"]["abstract_work"]/r["methods"]["dag"]["abstract_work"] for r in rows)[len(rows)//2],
      "guest_instructions":"NOT_MEASURED_USE_CALLGRIND","report":args.output}),flush=True)
if __name__=="__main__":main()
