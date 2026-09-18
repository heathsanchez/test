#!/usr/bin/env python3
"""Throwaway spike: test symbolic RIGIDness of constructed three-fuel C9 lifts."""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base

CASES=[
    (17592186097615515,27,27),
    (23010579391222555,26,27),
]
for n,k0,span in CASES:
    print("SOURCE",n,"BITLEN",n.bit_length())
    first_non=None
    rows=[]
    for k in range(1,k0+span+20):
        out,data=base.cylinder_status(k,n%(1<<k))
        q=n>>k
        # Interpret tail closure for the actual fixed-source q.
        actual=out
        if out=="TAIL_CLOSED":
            Q=data[-1]
            actual="CLOSED" if q>=Q else "TAIL_EXCEPTION"
        if k>=k0-2:
            rows.append((k,q,out,actual,data))
        if actual in ("DESCEND","CLOSED") and first_non is None:
            first_non=(k,q,out,actual,data)
    print("FIRST_FIXED_SOURCE_CLOSE",first_non)
    print("ROWS_FROM_ENTRY",rows[:80])
