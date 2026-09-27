#!/usr/bin/env python3
"""Select the weakest simple rho sufficient for the Collatz finite/asymptotic overlap.

Requirement at cutoff J0=271782 and L=21:
 rho*((J0+L+1)/(J0+1))^15 < 1.
Search simple dyadic rho=(2^k-c)/2^k, prefer rho closest to 1, then test
against every exact qualified state's best <=21 macro ratio.
"""
import json
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21;J0=271782
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
def ratio(j,b,m):
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
best=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if P[j][m]:
   r,b=min((ratio(j,b,m),b) for b in range(1,BMAX+1))
   best.append((r,b,j,m))
rho_emp=max(x[0] for x in best)
growth=Fraction((J0+BMAX+1)**15,(J0+1)**15)
# Closest-to-1 simple dyadic that still absorbs growth, among denom <=2^20.
candidates=[]
for k in range(1,21):
 den=1<<k
 # largest numerator < den/growth
 n=(den*growth.denominator-1)//growth.numerator
 if n<den and n>0:
  r=Fraction(n,den)
  if r*growth<1:candidates.append((r,k,den-n))
rho,k,c= max(candidates,key=lambda x:x[0])
fails=[{"j":j,"m":m,"best_b":b,"best_ratio":[r.numerator,r.denominator]}
       for r,b,j,m in best if r>rho]
# Also pick memorable looser constants that pass corpus and overlap.
named=[]
for r in [Fraction(1023,1024),Fraction(511,512),Fraction(255,256),Fraction(127,128),
          Fraction(63,64),Fraction(31,32),Fraction(15,16)]:
 named.append({"rho":[r.numerator,r.denominator],
               "absorbs_at_cutoff":r*growth<1,
               "corpus_failures":sum(1 for x in best if x[0]>r)})
result={"schema":"COLLATZ_SIMPLE_RHO_SELECTION_V0",
 "empirical_rho_star":[rho_emp.numerator,rho_emp.denominator],
 "cutoff_growth":[growth.numerator,growth.denominator],
 "weakest_needed_simple_dyadic":{"rho":[rho.numerator,rho.denominator],"k":k,"defect_units":c,
                                  "corpus_failures":len(fails)},
 "named_candidates":named,"first_failures":fails[:10],
 "status":"SIMPLE_RHO_TARGET_SELECTED" if not fails else "SIMPLE_RHO_TOO_STRONG",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
