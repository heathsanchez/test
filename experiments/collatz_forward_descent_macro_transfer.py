#!/usr/bin/env python3
"""Prospective transfer of forward q0 descent macros.

Train on earlier fixed sources that:
  * have no pre-q0 D/P certificate,
  * survive compiled grammar to q0 as RIGID,
  * then eventually descend.

From each training q0 orbit, collect every episode-word suffix (up to maxlen)
whose exact forward replay contains a value below the training source.

On an untouched held-out source, try those words from every q0 RIGID episode
start with matching initial anchor. Replay is exact; if the transferred path
contains a value below the held-out source, it is a valid direct lower-merge
certificate.

No held-out source contributes to the capability bank.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra
import collatz_fragment_transfer_probe as ft

def preq0_dp(n):
    k0=n.bit_length(); y=n
    for t in range(1,k0+1):
        y=base.T(y)
        if y<n:return ('D',t,y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:return ('P',t,y,p)
    return None

def candidate(n):
    if preq0_dp(n) is not None:return False
    ok,_=base.survives_to_q0(n)
    return ok and base.birth_status(n)[0]=='RIGID'

def q0_odd_starts_and_words(n,H=5000):
    k0=n.bit_length()
    _,y=base.forward_state(k0,n)
    t=k0
    # normalize to odd state
    while y%2==0 and y>=n:
        y=base.T(y);t+=1
    starts=[];words=[]
    if y<n:return starts,words
    for _ in range(256):
        if y<n:break
        assert y&1
        r,m,s,rp,mp,z=ra.episode(y)
        starts.append((t,r,m,y))
        words.append((r,s,rp))
        cur=y
        hit=False
        for j in range(1,r+s+1):
            cur=base.T(cur)
            if cur<n:
                hit=True
                break
        # Finish episode only for state progression if no hit.
        if hit:
            break
        y=z;t+=r+s
    return starts,words

def learn(lo,hi,maxlen):
    bank=defaultdict(dict); sources=0; macros=0
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        if not candidate(n):continue
        starts,words=q0_odd_starts_and_words(n)
        if not words:continue
        sources+=1
        # Every suffix ending at the first-descent episode is a descent macro.
        end=len(words)
        for a in range(max(0,end-maxlen),end):
            w=tuple(words[a:end])
            try:c=ft.fragment_cert(w)
            except AssertionError:continue
            key=(c['r0'],c['r1'],c['A'],c['B'],c['D'],c['word'])
            if key not in bank[c['r0']]:
                bank[c['r0']][key]=c;macros+=1
    return sources,{r:list(d.values()) for r,d in bank.items()},macros

def replay_from_current(c,m0):
    try:
        mend,mn,arg,end=ft.replay_fragment(c,m0)
        return mend,mn,arg,end
    except AssertionError:
        return None

def test(bank,lo,hi,K):
    cnt=Counter();closed=[];hard=[];best=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        if not candidate(n):continue
        ss,bs=ra.rigid_episode_segment(n,K)
        if not bs:continue
        cnt['sources']+=1;done=False;sourcebest=None
        for k,r,m,x in ss:
            for c in bank.get(r,()):
                cnt['attempts']+=1
                z=replay_from_current(c,m)
                if z is None:continue
                cnt['legal']+=1
                mend,mn,arg,end=z
                row=(mn-n,n,k,r,m,mn,arg,c['word'])
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
    ap.add_argument("--train-hi",type=int,default=8191)
    ap.add_argument("--held-hi",type=int,default=16383)
    ap.add_argument("--K",type=int,default=96)
    ap.add_argument("--maxlen",type=int,default=12)
    a=ap.parse_args()
    ns,bank,macros=learn(3,a.train_hi,a.maxlen)
    print("TRAIN",3,a.train_hi,"SOURCES",ns,"MACROS",macros,
          "ANCHORS",len(bank),"MAXLEN",a.maxlen)
    cnt,closed,hard,best=test(bank,a.train_hi+2,a.held_hi,a.K)
    print("HELD",a.train_hi+2,a.held_hi,"COUNTS",dict(cnt))
    print("CLOSED",len(closed))
    print("FIRST_CLOSED",closed[:30])
    print("BEST_GAPS",best[:30])
    print("HARD",len(hard),"FIRST_HARD",hard[:60])
    if closed:print("OBSERVED_FORWARD_DESCENT_MACRO_TRANSFER")
    else:print("NO_FORWARD_DESCENT_MACRO_TRANSFER")
    print("STATUS PROSPECTIVE_FORWARD_DESCENT_MACRO_SPIKE")

if __name__=="__main__":
    main()
