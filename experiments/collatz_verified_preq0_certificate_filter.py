#!/usr/bin/env python3
"""Strengthen least-counterexample q0 filtering with verified reverse certificates.

For each fixed source n and each orbit point y up to q0, try:
  D: y<n;
  P: immediate inverse odd predecessor;
  RQ: every nonredundant first-contraction certificate from the exact
      reverse-predecessor tree at Q=7,9,12.

Any predecessor p<n with T^k(p)=y is a lower-merge certificate for n.
"""
from __future__ import annotations
from collections import Counter
import collatz_q0_coalescence_component_audit as base
import collatz_reverse_predecessor_tree as rpt

def bank(Q):
    certs=rpt.enumerate_first_contractions(Q)
    _,selected=rpt.quotient(certs,Q)
    return [c for c,_ in selected]

BANKS={Q:bank(Q) for Q in (7,9,12)}
print("BANK_SIZES",{Q:len(BANKS[Q]) for Q in BANKS})

def cert_at_y(n,y,certs):
    for c in certs:
        if y % c.d != c.residue:
            continue
        num=c.a*y-c.c
        if num<=0 or num%c.d:
            continue
        p=num//c.d
        if p<n:
            # replay check
            x=p
            for _ in c.word:
                x=base.T(x)
            assert x==y
            return p,c
    return None

def first_cert(n,Q):
    k0=n.bit_length();y=n
    certs=BANKS[Q]
    for t in range(1,k0+1):
        y=base.T(y)
        if y<n:return ('D',t,y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:return ('P',t,y,p)
        z=cert_at_y(n,y,certs)
        if z is not None:
            p,c=z
            return (f'Q{Q}',t,y,p,c.d,c.residue,c.word)
    return None

def grammar_q0_rigid(n):
    ok,_=base.survives_to_q0(n)
    return ok and base.birth_status(n)[0]=='RIGID'

for hi in (8191,16383,32767,65535):
    baseN=[n for n in range(3,hi+1,2) if grammar_q0_rigid(n)]
    print("LIMIT",hi,"GRAMMAR",len(baseN))
    for Q in (7,9,12):
        cnt=Counter();live=[]
        for n in baseN:
            c=first_cert(n,Q)
            if c is None:
                live.append(n)
            else:
                cnt[c[0]]+=1
        print("FILTER",Q,"CLOSED",len(baseN)-len(live),"LIVE",len(live),
              "KINDS",dict(cnt),"LIVE_HEAD",live[:60])
print("STATUS VERIFIED_PREQ0_CERTIFICATE_FILTER")
