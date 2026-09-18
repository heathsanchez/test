#!/usr/bin/env python3
"""Spike: joint 2-adic / 3-adic separation of consecutive RIGID return centers."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_q0_rigid_recharge_audit as ra

def vp(x,p):
    x=abs(x); assert x
    v=0
    while x%p==0:x//=p;v+=1
    return v

def core6(x):
    x=abs(x);assert x
    while x%2==0:x//=2
    while x%3==0:x//=3
    return x

def det(a,b):
    pa,ua=a['q']; pb,ub=b['q']
    return pa*ub-pb*ua

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            w=tuple(branches[start:end])
            c=cache.setdefault(w,ra.certificate(w))
            m0=starts[start][2];m1=starts[end][2]
            out[r].append((c,m0,m1,starts[start][0]))
        last[r]=end
    return out

def audit(lo,hi,K):
    trans=[]; counts=Counter()
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        for r,seq in returns(n,K).items():
            sw=[]
            for i in range(len(seq)-1):
                a,m0,m1,k0=seq[i]; b,n0,n1,k1=seq[i+1]
                if a['q']==b['q']:continue
                z=ra.switch_law(a,b,n0,n1)
                if z is None:continue
                Kdet=det(a,b)
                assert vp(Kdet,2)==z['h']
                sw.append((i,a,b,z,Kdet,k1))
            for x,y in zip(sw,sw[1:]):
                if y[0]!=x[0]+1:continue
                kx=x[4]; ky=y[4]
                s0=(vp(kx,2),vp(kx,3),core6(kx).bit_length())
                s1=(vp(ky,2),vp(ky,3),core6(ky).bit_length())
                rel2='up' if s1[0]>s0[0] else ('down' if s1[0]<s0[0] else 'eq')
                rel3='up' if s1[1]>s0[1] else ('down' if s1[1]<s0[1] else 'eq')
                counts[(rel2,rel3)]+=1
                trans.append((n,r,x[3]['outcome'],y[3]['outcome'],s0,s1,
                              x[1]['q'],x[2]['q'],y[2]['q']))
    print("TRANSITIONS",len(trans))
    print("REL_COUNTS",dict(sorted(counts.items())))
    tests={
      'LEX_H2_H3':lambda a,b:(b[0],b[1])<(a[0],a[1]),
      'LEX_H2_NEGH3':lambda a,b:(b[0],-b[1])<(a[0],-a[1]),
      'LEX_NEGH2_H3':lambda a,b:(-b[0],b[1])<(-a[0],a[1]),
      'LEX_NEGH2_NEGH3':lambda a,b:(-b[0],-b[1])<(-a[0],-a[1]),
      'SUM_DOWN':lambda a,b:b[0]+b[1]<a[0]+a[1],
      'H2_MINUS_H3_DOWN':lambda a,b:b[0]-b[1]<a[0]-a[1],
      'H3_MINUS_H2_DOWN':lambda a,b:b[1]-b[0]<a[1]-a[0],
    }
    for name,fn in tests.items():
        bad=[z for z in trans if not fn(z[4],z[5])]
        print("TEST",name,"PASS",len(trans)-len(bad),"FAIL",len(bad),
              "FIRST_FAIL",bad[0] if bad else None)
    # Look specifically at every 2-adic increase.
    ups=[z for z in trans if z[5][0]>z[4][0]]
    print("H2_UP",len(ups),
          "H3_DOWN",sum(z[5][1]<z[4][1] for z in ups),
          "H3_EQ",sum(z[5][1]==z[4][1] for z in ups),
          "H3_UP",sum(z[5][1]>z[4][1] for z in ups))
    print("H2_UP_EXAMPLES",ups[:20])
    print("STATUS ADELlC_SWITCH_SEPARATION_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=8191)
    ap.add_argument("--K",type=int,default=80)
    a=ap.parse_args();audit(a.lo,a.hi,a.K)
