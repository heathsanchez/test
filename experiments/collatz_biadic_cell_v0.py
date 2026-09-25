#!/usr/bin/env python3
"""Test whether Collatz consequential state is an intrinsic Q2 x Q3 cell."""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base

def centre(c): return Fraction(c["B"],c["C"])
def qmod(q,p,k):
    if k<=0:return 0
    M=p**k
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
    return seqs,{r:tuple(pats[r][k] for k in sorted(pats[r])) for r in sorted(pats)}

def v3ball(m,cs):
    vals=[fk.vpz(fk.defect(c,m),3) for c in cs]
    if any(v is None for v in vals):
        return (None,None)
    rad=max(vals,default=0)
    # intrinsic common residue, independent of centre witness
    return (rad,m%(3**rad) if rad else 0)

def key(e,cs,mode):
    c=e["cert"]; m=e["m0"]; b3=v3ball(m,cs)
    if mode=="FULL": return (fk.semantic_id(c),)+b3
    # exact active 2-adic cylinder: certificate domain m == rho mod 2^(D+1)
    d2=c["D"]+1; rho=c["rho"]
    assert m%(1<<d2)==rho
    if mode=="BI_CELL": return (d2,rho)+b3
    if mode=="BI_CELL_SLOPE":
        return (d2,rho,fk.vpz(c["A"],3),c["D"])+b3
    if mode=="BI_CELL_CENTRE":
        q=centre(c)
        return (d2,qmod(q,2,d2))+b3
    if mode=="CONTROL": return (fk.semantic_id(c),)
    raise ValueError(mode)

def graph(seqs,bank,mode):
    nodes=set(); succ=defaultdict(set); exits=set()
    for r,seq in seqs:
        cs=bank[r]; ks=[key(e,cs,mode) for e in seq]
        nodes.update(ks)
        for a,b in zip(ks,ks[1:]):succ[a].add(b)
        if ks:exits.add(ks[-1])
    for n in nodes:succ.setdefault(n,set())
    classes,qnodes,qsucc,qexits,_=fk.refine_future_quotient(nodes,succ,exits)
    kern,prune=fk.greatest_kernel(qnodes,qsucc)
    return {"raw_nodes":len(nodes),"raw_ambiguous":sum(len(v)>1 for v in succ.values()),
            "future_classes":len(qnodes),"future_kernel":len(kern),
            "cycle":fk.canonical(fk.cycle_witness(kern,qsucc)),"prune":prune}

def analyze(lo,hi,K,out):
    seqs,bank=collect(lo,hi,K)
    result={"range":[lo|1,hi],"K":K,"representations":{}}
    for mode in ("CONTROL","BI_CELL","BI_CELL_CENTRE","BI_CELL_SLOPE","FULL"):
        x=graph(seqs,bank,mode);result["representations"][mode]=x
        print(mode,json.dumps(x,sort_keys=True))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--lo",type=int,required=True);ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--K",type=int,default=128);ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args();analyze(a.lo,a.hi,a.K,a.output)
