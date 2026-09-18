#!/usr/bin/env python3
"""Prospective sweep for high-fuel cycle lifts on actual q=0 RIGID trajectories.

Two observed concrete pattern cycles have fully-audited two-replay congruences:

  C5: anchor r=1, G(m)=(9m+17)/2^5,
      two-replay m == 535 (mod 2^11),
      endpoint x=2m-1 == 1069 (mod 2^12).

  C9: anchor r=1, G(m)=(729m+467)/2^9,
      two-replay m == 234357 (mod 2^19),
      endpoint x == 468713 (mod 2^20).

The earlier audits checked the least positive endpoint of each congruence.
This script instead follows actual hereditary q=0 RIGID fixed sources and
asks whether their boundary endpoint ever lands in ANY congruence lift.

At a hit, the exact composite episode word is replayed twice and every
intermediate fixed-source cylinder is checked.  A dangerous hit is one where
both replays remain RIGID throughout.

Bounded prospective discovery only.  This is not a Collatz proof.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra


CYCLES=[
    {
        'name':'C5',
        'r':1,'A':9,'B':17,'D':5,
        'rho':535,'bits':11,
        'word':((1,2,1),(1,1,1)),
    },
    {
        'name':'C9',
        'r':1,'A':729,'B':467,'D':9,
        'rho':234357,'bits':19,
        'word':((1,1,4),(4,1,1),(1,1,1)),
    },
]

for c in CYCLES:
    c['cert']=ra.certificate(c['word'])
    assert (c['cert']['A'],c['cert']['B'],c['cert']['D'])==(c['A'],c['B'],c['D'])
    C=(1<<c['D'])-c['A']
    mod=1<<(2*c['D']+1)
    assert (c['B']*pow(C,-1,mod))%mod==c['rho']
    c['endpoint_residue']=(1<<c['r'])*c['rho']-1
    c['endpoint_modulus']=1<<(c['r']+2*c['D']+1)


def actual_rigid(k:int,n:int)->bool:
    out,data=base.cylinder_status(k,n)
    return out=='RIGID'


def replay_twice_check(source:int,k0:int,y0:int,c):
    assert y0>0 and ((y0+1)%(1<<c['r'])==0)
    m0=(y0+1)>>c['r']
    mod=1<<(2*c['D']+1)
    assert m0%mod==c['rho']

    # Algebraic cofactor replay.
    m1=ra.replay(c['cert'],m0)
    m2=ra.replay(c['cert'],m1)

    # Concrete shortcut replay and RIGID check at every intermediate depth.
    y=y0
    k=k0
    first_non=None
    total_shortcut=sum(r+s for r,s,rp in c['word'])
    for rep in range(2):
        for _ in range(total_shortcut):
            y=base.T(y); k+=1
            if first_non is None and not actual_rigid(k,source):
                out,data=base.cylinder_status(k,source)
                first_non=(rep+1,k,out,data,y)
        expected=(1<<c['r'])*(m1 if rep==0 else m2)-1
        assert y==expected,(source,c['name'],rep,y,expected)
    return {
        'm0':m0,'m1':m1,'m2':m2,
        'end_y':y,'end_k':k,'first_nonrigid':first_non,
        'all_rigid':first_non is None,
    }


def audit(lo:int,hi:int,H:int):
    counts=Counter()
    hits=[]
    dangerous=[]
    for n in range(max(3,lo)|1,hi+1,2):
        survives,_=base.survives_to_q0(n)
        if not survives:
            continue
        if base.birth_status(n)[0]!='RIGID':
            continue
        counts['hereditary_birth_rigid']+=1

        k=n.bit_length()
        _,y=base.forward_state(k,n)
        for offset in range(H+1):
            kk=k+offset
            if offset:
                y=base.T(y)
            if not actual_rigid(kk,n):
                counts['left_rigid']+=1
                break
            counts['rigid_boundary_steps']+=1
            for c in CYCLES:
                if y % c['endpoint_modulus'] != c['endpoint_residue']:
                    continue
                counts['high_fuel_hits']+=1
                res=replay_twice_check(n,kk,y,c)
                row=(n,kk,y,c['name'],res)
                hits.append(row)
                if res['all_rigid']:
                    dangerous.append(row)
                    print('DANGEROUS_HIGH_FUEL_RIGID_TWO_REPLAY',row)
                    # Keep searching: multiple separators are useful.

    print('SOURCE_RANGE',lo,hi)
    print('HORIZON_AFTER_Q0',H)
    print('COUNTS',dict(counts))
    print('HIGH_FUEL_HITS',len(hits))
    for row in hits[:30]:
        print('HIGH_FUEL_HIT',row)
    print('DANGEROUS_RIGID_TWO_REPLAY_HITS',len(dangerous))
    if dangerous:
        print('SEPARATOR_HIGH_FUEL_COMPATIBLE_WITH_RIGID_TWO_REPLAY',dangerous[0])
    else:
        print('OBSERVED_NO_HIGH_FUEL_RIGID_TWO_REPLAY_IN_SOURCE_RANGE')
    print('STATUS BOUNDED_PROSPECTIVE_FAMILY_SWEEP_ONLY')


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--lo',type=int,default=3)
    ap.add_argument('--hi',type=int,default=8191)
    ap.add_argument('--H',type=int,default=128)
    a=ap.parse_args()
    audit(a.lo,a.hi,a.H)
