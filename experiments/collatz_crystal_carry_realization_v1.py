#!/usr/bin/env python3
"""Exact carry-realization audit for consecutive equality macro edges.

Build canonical live source-prefix sets through a tractable exact depth. For each
actual window m and start j, use the adaptive common-Q policy and ask whether an
equality macro edge is followed by another equality edge. Unlike the abstract
integer audit, P comes only from exact canonical lift/conservation realization.
Then mine which exact carry observables separate equality states from their
necessarily strict/exit successors. Bounded theorem discovery.
"""
import json
from fractions import Fraction
from collections import defaultdict,Counter
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=64
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
 for j in range(1,DEPTH+1):
  P[j][m]=P[j-1][m]-C[j][m]
  assert P[j-1][m]==P[j][m]+C[j][m]
def D(j,m):return (P[j][m]<<j)//F[j] if P[j][m] else None
def rr(j,b,m):
 if not P[j][m]:return Fraction(0)
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
G=defaultdict(list)
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  d=D(j,m)
  if d is not None:G[(j&1,d)].append((j,m))
policy={}
for q,xs in G.items():
 for b in range(1,BMAX+1):
  if all(j+b<=DEPTH and rr(j,b,m)<=1 for j,m in xs):
   policy[q]=b;break
assert len(policy)==len(G)
eq=[]; double=[]; features=Counter()
for q,xs in G.items():
 b=policy[q]
 for j,m in xs:
  if rr(j,b,m)!=1:continue
  j2=j+b
  if j2>DEPTH-BMAX or not P[j2][m]:continue
  q2=(j2&1,D(j2,m))
  if q2 not in policy:continue
  b2=policy[q2];r2=rr(j2,b2,m)
  row={"j":j,"m":m,"b":b,"j2":j2,"b2":b2,"r2":[r2.numerator,r2.denominator],
       "P":[P[j][m],P[j2][m],P[j2+b2][m]],
       "Cfirst":P[j][m]-P[j2][m],"Csecond":P[j2][m]-P[j2+b2][m],
       "phase":[j%125,j2%125],"D":[D(j,m),D(j2,m)]}
  eq.append(row)
  if r2==1:double.append(row)
  else:
   features[("second_exit_zero",row["Csecond"]==0)]+=1
result={"schema":"COLLATZ_CRYSTAL_CARRY_REALIZATION_V1",
 "realized_equality_states":len(eq),"realized_double_equalities":len(double),
 "first_double":double[:20],"sample_equality_successors":eq[:20],
 "feature_counts":{str(k):v for k,v in features.items()},
 "status":"BOUNDED_CARRY_FORBIDS_DOUBLE_EQUALITY" if not double else "REALIZED_SEPARATOR_REQUIRED",
 "universal":"NOT_PROVED",
 "next":"derive no-double-equality from exact canonical carry/conservation law, or refine using first realized separator",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
