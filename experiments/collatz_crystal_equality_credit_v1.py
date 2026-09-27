#!/usr/bin/env python3
"""Crystal equality-credit audit.

Candidate learned from adaptive productivity: no two consecutive equality-paying
macro steps. Test it exactly on the same finite live-origin corpus and emit the
first equality->equality separator if present. Bounded discovery only.
"""
import json
from fractions import Fraction
from collections import defaultdict
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
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
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
eq=[];viol=[]
for q,xs in G.items():
 b=policy[q]
 for j,m in xs:
  if rr(j,b,m)!=1:continue
  eq.append((j,m,q,b))
  j2=j+b
  if j2>DEPTH-BMAX or not P[j2][m]:continue
  q2=(j2&1,D(j2,m))
  if q2 not in policy:continue
  b2=policy[q2]; r2=rr(j2,b2,m)
  if r2==1:viol.append({"first":{"j":j,"m":m,"Q":q,"b":b},
    "second":{"j":j2,"m":m,"Q":q2,"b":b2}})
result={"schema":"COLLATZ_CRYSTAL_EQUALITY_CREDIT_V1",
 "equality_edges":len(eq),"consecutive_equality_violations":len(viol),
 "first_violations":viol[:20],
 "candidate_secondary_rank":"E=1 before equality macro edge, E=0 after; next macro must strictly contract or exit",
 "status":"BOUNDED_ONE_EQUALITY_CREDIT" if not viol else "SEPARATOR_REQUIRED",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
