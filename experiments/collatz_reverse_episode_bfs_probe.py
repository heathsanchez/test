#!/usr/bin/env python3
"""Exact source-specific reverse-episode BFS on q=0 RIGID endpoints.

For an odd endpoint x, every reverse episode with r odd shortcut steps followed
by s even shortcut steps starts at

    p = (2^s*x + 1) / 3^r
    y = 2^r*p - 1,

provided p is a positive odd integer and replaying y has episode type (r,s,*)
ending exactly at x.

This BFS explores only legal reverse blocks. It does not materialize the
synthetic grammar. At each newly found ancestor y, replay the block and record
its path minimum; any value below fixed source n is a lower-merge certificate.

Search is bounded by episode count and total reverse shortcut steps. Coverage
by minimal episode depth is reported.
"""
from __future__ import annotations
import argparse
from collections import Counter,deque
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base

def reverse_blocks(x,remaining,Rmax,Smax):
    out=[]
    for r in range(1,min(Rmax,remaining-1)+1):
        A=3**r
        for s in range(1,min(Smax,remaining-r)+1):
            num=(1<<s)*x+1
            if num%A:continue
            p=num//A
            if p<=0 or not(p&1):continue
            y=(1<<r)*p-1
            try:
                rr,mm,ss,rp,mp,z=ra.episode(y)
            except AssertionError:
                continue
            if rr!=r or ss!=s or z!=x:
                continue
            # Exact path minimum from y to x.
            q=y;mn=y;arg=0
            for t in range(1,r+s+1):
                q=base.T(q)
                if q<mn:mn=q;arg=t
            assert q==x
            out.append((y,r,s,mn,arg))
    return out

def search_from_endpoint(n,x,maxepisodes,maxsteps,Rmax,Smax):
    # state: odd value, episodes used, total reverse shortcut cost, word
    Q=deque([(x,0,0,tuple())])
    seen={(x,0):0}
    best=None
    while Q:
        cur,L,cost,word=Q.popleft()
        if L>=maxepisodes:continue
        rem=maxsteps-cost
        if rem<2:continue
        for y,r,s,mn,arg in reverse_blocks(cur,rem,Rmax,Smax):
            newL=L+1;newcost=cost+r+s
            newword=((r,s),)+word
            row=(mn-n,newL,newcost,y,mn,arg,newword,x)
            if best is None or row<best:best=row
            if mn<n:
                return row,best
            key=(y,newL)
            old=seen.get(key)
            if old is None or newcost<old:
                seen[key]=newcost
                Q.append((y,newL,newcost,newword))
    return None,best

def audit(lo,hi,K,maxepisodes,maxsteps,Rmax,Smax):
    cnt=Counter();closed=[];hard=[];bestall=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        starts,branches=ra.rigid_episode_segment(n,K)
        if not branches:continue
        cnt['sources']+=1;done=False;sourcebest=None
        # Search from every odd episode start on the concrete RIGID segment.
        for k,r,m,x in starts:
            row,b=search_from_endpoint(n,x,maxepisodes,maxsteps,Rmax,Smax)
            if b is not None:
                full=(b[0],n,k)+b[1:]
                if sourcebest is None or full<sourcebest:sourcebest=full
            if row is not None:
                full=(row[0],n,k)+row[1:]
                closed.append(full)
                cnt['closed']+=1
                cnt['closed_depth_'+str(row[1])]+=1
                done=True;break
        if sourcebest is not None:bestall.append(sourcebest)
        if not done:hard.append(n)
    bestall.sort()
    print("SOURCE_RANGE",lo,hi,"K",K,"MAXEP",maxepisodes,
          "MAXSTEPS",maxsteps,"RMAX",Rmax,"SMAX",Smax)
    print("COUNTS",dict(cnt))
    print("CLOSED",len(closed),"OF",cnt['sources'])
    print("FIRST_CLOSED",closed[:40])
    print("BEST_NONCLOSED",[z for z in bestall if z[0]>=0][:40])
    print("HARD",len(hard),"FIRST_HARD",hard[:120])
    print("STATUS REVERSE_EPISODE_BFS_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--maxepisodes",type=int,default=4)
    ap.add_argument("--maxsteps",type=int,default=28)
    ap.add_argument("--Rmax",type=int,default=20)
    ap.add_argument("--Smax",type=int,default=12)
    a=ap.parse_args()
    audit(a.lo,a.hi,a.K,a.maxepisodes,a.maxsteps,a.Rmax,a.Smax)
