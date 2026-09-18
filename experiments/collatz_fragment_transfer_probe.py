#!/usr/bin/env python3
"""Prospective transfer of verified RIGID episode fragments across sources.

Train on one source range. Every contiguous RIGID episode fragment becomes a
universal exact affine path capability keyed by its ending anchor.

On an untouched held-out source, whenever its current RIGID endpoint has that
ending anchor, invert the learned fragment.  Replay verifies the candidate
exactly.  If the candidate path visits any integer below the held-out source,
we have a transferable lower-merge certificate.

This is a prospective capability-transfer experiment, not a Collatz proof.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base

def fragment_cert(word):
    word=tuple(tuple(z) for z in word)
    assert word
    assert all(a[2]==b[0] for a,b in zip(word,word[1:]))
    A,B,D=1,0,0
    for r,s,rp in word:
        A,B,D=3**r*A,3**r*B+((1<<s)-1)*(1<<D),D+s+rp
    return {'word':word,'r0':word[0][0],'r1':word[-1][2],
            'A':A,'B':B,'D':D,
            'steps':sum(r+s for r,s,rp in word)}

def replay_fragment(c,m0):
    x=(1<<c['r0'])*m0-1
    mn=x; arg=0; t=0
    for expected in c['word']:
        r,m,s,rp,mp,y=ra.episode(x)
        assert (r,s,rp)==expected
        for _ in range(r+s):
            x=base.T(x);t+=1
            if x<mn:mn=x;arg=t
        assert x==y
    mend=(x+1)>>c['r1']
    return mend,mn,arg,x

def invert(c,mend):
    num=(1<<c['D'])*mend-c['B']
    if num<=0 or num%c['A']:return None
    p=num//c['A']
    if p<=0 or not (p&1):return None
    try:
        me,_,_,_=replay_fragment(c,p)
    except AssertionError:
        return None
    return p if me==mend else None

def learn(lo,hi,K,maxfrag):
    bank=defaultdict(dict)
    starts=max(3,lo)
    if starts%2==0:starts+=1
    sources=0
    for n in range(starts,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        sources+=1
        L=len(bs)
        for a in range(L):
            for b in range(a+1,min(L,a+maxfrag)+1):
                w=tuple(bs[a:b])
                c=fragment_cert(w)
                key=(c['r0'],c['r1'],c['A'],c['B'],c['D'])
                bank[c['r1']].setdefault(key,c)
    return sources,{r:list(d.values()) for r,d in bank.items()}

def heldout(bank,lo,hi,K):
    cnt=Counter();closed=[];hard=[];best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,r,m,x in ss:
            caps=bank.get(r,())
            cnt['endpoint_checks']+=1
            for c in caps:
                cnt['attempts']+=1
                p=invert(c,m)
                if p is None:continue
                cnt['legal']+=1
                mend,mn,arg,end=replay_fragment(c,p)
                assert mend==m
                y=(1<<c['r0'])*p-1
                gap=mn-n
                row=(gap,n,k,r,m,y,mn,arg,c['r0'],c['r1'],c['word'])
                if sourcebest is None or row<sourcebest:sourcebest=row
                if mn<n:
                    cnt['closed']+=1;closed.append(row);done=True;break
            if done:break
        if sourcebest is not None:best.append(sourcebest)
        if not done:hard.append(n)
    best.sort()
    return cnt,closed,hard,best

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--train-hi",type=int,default=4095)
    ap.add_argument("--held-hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--maxfrag",type=int,default=5)
    a=ap.parse_args()
    ns,bank=learn(3,a.train_hi,a.K,a.maxfrag)
    caps=sum(len(v) for v in bank.values())
    print("TRAIN_SOURCES",ns,"CAPABILITIES",caps,
          "ANCHORS",len(bank),"MAXFRAG",a.maxfrag)
    cnt,closed,hard,best=heldout(bank,a.train_hi+2,a.held_hi,a.K)
    print("HELD_COUNTS",dict(cnt))
    print("HELD_CLOSED",len(closed))
    print("FIRST_CLOSED",closed[:30])
    print("BEST_GAPS",best[:30])
    print("HELD_HARD",len(hard),"FIRST_HARD",hard[:60])
    if closed:print("OBSERVED_TRANSFERRED_FRAGMENT_LOWER_MERGES")
    else:print("NO_TRANSFERRED_FRAGMENT_LOWER_MERGE")
    print("STATUS PROSPECTIVE_FRAGMENT_TRANSFER_SPIKE")

if __name__=="__main__":
    main()
