#!/usr/bin/env python3
"""Symbolic reverse-cylinder search for q=0 sources entering three C9 replays.

Target cylinder:
    x = X0 + 2^L q,  X0=326575849, L=29.

Reverse shortcut operations preserve a power-of-two cylinder:
 E: b+2^M q -> 2b + 2^(M+1) q
 O: choose unique r mod 3 making the numerator divisible,
    q=r+3q', then
    b'=(2b+2^(M+1)r-1)/3, modulus 2^(M+1).

The O predecessor must be odd.  At reverse depth k a base 1<b<2^k is an
ordinary source already at q=0 by the time it reaches the target cylinder.

We test every such candidate for hereditary RIGIDness through the prefix and
through all 27 C9 shortcut steps.

Bounded by --depth; exact within that reverse-depth horizon.
"""
from __future__ import annotations
import argparse
import collatz_q0_coalescence_component_audit as base

X0=326575849
L0=29
C9_STEPS=27

def children(b:int,M:int):
    # Reverse even shortcut step.
    yield 2*b,M+1,'E'
    # Reverse odd shortcut step; choose endpoint-cylinder parameter residue.
    pow2=1<<(M+1)
    r=None
    for rr in (0,1,2):
        if (2*b+pow2*rr-1)%3==0:
            r=rr;break
    assert r is not None
    bp=(2*b+pow2*r-1)//3
    if bp>0 and bp&1:
        yield bp,M+1,'O'

def fixed_source_rigid_to(n:int,k:int):
    # Before q=0 use exact fixed-source tail semantics.
    for j in range(1,k+1):
        b=n%(1<<j); q=n>>j
        out,data=base.cylinder_status(j,b)
        if out in ('DESCEND','CLOSED'):
            return False,(j,b,q,out,data)
        if out=='TAIL_CLOSED' and q>=data[-1]:
            return False,(j,b,q,out,data)
    return True,None

def rigid_future(n:int,k:int,steps:int):
    for j in range(k,k+steps+1):
        out,data=base.cylinder_status(j,n)
        if out!='RIGID':
            return False,(j,out,data)
    return True,None

def audit(K:int):
    states={(X0,L0)}
    candidates=0; prefix_rigid=0; full_rigid=0
    first=[]
    for depth in range(1,K+1):
        nxt=set()
        for b,M in states:
            for bp,Mp,ch in children(b,M):
                # Horizon pruning: ratio bp/2^depth can shrink by at most /3
                # per future reverse O step. If even all remaining steps are O
                # cannot reach q0, discard.
                rem=K-depth
                if bp >= (1<<depth)*(3**rem):
                    continue
                nxt.add((bp,Mp))
        states=nxt
        for b,M in states:
            if not (1<b<(1<<depth)):
                continue
            candidates+=1
            # Verify exact target-cylinder hit.
            y=b
            for _ in range(depth):
                y=base.T(y)
            assert y>=X0 and (y-X0)%(1<<L0)==0,(depth,b,y)
            ok,why=fixed_source_rigid_to(b,depth)
            if not ok:
                if len(first)<20:first.append(('PREFIX_CLOSE',depth,b,y,why))
                continue
            prefix_rigid+=1
            ok2,why2=rigid_future(b,depth,C9_STEPS)
            if ok2:
                full_rigid+=1
                row=('THREE_REPLAY_Q0_RIGID',depth,b,y)
                print(*row)
                if len(first)<20:first.append(row)
            elif len(first)<20:
                first.append(('FUTURE_CLOSE',depth,b,y,why2))
        print("DEPTH",depth,"states",len(states),"candidates",candidates,
              "prefix_rigid",prefix_rigid,"full_rigid",full_rigid)
        if full_rigid:
            break
    print("MAX_DEPTH",K)
    print("Q0_CANDIDATES",candidates)
    print("PREFIX_HEREDITARY_RIGID",prefix_rigid)
    print("FULL_THREE_REPLAY_RIGID",full_rigid)
    for z in first: print("WITNESS",z)
    if full_rigid:
        print("SEPARATOR_THREE_REPLAY_EXISTS_AFTER_Q0")
    else:
        print("OBSERVED_NO_THREE_REPLAY_AFTER_Q0_IN_REVERSE_DEPTH")
    print("STATUS BOUNDED_SYMBOLIC_REVERSE_CYLINDER_ONLY")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--depth",type=int,default=80)
    a=ap.parse_args();audit(a.depth)
