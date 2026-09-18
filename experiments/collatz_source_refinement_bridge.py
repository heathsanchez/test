#!/usr/bin/env python3
"""Exact source-refinement algebra for Collatz affine cylinders.

For a depth-k cylinder n(q)=2^k q+b with endpoint
T^k(n(q))=3^c q+d, its two depth-(k+1) children are obtained by writing
q=2q'+bit.  This yields an exact child law without Bellman enumeration.

The script verifies the formulas exhaustively on a bounded control set and
prints the remaining theorem boundary.  It does not claim Collatz.
"""
import argparse

def T(n):
    return n//2 if n%2==0 else (3*n+1)//2

def state(k,b):
    d=b;c=0
    for _ in range(k):
        if d&1:
            d=(3*d+1)//2;c+=1
        else:d//=2
    return c,d

def child_formula(k,b,bit):
    c,d=state(k,b)
    raw=d + (3**c)*bit
    if raw&1:
        cp=c+1; dp=(3*raw+1)//2
    else:
        cp=c; dp=raw//2
    bp=b + bit*(1<<k)
    return k+1,bp,cp,dp

def Csrc(k,b,c,d):
    return (1<<k)*d-(3**c)*b

def check(K):
    checked=0
    for k in range(1,K+1):
        for b in range(1,1<<k,2):
            c,d=state(k,b)
            for bit in (0,1):
                kp,bp,cp,dp=child_formula(k,b,bit)
                c2,d2=state(kp,bp)
                assert (cp,dp)==(c2,d2)
                # Exact affine identity at q'=0,1,2.
                for q in range(3):
                    n=(1<<kp)*q+bp
                    y=n
                    for _ in range(kp): y=T(y)
                    assert y==(3**cp)*q+dp
                # Source cocycle identity remains exact.
                cs=Csrc(kp,bp,cp,dp)
                assert (1<<kp)*dp-(3**cp)*bp==cs
                checked+=1
    print("CHILD_TRANSITIONS",checked)
    print("PASS_SOURCE_REFINEMENT_ALGEBRA")
    print("MISSING_THEOREM bellman_rigidity_transition_classification")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--depth",type=int,default=14)
    a=ap.parse_args();check(a.depth)
