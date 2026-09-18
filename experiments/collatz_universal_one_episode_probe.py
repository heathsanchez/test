#!/usr/bin/env python3
"""Prospective universal one-episode reverse constructor.

Instead of learning fragments from earlier sources, enumerate every single
episode shape (r0,s,r1) in a bounded parameter box, keyed by the current
ending anchor r1.  Invert it at each hereditary RIGID endpoint, replay exactly,
and accept any candidate path that visits a value below the fixed source.

This asks whether the successful cross-source transfer is really a generic
one-episode theorem family rather than memorized examples.
"""
from __future__ import annotations
import argparse
from collections import Counter
import collatz_fragment_transfer_probe as ft
import collatz_q0_rigid_recharge_audit as ra

def caps_for_anchor(r1,R,S):
    out=[]
    for r0 in range(1,R+1):
        for s in range(1,S+1):
            try:
                c=ft.fragment_cert(((r0,s,r1),))
            except AssertionError:
                continue
            out.append(c)
    return out

def audit(lo,hi,K,R,S):
    cache={}
    cnt=Counter();closed=[];hard=[];best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,r,m,x in ss:
            caps=cache.setdefault(r,caps_for_anchor(r,R,S))
            for c in caps:
                cnt['attempts']+=1
                p=ft.invert(c,m)
                if p is None:continue
                cnt['legal']+=1
                mend,mn,arg,end=ft.replay_fragment(c,p)
                assert mend==m
                y=(1<<c['r0'])*p-1
                row=(mn-n,n,k,r,m,y,mn,arg,c['r0'],c['r1'],c['word'])
                if sourcebest is None or row<sourcebest:sourcebest=row
                if mn<n:
                    cnt['closed']+=1;closed.append(row);done=True;break
            if done:break
        if sourcebest is not None:best.append(sourcebest)
        if not done:hard.append(n)
    best.sort()
    print("RANGE",lo,hi,"K",K,"R",R,"S",S)
    print("COUNTS",dict(cnt))
    print("CLOSED",len(closed))
    print("FIRST_CLOSED",closed[:30])
    print("BEST_GAPS",best[:30])
    print("HARD",len(hard),"FIRST_HARD",hard[:60])
    print("STATUS UNIVERSAL_ONE_EPISODE_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=4097)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--R",type=int,default=20)
    ap.add_argument("--S",type=int,default=20)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.R,a.S)
