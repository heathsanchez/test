#!/usr/bin/env python3
"""Moving polynomial-window macro audit.

The finish uses X_j=(j+1)^15. Cover it by dyadic W_j=2^m with
m=ceil(log2 X_j), so W_j < 2 X_j. Test the actual envelope resource
A(j,m)=P_j(2^m)*2^(j-m)/(F_j*2^floor(6j/125))
along macro transitions where BOTH j and m advance to m(j+b).

Finite corpus is limited to m<=20, so this is a bounded falsifier of the
composition law, not universal evidence.
"""
import json
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21
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
def ceil_log2(n):
 return 0 if n<=1 else (n-1).bit_length()
def mwin(j):return ceil_log2((j+1)**15)
def A(j,m):
 # omit harmless global factor 2; exact resource proportional to envelope ratio
 if not P[j][m]:return Fraction(0)
 return Fraction(P[j][m]*(1<<j), F[j]*(1<<m)*(1<<((6*j)//125)))
rows=[];fails=[];growth=[]
for j in range(60,DEPTH-BMAX+1):
 m=mwin(j)
 if m>BITS:continue
 a=A(j,m)
 if a==0:continue
 found=None
 for b in range(1,BMAX+1):
  mp=mwin(j+b)
  if mp>BITS:continue
  ap=A(j+b,mp)
  if ap<=a:
   found=(b,mp,ap);break
 if found is None:
  fails.append({"j":j,"m":m,"A":[a.numerator,a.denominator]})
 else:
  b,mp,ap=found
  row={"j":j,"m":m,"b":b,"m_next":mp,"window_growth":mp-m,
       "ratio":[(ap/a).numerator,(ap/a).denominator]}
  rows.append(row)
  if mp>m:growth.append(row)
result={"schema":"COLLATZ_MOVING_POLYNOMIAL_WINDOW_MACRO_V0",
 "tested_starts":len(rows)+len(fails),"failures":len(fails),"first_failures":fails[:10],
 "max_minimum_block":max((r["b"] for r in rows),default=None),
 "window_growth_macro_count":len(growth),"first_growth_macros":growth[:20],
 "status":"BOUNDED_MOVING_WINDOW_MACRO" if not fails else "MOVING_WINDOW_SEPARATOR",
 "theorem_target":"prove envelope resource nonincrease within bounded macro steps while m(j)=ceil(log2((j+1)^15)) changes",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
