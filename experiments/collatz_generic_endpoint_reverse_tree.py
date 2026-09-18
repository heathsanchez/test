#!/usr/bin/env python3
"""Generic reverse-tree probe for a concrete C9 high-fuel endpoint lift.

Given X, enumerate the exact shortcut-Collatz reverse tree.  At reverse depth k,
a predecessor n is q=0-compatible iff 1<n<2^k.  Candidates n>X are already
closed by direct descent because T^k(n)=X<n.  For n<=X, test whether the source
survives to q=0 and is RIGID at birth.

Bounded reverse-tree discovery only; not a proof.
"""
from __future__ import annotations
import argparse
import collatz_q0_coalescence_component_audit as base

def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

def reverse_children(x:int):
    yield 2*x,'E'
    z=2*x-1
    if z%3==0:
        p=z//3
        if p>0 and p&1:
            yield p,'O'

def audit(X:int,depth:int):
    states={X:''}
    q0=direct=non=hered=0
    firstq=firstnon=firsthered=None
    maxfront=1
    for k in range(1,depth+1):
        nxt={}
        for y,w in states.items():
            for p,ch in reverse_children(y):
                nxt.setdefault(p,w+ch)
        states=nxt
        maxfront=max(maxfront,len(states))
        for n,w in states.items():
            if not (1<n<(1<<k)): continue
            q0+=1
            if firstq is None:firstq=(k,n,w)
            if n>X:
                direct+=1
                continue
            non+=1
            if firstnon is None:firstnon=(k,n,w)
            ok,_=base.survives_to_q0(n)
            if ok and base.birth_status(n)[0]=='RIGID':
                hered+=1
                if firsthered is None:firsthered=(k,n,w)
                print("HEREDITARY_NON_DIRECT",k,n,w)
                print("ENDPOINT",X)
                print("SEPARATOR_ENDPOINT_HAS_RIGID_NON_DIRECT_ANCESTOR")
                print("STATUS BOUNDED_GENERIC_REVERSE_TREE")
                return
    print("ENDPOINT",X)
    print("REVERSE_DEPTH",depth)
    print("MAX_FRONTIER",maxfront)
    print("Q0_COMPATIBLE",q0)
    print("DIRECT_DESCENT",direct)
    print("NON_DIRECT",non)
    print("HEREDITARY_NON_DIRECT",hered)
    print("FIRST_Q0",firstq)
    print("FIRST_NON_DIRECT",firstnon)
    print("FIRST_HEREDITARY_NON_DIRECT",firsthered)
    print("OBSERVED_NO_RIGID_NON_DIRECT_ANCESTOR")
    print("STATUS BOUNDED_GENERIC_REVERSE_TREE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--X",type=int,required=True)
    ap.add_argument("--depth",type=int,default=50)
    a=ap.parse_args()
    audit(a.X,a.depth)
