#!/usr/bin/env python3
"""Exact integer feasibility of two consecutive normalized equalities.

For each (j,b1,b2), reduce both equality ratios P1/P0 and P2/P1.
There exist positive nonincreasing integer counts iff both reduced ratios <=1;
integrality itself never obstructs after scaling P0 by denominator products.
This is a theorem-discovery audit: if feasible triples remain, count divisibility
cannot explain the observed no-double-equality law and Crystal must seek carry
conservation rather than add arbitrary features.
"""
import json,math
from collatz_live_origin_bridge_v1 import language_counts
DEPTH=2000;BMAX=64
_,F,_=language_counts(DEPTH)
def ratio(j,b):
 e=(6*(j+b))//125-(6*j)//125-b
 num=F[j+b];den=F[j]
 if e>=0:num*=2**e
 else:den*=2**(-e)
 g=math.gcd(num,den);return num//g,den//g
feasible=0; impossible=0; examples=[]
for j in range(60,DEPTH-2*BMAX):
 for b1 in range(1,BMAX+1):
  a,b=ratio(j,b1)
  for b2 in range(1,BMAX+1):
   c,d=ratio(j+b1,b2)
   if a<=b and c<=d:
    feasible+=1
    if len(examples)<20:
     # constructive integer witness to the two ratio equations.
     p0=b*d; p1=a*d; p2=a*c
     assert p0>=p1>=p2>0 and p1*b==p0*a and p2*d==p1*c
     examples.append({"j":j,"b1":b1,"b2":b2,"ratios":[[a,b],[c,d]],"integer_counts":[p0,p1,p2]})
   else: impossible+=1
result={"schema":"COLLATZ_CRYSTAL_TWO_EQUALITY_INTEGER_V1",
 "triples":feasible+impossible,"integer_feasible":feasible,"impossible":impossible,
 "first_feasible":examples,
 "conclusion":("COUNT_INTEGRALITY_NOT_THE_SEPARATOR" if feasible else "TWO_EQUALITIES_ARITHMETICALLY_IMPOSSIBLE"),
 "next_if_feasible":"promote exact carry/conservation realization constraints; do not add residue heuristics",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
