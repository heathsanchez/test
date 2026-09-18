#!/usr/bin/env python3
"""Large prospective sweep for the expanding C9 two-replay cylinder.

Cycle:
  G(m)=(729 m + 467)/512, anchor r=1.
Two replays require:
  m == 234357 (mod 2^19)
so the odd episode endpoint is:
  x=2m-1 == 468713 (mod 2^20).

To scale, we do NOT classify every post-q0 depth. We:
  1. retain sources whose q=0 birth is RIGID and which survive every pre-q0
     symbolic decision;
  2. follow the ordinary boundary orbit cheaply for H steps;
  3. only when the rare C9 high-fuel residue is hit, replay the exact RIGID
     status of the whole prefix and two cycle traversals.

A dangerous witness must remain RIGID through the hit and both replays.
Bounded prospective discovery only; not a Collatz proof.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

R=1
A=729
B=467
D=9
RHO=234357
MBITS=19
XRES=468713
XMOD=1<<20
WORD=((1,1,4),(4,1,1),(1,1,1))
CERT=ra.certificate(WORD)
assert (CERT['A'],CERT['B'],CERT['D'])==(A,B,D)
L=sum(r+s for r,s,rp in WORD)


def exact_status(k:int,n:int):
    return base.cylinder_status(k,n)


def rigid_prefix(n:int,k0:int,k1:int):
    for k in range(k0,k1+1):
        out,data=exact_status(k,n)
        if out!='RIGID':
            return False,(k,out,data)
    return True,None


def two_replay_rigid(n:int,k:int,y:int):
    assert y%XMOD==XRES
    m=(y+1)//2
    assert m%(1<<MBITS)==RHO
    m1=ra.replay(CERT,m)
    m2=ra.replay(CERT,m1)
    z=y
    kk=k
    first_non=None
    for rep in range(2):
        for _ in range(L):
            z=base.T(z); kk+=1
            if first_non is None:
                out,data=exact_status(kk,n)
                if out!='RIGID':
                    first_non=(rep+1,kk,out,data,z)
        expected=2*(m1 if rep==0 else m2)-1
        assert z==expected,(n,k,rep,z,expected)
    return {
        'm':m,'m1':m1,'m2':m2,'end_y':z,'end_k':kk,
        'first_nonrigid':first_non,'all_rigid':first_non is None,
    }


def audit(lo:int,hi:int,H:int):
    counts=Counter()
    hits=[]
    live=[]
    dangerous=[]
    for n in range(max(3,lo)|1,hi+1,2):
        if base.birth_status(n)[0]!='RIGID':
            continue
        counts['birth_rigid']+=1
        survives,_=base.survives_to_q0(n)
        if not survives:
            counts['pre_q0_closed']+=1
            continue
        counts['hereditary_q0_rigid_birth']+=1
        k0=n.bit_length()
        _,y=base.forward_state(k0,n)

        for t in range(H+1):
            if t:
                y=base.T(y)
            if y%XMOD!=XRES:
                continue
            k=k0+t
            counts['raw_high_fuel_hits']+=1
            row0=(n,k,y)
            hits.append(row0)

            ok,why=rigid_prefix(n,k0,k)
            if not ok:
                counts['hit_after_leaving_rigid']+=1
                continue
            counts['live_rigid_high_fuel_hits']+=1
            res=two_replay_rigid(n,k,y)
            row=(n,k,y,res)
            live.append(row)
            if res['all_rigid']:
                dangerous.append(row)
                print('DANGEROUS_C9_HIGH_FUEL_TWO_REPLAY',row)
            else:
                print('C9_HIGH_FUEL_BREAKER',row)

    print('SOURCE_RANGE',lo,hi)
    print('HORIZON_AFTER_Q0',H)
    print('COUNTS',dict(counts))
    print('RAW_HIGH_FUEL_HITS',len(hits))
    print('LIVE_RIGID_HIGH_FUEL_HITS',len(live))
    print('DANGEROUS_TWO_REPLAY_HITS',len(dangerous))
    if dangerous:
        print('SEPARATOR_EXPANDING_HIGH_FUEL_SURVIVES_RIGID',dangerous[0])
    else:
        print('OBSERVED_NO_EXPANDING_C9_TWO_REPLAY_RIGID_SURVIVOR')
    print('STATUS BOUNDED_LARGE_PROSPECTIVE_SWEEP_ONLY')


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--lo',type=int,default=3)
    ap.add_argument('--hi',type=int,default=65535)
    ap.add_argument('--H',type=int,default=512)
    a=ap.parse_args()
    audit(a.lo,a.hi,a.H)
