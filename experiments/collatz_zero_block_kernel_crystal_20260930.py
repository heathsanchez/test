#!/usr/bin/env python3
"""Bounded recurrent-kernel falsifier for an eventually-zero switch tail.

A fixed natural owner has only finitely many nonzero binary digits.  Therefore
an infinite centre-switch sequence with strictly increasing source-pulled
2-adic precision would eventually have every newly resolved source-bit block
equal to zero.  This script asks whether the observed exact zero-block switch
language has any recurrent source-free kernel.

Empty bounded kernel is only a theorem candidate.  Nonempty kernel yields the
next exact separator.
"""
from __future__ import annotations
import argparse,json
from collections import defaultdict,Counter
from contextlib import redirect_stdout
from fractions import Fraction
import io
with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra

def v2z(x):
    x=abs(int(x))
    if x==0:return None
    return (x&-x).bit_length()-1
def rv2(x):
    return v2z(x.numerator)-v2z(x.denominator)
def ctr(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])
def sid(c):
    return (c["r"],c["A"],c["B"],c["D"])

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            st=last[r]; w=tuple(branches[st:end])
            c=cache.setdefault(w,ra.certificate(w))
            m0=starts[st][2];m1=starts[end][2]
            assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
            out[r].append((c,m0,m1))
        last[r]=end
    return out

def tarjan(nodes,edges):
    g={n:set() for n in nodes}
    for a,b in edges:g.setdefault(a,set()).add(b);g.setdefault(b,set())
    idx=0;stack=[];on=set();I={};L={};comps=[]
    def go(v):
        nonlocal idx
        I[v]=L[v]=idx;idx+=1;stack.append(v);on.add(v)
        for w in g[v]:
            if w not in I:go(w);L[v]=min(L[v],L[w])
            elif w in on:L[v]=min(L[v],I[w])
        if L[v]==I[v]:
            c=[]
            while True:
                w=stack.pop();on.remove(w);c.append(w)
                if w==v:break
            comps.append(c)
    for v in g:
        if v not in I:go(v)
    return comps,g

def audit(lo,hi,K):
    events=[]; seqs=[]; maxzero=0; first_long=None
    start=max(3,lo)+(max(3,lo)%2==0)
    for n in range(start,hi+1,2):
        for anchor,seq in returns(n,K).items():
            if len(seq)<2:continue
            owner=seq[0][1]; Abar=Bbar=0
            Abar,Pbar=1,1; Bbar=0
            states=[]
            for c,m0,m1 in seq:
                pc=(Pbar*ctr(c)-Bbar)/Abar
                p=rv2(Fraction(owner)-pc); assert p is not None
                states.append((c,pc,p))
                Abar,Bbar,Pbar=(c["A"]*Abar,c["A"]*Bbar+c["B"]*Pbar,(1<<c["D"])*Pbar)
            sw=[]
            for a,b in zip(states,states[1:]):
                ca,pa,p0=a;cb,pb,p1=b
                if pa==pb:continue
                assert p1>p0
                block=(owner>>p0)&((1<<(p1-p0))-1)
                row={"source":n,"anchor":anchor,"owner":owner,"bits":owner.bit_length(),
                     "old":sid(ca),"new":sid(cb),"p0":p0,"p1":p1,
                     "block":block,"zero":block==0}
                events.append(row);sw.append(row)
            zrun=0
            for e in sw:
                if e["zero"]:
                    zrun+=1
                    if zrun>maxzero:maxzero=zrun;first_long=(n,anchor,list(sw))
                else:zrun=0
            if sw:seqs.append(sw)
    # Source-free overapprox: nodes are exact directed switch identities.
    nodes=set();edges=set();zero_events=0
    for sw in seqs:
        zs=[e for e in sw if e["zero"]]
        zero_events+=len(zs)
        for e in zs:nodes.add((e["old"],e["new"]))
        for a,b in zip(sw,sw[1:]):
            if a["zero"] and b["zero"]:
                u=(a["old"],a["new"]);v=(b["old"],b["new"])
                nodes|={u,v};edges.add((u,v))
    comps,g=tarjan(nodes,edges)
    cyc=[c for c in comps if len(c)>1 or (len(c)==1 and c[0] in g[c[0]])]
    # Exact source-wise recurrence is stronger than union SCC.
    src_cycles=[]
    for sw in seqs:
        z=[(e["old"],e["new"]) for e in sw if e["zero"]]
        seen={}
        for i,x in enumerate(z):
            if x in seen:src_cycles.append((x,seen[x],i));break
            seen[x]=i
    return {"range":[lo,hi],"switch_events":len(events),"zero_events":zero_events,
            "zero_fraction":(zero_events/len(events) if events else 0),
            "max_consecutive_zero_switches":maxzero,
            "union_nodes":len(nodes),"union_edges":len(edges),
            "cyclic_sccs":len(cyc),"cyclic_sizes":sorted((len(c) for c in cyc),reverse=True),
            "sourcewise_repeated_zero_switch_states":len(src_cycles),
            "first_sourcewise_repeat":src_cycles[:3],
            "candidate":"eventual all-zero switch tail has empty recurrent kernel"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--K",type=int,default=128);a=ap.parse_args()
    train=audit(3,8191,a.K);held=audit(8193,32767,a.K)
    verdict=("ZERO_BLOCK_KERNEL_BOUNDED_EMPTY"
      if train["cyclic_sccs"]==0 and held["cyclic_sccs"]==0
         and train["sourcewise_repeated_zero_switch_states"]==0
         and held["sourcewise_repeated_zero_switch_states"]==0
      else "ZERO_BLOCK_KERNEL_SURVIVES")
    print(json.dumps({"schema":"COLLATZ_ZERO_BLOCK_KERNEL_CRYSTAL_20260930",
      "train":train,"heldout":held,"verdict":verdict,"global_collatz":"UNKNOWN"},indent=2))
if __name__=="__main__":main()
