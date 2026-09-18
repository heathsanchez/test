#!/usr/bin/env python3
"""Prospective sweep for three exact replays of the expanding C9 return cycle.

C9:
    G(m) = (729 m + 467) / 2^9.

Three replays require
    v2((2^9-729)m-467) >= 28,
so m lies in one residue mod 2^28 and the odd endpoint
    y = 2m-1
lies in one residue mod 2^29.

For hereditary q=0 RIGID births, follow H boundary steps cheaply. On a rare
raw residue hit, check that the whole prefix is still RIGID and replay C9
three times, checking every intermediate boundary state.

Bounded prospective discovery only; not a Collatz proof.
"""
from __future__ import annotations
import argparse
from collections import Counter

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

A=729; B=467; D=9; R=1; REPLAYS=3
C=(1<<D)-A
BITS=REPLAYS*D+1
MMOD=1<<BITS
RHO=(B*pow(C,-1,MMOD))%MMOD
if RHO==0:RHO=MMOD
XRES=2*RHO-1
XMOD=1<<(BITS+1)
WORD=((1,1,4),(4,1,1),(1,1,1))
CERT=ra.certificate(WORD)
L=sum(r+s for r,s,rp in WORD)
assert (CERT['A'],CERT['B'],CERT['D'])==(A,B,D)

def rigid_prefix(n,k0,k1):
    for k in range(k0,k1+1):
        out,data=base.cylinder_status(k,n)
        if out!='RIGID':
            return False,(k,out,data)
    return True,None

def replay_n(n,k,y):
    m=(y+1)//2
    assert m%MMOD==RHO
    ms=[m]
    z=y; kk=k; first_non=None
    for rep in range(REPLAYS):
        m=ra.replay(CERT,m); ms.append(m)
        for _ in range(L):
            z=base.T(z); kk+=1
            if first_non is None:
                out,data=base.cylinder_status(kk,n)
                if out!='RIGID':
                    first_non=(rep+1,kk,out,data,z)
        assert z==2*m-1
    return {'ms':ms,'end_y':z,'end_k':kk,
            'first_nonrigid':first_non,'all_rigid':first_non is None}

def audit(lo,hi,H):
    counts=Counter(); raw=[]; live=[]; dangerous=[]
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
            k=k0+t
            counts['raw_hit']+=1
            raw.append((n,k,y))
            ok,why=rigid_prefix(n,k0,k)
            if not ok:
                counts['hit_after_leaving_rigid']+=1
                continue
            counts['live_rigid_hit']+=1
            res=replay_n(n,k,y)
            row=(n,k,y,res)
            live.append(row)
            if res['all_rigid']:
                dangerous.append(row)
                print('DANGEROUS_C9_THREE_REPLAY',row)
            else:
                print('C9_THREE_REPLAY_BREAKER',row)
    print('SOURCE_RANGE',lo,hi)
    print('HORIZON',H)
    print('THREE_REPLAY_M_RESIDUE',RHO,'mod',MMOD)
    print('THREE_REPLAY_ENDPOINT_RESIDUE',XRES,'mod',XMOD)
    print('COUNTS',dict(counts))
    print('RAW_THREE_REPLAY_HITS',len(raw))
    print('LIVE_RIGID_THREE_REPLAY_HITS',len(live))
    print('DANGEROUS_THREE_REPLAY_HITS',len(dangerous))
    if dangerous:
        print('SEPARATOR_C9_THREE_REPLAY_SURVIVES_RIGID',dangerous[0])
    else:
        print('OBSERVED_NO_C9_THREE_REPLAY_RIGID_SURVIVOR')
    print('STATUS BOUNDED_THREE_REPLAY_SWEEP_ONLY')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--lo',type=int,required=True)
    ap.add_argument('--hi',type=int,required=True)
    ap.add_argument('--H',type=int,default=512)
    a=ap.parse_args()
    audit(a.lo,a.hi,a.H)
