#!/usr/bin/env python3
"""Symbolic arithmetic audit for two consecutive equality-paying macro blocks.

Equality for block b at (j,m):
 P[j+b] F[j] 2^{-e} = P[j] F[j+b], with e=floor6diff-b.
This script factors the exact necessary divisibility conditions and tests whether
the phase/live-language terms alone forbid a second equality. Discovery only.
"""
import json,math
from collatz_live_origin_bridge_v1 import language_counts
DEPTH=2000;BMAX=64
q,F,_=language_counts(DEPTH)
def phase_e(j,b):return (6*(j+b))//125-(6*j)//125-b
# Reduce equality A/B = power of two to coprime divisibility obligations on P.
# For consecutive blocks, eliminate middle P and ask whether the product
# language/phase factor permits total equality. This is necessary, not sufficient.
rows=[]; phase_forbidden=0
for j in range(60,DEPTH-2*BMAX):
 for b1 in range(1,BMAX+1):
  for b2 in range(1,BMAX+1):
   e=phase_e(j,b1)+phase_e(j+b1,b2)
   # total normalized equality requires P2/P0 = (F2/F0)*2^e.
   num=F[j+b1+b2]; den=F[j]
   if e>=0:num*=2**e
   else:den*=2**(-e)
   g=math.gcd(num,den);num//=g;den//=g
   # Since 0<P2<=P0 integers, ratio must <=1.
   if num>den:phase_forbidden+=1
   rows.append((j,b1,b2,num,den))
result={"schema":"COLLATZ_CRYSTAL_TWO_EQUALITY_SYMBOLIC_V0",
 "triples":len(rows),"forbidden_by_phase_language_ratio":phase_forbidden,
 "all_forbidden":phase_forbidden==len(rows),
 "interpretation":"If all_forbidden, two equality blocks impossible without source counts. Otherwise carry/source integrality is still needed.",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
