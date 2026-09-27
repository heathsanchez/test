#!/usr/bin/env python3
"""Uniform strict macro contraction constants on the qualified exact corpus.

For every live fixed-window state choose b<=21 minimizing the exact envelope
ratio. Let rho*=max over states of those minima. Compute a conservative L=21
moving polynomial-window threshold J from rho*(1+L/(J+1))^15<1.

BOUNDED certificate only. Universal Collatz promotion requires an all-depth
carry/source-product proof of the same rho bound.
"""
import json
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21;FINITE_CUTOFF=271782
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
 if not P[j][m]:return Fraction(0)
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
best=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  opts=[(ratio(j,b,m),b) for b in range(1,BMAX+1) if j+b<=DEPTH]
  r,b=min(opts)
  best.append((r,b,j,m))
rho,bworst,jworst,mworst=max(best,key=lambda x:x[0])
strict=all(r<1 for r,_,_,_ in best)
def absorbs(j,L=BMAX):
 return rho*Fraction((j+L+1)**15,(j+1)**15)<1
J=None
if strict:
 hi=1
 while not absorbs(hi):hi*=2
 lo=0
 while lo+1<hi:
  mid=(lo+hi)//2
  if absorbs(mid):hi=mid
  else:lo=mid
 J=hi
result={"schema":"COLLATZ_UNIFORM_STRICT_MACRO_CONSTANTS_V0",
 "states":len(best),"all_strict":strict,
 "rho_star":[rho.numerator,rho.denominator],
 "delta_star":[(1-rho).numerator,(1-rho).denominator],
 "worst_state":{"j":jworst,"m":mworst,"best_block":bworst},
 "conservative_macro_span":BMAX,
 "polynomial_growth_absorption_J":J,
 "finite_cutoff":FINITE_CUTOFF,
 "overlap":J is not None and J<=FINITE_CUTOFF,
 "status":"BOUNDED_UNIFORM_STRICT_CONSTANTS" if strict else "STRICTNESS_OBSTRUCTION",
 "universal_macro_lemma":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
