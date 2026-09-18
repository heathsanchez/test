#!/usr/bin/env python3
"""Minimal-counterexample filter before q=0.

A true least lower-merge counterexample n cannot have T^t(n)<n at any earlier
time t, since that is already a lower-merge certificate. This is stronger than
survives_to_q0(), which only asks whether the current *compiled cylinder
grammar* closes the source.

This probe measures how much of the q=0 RIGID population disappears when we
impose the mathematically necessary fixed-source direct-descent condition.
"""
from __future__ import annotations
from collections import Counter
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

def first_direct_before_q0(n):
    k0=n.bit_length()
    y=n
    for t in range(1,k0+1):
        y=base.T(y)
        if y<n:
            return t,y
    return None

def grammar_survives(n):
    ok,_=base.survives_to_q0(n)
    return ok and base.birth_status(n)[0]=='RIGID'

def true_direct_survives(n):
    return first_direct_before_q0(n) is None

for hi in (8191,16383,32767,65535):
    cnt=Counter();rows=[]
    for n in range(3,hi+1,2):
        g=grammar_survives(n)
        d=true_direct_survives(n)
        if g:cnt['grammar_q0_rigid']+=1
        if d:cnt['no_direct_before_q0']+=1
        if g and d:
            cnt['both']+=1
            rows.append(n)
        if g and not d:cnt['grammar_but_direct_closed']+=1
    print("LIMIT",hi,"COUNTS",dict(cnt))
    print("TRUE_Q0_RIGID_HEAD",rows[:80])
print("STATUS MINIMAL_COUNTEREXAMPLE_Q0_FILTER")
