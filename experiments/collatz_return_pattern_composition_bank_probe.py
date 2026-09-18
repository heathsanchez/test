#!/usr/bin/env python3
"""Spike: composition closure of previously learned same-anchor return patterns.

A bank of verified return maps at anchor r is closed under word concatenation.
Every composed map is replay-checked when used.  At each later endpoint m',
invert every compiled map of composition length <=L; if the resulting
2^r*p-1 is below the fixed source n, we have an exact lower-merge certificate.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_q0_rigid_recharge_audit as ra

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            m0=starts[start][2];m1=starts[end][2]
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            out[r].append((c,m0,m1,starts[start][0],starts[end][0]))
        last[r]=end
    return out

def inverse(c,mend):
    num=(1<<c['D'])*mend-c['B']
    if num<=0 or num%c['A']:return None
    p=num//c['A']
    if p<=0 or not (p&1):return None
    if not ra.admissible(c,p):return None
    if ra.replay(c,p)!=mend:return None
    return p

def compile_bank(base,maxlen):
    # Return deduplicated certificates keyed by exact affine map.
    levels={1:list(base)}
    allc={}
    for c in base:
        allc[(c['A'],c['B'],c['D'])]=(1,c)
    for L in range(2,maxlen+1):
        cur=[]
        for prev in levels[L-1]:
            for tail in base:
                try:
                    c=ra.certificate(prev['word']+tail['word'])
                except AssertionError:
                    continue
                key=(c['A'],c['B'],c['D'])
                if key not in allc:
                    allc[key]=(L,c);cur.append(c)
        levels[L]=cur
    return sorted(allc.values(),key=lambda z:(z[0],z[1]['D'],z[1]['A'],z[1]['B']))

def audit(lo,hi,K,maxlen):
    cnt=Counter();witness=[];hard=[];bestgap=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        seqs=returns(n,K)
        if not seqs:continue
        cnt['sources']+=1
        closed=False
        source_best=None
        for r,seq in seqs.items():
            base=[]
            for idx,(actual,m0,m1,k0,k1) in enumerate(seq):
                if all(x['q']!=actual['q'] for x in base):
                    base.append(actual)
                compiled=compile_bank(base,maxlen)
                cnt['compiled_maps']+=len(compiled)
                for L,c in compiled:
                    # Do not count the actual immediate inverse as a discovery.
                    cnt['attempts']+=1
                    p=inverse(c,m1)
                    if p is None:continue
                    cnt['legal']+=1
                    y=(1<<r)*p-1
                    gap=y-n
                    if source_best is None or gap<source_best[0]:
                        source_best=(gap,y,n,r,k1,L,c['q'],actual['q'],c['word'])
                    if y<n:
                        row=(n,r,k1,y,m1,L,c['q'],actual['q'],c['word'])
                        witness.append(row)
                        cnt['closed']+=1;closed=True;break
                if closed:break
            if closed:break
        if source_best is not None:bestgap.append(source_best)
        if not closed:hard.append(n)
    bestgap.sort()
    print("SOURCE_RANGE",lo,hi,"K",K,"MAXLEN",maxlen)
    print("COUNTS",dict(cnt))
    print("CLOSED_SOURCES",len(witness))
    print("FIRST_WITNESSES",witness[:30])
    print("BEST_GAPS",bestgap[:30])
    print("HARD",len(hard),"FIRST_HARD",hard[:50])
    if witness:
        print("OBSERVED_COMPOSITION_BANK_LOWER_MERGES")
    else:
        print("NO_COMPOSITION_BANK_LOWER_MERGE")
    print("STATUS COMPOSITION_BANK_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--maxlen",type=int,default=3)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.maxlen)
