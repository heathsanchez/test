#!/usr/bin/env python3
"""Decisive bounded audit of the proposed Bias-Lift-or-Rigid bridge.

For each hard first-passage source in a complete odd-source window:
  * compute its first coefficient crossing independently;
  * require non-descent at that crossing (the only finite-crossing obstruction);
  * search the COMPLETE source-order owner table below n for any earlier/later
    coalescence to a smaller source up through the crossing endpoint.
This tests the protected consequence directly rather than assuming that a
same-(d,q) bias lift exists.

Separately classify the crossing endpoint in the exact K/I/B 12-odd <=19-cost
reverse chamber. If an uncovered hard source lands in B, then the proposed
"K/I bias lift or historical A/B rigid core" coverage is false at this boundary.
"""
from __future__ import annotations
import json
from itertools import combinations

BITS=20
N=(1<<BITS)-1
H=512
O=12; MOD=3**O

def T(x):
    return (3*x+1)//2 if x&1 else x//2

# qmin exactly as Lean recurrence.
qmin=[0]*(H+1)
for k in range(H):
    q=qmin[k]
    qmin[k+1]=q if 2**(k+1)<=3**q else q+1

def first_cross(n):
    y=n;q=0
    for d in range(1,H+1):
        b=y&1;y=T(y);q+=b
        if q<qmin[d]: return d,q,y
    return None

# Exact owner table: least positive source <=N reaching each visited state.
owner={}
owner_depth={}
for p in range(1,N+1):
    y=p
    for b in range(H+1):
        if y not in owner:
            owner[y]=p;owner_depth[y]=b
        if y==1 and b>0: break
        y=T(y)

def cocycle(w):
    C=0
    for i,a in enumerate(w): C=(1<<a)*C+3**i
    return C
def comps(total,parts):
    for cuts in combinations(range(1,total),parts-1):
        z=0;w=[]
        for c in cuts+(total,):w.append(c-z);z=c
        yield w
minS={}
for S in range(O,20):
    inv=pow(1<<S,-1,MOD)
    for w in comps(S,O):
        r=cocycle(w)*inv%MOD
        minS[r]=min(S,minS.get(r,99))
def chamber(y):
    s=minS.get(y%MOD)
    return "B" if s is None else ("K" if s<19 else "I")

hard=[]; uncovered=[]; byclass={"K":0,"I":0,"B":0}
for n in range(3,N+1,2):
    fc=first_cross(n)
    if fc is None: continue
    d,q,y=fc
    if y<n: continue
    # Search actual prefix through first crossing for a smaller owner.
    z=n;hit=None
    for a in range(d+1):
        p=owner.get(z)
        if p is not None and 0<p<n:
            hit={"a":a,"meeting":z,"p":p,"b":owner_depth[z]}
            break
        z=T(z)
    c=chamber(y);byclass[c]+=1
    row={"n":n,"d":d,"q":q,"y":y,"class":c,"lower_owner_before_cross":hit}
    hard.append(row)
    if hit is None:
        if len(uncovered)<100:uncovered.append(row)
out={
 "schema":"COLLATZ_BIAS_LIFT_RIGID_DECISION_V1",
 "source_bits":BITS,"source_max":N,"orbit_horizon":H,
 "hard_nondescending_first_crossings":len(hard),
 "hard_crossing_chamber_counts":byclass,
 "pre_cross_lower_source_covered":sum(r["lower_owner_before_cross"] is not None for r in hard),
 "pre_cross_uncovered_count":sum(r["lower_owner_before_cross"] is None for r in hard),
 "pre_cross_uncovered_sample":uncovered,
 "decision":(
   "PROPOSED_KI_OR_RIGID_COVERAGE_FALSIFIED_ON_BOUNDARY"
   if any(r["class"]=="B" for r in uncovered)
   else "NO_B_CLASS_UNCOVERED_WITNESS_ON_BOUNDARY"),
 "interpretation":"A B-class uncovered witness rejects the claim that the existing K/I chamber plus historical two-block rigid core already supplies universal bias-lift coverage. It does not reject lower-source coalescence or Collatz.",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
