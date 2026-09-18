#!/usr/bin/env python3
"""Spike: compile previously seen same-anchor return patterns into lower-merge certificates.

For a verified return certificate W
    F_W(m)=(A*m+B)/2^D
and a later endpoint m', solve
    p=(2^D*m'-B)/A.
If p is a legal positive integer, F_W(p)=m'.  Thus y=2^r*p-1 coalesces
with the fixed source n at the later endpoint.  If y<n, this is an exact
strong-induction lower-merge certificate.

The pattern bank grows monotonically along each fixed source/anchor.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base

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
    if num<=0 or num%c['A']:
        return None
    p=num//c['A']
    if p<=0 or not (p&1):
        return None
    if not ra.admissible(c,p):
        return None
    if ra.replay(c,p)!=mend:
        return None
    return p

def audit(lo,hi,K):
    counts=Counter(); witnesses=[]; hard=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        seqs=returns(n,K)
        if not seqs: continue
        counts['sources_with_returns']+=1
        source_closed=False
        for r,seq in seqs.items():
            bank=[]
            for idx,(c,m0,m1,k0,k1) in enumerate(seq):
                counts['returns']+=1
                # Bank contains all earlier distinct exact return patterns.
                for old in bank:
                    counts['bank_attempts']+=1
                    p=inverse(old,m1)
                    if p is None:
                        continue
                    counts['bank_legal']+=1
                    y=(1<<r)*p-1
                    if y<n:
                        counts['bank_lower_merge']+=1
                        row=(n,r,k1,y,m1,old['q'],c['q'],old['word'],c['word'])
                        witnesses.append(row)
                        source_closed=True
                        break
                if source_closed:break
                if all(old['q']!=c['q'] for old in bank):
                    bank.append(c)
            if source_closed:break
        if not source_closed:
            hard.append(n)
    print("SOURCE_RANGE",lo,hi,"DEPTH",K)
    print("COUNTS",dict(counts))
    print("SOURCES_CLOSED_BY_BANK",len(witnesses))
    print("FIRST_WITNESSES",witnesses[:30])
    print("SOURCES_WITH_RETURNS_NOT_CLOSED_BY_BANK",len(hard))
    print("FIRST_HARD",hard[:50])
    if witnesses:
        print("OBSERVED_RETURN_BANK_ACQUIRES_LOWER_MERGES")
    print("STATUS RETURN_PATTERN_CONSEQUENCE_BANK_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    a=ap.parse_args();audit(a.lo,a.hi,a.K)
