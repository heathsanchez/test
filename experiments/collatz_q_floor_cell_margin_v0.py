#!/usr/bin/env python3
"""Exact conditional floor-cell margin audit for Crystal Q.

For each observed Q=(j mod2,D_j), collect exact rational Z_(j+1)=2^(j+1)P_(j+1)/F_(j+1).
Compute min/max by integer cross multiplication, verify the whole conditional interval
lies in one floor cell, and report the smallest exact distance to either integer boundary.
This discovers the sharp inequality target; bounded evidence only.
"""
import json,math
from collections import defaultdict
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
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
def z(j,m):return Fraction(P[j][m]<<j,F[j])
def Q(j,m):
 x=z(j,m);return (j&1,x.numerator//x.denominator)
groups=defaultdict(list)
for j in range(60,DEPTH):
 for m in range(1,BITS+1):
  if P[j][m] and P[j+1][m]:
   groups[Q(j,m)].append((j,m,z(j+1,m)))
bad=[]; margins=[]; summaries=[]
for q,xs in groups.items():
 lo=min(x[2] for x in xs);hi=max(x[2] for x in xs)
 floors={x[2].numerator//x[2].denominator for x in xs}
 if len(floors)!=1:
  bad.append({"Q":list(q),"floors":sorted(floors)})
  continue
 d=next(iter(floors))
 left=lo-d;right=(d+1)-hi
 margin=min(left,right);margins.append((margin,q,d,lo,hi,len(xs)))
 summaries.append((q,d,lo,hi,len(xs)))
margins.sort(key=lambda x:x[0])
def fs(x):return [x.numerator,x.denominator]
result={"schema":"COLLATZ_Q_FLOOR_CELL_MARGIN_V0","q_classes":len(groups),
 "multi_floor_classes":len(bad),"first_bad":bad[:10],
 "smallest_margins":[{"Q":list(q),"next_D":d,"count":cnt,
   "lo":fs(lo),"hi":fs(hi),"margin":fs(m)}
   for m,q,d,lo,hi,cnt in margins[:20]],
 "zero_margin_classes":sum(1 for x in margins if x[0]==0),
 "status":"BOUNDED_STRICT_FLOOR_CELL_SEPARATION" if not bad and all(x[0]>0 for x in margins) else "BOUNDARY_OR_COLLISION",
 "theorem_target":"prove conditional Z_(j+1) interval for each lawful Q lies in its unique integer floor cell",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
