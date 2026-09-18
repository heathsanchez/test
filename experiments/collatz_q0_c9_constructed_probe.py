#!/usr/bin/env python3
"""Probe an explicit q=0 all-odd-prefix lift into one C9 block.

R=397 solves (3^R-1)/2 == 1769 (mod 2^11).
Source n=2^R-1 reaches q=0 after R bits, the bit-zero exit is at R+1,
and then the endpoint lies in the one-C9 return cylinder.

We classify the full depth R+10 state using the exact bounded Complete-O
search. This is a finite but very large-integer test.
"""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base

R=397
n=(1<<R)-1
k=R+10
x=n
for _ in range(k):
    x=base.T(x)
print("SOURCE_BITS",n.bit_length(),"DEPTH",k)
exit0=(pow(3,R)-1)//2
print("EVEN_EXIT_MOD_2_11",exit0%(1<<11))
print("C9_TARGET",1769)
print("END_GT_SOURCE",x>n)
c,d=base.forward_state(k,n)
assert d==x
print("ODD_COUNT",c,"EXTRA_BUDGET",k-c)
opt=base.best_complete_o_within_source_cost(k,n)
print("OPT",opt)
print("SOURCE",n)
print("STATUS",base.cylinder_status(k,n))
print("EXPECTED_RIGID",opt==(k,n) and d>=n)
