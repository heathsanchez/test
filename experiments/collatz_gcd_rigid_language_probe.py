#!/usr/bin/env python3
"""Spike: do gcd>1 deterministic return cycles occur inside RIGID language?"""
from __future__ import annotations
from math import gcd
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

WORDS=[
((1,7,3),(3,1,1)),
((1,3,5),(5,3,1)),
((1,6,5),(5,1,1)),
((2,1,4),(4,3,2)),
((2,2,4),(4,2,2)),
((2,3,4),(4,1,2)),
]
for w in WORDS:
    c=ra.certificate(w)
    g=gcd(abs(c['B']),abs(c['C']))
    rho=c['rho']; mod=c['modulus']
    m=rho if rho>0 else mod
    x=(1<<c['r'])*m-1
    mend=ra.replay(c,m)
    y=(1<<c['r'])*mend-1
    total=sum(r+s for r,s,rp in w)
    yy=x
    allrigid=True; first=None
    for k in range(1,total+1):
        yy=base.T(yy)
        out,data=base.cylinder_status(k,x)
        if out!="RIGID" and first is None:
            allrigid=False; first=(k,out,data,yy)
    assert yy==y
    print("GCD_PATTERN",w,"A",c['A'],"B",c['B'],"D",c['D'],"C",c['C'],
          "gcd",g,"q",c['q'],"m",m,"x",x,"end",y,
          "all_prefix_rigid",allrigid,"first_non",first)
print("STATUS GCD_RIGID_LANGUAGE_SPIKE")
