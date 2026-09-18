#!/usr/bin/env python3
"""Profile the 51 sources that survive universal reverse-episode depth 5.

This is a finite residual audit: first q=0 non-RIGID classifier event, first
direct descent, and first immediate lower-predecessor event.
"""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base

SOURCES=[4167,4233,4255,4263,4265,4399,4409,4511,4591,4719,4735,4763,4767,4863,4935,5055,5151,5223,5247,5403,5479,5535,5679,5705,5887,6079,6171,6265,6267,6271,6303,6471,6591,6635,6823,6895,6939,7145,7167,7323,7327,7335,7527,7707,7839,7935,7963,8073,8155,8175,8185]

def first_classifier_exit(n,H=500):
    k0=n.bit_length()
    for k in range(k0,H+1):
        out,data=base.cylinder_status(k,n)
        if out!='RIGID':
            return k,out,data
    return None

def first_direct(n,H=5000):
    y=n
    for t in range(1,H+1):
        y=base.T(y)
        if y<n:return t,y
    return None

def first_p(n,H=5000):
    y=n
    for t in range(1,H+1):
        y=base.T(y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:
                return t,y,p
    return None

rows=[]
for n in SOURCES:
    e=first_classifier_exit(n)
    d=first_direct(n)
    p=first_p(n)
    rows.append((n,n.bit_length(),e,d,p))
    print("RESIDUAL",n,"bits",n.bit_length(),"exit",e,"direct",d,"P",p)
print("N",len(rows))
print("NO_EXIT_500",[x[0] for x in rows if x[2] is None])
print("NO_DIRECT_5000",[x[0] for x in rows if x[3] is None])
print("NO_P_5000",[x[0] for x in rows if x[4] is None])
print("MAX_EXIT",max((x[2][0],x[0],x[2]) for x in rows if x[2]))
print("MAX_DIRECT",max((x[3][0],x[0],x[3]) for x in rows if x[3]))
print("STATUS DEPTH5_RESIDUAL_PROFILE")
