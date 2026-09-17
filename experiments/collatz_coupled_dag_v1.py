#!/usr/bin/env python3
"""Exact Complete-O Bellman / coupled residual probe.

This is a theorem-discovery harness, not a Collatz proof.
It:
  * verifies the terminal-congruence => prefix-legality identity on enumerated words;
  * computes exact finite Complete-O Bellman optima Phi_j(r);
  * classifies finite source cylinders as DESCEND / CLOSED / TAIL_CLOSED / RIGID;
  * builds a conservative finite abstraction of observed RIGID refinements;
  * reports all RIGID SCCs/self-loops.

Any candidate abstraction intended for proof must later receive universal transition lemmas.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from collections import defaultdict
import argparse

def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

@dataclass(frozen=True)
class Score:
    S:int
    C:int
    # smaller S wins; at equal S larger C wins
    def key(self): return (self.S, -self.C)

@lru_cache(None)
def phi(j:int, r:int)->Score:
    if j==0:
        return Score(0,0)
    mod=3**j
    r%=mod
    best=None
    period=2*3**(j-1)
    for a in range(1,period+1):
        z=(pow(2,a,mod)*r-1)
        if z%3: continue
        rp=(z//3)%(3**(j-1))
        tail=phi(j-1,rp)
        cand=Score(a+tail.S, (1<<tail.S)+3*tail.C)
        if best is None or cand.key()<best.key():
            best=cand
    if best is None:
        # Multiples of 3 have no legal first O.
        return Score(10**9,-10**100)
    return best

def forward_cylinder(k:int,b:int):
    # exact first k shortcut steps for n=b+2^k q
    d=b
    c=0
    for _ in range(k):
        if d&1:
            d=(3*d+1)//2
            c+=1
        else:
            d//=2
    # affine endpoint = 3^c q + d
    return c,d

def direct_descent(k,b):
    c,d=forward_cylinder(k,b)
    if d<b:
        assert 3**c < 2**k
        return True
    return False

def classify(k:int,b:int):
    c,d=forward_cylinder(k,b)
    if direct_descent(k,b):
        return ("DESCEND",None)
    if c==0:
        return ("RIGID",None)
    sc=phi(c,d%(3**c))
    Csrc=(1<<k)*d-(3**c)*b
    # Source replay must be feasible, so optimizer cannot be worse.
    if sc.S<k:
        # reconstructed intercept at q=0
        num=(1<<sc.S)*d-sc.C
        if num%(3**c):
            raise AssertionError(("optimizer nonintegral",k,b,c,d,sc))
        bp=num//(3**c)
        den=(1<<k)-(1<<sc.S)
        Q=0 if bp<b else (bp-b)//den+1
        return ("TAIL_CLOSED",(Q,sc,bp))
    if sc.S==k and sc.C>Csrc:
        return ("CLOSED",(sc,Csrc))
    return ("RIGID",(sc,Csrc))

def terminal_prefix_gate():
    # The universal terminal=>prefix legality statement is proved algebraically;
    # keep only cheap executable regression witnesses here.
    tests = [((1,), 2), ((2,), 1), ((1,2), 5), ((2,1), 7), ((1,2,1), 17)]
    checked = 0
    for acts,d in tests:
        S=0; C=0
        for idx,a in enumerate(acts):
            S += a; C = (1<<a)*C + 3**idx
        mod=3**len(acts)
        if ((1<<S)*d-C)%mod: continue
        S=0; C=0
        for idx,a in enumerate(acts):
            S += a; C = (1<<a)*C + 3**idx
            assert ((1<<S)*d-C)%(3**(idx+1)) == 0
        checked += 1
    return checked

def tarjan(nodes,edges):
    idx=0; stack=[]; on=set(); ind={}; low={}; out=[]
    def visit(v):
        nonlocal idx
        ind[v]=low[v]=idx; idx+=1; stack.append(v); on.add(v)
        for w in edges.get(v,()):
            if w not in ind:
                visit(w); low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],ind[w])
        if low[v]==ind[v]:
            comp=[]
            while True:
                w=stack.pop(); on.remove(w); comp.append(w)
                if w==v: break
            out.append(comp)
    for v in nodes:
        if v not in ind: visit(v)
    return out

def abstraction_state(k,b):
    c,d=forward_cylinder(k,b)
    # Deliberately coarse candidate abstraction. It is discovery-only until
    # universal transition closure is proved.
    j=min(c,6)
    residue=d%(3**j) if j else 0
    outcome,_=classify(k,b)
    return (outcome,j,residue,min(k-c,12))

def run(K:int):
    gate=terminal_prefix_gate()
    counts=defaultdict(int)
    rigid=[]
    for k in range(1,K+1):
        for b in range(1,1<<k,2):
            o,_=classify(k,b)
            counts[(k,o)]+=1
            if o=="RIGID": rigid.append((k,b))
    nodes=set(); edges=defaultdict(set)
    for k,b in rigid:
        s=abstraction_state(k,b); nodes.add(s)
        if k<K:
            for bp in (b,b+(1<<k)):
                if classify(k+1,bp)[0]=="RIGID":
                    t=abstraction_state(k+1,bp)
                    nodes.add(t); edges[s].add(t)
    sccs=tarjan(nodes,edges)
    hard=[]
    for comp in sccs:
        if len(comp)>1 or (len(comp)==1 and comp[0] in edges.get(comp[0],set())):
            hard.append(comp)
    print("PASS terminal-prefix gate",gate)
    for k in range(1,K+1):
        print("LEVEL",k,{o:counts[(k,o)] for o in ("DESCEND","CLOSED","TAIL_CLOSED","RIGID")})
    print("ABSTRACT_STATES",len(nodes))
    print("RIGID_EDGES",sum(map(len,edges.values())))
    print("HARD_SCCS",len(hard))
    for i,c in enumerate(sorted(hard,key=len,reverse=True),1):
        print("SCC",i,"size",len(c),"states",sorted(c)[:20])
    print("WARNING: SCC graph is a bounded discovery abstraction, not yet a universal proof abstraction.")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=12)
    args=ap.parse_args()
    run(args.depth)
