#!/usr/bin/env python3
"""Dyadic live-shell transfer audit for the irreducible window-extension lemma.

S_j(m)=P_j(2^(m+1))-P_j(2^m): live origins introduced by shell m+1.
Measure normalized shell resource with the same F/phase normalization and test
whether every nonempty shell itself gets a rho=511/512 contraction within 21,
plus how shell mass compares to the old live prefix.

If shells obey the same macro law independently, arbitrary windows follow by
additivity. This is the cleanest possible promotion route.
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
def shell(j,m): # added going m -> m+1
 return P[j][m+1]-P[j][m]
def ratio_shell(j,b,m):
 s=shell(j,m)
 if not s:return Fraction(0)
 sp=shell(j+b,m)
 a=Fraction(sp*F[j],s*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
rows=[];bad=[];histb=Counter();worst=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS):
  s=shell(j,m)
  if s<=0:continue
  vals=[(ratio_shell(j,b,m),b) for b in range(1,BMAX+1)]
  wins=[(r,b) for r,b in vals if r<=RHO]
  if not wins:
   bad.append({"j":j,"m":m,"shell":s,
               "best":[min(vals)[0].numerator,min(vals)[0].denominator],
               "best_b":min(vals)[1]})
  else:
   b=min(b for r,b in wins);histb[b]+=1
  r,b=min(vals);worst.append((r,j,m,b,s))
worst.sort(reverse=True)
result={"schema":"COLLATZ_DYADIC_SHELL_TRANSFER_V0",
 "nonempty_shell_states":len(worst),"shell_bad_through_21":len(bad),
 "first_bad_shells":bad[:20],"first_certifying_block_histogram":dict(sorted(histb.items())),
 "worst_best_shell_ratios":[{"ratio":[r.numerator,r.denominator],"j":j,"m":m,"b":b,"shell":s}
                            for r,j,m,b,s in worst[:20]],
 "status":"BOUNDED_SHELL_MACRO_LAW" if not bad else "SHELL_MACRO_OBSTRUCTION",
 "implication_if_universal":"shellwise macro contraction plus additivity promotes prefix contraction across arbitrary dyadic window extension",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
