#!/usr/bin/env python3
"""Throwaway spike: Complete-O pumping of repeated concrete return words.

For C9, G(m)=(729m+467)/512 has ordinary shortcut length D=9 and odd
count R=6 per return cycle at anchor r=1.  For each t, choose the least exact
t-replay start residue.  The corresponding ordinary source x=2m-1 executes
the same cycle word t times.  Classifying the length 9t cylinder tests whether
that repeated word remains Complete-O optimal.  The Bellman endpoint residue
mod 3^(6t) and the source cocycle are word invariants, so the result does not
depend on which 2-adic lift of the t-replay cylinder is chosen.
"""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base

A=729;B=467;D=9;R=6;anchor=1
C=(1<<D)-A

def start_m(t:int):
    bits=t*D+1
    mod=1<<bits
    return (B*pow(C,-1,mod))%mod

def replay(m:int):
    z=A*m+B
    assert z%(1<<D)==0
    return z>>D

for t in range(1,7):
    m=start_m(t)
    x=(1<<anchor)*m-1
    mm=m
    for _ in range(t):
        mm=replay(mm)
    y=(1<<anchor)*mm-1
    # independent concrete check
    yy=x
    for _ in range(t*D):
        yy=base.T(yy)
    assert yy==y
    out,data=base.cylinder_status(t*D,x)
    c,d=base.forward_state(t*D,x)
    assert c==t*R and d==y
    print("PUMP",t,"k",t*D,"c",c,"start",x,"end",y,"out",out,"data",data)
    if out!="RIGID":
        print("FIRST_NONRIGID_REPEAT",t,out,data)
        break
else:
    print("C9_RIGID_THROUGH_REPEAT",6)
print("STATUS SOURCE_INDEPENDENT_WORD_PUMP_SPIKE")
