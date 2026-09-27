#!/usr/bin/env python3
"""Crystal cycle: derive the local carry law behind equality credit.

Residual consumed:
 UNIVERSAL_SECOND_EQUALITY_CARRY_EXCLUSION.

We combine only exact identities already present in the campaign:
  F[j+1]+H[j+1]=2F[j]
  P[j+1,m]+C[j+1,m]=P[j,m]
and the exact normalized ratio definition.

For b=1 this proves, algebraically:
 normalized equality iff H[j+1]=0, phase jump=0, and C[j+1,m]=0.
Then Crystal asks whether the next policy block's positive source loss can be
reduced to a finite phase-language obligation. Bounded source evidence is kept
separate from the universal theorem obligation.
"""
from __future__ import annotations
import json
from fractions import Fraction
from collections import defaultdict,Counter
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512;BMAX=64
qmin,F,H=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,qmin)
 if z:
  j,_,_=z;hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):
  P[j][m]=P[j-1][m]-C[j][m]
  assert P[j][m]+C[j][m]==P[j-1][m]

def rr(j,b,m):
 if not P[j][m]:return Fraction(0)
 a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
 e=(6*(j+b))//125-(6*j)//125-b
 return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))
def D(j,m):return (P[j][m]<<j)//F[j] if P[j][m] else None

cycles=[]
# C1: exact one-step theorem equivalence over every realized window.
bad=[];checked=0
for j in range(60,DEPTH):
 d=(6*(j+1))//125-(6*j)//125
 for m in range(1,BITS+1):
  if not P[j][m]:continue
  eq=(rr(j,1,m)==1)
  law=(H[j+1]==0 and d==0 and C[j+1][m]==0)
  checked+=1
  if eq!=law:bad.append({"j":j,"m":m,"eq":eq,"H":H[j+1],"phasejump":d,"C":C[j+1][m]})
cycles.append({"cycle":1,"capability":"EXACT_ONE_STEP_EQUALITY_CARRY_IDENTITY",
 "checks":checked,"mismatches":len(bad),"first":bad[:20],
 "proof_skeleton":"substitute F'=2F-H and P'=P-C into normalized equality; nonnegative H,C and phasejump in {0,1} force H=C=0,d=0"})

# C2: common-Q adaptive policy and realized equality. Identify whether every
# equality policy block is actually b=1; if not, preserve the longer-block
# residual rather than overgeneralizing the one-step identity.
G=defaultdict(list)
for j in range(60,DEPTH-BMAX+1):
 for m in range(1,BITS+1):
  if P[j][m]:G[(j&1,D(j,m))].append((j,m))
policy={}
for q,xs in G.items():
 for b in range(1,BMAX+1):
  if all(rr(j,b,m)<=1 for j,m in xs):policy[q]=b;break
eq=[];long=[]
for q,xs in G.items():
 b=policy[q]
 for j,m in xs:
  if rr(j,b,m)==1:
   row=(j,m,b);eq.append(row)
   if b!=1:long.append(row)
cycles.append({"cycle":2,"capability":"EQUALITY_BLOCK_LENGTH_SEPARATOR",
 "realized_equalities":len(eq),"one_step":len(eq)-len(long),
 "longer":len(long),"first_longer":[list(x) for x in long[:20]]})

# C3: for one-step equality states, exact identity gives C[j+1,m]=0.
# Measure the first future k with positive C, and whether it occurs before or
# at the next policy endpoint. This localizes the universal source-hit theorem.
waits=[];miss=[]
for j,m,b in eq:
 if b!=1:continue
 j2=j+1
 if j2>DEPTH-BMAX or not P[j2][m]:continue
 q2=(j2&1,D(j2,m)); b2=policy[q2]
 first=None
 for k in range(j2+1,min(DEPTH,j2+b2)+1):
  if C[k][m]>0:
   first=k;break
 if first is None:miss.append({"j":j,"m":m,"next_b":b2})
 else:waits.append(first-j2)
cycles.append({"cycle":3,"capability":"POST_EQUALITY_SOURCE_HIT",
 "tested":len(waits)+len(miss),"positive_hit":len(waits),"miss":len(miss),
 "max_wait":max(waits,default=None),"wait_hist":dict(Counter(waits)),
 "first_miss":miss[:20]})

if bad:
 status="IDENTITY_REJECTED"; residual={"name":"ONE_STEP_IDENTITY_COUNTEREXAMPLE","examples":bad[:20]}
elif long:
 status="UNKNOWN"; residual={"name":"LONG_EQUALITY_BLOCK_IDENTITY",
  "count":len(long),"next":"derive block equality as simultaneous zero language-terminal and source-crossing mass across the whole block"}
elif miss:
 status="UNKNOWN"; residual={"name":"POST_EQUALITY_SOURCE_HIT_GAP","examples":miss[:20],
  "next":"derive which canonical source/carry congruence prevents these fixed-origin windows from avoiding the next policy block"}
else:
 status="BOUNDED_POST_EQUALITY_HIT"; residual={
  "name":"UNIVERSAL_POST_EQUALITY_SOURCE_HIT",
  "statement":"H[j+1]=0, phasejump=0, C[j+1,m]=0 on equality; prove canonical lift forces C>0 within the next warranted policy block for every live fixed-origin window",
  "max_bounded_wait":max(waits,default=None),
  "next":"derive from canonical source-prefix congruence / qmin threshold; bounded max wait is discovery evidence only"}

print(json.dumps({"schema":"COLLATZ_CRYSTAL_CARRY_EXCLUSION_LAW_V1",
 "cycles":cycles,"status":status,"residual":residual,"global_collatz":"UNKNOWN"},indent=2))
