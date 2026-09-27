#!/usr/bin/env python3
"""Exact composition audit for the sole bounded recharge SCC."""
import json
from fractions import Fraction
import collatz_q0_rigid_recharge_audit as r
a=r.certificate(((2,3,2),))   # q=7/23
b=r.certificate(((2,1,2),))   # q=-1
def compose(cs):
 A,B,D=1,0,0
 for c in cs:
  B=c["A"]*B+c["B"]*(1<<D); A=c["A"]*A; D+=c["D"]
 return A,B,D
def transition_congruence(c,d):
 # enumerate exactly modulo lcm power needed to require c-domain and d-domain after c.
 bits=max(c["D"]+1,d["D"]+1+c["D"])
 M=1<<bits; sols=[]
 for m in range(1,M,2):
  if not r.admissible(c,m): continue
  mp=r.replay(c,m)
  if r.admissible(d,mp): sols.append(m)
 return bits,sols
abits,asol=transition_congruence(a,b)
bbits,bsol=transition_congruence(b,a)
A,B,D=compose((a,b))
C=(1<<D)-A
q=None if C==0 else Fraction(B,C)
# A full cycle must start in a-domain, land in b-domain, then return to a-domain.
bits=max(abits,D+a["D"]+1)
M=1<<bits; cyc=[]
for m in range(1,M,2):
 if not r.admissible(a,m): continue
 m1=r.replay(a,m)
 if not r.admissible(b,m1): continue
 m2=r.replay(b,m1)
 if r.admissible(a,m2):cyc.append((m,m1,m2))
print(json.dumps({"schema":"COLLATZ_RECHARGE_SCC_COMPOSITION_V0",
 "a_to_b":{"bits":abits,"classes":asol},"b_to_a":{"bits":bbits,"classes":bsol},
 "cycle_map":{"A":A,"B":B,"D":D,"C":C,"fixed_point":None if q is None else [q.numerator,q.denominator]},
 "cycle_test_bits":bits,"cycle_classes":cyc[:100],"cycle_class_count":len(cyc),
 "verdict":"NO_SYMBOLIC_TWO_MAP_CYCLE" if not cyc else "SYMBOLIC_CYCLE_RESIDUAL",
 "global_collatz":"UNKNOWN"},indent=2))
