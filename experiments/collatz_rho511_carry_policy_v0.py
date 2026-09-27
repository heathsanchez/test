#!/usr/bin/env python3
"""Compile rho=511/512 adaptive macro policy into carry-native signatures.

Target y(j,m)=smallest b<=21 certifying normalized contraction <=511/512.
Candidate features use only exact local recurrence data available at the state:
phase data from j/qmin, live count P, and bounded exit-count prefix C_{j+t}.
Search greedily for a small feature set that removes policy collisions, with
leave-one-feature-out ablation. Bounded discovery only.
"""
import json
from fractions import Fraction
from collections import defaultdict,Counter
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=21;RHO=Fraction(511,512)
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
def ratio(j,b,m):
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
rows=[]
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  y=next(b for b in range(1,BMAX+1) if ratio(j,b,m)<=RHO)
  exits=tuple(C[j+t][m] for t in range(1,BMAX+1))
  jumps=tuple(qmin[j+t]-qmin[j+t-1] for t in range(1,BMAX+1))
  # Carry-native descriptors; no D.
  feat={"jmod125":j%125,"qpar":qmin[j]&1,"P":P[j][m],"Pbit":P[j][m].bit_length(),
        "m":m}
  for t in range(1,BMAX+1):
   feat[f"exit{t}"]=exits[t-1]
   feat[f"jump{t}"]=jumps[t-1]
  rows.append((y,feat,j,m))
names=list(rows[0][1])
def collisions(sel):
 g=defaultdict(set)
 for y,f,_,_ in rows:g[tuple(f[n] for n in sel)].add(y)
 return sum(len(v)-1 for v in g.values()),sum(1 for v in g.values() if len(v)>1),len(g)
# Greedy consequence splitter.
sel=[]; history=[]
base=collisions(sel)
while base[0] and len(sel)<12:
 best=None
 for n in names:
  if n in sel:continue
  c=collisions(sel+[n])
  key=(c[0],c[1],-c[2],n)
  if best is None or key<best[0]:best=(key,n,c)
 sel.append(best[1]);base=best[2];history.append({"add":best[1],"collision_excess":base[0],"ambiguous_classes":base[1],"classes":base[2]})
abl=[]
for n in sel:
 c=collisions([x for x in sel if x!=n])
 abl.append({"remove":n,"collision_excess":c[0],"ambiguous_classes":c[1]})
# Exact first collisions if unresolved.
g=defaultdict(list)
for y,f,j,m in rows:g[tuple(f[n] for n in sel)].append((y,j,m))
examples=[]
for k,xs in g.items():
 if len({x[0] for x in xs})>1:
  examples.append({"signature":list(k),"members":[{"b":b,"j":j,"m":m} for b,j,m in xs[:12]]})
result={"schema":"COLLATZ_RHO511_CARRY_POLICY_V0","states":len(rows),
 "policy_histogram":dict(sorted(Counter(y for y,_,_,_ in rows).items())),
 "selected_features":sel,"selection_history":history,"ablation":abl,
 "final_collision_excess":base[0],"final_ambiguous_classes":base[1],
 "first_collisions":examples[:10],
 "status":"BOUNDED_CARRY_POLICY_SEPARATED" if base[0]==0 else "CARRY_POLICY_RESIDUAL",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
