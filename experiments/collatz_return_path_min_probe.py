#!/usr/bin/env python3
"""Spike: path-minimum consequence of alternative return-pattern inverses.

At a later same-anchor endpoint, invert a previously seen distinct return
pattern. Even if its starting predecessor y is above source n, its certified
forward path to the common endpoint may visit z<n. Then z coalesces with n,
giving the strong-induction lower merge.
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

def path_min(c,p):
    x=(1<<c['r'])*p-1
    mn=x; arg=0; y=x
    steps=sum(r+s for r,s,rp in c['word'])
    assert steps==c['D']
    for t in range(1,steps+1):
        y=base.T(y)
        if y<mn:mn=y;arg=t
    mend=(y+1)>>c['r']
    return mn,arg,y,mend

def audit(lo,hi,K):
    cnt=Counter(); closed=[]; legalrows=[]; hard=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        seqs=returns(n,K)
        if not seqs:continue
        cnt['sources']+=1; source_closed=False
        for r,seq in seqs.items():
            bank=[]
            for actual,m0,m1,k0,k1 in seq:
                # Try only genuinely earlier distinct patterns.
                for old in bank:
                    cnt['attempts']+=1
                    p=inverse(old,m1)
                    if p is None:continue
                    cnt['legal']+=1
                    y=(1<<r)*p-1
                    mn,arg,end,mend=path_min(old,p)
                    assert mend==m1
                    row=(n,r,k1,y,mn,arg,end,old['q'],actual['q'],old['word'])
                    legalrows.append(row)
                    if mn<n:
                        cnt['path_min_lower_merge']+=1
                        closed.append(row);source_closed=True;break
                if source_closed:break
                if all(z['q']!=actual['q'] for z in bank):
                    bank.append(actual)
            if source_closed:break
        if not source_closed:hard.append(n)
    print("SOURCE_RANGE",lo,hi,"K",K)
    print("COUNTS",dict(cnt))
    print("CLOSED_BY_PATH_MIN",len(closed))
    print("FIRST_CLOSED",closed[:30])
    legalrows.sort(key=lambda z:(z[4]-z[0],z[4],z[0]))
    print("CLOSEST_PATH_MINIMA",legalrows[:30])
    print("HARD",len(hard),"FIRST_HARD",hard[:60])
    if closed:print("OBSERVED_ALTERNATIVE_RETURN_PATH_MIN_LOWER_MERGES")
    else:print("NO_ALTERNATIVE_RETURN_PATH_MIN_LOWER_MERGE")
    print("STATUS RETURN_PATH_MIN_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    a=ap.parse_args();audit(a.lo,a.hi,a.K)
