#!/usr/bin/env python3
"""Trace the smallest observed live-RIGID C9 two-replay survivor.

Source 5,054,715 reaches y=157,755,113 at k=41, which lies in the exact
two-replay C9 endpoint cylinder.  It executes C9 twice entirely inside RIGID.
The C9 defect valuation is exactly 19, so a third replay is impossible.

This audit follows the fixed source afterward, reconstructs exact return
patterns/switches, and records the first non-RIGID boundary state.
"""
from __future__ import annotations
import argparse
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

N=5054715
START_K=41
START_Y=157755113
WORD=((1,1,4),(4,1,1),(1,1,1))
C9=ra.certificate(WORD)

def main(H:int):
    k0=N.bit_length()
    _,y=base.forward_state(START_K,N)
    assert y==START_Y
    m=(y+1)//2
    C=(1<<C9['D'])-C9['A']
    V=ra.v2(abs(C*m-C9['B']))
    print("SOURCE",N,"Q0_K",k0,"START_K",START_K,"Y",y)
    print("C9_M0",m,"DEFECT_V",V,"REPLAY_BUDGET",(V-1)//C9['D'])
    ms=[m]
    for _ in range(2):
        m=ra.replay(C9,m);ms.append(m)
    print("C9_TWO_REPLAY_TRACE",ms)

    starts,branches=ra.rigid_episode_segment(N,H)
    cache={};last={};lastret={};switches=[]
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            m0=starts[start][2];m1=starts[end][2]
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            if starts[start][0]>=START_K-5:
                print("RETURN",r,starts[start][0],m0,m1,c['q'],c['D'],word)
            if r in lastret and lastret[r]['q']!=c['q']:
                z=ra.switch_law(lastret[r],c,m0,m1)
                if z is not None:
                    row=(r,starts[start][0],lastret[r]['q'],c['q'],m0,m1,z)
                    switches.append(row)
                    if starts[start][0]>=START_K-5:
                        print("SWITCH",row)
            lastret[r]=c
        last[r]=end

    _,y=base.forward_state(k0,N)
    first_non=None
    for k in range(k0,k0+H+1):
        if k>k0:y=base.T(y)
        out,data=base.cylinder_status(k,N)
        if k>=START_K and (k<=START_K+40 or out!='RIGID'):
            print("STATE",k,y,out,data)
        if k>=START_K and out!='RIGID':
            first_non=(k,y,out,data)
            break
    print("FIRST_NONRIGID_AFTER_TWO_REPLAY_ENTRY",first_non)
    print("POST_ENTRY_SWITCHES",len([s for s in switches if s[1]>=START_K]))
    print("STATUS EXACT_TWO_REPLAY_SURVIVOR_TRACE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--H",type=int,default=200)
    a=ap.parse_args()
    main(a.H)
