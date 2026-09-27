#!/usr/bin/env python3
"""Mine the exact local law behind one equality credit.

For every realized equality macro edge, audit:
 A) exits during equality block are zero;
 B) next policy block has positive exits (or exhausts);
 C) phase/block pattern support.
Then emit exact counterexamples to either implication.
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
  if P[j][m]:G[(j&1,D(j,m))].append((j,m))
policy={}
for q,xs in G.items():
 for b in range(1,BMAX+1):
  if all(rr(j,b,m)<=1 for j,m in xs):policy[q]=b;break
badA=[];badB=[];pat=Counter();total=0
for q,xs in G.items():
 b=policy[q]
 for j,m in xs:
  if rr(j,b,m)!=1:continue
  total+=1;j2=j+b
  exits1=P[j][m]-P[j2][m]
  if exits1!=0:badA.append((j,m,b,exits1))
  if j2<=DEPTH-BMAX and P[j2][m]:
   q2=(j2&1,D(j2,m));b2=policy[q2]
   exits2=P[j2][m]-P[j2+b2][m]
   if exits2<=0:badB.append((j,m,b,j2,b2,exits2))
   pat[(j%125,b,j2%125,b2)]+=1
result={"schema":"COLLATZ_CRYSTAL_EQUALITY_LOCAL_LAW_V1","equality_states":total,
 "equality_with_positive_exit":len(badA),"first_bad_A":badA[:20],
 "next_macro_without_positive_exit":len(badB),"first_bad_B":badB[:20],
 "phase_block_patterns":[{"pattern":list(k),"count":v} for k,v in pat.most_common()],
 "candidate":"equality macro iff zero carry loss at a paying phase; exact next carry block must lose >=1 live source",
 "status":"BOUNDED_LOCAL_LAW" if not badA and not badB else "LOCAL_LAW_SEPARATOR",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
