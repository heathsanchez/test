#!/usr/bin/env python3
"""High-fuel lift audit for the smallest expanding RIGID return-cycle separator.

Discovery-only: this is not a Collatz proof.

Observed RIGID cycle at source 26863, anchor r=1:
    G(m) = (729*m + 467) / 512.
One replay requires v2((-217)m-467) >= 10.
Two replays require >= 19, whose least positive residue is m=234357 mod 2^19.

The corresponding episode anchor is x=2*m-1=468713.  We enumerate the exact
shortcut-Collatz reverse tree of x.  At reverse depth k, a predecessor n is a
q=0-compatible source iff 1<n<2^k.  If n>x, then T^k(n)=x<n and the source is
already closed by direct descent.

The audit asks whether any q=0-compatible lift of the two-replay congruence can
avoid that direct descent in the searched reverse depth.
"""
from __future__ import annotations
import argparse

A=729
B=467
D=9
R=1
C=(1<<D)-A

def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

def v2(x:int)->int:
    assert x
    x=abs(x)
    return (x & -x).bit_length()-1

def reverse_children(x:int):
    yield 2*x, "E"
    z=2*x-1
    if z%3==0:
        p=z//3
        if p>0 and p&1:
            yield p, "O"

def least_fuel_m(replays:int)->tuple[int,int]:
    assert replays>=1
    bits=replays*D+1
    mod=1<<bits
    rho=(B*pow(C,-1,mod))%mod
    if rho==0:
        rho=mod
    assert rho&1
    return rho,bits

def replay_cycle(m:int)->int:
    num=A*m+B
    assert num%(1<<D)==0
    return num>>D

def audit(max_depth:int):
    m,bits=least_fuel_m(2)
    assert bits==19 and m==234357
    d0=C*m-B
    assert v2(d0)==19
    m1=replay_cycle(m)
    m2=replay_cycle(m1)
    assert (m,m1,m2)==(234357,333685,475111)
    assert v2(C*m1-B)==10
    x=(1<<R)*m-1
    assert x==468713

    states={x:""}
    q0=0
    direct=0
    non_direct=[]
    first_q0=None
    max_states=1
    for k in range(1,max_depth+1):
        nxt={}
        for y,w in states.items():
            for p,ch in reverse_children(y):
                # One witness word per predecessor value is enough.
                nxt.setdefault(p,w+ch)
        states=nxt
        max_states=max(max_states,len(states))
        for n,w in states.items():
            if 1<n<(1<<k):
                q0+=1
                if first_q0 is None:
                    first_q0=(k,n,w)
                assert T_iter(n,k)==x
                if n>x:
                    direct+=1
                else:
                    non_direct.append((k,n,w))
                    if len(non_direct)>=20:
                        break
        if len(non_direct)>=20:
            break

    print("CYCLE_MAP",A,B,D,C)
    print("TWO_REPLAY_RESIDUE",m,"mod",1<<19)
    print("TWO_REPLAY_TRACE",m,m1,m2)
    print("ANCHOR_ENDPOINT",x)
    print("REVERSE_DEPTH",max_depth)
    print("MAX_FRONTIER_STATES",max_states)
    print("Q0_COMPATIBLE_LIFTS",q0)
    print("DIRECT_DESCENT_LIFTS",direct)
    print("FIRST_Q0_LIFT",first_q0)
    print("NON_DIRECT_LIFTS",len(non_direct))
    for row in non_direct:
        print("NON_DIRECT_HIGH_FUEL_LIFT",row)
    if non_direct:
        print("SEPARATOR_HIGH_FUEL_LIFT_AVOIDS_DIRECT_DESCENT")
    else:
        print("OBSERVED_ALL_HIGH_FUEL_Q0_LIFTS_DIRECT_DESCEND")
    print("STATUS BOUNDED_REVERSE_TREE_DISCOVERY_ONLY")

def T_iter(n:int,k:int)->int:
    for _ in range(k):
        n=T(n)
    return n

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=40)
    a=ap.parse_args()
    audit(a.depth)
