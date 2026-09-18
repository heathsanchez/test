#!/usr/bin/env python3
"""Universal reverse-episode BFS restricted to genuine minimal-counterexample candidates.

Necessary pre-q0 conditions for a least lower-merge counterexample:
  * no direct descent T^t(n)<n;
  * no immediate inverse-odd witness p=(2y-1)/3<n with T(p)=y.

After those filters, require the existing compiled q0 RIGID grammar and run the
exact universal reverse-episode BFS.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra
import collatz_universal_reverse_episode_bfs_v2 as bfs

def preq0_certificate(n):
    k0=n.bit_length(); y=n
    for t in range(1,k0+1):
        y=base.T(y)
        if y<n:
            return ('D',t,y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:
                return ('P',t,y,p)
    return None

def candidate_segment(n,K):
    if preq0_certificate(n) is not None:
        return [],[]
    return ra.rigid_episode_segment(n,K)

def audit(lo,hi,K,L,R,S):
    pow3=[1]*(R+1)
    for i in range(1,R+1):pow3[i]=pow3[i-1]*3
    cnt=Counter();closed=[];hard=[];prefilter=Counter()
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        cert=preq0_certificate(n)
        if cert is not None:
            prefilter[cert[0]]+=1
            continue
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False
        for k,r,m,x in ss:
            row,legal,states=bfs.search_endpoint(n,r,m,L,R,S,pow3)
            cnt['legal_edges']+=legal;cnt['states']+=states
            if row is not None and row[0]<0:
                full=(row[0],n,k,r,m)+row[2:]
                closed.append(full);cnt['closed']+=1;done=True;break
        if not done:hard.append(n)
    print("RANGE",lo,hi,"K",K,"L",L,"R",R,"S",S)
    print("PREFILTER",dict(prefilter))
    print("COUNTS",dict(cnt))
    print("CLOSED",len(closed))
    print("FIRST_CLOSED",closed[:25])
    print("HARD",len(hard),"ALL_HARD",hard)
    print("STATUS MINIMAL_CANDIDATE_REVERSE_BFS")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=4097)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--L",type=int,default=5)
    ap.add_argument("--R",type=int,default=14)
    ap.add_argument("--S",type=int,default=14)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.L,a.R,a.S)
