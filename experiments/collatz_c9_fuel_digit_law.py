#!/usr/bin/env python3
"""Exact C9 replay-fuel digit law.

C9 cycle:
    G(m)=(729m+467)/512.
Its fixed-point defect is
    Delta(m)=(-217)m-467.

r exact replays require
    Delta(m) == 0 mod 2^(9r+1).

There is one odd residue m_r modulo 2^(9r+1).  Writing Q=512, the lift from
r to r+1 appends one base-Q digit.  After the initial 10-bit residue m_1=885,
the appended digits are periodic with period five:

    228, 311, 476, 294, 443.

The period is explained exactly by Q^5 == 1 mod 217.

This is pure integer arithmetic; no bounded Collatz claim is made.
"""
from __future__ import annotations
import argparse

A=729; B=467; D=9
C=(1<<D)-A   # -217
Q=1<<D
DEN=217
DIGITS=(228,311,476,294,443)

def residue(r:int)->int:
    assert r>=1
    bits=D*r+1
    mod=1<<bits
    x=(B*pow(C,-1,mod))%mod
    return mod if x==0 else x

def lift_digit(r:int)->int:
    """Digit appended when lifting r replays to r+1."""
    a=residue(r)
    b=residue(r+1)
    step=1<<(D*r+1)
    assert (b-a)%step==0
    d=(b-a)//step
    assert 0<=d<Q
    return d

def main(R:int):
    assert C==-DEN
    assert pow(Q,5,DEN)==1
    assert all(pow(Q,j,DEN)!=1 for j in range(1,5))
    assert residue(1)==885
    observed=[]
    for r in range(1,R):
        d=lift_digit(r)
        observed.append(d)
        expected=DIGITS[(r-1)%5]
        assert d==expected,(r,d,expected)
        # Exact next-level congruence.
        rr=residue(r+1)
        assert (C*rr-B)%(1<<(D*(r+1)+1))==0
    print("C9_Q",Q)
    print("C9_DENOMINATOR",DEN)
    print("ORDER_512_MOD_217 5")
    print("INITIAL_RESIDUE",residue(1),"mod",1<<(D+1))
    print("PERIODIC_LIFT_DIGITS",DIGITS)
    print("CHECKED_REPLAY_LEVELS",R)
    print("OBSERVED_DIGITS",tuple(observed))
    print("THREE_REPLAY_REQUIRES_Q_MOD_512",DIGITS[1])
    print("PASS_C9_PERIODIC_FUEL_DIGIT_LAW")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--levels",type=int,default=30)
    a=ap.parse_args()
    main(a.levels)
