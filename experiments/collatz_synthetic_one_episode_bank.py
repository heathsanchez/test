#!/usr/bin/env python3
"""Synthetic one-episode inverse-constructor coverage of q=0 RIGID sources.

No training data is used. At every odd RIGID episode endpoint with anchor rp
and cofactor m, enumerate all reverse episode constructors (r,s,rp) in the
specified finite envelope. Invert exactly:
    p = (2^(s+rp)m - (2^s-1)) / 3^r.
Replay the episode; if its path reaches any value below the fixed source n,
we have a lower-merge certificate.

This asks whether the transferred fragment bank is compressible to one
parameterized constructor family.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base

def inverse_episode(r,s,rp,m):
    A=3**r; D=s+rp; B=(1<<s)-1
    num=(1<<D)*m-B
    if num<=0 or num%A:return None
    p=num//A
    if p<=0 or not (p&1):return None
    x=(1<<r)*p-1
    # exact episode type verification
    try:
        rr,mm,ss,rrp,mp,y=ra.episode(x)
    except AssertionError:
        return None
    if (rr,ss,rrp)!=(r,s,rp) or mp!=m:return None
    mn=x;arg=0;z=x
    for t in range(1,r+s+1):
        z=base.T(z)
        if z<mn:mn=z;arg=t
    return p,x,mn,arg,z

def audit(lo,hi,K,Rmax,Smax):
    cnt=Counter();closed=[];hard=[];wins=Counter();best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        starts,branches=ra.rigid_episode_segment(n,K)
        if not branches:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,rp,m,x in starts:
            for r in range(1,Rmax+1):
                for s in range(1,Smax+1):
                    cnt['attempts']+=1
                    z=inverse_episode(r,s,rp,m)
                    if z is None:continue
                    cnt['legal']+=1
                    p,y,mn,arg,end=z
                    gap=mn-n
                    row=(gap,n,k,rp,m,r,s,y,mn,arg)
                    if sourcebest is None or row<sourcebest:sourcebest=row
                    if mn<n:
                        cnt['closed']+=1;closed.append(row);wins[(r,s,rp)]+=1
                        done=True;break
                if done:break
            if done:break
        if sourcebest is not None:best.append(sourcebest)
        if not done:hard.append(n)
    best.sort()
    print("SOURCE_RANGE",lo,hi,"K",K,"RMAX",Rmax,"SMAX",Smax)
    print("COUNTS",dict(cnt))
    print("CLOSED",len(closed),"OF",cnt['sources'])
    print("TOP_WINNERS",wins.most_common(30))
    print("FIRST_CLOSED",closed[:30])
    print("BEST_NONCLOSED",[x for x in best if x[0]>=0][:30])
    print("HARD",len(hard),"FIRST_HARD",hard[:80])
    print("STATUS SYNTHETIC_ONE_EPISODE_BANK")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--Rmax",type=int,default=20)
    ap.add_argument("--Smax",type=int,default=12)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.Rmax,a.Smax)
