#!/usr/bin/env python3
"""Falsify or promote the Crystal-discovered two-coordinate macro quotient.

Q(j,m)=(j mod 2, floor(2^j P_j(2^m)/F_j)).
Protected successor signature records the next live Q (or EXIT), terminal exits,
and minimum envelope-paying block <=21. Same Q with differing signature is an
exact separator. Bounded test only.
"""
import json
from collections import defaultdict
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
def Q(j,m):
 return (j&1,(P[j][m]<<j)//F[j]) if P[j][m] else None
def good(j,b,m):
 if not P[j][m]:return True
 a=P[j+b][m]*F[j];d=P[j][m]*F[j+b]
 e=(6*(j+b))//125-(6*j)//125-b
 return a <= (d<<e) if e>=0 else (a<<(-e))<=d
def block(j,m):
 for b in range(1,BMAX+1):
  if j+b<=DEPTH and good(j,b,m):return b
 return 0
groups=defaultdict(list)
for j in range(60,DEPTH-BMAX):
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  q=Q(j,m);nq=Q(j+1,m)
  # retain exact exit count only as a falsifier initially; macro target included.
  sig=(nq,C[j+1][m],block(j,m))
  groups[q].append((j,m,sig))
seps=[]
for q,xs in groups.items():
 base=xs[0]
 for x in xs[1:]:
  if x[2]!=base[2]:
   seps.append({"Q":list(q),"left":{"j":base[0],"m":base[1],"sig":repr(base[2])},
    "right":{"j":x[0],"m":x[1],"sig":repr(x[2])}})
   break
result={"schema":"COLLATZ_CRYSTAL_Q_TRANSITION_FALSIFIER_V0",
 "states":sum(map(len,groups.values())),"q_classes":len(groups),
 "separator_count":len(seps),"first_separators":seps[:20],
 "status":"BOUNDED_TRANSITION_QUOTIENT" if not seps else "Q_INSUFFICIENT_SPLIT_REQUIRED",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
