#!/usr/bin/env python3
"""Throwaway spike: verify alleged high-fuel hereditary RIGID source witnesses."""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base
import collatz_high_fuel_rigid_family_sweep as sweep

SOURCES=[53199515,54652583,119476679,45126427]

for n in SOURCES:
    survives,why=base.survives_to_q0(n)
    birth=base.birth_status(n)[0] if survives else None
    print("SOURCE",n,"SURVIVES_Q0",survives,"WHY",why,"BIRTH",birth)
    if not survives or birth!="RIGID":
        continue
    k=n.bit_length()
    _,y=base.forward_state(k,n)
    hits=[]
    for offset in range(257):
        kk=k+offset
        if offset:
            y=base.T(y)
        if not sweep.actual_rigid(kk,n):
            print("LEAVES_RIGID",n,kk,base.cylinder_status(kk,n),y)
            break
        for c in sweep.CYCLES:
            if y % c['endpoint_modulus'] == c['endpoint_residue']:
                res=sweep.replay_twice_check(n,kk,y,c)
                row=(kk,y,c['name'],res)
                hits.append(row)
                print("HIGH_FUEL_HIT",n,row)
    print("HITS",n,len(hits))
