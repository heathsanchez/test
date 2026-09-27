#!/usr/bin/env python3
"""Crystal: exact first-crossing split and deficit-one descent residual.

This corrects the previous heuristic: qmin(d)-q need not be one at a first
coefficient crossing. We first derive/test the exact local crossing law from
the previous live condition, then quotient first crossings by the minimum
consequential separator and identify the actual nondescending residual.

Finite census is discovery/falsification only; global Collatz remains UNKNOWN.
"""
from __future__ import annotations
import json
from collections import Counter,defaultdict
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20; DEPTH=512
qmin,F,H=language_counts(DEPTH)

def aff(n,d):
 y=n;q=0;b=0
 for k in range(d):
  if y&1:
   b=3*b+(1<<k);q+=1;y=(3*y+1)//2
  else:y//=2
 return y,q,b

rows=[]; law_bad=[]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,qmin)
 if not z:continue
 d,y,q=z
 yp,qp,b=aff(n,d)
 assert (yp,qp)==(y,q)
 # Exact local first-crossing constraints: previous prefix was live.
 qprev=aff(n,d-1)[1] if d else 0
 prev_live=(d==0 or qprev>=qmin[d-1])
 bit=q-qprev
 law=(prev_live and q<qmin[d] and qprev>=qmin[d-1] and bit in (0,1))
 if not law:law_bad.append((n,d,qprev,q,bit))
 rows.append({"n":n,"d":d,"q":q,"qprev":qprev,"bit":bit,
              "deficit":qmin[d]-q,"qmin_jump":qmin[d]-qmin[d-1],
              "y":y,"b":b,"descending":y<n,
              "margin":((1<<d)-3**q)*n-b})

# Crystal consequential quotient: which exact local observables separate
# descending from nondescending first crossings?
hard=[r for r in rows if not r["descending"]]
features=["deficit","qmin_jump","bit"]
seps=[]
for f in features:
 hv=set(r[f] for r in hard); dv=set(r[f] for r in rows if r["descending"])
 if hv and hv.isdisjoint(dv):seps.append({"feature":f,"hard_values":sorted(hv)})
joint=defaultdict(set)
for r in rows:joint[(r["deficit"],r["qmin_jump"],r["bit"])].add(r["descending"])
conflicts=[{"role":list(k),"outcomes":sorted(v)} for k,v in joint.items() if len(v)>1]

# The earlier deficit-one experiment is retained as a bounded capability only.
def1=[r for r in rows if r["deficit"]==1]
def1hard=[r for r in def1 if not r["descending"]]
defhist=Counter(r["deficit"] for r in rows)
hardhist=Counter(r["deficit"] for r in hard)

if law_bad:
 status="LOCAL_CROSSING_LAW_REJECTED"; residual={"name":"CROSSING_LAW_BUG","examples":law_bad[:20]}
elif hard:
 status="UNKNOWN"; residual={
  "name":"FIRST_CROSSING_NONDESCENT_CLASSES",
  "hard_count":len(hard),"deficit_hist":dict(hardhist),
  "first":hard[:30],
  "next":"apply the warranted canonical-M/source-tail/carry reductions to these actual hard classes; do not assume deficit one"}
else:
 status="BOUNDED_ALL_FIRST_CROSSINGS_DESCEND"; residual={
  "name":"UNIVERSAL_FIRST_CROSSING_DESCENT",
  "next":"derive affine margin negativity from exact first-crossing prefix constraints"}

print(json.dumps({"schema":"COLLATZ_CRYSTAL_FIRST_CROSSING_SPLIT_V1",
 "crossings":len(rows),"local_law_violations":len(law_bad),
 "deficit_hist":dict(defhist),"nondescending":len(hard),
 "deficit_one":{"count":len(def1),"nondescending":len(def1hard)},
 "single_feature_separators":seps,"joint_role_conflicts":conflicts,
 "status":status,"residual":residual,"global_collatz":"UNKNOWN"},indent=2))
