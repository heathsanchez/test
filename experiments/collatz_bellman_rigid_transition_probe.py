#!/usr/bin/env python3
"""Bounded Bellman RIGID->RIGID transition classifier.

Purpose: find the smallest exact separator for the proposed universal
transition theorem.  This deliberately uses only modest depths; it is a
theorem-discovery audit, not a proof of Collatz.

It imports the already-qualified source-refinement formulas and Complete-O
classifier, enumerates concrete RIGID parents/children, and reports the exact
transition signatures.  In particular it tests whether every observed
RIGID->RIGID child is the unique -1 3-adic lift.  Any counterexample is printed
as the next obstruction rather than hidden.
"""
import argparse, importlib.util, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parent

def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/file)
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
dag=load("dag","collatz_coupled_dag_v1.py")
bridge=load("bridge","collatz_source_refinement_bridge.py")

def run(K,J):
    total=0; minus=0; counter=[]
    signatures={}
    for k in range(1,K):
        for b in range(1,1<<k,2):
            if dag.classify(k,b)[0]!="RIGID": continue
            c,d=dag.forward_cylinder(k,b)
            for bit in (0,1):
                kp,bp,cp,dp=bridge.child_formula(k,b,bit)
                if dag.classify(kp,bp)[0]!="RIGID": continue
                total+=1
                j=min(J,c,cp)
                mod=3**j if j else 1
                rp=d%mod if j else 0
                rc=dp%mod if j else 0
                sig=(bit,cp-c,rp,rc)
                signatures[sig]=signatures.get(sig,0)+1
                isminus=(j>0 and rp==mod-1 and rc==mod-1)
                minus+=isminus
                if not isminus and len(counter)<30:
                    counter.append((k,b,c,d,bit,kp,bp,cp,dp,j,rp,rc))
    print("RIGID_TRANSITIONS",total)
    print("MINUS_ONE_TRANSITIONS",minus)
    print("NON_MINUS_TRANSITIONS",total-minus)
    print("SIGNATURES",len(signatures))
    for x in counter: print("COUNTEREXAMPLE",x)
    if total==minus:
        print("OBSERVED_ALL_RIGID_TRANSITIONS_MINUS_ONE")
    else:
        print("SEPARATOR_NON_MINUS_RIGID_TRANSITION")
    print("STATUS BOUNDED_DISCOVERY_ONLY")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--depth",type=int,default=9);ap.add_argument("--j",type=int,default=4)
    a=ap.parse_args();run(a.depth,a.j)
