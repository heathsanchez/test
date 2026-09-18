#!/usr/bin/env python3
"""Universal bounded reverse-episode BFS on hereditary RIGID endpoints.

From a current odd endpoint represented by (r_cur,m_cur), enumerate every
single predecessor episode (r_prev,s,r_cur) inside r_prev<=R, s<=S for which
exact inversion is integral and replay-valid. Recursively extend those legal
predecessors to depth L.

Every reached predecessor comes with an exact forward fragment back to the
source orbit's current endpoint. If that fragment visits any integer below the
fixed source n, it is a lower-merge certificate.

This is the grammar-complete bounded version of short-fragment transfer:
no training corpus is used.
"""
from __future__ import annotations
import argparse
from collections import Counter,deque
import collatz_fragment_transfer_probe as ft
import collatz_q0_rigid_recharge_audit as ra

def one_predecessors(r_cur,m_cur,R,S):
    for r_prev in range(1,R+1):
        for s in range(1,S+1):
            c=ft.fragment_cert(((r_prev,s,r_cur),))
            p=ft.invert(c,m_cur)
            if p is not None:
                yield r_prev,p,(r_prev,s,r_cur)

def replay_word(word,m0):
    c=ft.fragment_cert(tuple(word))
    mend,mn,arg,end=ft.replay_fragment(c,m0)
    return mend,mn,arg,end,c

def search_endpoint(n,r_end,m_end,L,R,S):
    # node = (r_current,m_current,forward_word_to_target)
    q=deque([(r_end,m_end,())])
    seen={(0,r_end,m_end)}
    best=None
    legal=0
    for depth in range(1,L+1):
        nq=deque()
        while q:
            r_cur,m_cur,word_to_target=q.popleft()
            for r_prev,m_prev,ep in one_predecessors(r_cur,m_cur,R,S):
                legal+=1
                word=(ep,)+word_to_target
                key=(depth,r_prev,m_prev)
                if key in seen:continue
                seen.add(key)
                mend,mn,arg,end,c=replay_word(word,m_prev)
                assert mend==m_end
                y=(1<<r_prev)*m_prev-1
                row=(mn-n,n,y,mn,arg,depth,word,r_prev,r_end,m_prev,m_end)
                if best is None or row<best:best=row
                if mn<n:
                    return row,legal,len(seen)
                nq.append((r_prev,m_prev,word))
        q=nq
        if not q:break
    return None if best is None else best,legal,len(seen)

def audit(lo,hi,K,L,R,S):
    cnt=Counter();closed=[];hard=[];best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,r,m,x in ss:
            row,legal,states=search_endpoint(n,r,m,L,R,S)
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
    print("HARD",len(hard),"FIRST_HARD",hard[:60])
    print("STATUS UNIVERSAL_REVERSE_EPISODE_BFS_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=4097)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--L",type=int,default=3)
    ap.add_argument("--R",type=int,default=20)
    ap.add_argument("--S",type=int,default=20)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.L,a.R,a.S)
