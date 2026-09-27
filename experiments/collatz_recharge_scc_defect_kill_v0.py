#!/usr/bin/env python3
"""Exact kill of the sole bounded recharge SCC by defect-fuel repeatability."""
from fractions import Fraction
import json
A,B,D=81,95,8
C=(1<<D)-A
q=Fraction(B,C)
assert C==175 and q==Fraction(19,35)
def v2(x):
 x=abs(x); return None if x==0 else (x&-x).bit_length()-1
# Symbolic cycle entry class from qualified composition audit.
m=1873
delta=C*m-B
v=v2(delta)
assert v is not None
max_repeats=(v-1)//D
# Exact transport after each lap: 2^D Delta' = A Delta, A odd.
# Infinite repetition would require unbounded v2(delta), hence delta=0.
assert q.denominator!=1
print(json.dumps({"schema":"COLLATZ_RECHARGE_SCC_DEFECT_KILL_V0",
 "cycle":{"A":A,"B":B,"D":D,"C":C,"fixed_point":[q.numerator,q.denominator]},
 "witness_entry":m,"entry_defect":delta,"entry_v2":v,"max_repeats_from_witness":max_repeats,
 "theorem":"any integer entry has finite consecutive repetitions unless C*m-B=0; zero defect requires m=B/C=19/35, not an integer",
 "verdict":"SOLE_SYMBOLIC_RECHARGE_SCC_NOT_INFINITELY_REPEATABLE",
 "global_collatz":"UNKNOWN"},indent=2))
