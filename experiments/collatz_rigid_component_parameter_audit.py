#!/usr/bin/env python3
"""Concrete-parameter audit for recurrent Collatz RIGID obligations.

This audit keeps the fixed integer parameter n=2^k q+b explicit.

Universal source-refinement law:
    eps = q mod 2
    q'  = (q-eps)/2 = floor(q/2)
    b'  = b + eps*2^k

Hence every fixed integer reaches q=0 after finitely many source refinements.
At q=0, b=n is fixed and the child law is simply
    d' = T(d),  c' = c + [d odd].

The second phase audits the exact Complete-O/direct-descent classifier on this
q=0 boundary for small depths and tests simple candidate internal ranks.
It is discovery only; it does not claim Collatz or universal SCC termination.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict

import collatz_coupled_dag_v1 as dag


def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1


def refine_fixed(n:int,k:int,b:int,q:int):
    assert n==(1<<k)*q+b
    eps=q&1
    qp=(q-eps)//2
    bp=b+eps*(1<<k)
    assert n==(1<<(k+1))*qp+bp
    return eps,bp,qp


def concrete_status(k:int,n:int):
    """Status of the fixed q=0 integer, respecting tail exceptions."""
    out,data=dag.classify(k,n)
    if out=="TAIL_CLOSED":
        Q=data[0]
        return ("CLOSED" if Q==0 else "TAIL_EXCEPTION"),data
    return out,data


def parameter_gate(N:int):
    checks=0
    max_steps=0
    for n in range(1,N+1):
        # canonical start k=0,b=0,q=n
        k=0;b=0;q=n;steps=0
        while q:
            eps,b,q=refine_fixed(n,k,b,q)
            k+=1;steps+=1;checks+=1
        assert b==n
        assert steps==n.bit_length()
        max_steps=max(max_steps,steps)
    return checks,max_steps


def boundary_audit(N:int,K:int):
    outcomes=Counter()
    transitions=Counter()
    examples=defaultdict(list)
    internal=[]
    for n in range(3,N+1,2):
        k0=n.bit_length()
        if k0>K: continue
        prev=None
        d=n;c=0
        # recompute endpoint incrementally from 0 to K so q=0 begins exactly at k0
        vals=[(0,0,n)]
        x=n
        for k in range(1,K+1):
            odd=x&1
            x=dag.T(x)
            c+=odd
            vals.append((k,c,x))
        for k,c,d in vals:
            if k<k0: continue
            c2,d2=dag.forward_cylinder(k,n)
            assert (c,d)==(c2,d2)
            status,data=concrete_status(k,n)
            outcomes[status]+=1
            if len(examples[status])<8:
                examples[status].append((n,k,c,d,data))
            cur=(status,n,k,c,d)
            if prev is not None:
                transitions[(prev[0],status)]+=1
                if prev[0]=="RIGID" and status=="RIGID":
                    pn,pk,pc,pd=prev[1:]
                    internal.append((n,pk,pc,pd,k,c,d))
            prev=cur
    return outcomes,transitions,examples,internal


def rank_audit(internal):
    # Candidate one-coordinate ranks on q=0 internal RIGID edges.
    funcs={
        "endpoint_d": lambda n,k,c,d:d,
        "excess_d_minus_n": lambda n,k,c,d:d-n,
        "even_budget_k_minus_c": lambda n,k,c,d:k-c,
        "v2_d_plus_1": lambda n,k,c,d:v2(d+1),
        "odd_count_c": lambda n,k,c,d:c,
    }
    report={}
    for name,f in funcs.items():
        dec=eq=inc=0;bad=[]
        for n,k,c,d,kp,cp,dp in internal:
            a=f(n,k,c,d);b=f(n,kp,cp,dp)
            if b<a: dec+=1
            elif b==a:eq+=1
            else:inc+=1
            if b>=a and len(bad)<5:
                bad.append((n,k,c,d,kp,cp,dp,a,b))
        report[name]=(dec,eq,inc,bad)
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parameter-N",type=int,default=4096)
    ap.add_argument("--boundary-N",type=int,default=255)
    ap.add_argument("--depth",type=int,default=9)
    a=ap.parse_args()

    checks,max_steps=parameter_gate(a.parameter_N)
    outcomes,transitions,examples,internal=boundary_audit(a.boundary_N,a.depth)
    ranks=rank_audit(internal)

    print("PARAMETER_REFINEMENTS",checks)
    print("MAX_PARAMETER_COUNTDOWN",max_steps)
    print("PASS_Q_HALVING_LAW")
    print("BOUNDARY_OUTCOMES",dict(sorted(outcomes.items())))
    print("BOUNDARY_TRANSITIONS",dict(sorted((str(k),v) for k,v in transitions.items())))
    print("RIGID_INTERNAL_EDGES",len(internal))
    for status,rows in sorted(examples.items()):
        print("EXAMPLES",status,rows)
    for name,(dec,eq,inc,bad) in ranks.items():
        print("RANK",name,"decrease",dec,"equal",eq,"increase",inc)
        for row in bad:
            print("RANK_SEPARATOR",name,row)
    print("AUTHORITATIVE_RESIDUAL q_zero_boundary_rigid_or_tail_exception")
    print("MISSING_THEOREM termination_of_q_zero_boundary_obligations")


if __name__=="__main__":
    main()
