#!/usr/bin/env python3
"""Quotient falsifier: nearest-centre label vs intrinsic 3-adic ball/port."""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base

def centre(c): return Fraction(c["B"],c["C"])

def qmod(q,k):
    if k<=0: return 0
    M=3**k
    return (q.numerator*pow(q.denominator,-1,M))%M

def collect(lo,hi,K):
    pats=defaultdict(dict); seqs=[]
    for n in range(lo|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives or base.birth_status(n)[0]!="RIGID" or not fk.completed_rigid_source(n,K): continue
        for r,seq in fk.return_sequences(n,K).items():
            if not seq: continue
            seqs.append((r,seq))
            for e in seq:
                c=e["cert"]; pats[r][fk.semantic_id(c)]=c
    bank={r:tuple(pats[r][k] for k in sorted(pats[r])) for r in sorted(pats)}
    return seqs,bank

def graph(seqs,bank,mode):
    succ=defaultdict(set); exits=set(); nodes=set()
    for r,seq in seqs:
        cs=sorted(bank[r],key=fk.semantic_tuple)
        keys=[]
        for e in seq:
            pid=fk.semantic_id(e["cert"]); m=e["m0"]
            vals=[fk.vpz(fk.defect(c,m),3) for c in cs]
            if any(v is None for v in vals):
                rad=None; inds=[i for i,v in enumerate(vals) if v is None]
            else:
                rad=max(vals,default=0); inds=[i for i,v in enumerate(vals) if v==rad]
            iq=min(inds,key=lambda i:(centre(cs[i]).numerator,centre(cs[i]).denominator,fk.semantic_tuple(cs[i])))
            q=centre(cs[iq])
            if mode=="CONTROL": key=(pid,)
            elif mode=="NEAREST": key=(pid,(q.numerator,q.denominator),rad)
            elif mode=="BALL":
                key=(pid,None,None) if rad is None else (pid,rad,qmod(q,rad))
            elif mode=="PORT":
                # intrinsic oriented shell: common ball at depth r + actual point's next trit
                key=(pid,None,None,None) if rad is None else (pid,rad,m%(3**rad), (m//(3**rad))%3)
            elif mode=="CENTRE_PORT":
                # centre's next trit plus point's relative outgoing trit
                if rad is None: key=(pid,None,None,None)
                else: key=(pid,rad,qmod(q,rad+1),(m//(3**rad))%3)
            else: raise ValueError(mode)
            keys.append(key); nodes.add(key)
        for a,b in zip(keys,keys[1:]): succ[a].add(b)
        if keys: exits.add(keys[-1])
    for n in nodes: succ.setdefault(n,set())
    classes,qnodes,qsucc,qexits,rounds=fk.refine_future_quotient(nodes,succ,exits)
    kern,prune=fk.greatest_kernel(qnodes,qsucc)
    ambiguity=sum(len(v)>1 for v in succ.values())
    return {"raw_nodes":len(nodes),"raw_ambiguous":ambiguity,"future_classes":len(qnodes),
            "future_kernel":len(kern),"cycle":fk.canonical(fk.cycle_witness(kern,qsucc)),
            "prune":prune}

def analyze(lo,hi,K,out):
    seqs,bank=collect(lo,hi,K)
    result={"range":[lo|1,hi],"K":K,"representations":{}}
    for mode in ("CONTROL","BALL","PORT","CENTRE_PORT","NEAREST"):
        result["representations"][mode]=graph(seqs,bank,mode)
        print(mode,json.dumps(result["representations"][mode],sort_keys=True))
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--lo",type=int,required=True); ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--K",type=int,default=128); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); analyze(a.lo,a.hi,a.K,a.output)
