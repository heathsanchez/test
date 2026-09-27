#!/usr/bin/env python3
"""Crystal theorem extraction for the finite first-crossing branch.

Derive exact consequences of the first-crossing prefix, then search for the
smallest algebraic residual needed for strict descent. No finite census result
is promoted to a universal theorem.
"""
from __future__ import annotations
import json
from collections import Counter,defaultdict
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
qmin,F,H=language_counts(DEPTH)

def aff(n,d):
 y=n;q=0;b=0
 for k in range(d):
  if y&1:b=3*b+(1<<k);q+=1;y=(3*y+1)//2
  else:y//=2
 return y,q,b

rows=[]; deficit_bad=[]; strict_bad=[]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,qmin)
 if not z:continue
 d,y,q=z; yp,qa,b=aff(n,d); assert (yp,qa)==(y,q)
 qp=aff(n,d-1)[1]
 bit=q-qp
 jump=qmin[d]-qmin[d-1]
 # exact first-crossing premises
 assert qp>=qmin[d-1] and q<qmin[d] and bit in (0,1) and jump in (0,1)
 # Candidate derived law. Keep counterexamples if any.
 if qmin[d]-q!=1: deficit_bad.append((n,d,qp,q,bit,jump,qmin[d-1],qmin[d]))
 margin=((1<<d)-3**q)*n-b
 if n>1 and margin<=0: strict_bad.append((n,d,q,b,margin,y))
 rows.append((n,d,q,qp,bit,jump,margin,y))

# Mine exact local predecessor states for a proof of deficit=1.
patterns=Counter((r[4],r[5],qmin[r[1]-1]-r[3],qmin[r[1]]-r[2]) for r in rows)
# Strict descent residual: normalize by the one-step predecessor affine state.
hard_features=[]
for n,d,q,qp,bit,jump,margin,y in rows:
 if n==1:continue
 yprev,qprev,bprev=aff(n,d-1)
 hard_features.append({
  "d":d,"last_bit":bit,"jump":jump,
  "prev_gap":3**qprev-(1<<(d-1)),
  "prev_y_minus_n":yprev-n,
  "margin":margin,
  "descending":margin>0})
mins={
 "minimum_margin":min(x["margin"] for x in hard_features),
 "minimum_prev_gap":min(x["prev_gap"] for x in hard_features),
}
result={"schema":"COLLATZ_CRYSTAL_FIRST_CROSSING_THEOREM_V1",
 "crossings":len(rows),"nontrivial":sum(n>1 for n,*_ in rows),
 "deficit_one_counterexamples":deficit_bad[:20],
 "strict_descent_counterexamples":strict_bad[:20],
 "local_pattern_counts":{str(k):v for k,v in patterns.items()},
 "bounded_minima":mins,
 "status":"BOUNDED_FINITE_BRANCH_EMPTY" if not deficit_bad and not strict_bad else "RESIDUAL_WITNESS",
 "residual":{
   "name":"UNIVERSAL_FIRST_CROSSING_DESCENT",
   "deficit_subgoal":"derive qmin(d)-q=1 from previous-live/current-crossing plus exact qmin and last-bit transition",
   "margin_subgoal":"for n>1 prove bias(n,d) < (2^d-3^q)n at that first crossing",
   "formal_target":"Lean theorem: firstCoefficientCrossing n d -> 1<n -> iter shortcut d n < n",
   "warning":"bounded emptiness is discovery evidence only; never-crossing branch remains separate"
 },
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
