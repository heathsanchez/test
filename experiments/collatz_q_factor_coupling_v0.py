#!/usr/bin/env python3
"""Consequence audit for the normalized-density floor transition.

For each observed Q class, independently vary the three exact ingredients of
Z' = Z * S * R where S=2*(1-C/P), R=F_j/F_(j+1), across the observed conditional
ranges. Test interval products with exact rationals. This identifies which
ingredient couplings are actually required to preserve the successor floor.
Bounded theorem discovery only.
"""
import json,itertools
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
G=defaultdict(list)
for j in range(60,DEPTH):
 for m in range(1,BITS+1):
  if not P[j][m] or not P[j+1][m]:continue
  Z=Fraction(P[j][m]<<j,F[j]); D=Z.numerator//Z.denominator
  frac=Z-D
  S=Fraction(2*(P[j][m]-C[j+1][m]),P[j][m])
  R=Fraction(F[j],F[j+1])
  Zp=Z*S*R; dp=Zp.numerator//Zp.denominator
  G[(j&1,D)].append((frac,S,R,dp,j,m))
bad_full=[];bad_pair={k:[] for k in ("fracS","fracR","SR")}
strict=0
for q,xs in G.items():
 ds={x[3] for x in xs}
 if len(ds)!=1:continue
 d=next(iter(ds)); D=q[1]
 ranges=[(min(x[i] for x in xs),max(x[i] for x in xs)) for i in range(3)]
 # Full independent box: Z=(D+frac), successor=(D+frac)*S*R.
 vals=[(D+f)*s*r for f in ranges[0] for s in ranges[1] for r in ranges[2]]
 lo,hi=min(vals),max(vals)
 if not (lo>=d and hi<d+1):
  bad_full.append({"Q":list(q),"next_D":d,"count":len(xs)})
 else: strict+=1
 # Keep two ingredients coupled by observed tuples, free the third over range.
 # This detects which coupling is needed.
 for name,pair,free in (("fracS",(0,1),2),("fracR",(0,2),1),("SR",(1,2),0)):
  vlo=[] 
  for x in xs:
   for zfree in ranges[free]:
    a=[x[0],x[1],x[2]];a[free]=zfree
    vlo.append((D+a[0])*a[1]*a[2])
  if not (min(vlo)>=d and max(vlo)<d+1):
   bad_pair[name].append(list(q))
result={"schema":"COLLATZ_Q_FACTOR_COUPLING_V0","q_classes":len(G),
 "full_independent_box_safe":strict,
 "full_independent_box_fail":len(bad_full),
 "pair_coupling_fail_counts":{k:len(v) for k,v in bad_pair.items()},
 "interpretation":{
  "fracS":"fail means coupling of fractional position and survival is insufficient if F-ratio is freed",
  "fracR":"fail means coupling of fractional position and F-ratio is insufficient if survival is freed",
  "SR":"fail means coupling of survival and F-ratio is insufficient if fractional position is freed"},
 "status":"FACTOR_COUPLING_SEPARATOR",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
