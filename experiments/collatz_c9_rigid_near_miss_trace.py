#!/usr/bin/env python3
"""Trace the unique million-range still-RIGID C9 17-bit near miss.

Source 966655 reaches y=5580521 at k=26.  This matches the C9 two-replay
endpoint through 17 low bits but flips the next required bit.  The state can
execute the C9 return word once and remain RIGID, but has only one replay of
fuel.

This audit prints the exact post-near-miss RIGID return/switch itinerary until
the first non-RIGID boundary state or the requested horizon.
"""
from __future__ import annotations
import argparse

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

N=966655
START_K=26
TARGET=468713
C9_WORD=((1,1,4),(4,1,1),(1,1,1))
C9=ra.certificate(C9_WORD)

def main(H:int):
    k0=N.bit_length()
    _,y0=base.forward_state(START_K,N)
    assert y0==5580521
    print("SOURCE",N,"Q0_K",k0,"START_K",START_K,"Y",y0)
    print("TARGET_DIFF",y0-TARGET,"V2",ra.v2(y0-TARGET))
    m0=(y0+1)//2
    C=(1<<C9['D'])-C9['A']
    print("C9_DEFECT",C*m0-C9['B'],"V",ra.v2(abs(C*m0-C9['B'])))
    print("C9_ADMISSIBLE",ra.admissible(C9,m0))
    if ra.admissible(C9,m0):
        print("C9_M1",ra.replay(C9,m0))

    # Full q0 RIGID episode segment for this source.
    starts,branches=ra.rigid_episode_segment(N,H)
    print("EPISODE_COUNT",len(branches))
    for i,(st,br) in enumerate(zip(starts,branches)):
        k,r,m,x=st
        if k>=START_K-10:
            print("EP",i,k,r,m,x,br)

    # Reconstruct exact consecutive return patterns per anchor, as in the main audit.
    cache={}; last={}; lastret={}
    switches=[]
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            mstart=starts[start][2]; mend=starts[end][2]
            assert ra.admissible(c,mstart)
            assert ra.replay(c,mstart)==mend
            row=(r,starts[start][0],mstart,mend,c['q'],c['D'],word)
            if starts[start][0]>=START_K-10:
                print("RETURN",row)
            if r in lastret and lastret[r]['q']!=c['q']:
                z=ra.switch_law(lastret[r],c,mstart,mend)
                if z is not None:
                    sw=(r,starts[start][0],lastret[r]['q'],c['q'],mstart,mend,z)
                    switches.append(sw)
                    if starts[start][0]>=START_K-10:
                        print("SWITCH",sw)
            lastret[r]=c
        last[r]=end

    first_non=None
    _,y=base.forward_state(k0,N)
    for k in range(k0,k0+H+1):
        if k>k0:y=base.T(y)
        out,data=base.cylinder_status(k,N)
        if k>=START_K and (k<=START_K+40 or out!='RIGID'):
            print("STATE",k,y,out,data)
        if k>=START_K and out!='RIGID':
            first_non=(k,y,out,data)
            break
    print("FIRST_NONRIGID_AFTER_NEAR_MISS",first_non)
    print("POST_NEAR_SWITCHES",len([s for s in switches if s[1]>=START_K]))
    print("STATUS EXACT_TARGETED_DIAGNOSTIC")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--H",type=int,default=160)
    a=ap.parse_args()
    main(a.H)
