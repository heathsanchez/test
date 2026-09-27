#!/usr/bin/env python3
"""Local arithmetic contradiction compiler for rho=511/512 BAD.

BAD means ratio(j,b,m)>rho for every b=1..21. Cross-multiply each inequality
to obtain an exact integer lower bound LB_b on P[j+b] as a function of P[j].
Compare LB_b to the actual monotone live trajectory and identify the first
horizon contradiction. Also measure whether the contradiction is already
forced by monotonicity alone (LB_b>P0), or requires an exit/carry upper bound.

Bounded discovery; outputs theorem-shaped integer inequalities.
"""
import json
from fractions import Fraction
from collections import Counter
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21;RHO=Fraction(511,512)
qmin,F,_=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,qmin)
 if z:
  j,_,_=z;hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)];P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
def allowed_factor(j,b):
 # ratio = (Pb/P0)/(F_b/F_0 * 2^e). BAD ratio>rho =>
 # Pb > rho*P0*(F_b/F0)*2^e.
 e=(6*(j+b))//125-(6*j)//125-b
 return RHO*Fraction(F[j+b],F[j])*Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
def bad_lb(j,b,p0):
 x=allowed_factor(j,b)*p0
 return x.numerator//x.denominator+1
rows=[]; mono_kills=Counter(); firstkills=Counter(); gaps=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  p0=P[j][m]
  if not p0:continue
  first=None
  for b in range(1,BMAX+1):
   lb=bad_lb(j,b,p0); actual=P[j+b][m]
   if lb>p0:mono_kills[b]+=1
   if actual<lb and first is None:first=(b,lb,actual)
  if first:
   b,lb,a=first;firstkills[b]+=1;gaps.append((lb-a,j,m,b,p0,lb,a))
  rows.append((j,m,first))
gaps.sort()
result={"schema":"COLLATZ_BAD_INTEGER_CONTRADICTION_V0","states":len(rows),
 "states_with_contradiction_by_21":sum(x[2] is not None for x in rows),
 "first_contradiction_histogram":dict(sorted(firstkills.items())),
 "monotonicity_alone_kills_by_horizon":dict(sorted(mono_kills.items())),
 "smallest_integer_gaps":[{"gap":g,"j":j,"m":m,"b":b,"P0":p,"bad_lb":lb,"actual":a}
                          for g,j,m,b,p,lb,a in gaps[:30]],
 "status":"BOUNDED_BAD_INTEGER_CONTRADICTION",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
