#!/usr/bin/env python3
"""Profile the isolated 28-bit C9 hard-source neighborhood.

Prints and flushes before/after each expensive symbolic classifier call so an
external wall-time cutoff identifies the exact source/call responsible for the
pathological shard runtime.
"""
from __future__ import annotations
import argparse
import collatz_q0_coalescence_component_audit as base

def main(lo:int,hi:int):
    for n in range(max(3,lo)|1,hi+1,2):
        print("BEGIN",n,flush=True)
        b=base.birth_status(n)
        print("BIRTH",n,b,flush=True)
        s=base.survives_to_q0(n)
        print("SURVIVES",n,s,flush=True)
    print("PROFILE_COMPLETE",lo,hi,flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=218263037)
    ap.add_argument("--hi",type=int,default=218263548)
    a=ap.parse_args()
    main(a.lo,a.hi)
