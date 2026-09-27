#!/usr/bin/env python3
"""Crystal separator mining for fixed-origin misses.

Compare equality-origin states that eventually hit an eligible terminal event
against the 14 misses. Candidate observables are only exact source-window facts:
P, density D, slack to full odd-source capacity, first-crossing support frontier.
Find the smallest single observable/threshold separating misses if one exists.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
q,F,H=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,q)
 if z:hist[z[0]][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)];P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
def pj(j):return (6*(j+1))//125-(6*j)//125
rows=[]
for j in range(60,DEPTH-1):
 if not(H[j+1]==0 and pj(j)==0):continue
 for m in range(1,BITS+1):
  if not P[j][m] or P[j+1][m]!=P[j][m]:continue
  found=None
  for t in range(j+2,DEPTH+1):
   if H[t]>0 and pj(t-1)==0 and C[t][m]>0:found=t;break
  rows.append({"j":j,"m":m,"hit":found is not None,
   "P":P[j][m],"D":(P[j][m]<<j)//F[j],
   "capacity":1<<(m-1),"slack":(1<<(m-1))-P[j][m],
   "j_minus_m":j-m})
miss=[r for r in rows if not r["hit"]]; hit=[r for r in rows if r["hit"]]
features=["m","P","D","slack","j_minus_m"]
seps=[]
for f in features:
 a=sorted(set(r[f] for r in miss)); b=sorted(set(r[f] for r in hit))
 if set(a).isdisjoint(b):seps.append({"feature":f,"type":"disjoint","miss_values":a[:30]})
 # threshold separators
 vals=sorted(set(a+b))
 for v in vals:
  if all(r[f]>=v for r in miss) and all(r[f]<v for r in hit):
   seps.append({"feature":f,"type":">=","threshold":v});break
  if all(r[f]<=v for r in miss) and all(r[f]>v for r in hit):
   seps.append({"feature":f,"type":"<=","threshold":v});break
result={"schema":"COLLATZ_CRYSTAL_ORIGIN_SEPARATOR_V1","states":len(rows),
 "hits":len(hit),"misses":len(miss),"miss_rows":miss,
 "single_feature_separators":seps,
 "status":"SEPARATOR_FOUND" if seps else "COMPOUND_SEPARATOR_REQUIRED",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
