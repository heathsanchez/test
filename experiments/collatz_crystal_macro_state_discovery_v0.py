#!/usr/bin/env python3
"""Crystal-generated Collatz macro-state discovery V0.

Bounded developmental experiment, NOT a Collatz proof.

Construct exact live-origin states from source windows. Target consequence is the
minimum block b<=21 that restores the qualified 6/125 envelope, or FAIL.
Generate anonymous arithmetic observables from exact (j,m,P,F,qmin) state,
search minimum feature subsets that separate target outcomes on discovery data,
then test unchanged on held-out depths. A held-out collision emits an exact
separator pair. Historical rejected scalar ranks are not offered as authority.
"""
from __future__ import annotations
import itertools,json,math
from collatz_live_origin_bridge_v1 import language_counts,first_crossing

BITS=20; DEPTH=512; BMAX=21
qmin,F,_=language_counts(DEPTH)
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
    for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]

def good(j,b,m):
    if not P[j][m]:return True
    a=P[j+b][m]*F[j];d=P[j][m]*F[j+b]
    e=(6*(j+b))//125-(6*j)//125-b
    return a <= (d<<e) if e>=0 else (a<<(-e))<=d

def target(j,m):
    for b in range(1,BMAX+1):
        if j+b<=DEPTH and good(j,b,m):return b
    return 0

# Anonymous generated observables. Values are intentionally small/discrete:
# consequence-driven selection decides which distinctions matter.
def obs(j,m):
    p=P[j][m]; f=F[j]
    return (
      j%2,j%3,j%5,j%7,j%21,j%125,
      m%2,m%3,m%5,m,
      qmin[j]-qmin[j-1],
      qmin[j]%2,qmin[j]%3,qmin[j]%5,qmin[j]%7,
      (6*j)//125%2,(6*j)//125%3,
      min(p,7), p.bit_length() if p else 0,
      min(C[j][m],7),
      (p<<j)//f if f else 0, # coarse exact density numerator quotient
    )

states=[]
for j in range(60,DEPTH-BMAX+1):
    for m in range(1,BITS+1):
        if P[j][m]:
            states.append((j,m,target(j,m),obs(j,m)))
assert states and all(t for _,_,t,_ in states)

# Freeze prospective holdout by depth residue; search only discovery.
disc=[s for s in states if s[0]%11 not in (0,1)]
hold=[s for s in states if s[0]%11 in (0,1)]
N=len(states[0][3])

def collision(data,idx):
    seen={}
    for j,m,t,o in data:
        key=tuple(o[i] for i in idx)
        if key in seen and seen[key][2]!=t:return seen[key],(j,m,t,o),key
        seen[key]=(j,m,t,o)
    return None

best=None
for k in range(1,6):
    for idx in itertools.combinations(range(N),k):
        if collision(disc,idx) is None:
            best=idx;break
    if best:break

result={"schema":"COLLATZ_CRYSTAL_MACRO_STATE_DISCOVERY_V0",
 "states":len(states),"discovery_states":len(disc),"holdout_states":len(hold),
 "observable_count":N,"max_feature_subset_searched":5,
 "minimum_discovery_separator":list(best) if best else None,
 "discovery_collision":None if best else "NO_SUBSET_UP_TO_5",
 "historical_negative_controls":["depth alone rejected","lattice cap rejected","running coefficient ceiling rejected","one-step positive hazard rejected"],
 "global_collatz":"UNKNOWN"}

if best:
    hc=collision(hold,best)
    result["holdout_pass"]=hc is None
    if hc:
        a,b,key=hc
        result["holdout_separator"]={
          "key":list(key),
          "left":{"j":a[0],"m":a[1],"target_block":a[2],"observables":list(a[3])},
          "right":{"j":b[0],"m":b[1],"target_block":b[2],"observables":list(b[3])}}
        # Find cheapest single extra observable separating this exact pair.
        result["candidate_new_observables"]=[i for i in range(N) if i not in best and a[3][i]!=b[3][i]]
    else:
        result["holdout_separator"]=None
        result["status"]="BOUNDED_HELDOUT_MACRO_QUOTIENT"
else:
    result["holdout_pass"]=False
    result["status"]="UNKNOWN_EXPRESSIVITY"

print(json.dumps(result,indent=2))
