#!/usr/bin/env python3
"""Spike: S-unit-free defect core across exact RIGID return switches.

For a return certificate c with fixed point q=p/u define E_c(m)=u*m-p.
Inside c:
    E_c(F_c(m)) = 3^R * E_c(m) / 2^D.
Therefore the prime-to-6 core
    kappa(E)=|E| / (2^v2(E) 3^v3(E))
is exactly invariant during a fixed return.  This script measures the only
place it can change: a switch between distinct return patterns.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_q0_rigid_recharge_audit as ra

def vp(x,p):
    x=abs(x); v=0
    if x==0:return 10**9
    while x%p==0:
        x//=p;v+=1
    return v

def core6(x):
    x=abs(x)
    assert x
    while x%2==0:x//=2
    while x%3==0:x//=3
    return x

def defect(c,m):
    p,u=c['q']
    return u*m-p

def returns_for_source(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={}; last={}; seqs=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            m0=starts[start][2];m1=starts[end][2]
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            seqs[r].append((c,m0,m1,starts[start][0]))
        last[r]=end
    return seqs

def audit(N,K):
    cnt=Counter(); bad_transport=[]; rows=[]
    for n in range(3,N+1,2):
        for r,seq in returns_for_source(n,K).items():
            for i in range(len(seq)-1):
                w,m0,m1,k0=seq[i]
                v,n0,n1,k1=seq[i+1]
                assert m1==n0
                # Same pattern is not a switch; its core must be invariant.
                ew0=defect(w,m0); ew1=defect(w,m1)
                assert core6(ew0)==core6(ew1)
                if w['q']==v['q']:
                    cnt['same']+=1
                    continue
                z=ra.switch_law(w,v,m1,n1)
                if z is None:continue
                ev0=defect(v,m1); ev1=defect(v,n1)
                assert core6(ev0)==core6(ev1)
                a=core6(ew1); b=core6(ev0)
                rel='down' if b<a else ('equal' if b==a else 'up')
                cnt[z['outcome']+'_'+rel]+=1
                ratio=(a,b)
                row=(n,r,k1,z['outcome'],z['h'],a,b,ew1,ev0,w['q'],v['q'])
                rows.append(row)
    print("COUNTS",dict(sorted(cnt.items())))
    for outcome in ('drop','recharge','flat'):
        sub=[x for x in rows if x[3]==outcome]
        if not sub:continue
        print("OUTCOME",outcome,"N",len(sub),
              "down",sum(x[6]<x[5] for x in sub),
              "equal",sum(x[6]==x[5] for x in sub),
              "up",sum(x[6]>x[5] for x in sub))
        print("FIRST",sub[:12])
    # Test simple candidate orders.
    tests={
      'KAPPA_NONINCREASE': lambda x:x[6]<=x[5],
      'KAPPA_STRICT_DROP_ON_RECHARGE': lambda x:(x[3]!='recharge' or x[6]<x[5]),
      'H_KAPPA_LEX': lambda x:(x[4],x[6]) < (x[4]+(0 if x[3]=='recharge' else 0),x[5]),
    }
    for name,fn in tests.items():
        bad=[x for x in rows if not fn(x)]
        print("TEST",name,"pass",len(rows)-len(bad),"fail",len(bad),
              "first_fail",bad[0] if bad else None)
    print("STATUS S_UNIT_CORE_SWITCH_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    a=ap.parse_args();audit(a.N,a.K)
