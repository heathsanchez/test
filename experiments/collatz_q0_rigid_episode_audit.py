#!/usr/bin/env python3
"""Episode-level audit of the q=0 Collatz RIGID boundary.

After the fixed parameter q has reached zero, b=n is fixed and d=T^k(n).
This script collapses shortcut steps into maximal odd/even episodes and asks
what survives after requiring every protected shortcut state to remain RIGID.

It verifies the exact episode algebra and reports whether simple episode-level
coefficient contraction is universal on the bounded hard sample.  Any failure
is emitted as a separator, not hidden.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_coupled_dag_v1 as dag


def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1


def odd_run(d:int):
    assert d>0 and d&1
    r=v2(d+1)
    m=(d+1)>>r
    y=(3**r)*m-1
    x=d
    for _ in range(r):
        assert x&1
        x=dag.T(x)
    assert x==y and y%2==0
    return r,m,y


def full_episode(d:int):
    r,m,y=odd_run(d)
    s=v2(y)
    z=y>>s
    x=d
    for _ in range(r+s):
        x=dag.T(x)
    assert x==z and z&1
    # exact affine multiplier numerator/denominator on d+1 coordinates:
    # z = (3^r*(d+1)/2^r - 1)/2^s
    return r,s,z


def exact_formula_gate(N:int):
    checked=0
    for d in range(1,N+1,2):
        r,s,z=full_episode(d)
        lhs=(1<<(r+s))*z
        rhs=(3**r)*(d+1)-(1<<r)
        # From 2^s z = 3^r(d+1)/2^r - 1.
        assert lhs==rhs
        checked+=1
    return checked


def status(k:int,n:int):
    out,data=dag.classify(k,n)
    if out=="TAIL_CLOSED" and data[0]>0:
        return "TAIL_EXCEPTION"
    if out=="TAIL_CLOSED":
        return "CLOSED"
    return out


def hard_episode_audit(N:int,K:int):
    counts=Counter();seps=[]
    for n in range(3,N+1,2):
        k0=n.bit_length()
        if k0>=K: continue
        # cache q=0 statuses and endpoints at each depth.
        st={}
        for k in range(k0,K+1):
            c,d=dag.forward_cylinder(k,n)
            st[k]=(status(k,n),c,d)
        k=k0
        while k<K:
            s0,c0,d0=st[k]
            if s0!="RIGID" or not (d0&1):
                k+=1;continue
            r,s,z=full_episode(d0)
            end=k+r+s
            if end>K:
                break
            # Require every shortcut state in the episode to stay RIGID.
            if all(st[j][0]=="RIGID" for j in range(k,end+1)):
                counts["hard_episodes"]+=1
                contract=(3**r < (1<<(r+s)))
                counts["coef_contract" if contract else "coef_noncontract"]+=1
                if not contract and len(seps)<20:
                    seps.append((n,k,d0,r,s,z,end,st[end][2]))
            k=max(k+1,end)
    return counts,seps


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--formula-N",type=int,default=4095)
    ap.add_argument("--boundary-N",type=int,default=255)
    ap.add_argument("--depth",type=int,default=9)
    a=ap.parse_args()
    checked=exact_formula_gate(a.formula_N)
    counts,seps=hard_episode_audit(a.boundary_N,a.depth)
    print("EPISODE_FORMULA_CASES",checked)
    print("PASS_Q_ZERO_EPISODE_ALGEBRA")
    print("HARD_EPISODE_COUNTS",dict(counts))
    for x in seps:
        print("NONCONTRACTING_HARD_EPISODE",x)
    if counts["coef_noncontract"]:
        print("SEPARATOR_COEFFICIENT_CONTRACTION_NOT_UNIVERSAL")
    else:
        print("OBSERVED_ALL_HARD_EPISODES_COEFFICIENT_CONTRACT")
    print("MISSING_THEOREM termination_under_rigid_episode_switches")


if __name__=="__main__":
    main()
