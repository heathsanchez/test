#!/usr/bin/env python3
"""Optimized exact universal reverse-episode BFS.

For current odd endpoint y=2^r1*m1-1, a predecessor episode (r0,s,r1)
exists exactly when
    m0 = (2^s*y + 1) / 3^r0
is a positive odd integer.
Then x0=2^r0*m0-1 executes exactly r0 odd shortcut steps followed by
exactly s even shortcut steps to y. No candidate replay is needed.

The BFS carries the minimum integer seen along the certified forward path
incrementally, so extending a state costs only the new local episode.

This is mathematically equivalent to collatz_universal_reverse_episode_bfs.py
but much cheaper.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base

def local_episode(r0,m0,s,r1,m1):
    x=(1<<r0)*m0-1
    target=(1<<r1)*m1-1
    y=x; mn=x; arg=0
    for t in range(1,r0+s+1):
        y=base.T(y)
        if y<mn:mn=y;arg=t
    assert y==target,(r0,m0,s,r1,m1,x,y,target)
    return mn,arg,x,target

def predecessors(r1,m1,R,S,pow3):
    y=(1<<r1)*m1-1
    for r0 in range(1,R+1):
        den=pow3[r0]
        for s in range(1,S+1):
            num=(1<<s)*y+1
            if num%den:continue
            m0=num//den
            if m0>0 and m0&1:
                yield r0,m0,s

def search_endpoint(n,r_end,m_end,L,R,S,pow3):
    # frontier tuple:
    # (r_current,m_current,path_min_to_target,word_forward)
    xend=(1<<r_end)*m_end-1
    front=[(r_end,m_end,xend,())]
    seen={(0,r_end,m_end)}
    best=None;legal=0;states=1
    for depth in range(1,L+1):
        nxt=[]
        for r1,m1,tail_min,word_tail in front:
            for r0,m0,s in predecessors(r1,m1,R,S,pow3):
                legal+=1
                key=(depth,r0,m0)
                if key in seen:continue
                seen.add(key);states+=1
                local_min,arg,x0,target=local_episode(r0,m0,s,r1,m1)
                mn=min(local_min,tail_min)
                word=((r0,s,r1),)+word_tail
                row=(mn-n,n,x0,mn,depth,word,r0,r_end,m0,m_end,arg)
                if best is None or row<best:best=row
                if mn<n:
                    return row,legal,states
                nxt.append((r0,m0,mn,word))
        front=nxt
        if not front:break
    return best,legal,states

def audit(lo,hi,K,L,R,S):
    pow3=[1]*(R+1)
    for i in range(1,R+1):pow3[i]=pow3[i-1]*3
    cnt=Counter();closed=[];hard=[];best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,r,m,x in ss:
            row,legal,states=search_endpoint(n,r,m,L,R,S,pow3)
            cnt['legal_edges']+=legal;cnt['states']+=states
            if row is None:continue
            full=(row[0],n,k,r,m)+row[2:]
            if sourcebest is None or full<sourcebest:sourcebest=full
            if row[0]<0:
                cnt['closed']+=1;closed.append(full);done=True;break
        if sourcebest is not None:best.append(sourcebest)
        if not done:hard.append(n)
    best.sort()
    print("RANGE",lo,hi,"K",K,"L",L,"R",R,"S",S)
    print("COUNTS",dict(cnt))
    print("CLOSED",len(closed))
    print("FIRST_CLOSED",closed[:25])
    print("BEST_GAPS",best[:25])
    print("HARD",len(hard),"ALL_HARD",hard)
    print("STATUS UNIVERSAL_REVERSE_EPISODE_BFS_V2")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=4097)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--L",type=int,default=4)
    ap.add_argument("--R",type=int,default=14)
    ap.add_argument("--S",type=int,default=14)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.L,a.R,a.S)
