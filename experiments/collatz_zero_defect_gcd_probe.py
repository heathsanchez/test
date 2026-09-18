#!/usr/bin/env python3
"""Spike: arithmetic obstruction for zero-defect concrete RIGID cycles."""
from __future__ import annotations
from math import gcd
import collatz_q0_rigid_recharge_audit as ra

# Re-run bounded audit logic indirectly by reconstructing cycles for selected sources.
# This uses the same concrete-cycle extractor as the main script.
SOURCES=[7527,7963,8959,10617,11945,12583,13439,13503,16551,16777,20895,31343]

def cycles_for_source(n,H=128):
    starts,branches=ra.rigid_episode_segment(n,H)
    cache={};last={};last_return={};seqs={};cert_by_edge={}
    from collections import defaultdict
    seqs=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            m0=starts[start][2];m1=starts[end][2]
            if r in last_return:
                old=last_return[r]
                if old['q']!=c['q']:
                    z=ra.switch_law(old,c,m0,m1)
                    if z is not None:
                        e=((old['r'],)+old['q'],(c['r'],)+c['q'])
                        cert_by_edge[e]=(old,c)
                        seqs[r].append((e,m0,m1,z['outcome']))
            last_return[r]=c
        last[r]=end
    out=[]
    for r,seq in seqs.items():
        if not seq: continue
        nodes=[seq[0][0][0]]
        for row in seq: nodes.append(row[0][1])
        first={}
        for i,node in enumerate(nodes):
            if node in first:
                a=first[node];b=i
                A,B,D=1,0,0
                for j in range(a,b):
                    target=cert_by_edge[seq[j][0]][1]
                    B=target['A']*B+target['B']*(1<<D)
                    A=target['A']*A;D+=target['D']
                out.append((n,r,tuple(seq[j][3] for j in range(a,b)),A,B,D))
            else:first[node]=i
    return out

seen=set()
rows=[]
for n in SOURCES:
    for row in cycles_for_source(n):
        key=row[1:]
        if key in seen: continue
        seen.add(key)
        n,r,outcomes,A,B,D=row
        C=(1<<D)-A
        g=gcd(abs(B),abs(C))
        fixed=None
        integral=False
        if C!=0:
            fixed=(B,C)
            integral=(B%C==0)
        rows.append((n,r,outcomes,A,B,D,C,g,integral,fixed))
for z in rows:
    print("CYCLE_ARITH",z)
print("GCD_GT1",sum(1 for z in rows if z[7]>1),"OF",len(rows))
print("POSITIVE_C_GT0",sum(1 for z in rows if z[6]>0))
print("INTEGRAL_FIXEDPOINTS",sum(1 for z in rows if z[8]))
print("STATUS ZERO_DEFECT_GCD_SPIKE")
