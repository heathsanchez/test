#!/usr/bin/env python3
"""Throwaway spike: test three-replay C9 high-fuel lifts."""
from __future__ import annotations
import collatz_multi_cycle_high_fuel_lift as mc

A=729;B=467;D=9;r=1
C=(1<<D)-A
bits=3*D+1
mod=1<<bits
m=(B*pow(C,-1,mod))%mod
x=(1<<r)*m-1
print("THREE_REPLAY", "bits",bits,"m",m,"endpoint",x)
for depth in (35,40,45,50):
    res=mc.reverse_audit(x,depth)
    print("DEPTH",depth,res)
    if res['hereditary']:
        print("SEPARATOR_THREE_REPLAY_HEREDITARY",res['first_hered'])
        break
else:
    print("OBSERVED_NO_THREE_REPLAY_HEREDITARY_LIFT_TO_DEPTH",50)
print("STATUS BOUNDED_SPIKE_ONLY")
