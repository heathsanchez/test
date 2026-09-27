#!/usr/bin/env python3
"""Test scale structure of the Crystal density coordinate D.

The finish window has growing m, so D is potentially unbounded.  Fit no model:
compute exact observed transitions (parity,D)->D' and test theorem-shaped
scale inequalities D' <= a D + b with small rational a,b, plus dyadic
renormalization behavior across m. Emits exact counterexamples.
"""
import json
from fractions import Fraction
from collections import defaultdict
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
def D(j,m):return ((P[j][m]<<j)//F[j]) if P[j][m] else None
trans=[]
for j in range(60,DEPTH):
 for m in range(1,BITS+1):
  d=D(j,m);dp=D(j+1,m)
  if d is not None and dp is not None:trans.append((j&1,d,dp,j,m))
# Search small rational multiplicative envelopes dp <= ceil(a*d)+b,
# minimizing a then b is not claimed; report failures for useful candidates.
cands=[(Fraction(1,1),0),(Fraction(17,16),1),(Fraction(9,8),1),
       (Fraction(5,4),1),(Fraction(3,2),1),(Fraction(2,1),0)]
tests=[]
for a,b in cands:
 bad=[]
 for e,d,dp,j,m in trans:
  rhs=(a.numerator*d + a.denominator-1)//a.denominator+b
  if dp>rhs:
   bad.append({"parity":e,"D":d,"Dnext":dp,"j":j,"m":m,"rhs":rhs})
 tests.append({"a":[a.numerator,a.denominator],"b":b,"failures":len(bad),"first":bad[:3]})
# Cross-window dyadic scale: compare D(j,m+1) to 2D(j,m).
scale=[]
for j in range(60,DEPTH+1):
 for m in range(1,BITS):
  a=D(j,m);b=D(j,m+1)
  if a is not None and b is not None:
   scale.append(b-2*a)
result={"schema":"COLLATZ_Q_SCALE_LAW_V0","transitions":len(trans),
 "max_D":max(x[1] for x in trans),"max_Dnext":max(x[2] for x in trans),
 "candidate_envelopes":tests,
 "dyadic_scale_error":{"count":len(scale),"min":min(scale) if scale else None,
                        "max":max(scale) if scale else None,
                        "distinct":len(set(scale))},
 "structural_warning":"D is not proven bounded at polynomial source windows; bounded DAG cannot be promoted without a scale/rank theorem.",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
