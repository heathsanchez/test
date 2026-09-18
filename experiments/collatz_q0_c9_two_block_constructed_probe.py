#!/usr/bin/env python3
"""Probe explicit q=0 all-odd lift into two C9 blocks.

R=19853 solves (3^R-1)/2 == 468713 (mod 2^20).
"""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base

R=19853
n=(1<<R)-1
k=R+1+18
exit0=(pow(3,R)-1)//2
assert exit0%(1<<20)==468713
x=n
for _ in range(k): x=base.T(x)
c,d=base.forward_state(k,n)
assert d==x
print("SOURCE_BITS",n.bit_length(),"DEPTH",k)
print("EVEN_EXIT_MOD_2_20",exit0%(1<<20))
print("END_GT_SOURCE",x>n)
print("ODD_COUNT",c,"EXTRA_BUDGET",k-c)
opt=base.best_complete_o_within_source_cost(k,n)
print("OPT_IS_SOURCE",opt==(k,n))
print("OPT_COST",None if opt is None else opt[0])
print("STATUS_NAME",base.cylinder_status(k,n)[0])
print("EXPECTED_RIGID",opt==(k,n) and d>=n)
