#!/usr/bin/env python3
"""Synthetic multi-episode inverse-constructor coverage of q=0 RIGID sources.

Enumerate ALL reverse episode fragments of length 1..Lmax within:
  * starting anchor r0 <= R0max
  * total cofactor-map denominator exponent D <= Dmax
for each ending anchor actually encountered.

Capabilities are source-independent exact affine maps. They are sorted by
asymptotic contraction ratio before replay. Coverage is reported cumulatively
by fragment length, so the marginal value of composition is explicit.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from functools import lru_cache
from fractions import Fraction

import collatz_fragment_transfer_probe as ft
import collatz_q0_rigid_recharge_audit as ra

@lru_cache(None)
def bank_for_end(rend:int,Lmax:int,Dmax:int,R0max:int):
    caps={}
    # Build words backwards. partial is tuple in forward order.
    def rec(current_end, rev_eps, cost, depth):
        if depth>=1:
            w=tuple(reversed(rev_eps))
            c=ft.fragment_cert(w)
            key=(c['r0'],c['r1'],c['A'],c['B'],c['D'])
            old=caps.get(key)
            if old is None or len(c['word'])<len(old['word']):
                caps[key]=c
        if depth==Lmax:
            return
        # prepend episode (rprev,s,current_end), adding s+current_end to D.
        base_cost=cost+current_end
        if base_cost+1>Dmax:
            return
        for s in range(1,Dmax-base_cost+1):
            newcost=base_cost+s
            # rprev is unconstrained by D until/if another episode is prepended.
            for rprev in range(1,R0max+1):
                rec(rprev, rev_eps+((rprev,s,current_end),), newcost, depth+1)

    # Important: at first recursion, cost 0 and current_end=rend.
    rec(rend,tuple(),0,0)

    vals=list(caps.values())
    def slope_key(c):
        # start integer / ending integer asymptotic ratio
        # ~ 2^(r0 + D - r1) / A
        num_exp=c['r0']+c['D']-c['r1']
        return (Fraction(1<<num_exp,c['A']) if num_exp>=0
                else Fraction(1,c['A']*(1<<(-num_exp))),
                len(c['word']),c['D'])
    vals.sort(key=slope_key)
    return tuple(vals)

def classify(n,K,Lmax,Dmax,R0max):
    starts,branches=ra.rigid_episode_segment(n,K)
    if not branches:return None,None
    best=None
    for k,r,m,x in starts:
        for c in bank_for_end(r,Lmax,Dmax,R0max):
            p=ft.invert(c,m)
            if p is None:continue
            mend,mn,arg,end=ft.replay_fragment(c,p)
            assert mend==m
            gap=mn-n
            row=(gap,k,r,m,(1<<c['r0'])*p-1,mn,arg,
                 len(c['word']),c['D'],c['word'])
            if best is None or row<best:best=row
            if gap<0:return row,best
    return None,best

def audit(lo,hi,K,Lmax,Dmax,R0max):
    sources=[n for n in range(max(3,lo)|1,hi+1,2)
             if ra.rigid_episode_segment(n,K)[1]]
    print("SOURCES",len(sources),"RANGE",lo,hi,"K",K,
          "LMAX",Lmax,"DMAX",Dmax,"R0MAX",R0max)
    residual=set(sources)
    allwins=[]
    for L in range(1,Lmax+1):
        closed=[];best=[]
        for n in sorted(residual):
            row,b=classify(n,K,L,Dmax,R0max)
            if row is not None:
                closed.append((n,row))
            elif b is not None:
                best.append((b[0],n,b))
        for n,_ in closed:residual.remove(n)
        bylen=Counter(row[7] for _,row in closed)
        words=Counter(row[9] for _,row in closed)
        anchors=sorted({r for n in sources for _,r,_,_ in ra.rigid_episode_segment(n,K)[0]})
        banks={r:len(bank_for_end(r,L,Dmax,R0max)) for r in anchors}
        print("LEVEL",L,"NEW_CLOSED",len(closed),
              "CUM_CLOSED",len(sources)-len(residual),
              "RESIDUAL",len(residual),
              "WIN_LENGTHS",dict(bylen),
              "BANK_TOTAL",sum(banks.values()))
        print("TOP_WORDS",words.most_common(20))
        print("FIRST_CLOSED",closed[:20])
        best.sort()
        print("BEST_RESIDUAL",best[:20])
        print("RESIDUAL_HEAD",sorted(residual)[:80])
        allwins.extend(closed)
    print("FINAL_CLOSED",len(sources)-len(residual),"OF",len(sources))
    print("FINAL_RESIDUAL",len(residual),sorted(residual)[:120])
    print("STATUS SYNTHETIC_MULTI_EPISODE_BANK")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    ap.add_argument("--Lmax",type=int,default=2)
    ap.add_argument("--Dmax",type=int,default=18)
    ap.add_argument("--R0max",type=int,default=20)
    a=ap.parse_args();audit(a.lo,a.hi,a.K,a.Lmax,a.Dmax,a.R0max)
