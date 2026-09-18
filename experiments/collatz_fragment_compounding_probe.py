#!/usr/bin/env python3
"""Prospective developmental compounding of transferable RIGID fragments.

Process disjoint dyadic source batches in chronological order. Before learning
from a batch, test the frozen bank accumulated from all earlier batches.
Then acquire verified fragments from that batch and move on.

Metrics:
  * bank size before/after
  * pre-acquisition closure on genuinely new sources
  * unique winning capabilities
  * marginal capabilities acquired from the batch
  * residual source list

This is an exact prospective capability-compounding experiment, not a proof.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter
import collatz_fragment_transfer_probe as ft
import collatz_q0_rigid_recharge_audit as ra

def learn_range(lo,hi,K,maxfrag):
    bank=defaultdict(dict)
    start=max(3,lo)
    if start%2==0:start+=1
    sources=0
    for n in range(start,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        sources+=1
        L=len(bs)
        for a in range(L):
            for b in range(a+1,min(L,a+maxfrag)+1):
                c=ft.fragment_cert(tuple(bs[a:b]))
                key=(c['r0'],c['r1'],c['A'],c['B'],c['D'])
                bank[c['r1']].setdefault(key,c)
    return sources,bank

def merge(dst,src):
    added=0
    for r,d in src.items():
        out=dst.setdefault(r,{})
        for k,c in d.items():
            if k not in out:
                out[k]=c;added+=1
    return added

def freeze(bank):
    return {r:list(d.values()) for r,d in bank.items()}

def test_bank(bank,lo,hi,K):
    cnt=Counter();closed=[];hard=[];wins=Counter();best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,r,m,x in ss:
            for c in bank.get(r,()):
                cnt['attempts']+=1
                p=ft.invert(c,m)
                if p is None:continue
                cnt['legal']+=1
                mend,mn,arg,end=ft.replay_fragment(c,p)
                assert mend==m
                y=(1<<c['r0'])*p-1
                gap=mn-n
                cap=(c['r0'],c['r1'],c['A'],c['B'],c['D'],c['word'])
                row=(gap,n,k,r,m,y,mn,arg,cap)
                if sourcebest is None or row<sourcebest:sourcebest=row
                if mn<n:
                    cnt['closed']+=1;closed.append(row);wins[cap]+=1;done=True;break
            if done:break
        if sourcebest is not None:best.append(sourcebest)
        if not done:hard.append(n)
    best.sort()
    return cnt,closed,hard,wins,best

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--K",type=int,default=96)
    ap.add_argument("--maxfrag",type=int,default=5)
    ap.add_argument("--bits-lo",type=int,default=9)
    ap.add_argument("--bits-hi",type=int,default=14)
    a=ap.parse_args()

    bank=defaultdict(dict)
    history=[]
    # Seed with all sources below first dyadic batch lower edge.
    seed_hi=(1<<a.bits_lo)-1
    ns,seed=learn_range(3,seed_hi,a.K,a.maxfrag)
    added=merge(bank,seed)
    print("SEED",3,seed_hi,"sources",ns,"bank",sum(len(d) for d in bank.values()),
          "added",added)

    for b in range(a.bits_lo,a.bits_hi+1):
        lo=(1<<b)+1
        hi=(1<<(b+1))-1
        frozen=freeze(bank)
        before=sum(len(v) for v in frozen.values())
        cnt,closed,hard,wins,best=test_bank(frozen,lo,hi,a.K)
        print("BATCH_TEST",b,lo,hi,
              "bank_before",before,
              "sources",cnt['sources'],
              "closed",len(closed),
              "hard",len(hard),
              "legal",cnt['legal'],
              "closure_frac",f"{len(closed)}/{cnt['sources']}")
        print("TOP_WINNERS",b,wins.most_common(12))
        print("BEST_GAPS",b,best[:12])
        print("HARD_HEAD",b,hard[:40])

        ns,new=learn_range(lo,hi,a.K,a.maxfrag)
        add=merge(bank,new)
        after=sum(len(d) for d in bank.values())
        print("BATCH_LEARN",b,"sources",ns,"new_caps",add,
              "bank_after",after)
        history.append((b,cnt['sources'],len(closed),len(hard),before,add,after))

    print("HISTORY",history)
    print("STATUS PROSPECTIVE_FRAGMENT_COMPOUNDING_SPIKE")

if __name__=="__main__":
    main()
