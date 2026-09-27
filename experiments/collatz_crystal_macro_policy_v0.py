#!/usr/bin/env python3
"""Extract the common macro policy beta(Q) and compress it.

For each observed Q, choose the smallest b<=21 that pays envelope debt for all
realizations. Record worst exact slack. Then test whether beta factors through
simple generated observables of (parity,D): D mod small bases, bit length, and
coarse dyadic bands. Emits minimum separating feature subsets or collisions.
Bounded theorem discovery only.
"""
import json,itertools
from collections import defaultdict
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
def D(j,m):return (P[j][m]<<j)//F[j] if P[j][m] else None
def ratio(j,b,m):
 # resource ratio actual/envelope target:
 # (P[j+b]/P[j]) / ((F[j+b]/F[j])*2^(floor6diff-b))
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
  vals=[ratio(j,b,m) for j,m in xs]
  if vals and max(vals)<=1:
   policy[q]=(b,max(vals));break
assert len(policy)==len(G)
# Generated observables of Q only.
def obs(q):
 e,d=q
 return (e,d%2,d%3,d%4,d%5,d%7,d%8,d%16,d.bit_length(),
         d>>(max(0,d.bit_length()-4)), d//64,d//256,d//1024)
items=[(q,policy[q][0],obs(q)) for q in policy]
def collision(idx):
 seen={}
 for q,b,o in items:
  k=tuple(o[i] for i in idx)
  if k in seen and seen[k][1]!=b:return seen[k],(q,b,o)
  seen[k]=(q,b,o)
 return None
best=None
for k in range(1,5):
 for idx in itertools.combinations(range(len(items[0][2])),k):
  if collision(idx) is None:best=idx;break
 if best:break
histb=defaultdict(int)
for b,_ in policy.values():histb[b]+=1
worst=sorted(((sl,q,b) for q,(b,sl) in policy.items()),reverse=True)[:10]
result={"schema":"COLLATZ_CRYSTAL_MACRO_POLICY_V0","q_classes":len(G),
 "beta_histogram":dict(sorted(histb.items())),
 "max_beta":max(histb),"minimum_generated_policy_features":list(best) if best else None,
 "worst_resource_ratios":[{"Q":list(q),"beta":b,"ratio":[sl.numerator,sl.denominator]}
                          for sl,q,b in worst],
 "status":"BOUNDED_COMMON_POLICY_EXTRACTED",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
