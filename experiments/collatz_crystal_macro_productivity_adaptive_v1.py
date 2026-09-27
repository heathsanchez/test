#!/usr/bin/env python3
"""Macro-policy productivity audit.

Build the exact observed state graph on concrete (j,m) live-origin states.
At each state choose its Q-class common policy beta(Q), then jump beta steps.
Classify jump resource ratio as <1, =1, or exit. Measure maximal consecutive
equality-paying macro chain before strict decrease/exit. Detect equality cycles.

Bounded theorem discovery only; universal productivity remains to be proved.
"""
import json
from collections import defaultdict
from fractions import Fraction
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

# Follow concrete policy jumps while state remains in qualified domain.
maxeq=0;worst=None; unresolved=[]; equality_edges=0; strict_edges=0; exits=0
for j0 in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if not P[j0][m]:continue
  j=j0; streak=0; seen=set()
  while j<=DEPTH-BMAX and P[j][m]:
   q=(j&1,D(j,m))
   if q not in policy:break
   key=(j,m)
   if key in seen:
    unresolved.append({"j":j0,"m":m,"reason":"equality_cycle"});break
   seen.add(key);b=policy[q];r=rr(j,b,m)
   if P[j+b][m]==0:
    exits+=1;break
   if r<1:
    strict_edges+=1
    if streak>maxeq:maxeq=streak;worst={"j":j0,"m":m,"strict_at":j+b}
    break
   assert r==1
   equality_edges+=1;streak+=1;j+=b
  else:
   if streak:
    unresolved.append({"j":j0,"m":m,"reason":"depth_boundary","streak":streak})
result={"schema":"COLLATZ_CRYSTAL_MACRO_PRODUCTIVITY_ADAPTIVE_V1",
 "q_classes":len(G),"policy_classes":len(policy),
 "equality_edges_examined":equality_edges,"strict_edges":strict_edges,"exit_edges":exits,
 "max_completed_equality_streak":maxeq,"worst_completed":worst,
 "unresolved_boundary_or_cycles":len(unresolved),"first_unresolved":unresolved[:20],
 "status":"BOUNDED_MACRO_PRODUCTIVITY" if not any(x["reason"]=="equality_cycle" for x in unresolved) else "EQUALITY_CYCLE_OBSTRUCTION",
 "theorem_target":"equality-paying macro steps cannot form an infinite lawful chain; uniformly reach strict decrease or exit",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
