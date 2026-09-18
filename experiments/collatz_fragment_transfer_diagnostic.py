#!/usr/bin/env python3
"""Diagnose why prospective cross-source fragment transfer leaves residuals.

Train is frozen at sources <=4095. Held-out is 4097..8191.
Sweep maximum fragment length and classify each held-out hard source by:
  NO_ANCHOR   - no endpoint anchor represented in bank
  NO_LEGAL    - represented anchor(s), but no exact inverse fragment applies
  ABOVE_ONLY  - exact inverse(s) apply, but every replay path stays >= source
  CLOSED      - some transferred replay path dips below source

This is prospective and does not learn from held-out sources.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_fragment_transfer_probe as ft
import collatz_q0_rigid_recharge_audit as ra

def learn(hi,K,maxfrag):
    bank=defaultdict(dict)
    for n in range(3,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs: continue
        L=len(bs)
        for a in range(L):
            for b in range(a+1,min(L,a+maxfrag)+1):
                c=ft.fragment_cert(tuple(bs[a:b]))
                key=(c['r0'],c['r1'],c['A'],c['B'],c['D'])
                bank[c['r1']].setdefault(key,c)
    return {r:list(d.values()) for r,d in bank.items()}

def classify_source(n,bank,K):
    ss,bs=ra.rigid_episode_segment(n,K)
    if not bs:return None
    saw_anchor=False;saw_legal=False;best=None;bestrow=None
    for k,r,m,x in ss:
        caps=bank.get(r,())
        if caps:saw_anchor=True
        for c in caps:
            p=ft.invert(c,m)
            if p is None: continue
            saw_legal=True
            mend,mn,arg,end=ft.replay_fragment(c,p)
            assert mend==m
            gap=mn-n
            row=(gap,k,r,m,(1<<c['r0'])*p-1,mn,arg,c['word'])
            if best is None or gap<best:
                best=gap;bestrow=row
            if gap<0:return 'CLOSED',row
    if not saw_anchor:return 'NO_ANCHOR',None
    if not saw_legal:return 'NO_LEGAL',None
    return 'ABOVE_ONLY',bestrow

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--K",type=int,default=96)
    ap.add_argument("--train-hi",type=int,default=4095)
    ap.add_argument("--held-lo",type=int,default=4097)
    ap.add_argument("--held-hi",type=int,default=8191)
    ap.add_argument("--maxfrag-hi",type=int,default=10)
    a=ap.parse_args()

    held=[n for n in range(a.held_lo|1,a.held_hi+1,2)
          if ra.rigid_episode_segment(n,a.K)[1]]
    print("HELD_SOURCES",len(held))
    for mf in range(1,a.maxfrag_hi+1):
        bank=learn(a.train_hi,a.K,mf)
        cnt=Counter();best=[];examples=defaultdict(list)
        for n in held:
            cls,row=classify_source(n,bank,a.K)
            cnt[cls]+=1
            if row is not None:
                best.append((row[0],n,cls,row))
            if len(examples[cls])<15: examples[cls].append((n,row))
        best.sort()
        print("FRAGLEN",mf,
              "BANK",sum(len(v) for v in bank.values()),
              "ANCHORS",len(bank),
              "COUNTS",dict(cnt),
              "CLOSURE",f"{cnt['CLOSED']}/{len(held)}")
        print("EXAMPLES_NO_ANCHOR",examples['NO_ANCHOR'])
        print("EXAMPLES_NO_LEGAL",examples['NO_LEGAL'])
        print("EXAMPLES_ABOVE_ONLY",examples['ABOVE_ONLY'])
        print("BEST_NONCLOSED",[z for z in best if z[2]!='CLOSED'][:12])
    print("STATUS FRAGMENT_TRANSFER_RESIDUAL_DIAGNOSTIC")

if __name__=="__main__":
    main()
