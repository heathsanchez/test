#!/usr/bin/env python3
"""Exact local lift probe for the candidate recurrent Complete-O residual.

Avoids constructing the full Phi_j table.  It studies the one arithmetic
feature suggested by the bounded coupled DAG: the residue -1 mod 3^j.

This is a discovery/qualification harness, not a Collatz proof.  Its purpose is
to replace a global Bellman census with exact local lift identities and expose
the remaining theorem boundary.
"""
import argparse

def odd_shortcut(x:int)->int:
    assert x>0 and x&1
    return (3*x+1)//2

def lift_minus_one(j:int):
    """All three lifts of -1 mod 3^j to mod 3^(j+1)."""
    m=3**j
    base=m-1
    return [base+t*m for t in range(3)]

def unique_minus_one_lift(j:int):
    m=3**(j+1)
    xs=lift_minus_one(j)
    good=[x for x in xs if (x+1)%m==0]
    assert good==[m-1]
    return good[0]

def preservation_identity(j:int,q:int):
    """Odd representatives of -1 mod 3^j remain there after an odd step."""
    m=3**j
    x=m*q-1
    if x<=0 or not x&1: return False
    y=odd_shortcut(x)
    assert (y+1)%m==0
    return True

def exit_identity(j:int,q:int):
    """Even representatives of -1 mod 3^j leave it under the even step."""
    m=3**j
    x=m*q-1
    if x<=0 or x&1: return False
    y=x//2
    assert (y+1)%m!=0
    return True

def run(J:int,Q:int):
    odd=even=0
    for j in range(1,J+1):
        r=unique_minus_one_lift(j)
        assert r==3**(j+1)-1
        for q in range(1,Q+1):
            odd += preservation_identity(j,q)
            even += exit_identity(j,q)
    print("LEVELS",J)
    print("UNIQUE_LIFTS",J)
    print("ODD_PRESERVATION",odd)
    print("EVEN_EXITS",even)
    print("PASS_MINUS_ONE_LOCAL_LIFT")
    print("MISSING_THEOREM hereditary_rigid_lift_forces_unique_minus_one_lift")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--levels",type=int,default=20)
    ap.add_argument("--reps",type=int,default=1000)
    a=ap.parse_args()
    run(a.levels,a.reps)
