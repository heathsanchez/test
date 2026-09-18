#!/usr/bin/env python3
"""Reverse-tree audit for the least C9 three-replay endpoint.

C9 three-replay fuel gives
    m == 163287925 (mod 2^28)
and least odd endpoint
    x = 326575849.

Enumerate the exact shortcut-Collatz reverse tree. At reverse depth k, a source
n is q=0-compatible iff 1<n<2^k. A compatible n>x is already direct descent
because T^k(n)=x<n. A compatible n<=x is the first genuinely non-direct
candidate; test whether it survives to q=0 and is RIGID at birth.

Bounded reverse-tree discovery only; not a proof.
"""
from __future__ import annotations
import argparse
import collatz_q0_coalescence_component_audit as base

X=326575849

def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

def reverse_children(x:int):
    yield 2*x,'E'
    z=2*x-1
    if z%3==0:
        p=z//3
        if p>0 and p&1:
            yield p,'O'

def audit(depth:int):
    states={X:''}
    q0=direct=non_direct=hereditary=0
    first_q0=first_non=first_hered=None
    max_front=1
    for k in range(1,depth+1):
        nxt={}
        for y,w in states.items():
            for p,ch in reverse_children(y):
                nxt.setdefault(p,w+ch)
        states=nxt
        max_front=max(max_front,len(states))
        for n,w in states.items():
            if not (1<n<(1<<k)):
                continue
            q0+=1
            if first_q0 is None:first_q0=(k,n,w)
            # exact replay
            y=n
            for _ in range(k): y=T(y)
            assert y==X
            if n>X:
                direct+=1
                continue
            non_direct+=1
            if first_non is None:first_non=(k,n,w)
            ok,_=base.survives_to_q0(n)
            if ok and base.birth_status(n)[0]=='RIGID':
                hereditary+=1
                if first_hered is None:first_hered=(k,n,w)
                print("HEREDITARY_NON_DIRECT_THREE_REPLAY_ANCESTOR",k,n,w)
                return summarize(depth,max_front,q0,direct,non_direct,hereditary,
                                 first_q0,first_non,first_hered)
    return summarize(depth,max_front,q0,direct,non_direct,hereditary,
                     first_q0,first_non,first_hered)

def summarize(depth,max_front,q0,direct,non_direct,hereditary,
              first_q0,first_non,first_hered):
    print("ENDPOINT",X)
    print("REVERSE_DEPTH",depth)
    print("MAX_FRONTIER",max_front)
    print("Q0_COMPATIBLE",q0)
    print("DIRECT_DESCENT",direct)
    print("NON_DIRECT",non_direct)
    print("HEREDITARY_NON_DIRECT",hereditary)
    print("FIRST_Q0",first_q0)
    print("FIRST_NON_DIRECT",first_non)
    print("FIRST_HEREDITARY_NON_DIRECT",first_hered)
    if first_hered:
        print("SEPARATOR_THREE_REPLAY_ENDPOINT_HAS_RIGID_NON_DIRECT_ANCESTOR")
    else:
        print("OBSERVED_NO_RIGID_NON_DIRECT_ANCESTOR")
    print("STATUS BOUNDED_THREE_REPLAY_REVERSE_TREE_ONLY")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=45)
    a=ap.parse_args()
    audit(a.depth)
