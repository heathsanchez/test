#!/usr/bin/env python3
"""Compounding C9 two-replay sweep.

Scan hereditary q=0 RIGID source trajectories for the exact C9 two-replay
endpoint cylinder.  A live hit that survives both C9 replays is not immediately
treated as a new obstruction.  Instead acquire an exact concrete endpoint
certificate by iterating that endpoint to 1 once, cache it, and reuse it for
every later source hitting the same endpoint.

This implements:
    discover -> verify -> compile/cache -> reuse.

Only a live endpoint that does not reach 1 within the explicit guard remains
UNRESOLVED.  Finite endpoint certificates are exact; the source sweep is
bounded discovery and is not a Collatz proof.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

R=1
A=729; B=467; D=9
RHO=234357; MBITS=19
XRES=468713; XMOD=1<<20
WORD=((1,1,4),(4,1,1),(1,1,1))
CERT=ra.certificate(WORD)
L=sum(r+s for r,s,rp in WORD)

# Frozen before the prospective 27-bit holdout.  These are the unique live
# C9 two-replay endpoints discovered below 2^26.
FROZEN_ENDPOINTS={
    147269353,
    153560809,
    157755113,
    260515561,
    373761769,
    1205282537,
    1290217193,
    1928799977,
    2196186857,
    4083623657,
    # Acquired prospectively on the 27-bit holdout:
    733423337,
    1076307689,
    2786535145,
    17417316073,
    18786756329,
    64877962985,
}

def rigid_prefix(n,k0,k1):
    for k in range(k0,k1+1):
        out,data=base.cylinder_status(k,n)
        if out!='RIGID':
            return False,(k,out,data)
    return True,None

def replay_twice(n,k,y):
    m=(y+1)//2
    m1=ra.replay(CERT,m)
    m2=ra.replay(CERT,m1)
    z=y; kk=k; first_non=None
    for rep,target in enumerate((m1,m2),1):
        for _ in range(L):
            z=base.T(z); kk+=1
            if first_non is None:
                out,data=base.cylinder_status(kk,n)
                if out!='RIGID':
                    first_non=(rep,kk,out,data,z)
        assert z==2*target-1
    return first_non is None,(m,m1,m2,z,kk,first_non)

def endpoint_certificate(x:int,guard:int):
    y=x
    for t in range(guard+1):
        if y==1:
            return t
        y=base.T(y)
    return None

def audit(lo:int,hi:int,H:int,guard:int):
    counts=Counter()
    cache={}
    frozen_steps={}
    for x in sorted(FROZEN_ENDPOINTS):
        steps=endpoint_certificate(x,guard)
        assert steps is not None, ("frozen endpoint lost certificate",x)
        cache[x]=steps
        frozen_steps[x]=steps
    acquisitions=[]
    reused=Counter()
    frozen_reuse=Counter()
    unresolved=[]

    for n in range(max(3,lo)|1,hi+1,2):
        if base.birth_status(n)[0]!='RIGID':
            continue
        ok,_=base.survives_to_q0(n)
        if not ok:
            continue
        counts['hereditary_birth_rigid']+=1
        k0=n.bit_length()
        _,y=base.forward_state(k0,n)

        for t in range(H+1):
            if t:y=base.T(y)
            if y%XMOD!=XRES:
                continue
            counts['raw_high_fuel_hit']+=1
            k=k0+t
            ok,_=rigid_prefix(n,k0,k)
            if not ok:
                counts['hit_after_rigid_exit']+=1
                continue
            counts['live_high_fuel_hit']+=1
            all_rigid,trace=replay_twice(n,k,y)
            if not all_rigid:
                counts['replay_breaker']+=1
                continue

            counts['live_two_replay']+=1
            if y in FROZEN_ENDPOINTS:
                frozen_reuse[y]+=1
            if y not in cache:
                steps=endpoint_certificate(y,guard)
                cache[y]=steps
                if steps is None:
                    unresolved.append((n,k,y,trace))
                    print("UNRESOLVED_LIVE_ENDPOINT",n,k,y,trace)
                else:
                    acquisitions.append((y,steps,n,k))
                    print("ACQUIRE_ENDPOINT_CERT",y,"TO_ONE_STEPS",steps,
                          "FIRST_SOURCE",n,"AT_K",k)
            else:
                reused[y]+=1
            if cache[y] is not None:
                counts['closed_by_endpoint_cert']+=1

    print("SOURCE_RANGE",lo,hi)
    print("HORIZON",H)
    print("ENDPOINT_GUARD",guard)
    print("COUNTS",dict(counts))
    print("FROZEN_BANK_SIZE",len(FROZEN_ENDPOINTS))
    print("FROZEN_BANK_STEPS",dict(sorted(frozen_steps.items())))
    print("UNIQUE_ENDPOINTS",len(cache))
    print("ACQUIRED_CERTIFICATES",len(acquisitions))
    print("ACQUISITIONS",acquisitions)
    print("FROZEN_REUSE_HITS",dict(sorted(frozen_reuse.items())))
    print("REUSED_ENDPOINT_HITS",dict(sorted(reused.items())))
    print("UNRESOLVED_ENDPOINTS",len(unresolved))
    if unresolved:
        print("SEPARATOR_UNRESOLVED_LIVE_HIGH_FUEL_ENDPOINT",unresolved[0])
    else:
        print("PASS_ALL_LIVE_HIGH_FUEL_ENDPOINTS_COMPILED")
    print("STATUS BOUNDED_COMPOUNDING_SWEEP_ONLY")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,required=True)
    ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--H",type=int,default=512)
    ap.add_argument("--guard",type=int,default=10000)
    a=ap.parse_args()
    audit(a.lo,a.hi,a.H,a.guard)
