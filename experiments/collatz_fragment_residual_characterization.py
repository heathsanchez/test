#!/usr/bin/env python3
"""Characterize held-out residuals after transferable-fragment closure.

Train fragment bank on sources <16384, test 16385..32767. Split held-out
RIGID-return sources into CLOSED/HARD and compare exact structural features:
birth endpoint, first episode, RIGID segment length, anchor counts, and
eventual first non-RIGID outcome.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import collatz_fragment_transfer_probe as ft
import collatz_q0_rigid_recharge_audit as ra
import collatz_q0_coalescence_component_audit as base

TRAIN_HI=16383
LO=16385
HI=32767
K=128
MAXFRAG=5

def build_bank():
    ns,bank=ft.learn(3,TRAIN_HI,96,MAXFRAG)
    return bank

def source_closed(bank,n):
    ss,bs=ra.rigid_episode_segment(n,96)
    if not bs:return False,None
    for k,r,m,x in ss:
        for c in bank.get(r,()):
            p=ft.invert(c,m)
            if p is None:continue
            mend,mn,arg,end=ft.replay_fragment(c,p)
            if mn<n:
                return True,(k,r,m,mn,arg,c['word'])
    return False,None

def features(n):
    k0=n.bit_length()
    c0,d0=base.forward_state(k0,n)
    ss,bs=ra.rigid_episode_segment(n,K)
    if not bs:return None
    first=bs[0]
    lastk=ss[-1][0] if ss else k0
    anchors=Counter(z[1] for z in ss)
    # Find first non-RIGID after q0.
    first_non=None
    for k in range(k0,K+1):
        out,data=base.cylinder_status(k,n)
        if out!='RIGID':
            first_non=(k,out,data)
            break
    # Direct descent time in ordinary orbit after q0, bounded.
    y=d0; direct=None
    for t in range(1,257):
        y=base.T(y)
        if y<n:
            direct=(t,y);break
    return {
        'k0':k0,'c0':c0,'slack0':k0-c0,'d0':d0,
        'ratio_bucket':(d0*16)//n,
        'first':first,
        'episodes':len(bs),
        'rigid_span':(first_non[0]-k0 if first_non else K-k0+1),
        'first_non':first_non[1] if first_non else 'NONE',
        'max_anchor':max(anchors,default=0),
        'anchor_signature':tuple(sorted(anchors.items())),
        'direct_t':direct[0] if direct else None,
    }

bank=build_bank()
C=Counter();H=Counter()
closed_rows=[];hard_rows=[]
for n in range(LO,HI+1,2):
    ss,bs=ra.rigid_episode_segment(n,96)
    if not bs:continue
    closed,w=source_closed(bank,n)
    f=features(n)
    row=(n,f,w)
    (closed_rows if closed else hard_rows).append(row)
    tgt=C if closed else H
    tgt[('first',f['first'])]+=1
    tgt[('slack0',f['slack0'])]+=1
    tgt[('ratio',f['ratio_bucket'])]+=1
    tgt[('first_non',f['first_non'])]+=1
    tgt[('episodes_bucket',min(f['episodes'],10))]+=1
    tgt[('rigid_span_bucket',min(f['rigid_span']//5,10))]+=1
    tgt[('max_anchor',min(f['max_anchor'],15))]+=1

print("CLOSED",len(closed_rows),"HARD",len(hard_rows))
for name,cnt in [('CLOSED',C),('HARD',H)]:
    print("GROUP",name)
    for kind in ['first','slack0','ratio','first_non','episodes_bucket','rigid_span_bucket','max_anchor']:
        vals=[(k[1],v) for k,v in cnt.items() if k[0]==kind]
        vals.sort(key=lambda z:(-z[1],repr(z[0])))
        print(kind,vals[:25])
print("HARD_ROWS_HEAD")
for n,f,w in hard_rows[:80]:
    print("HARD",n,f)
print("CLOSED_ROWS_HEAD")
for n,f,w in closed_rows[:20]:
    print("CLOSEDROW",n,f,"W",w)
print("STATUS HELD_RESIDUAL_CHARACTERIZATION")
