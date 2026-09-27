#!/usr/bin/env python3
"""Crystal relational capability acquisition for first descent.

Consumes NO_AFFINE_SEPARATOR. Snapshot features are forbidden. Candidate
capabilities are relations between consecutive authoritative source-product
states. Score by conditional uncertainty of the protected future; promote only
a positive-gain relational law and emit the remaining residual.
"""
from __future__ import annotations
import sys,json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
BITS=16;DEPTH=256
rows=[]
for n in range(3,1<<BITS,2):
 s=initial(n); trace=[]
 for k in range(DEPTH+1):
  if k and s.endpoint<n:break
  t=advance(s); trace.append((s,t)); s=t
 first=len(trace)
 for idx,(a,b) in enumerate(trace):
  ga=a.endpoint-a.source; gb=b.endpoint-b.source
  ra=a.endpoint_residue-a.source_residue; rb=b.endpoint_residue-b.source_residue
  rows.append({"remaining":first-idx,
   "gap_direction":(gb>ga)-(gb<ga),
   "gap_contract":abs(gb)<abs(ga),
   "residue_gap_direction":(rb>ra)-(rb<ra),
   "residue_gap_contract":abs(rb)<abs(ra),
   "tail_drop":a.tail-b.tail,
   "tail_halves":b.tail*2 in (a.tail,a.tail-1),
   "odd_step":b.odd_steps>a.odd_steps,
   "endpoint_contract":b.endpoint<a.endpoint,
   "source_residue_jump":b.source_residue-a.source_residue,
   "endpoint_residue_jump":b.endpoint_residue-a.endpoint_residue})
features=[k for k in rows[0] if k!="remaining"]
def ambiguity(f=None):
 g=defaultdict(set)
 for r in rows:g[r[f] if f else 0].add(r["remaining"])
 return sum(len(v)-1 for v in g.values()),sum(len(v)>1 for v in g.values()),len(g)
base=ambiguity();scores=[]
for f in features:
 a=ambiguity(f);scores.append({"capability":f,"ambiguity":a,"gain":base[0]-a[0]})
scores.sort(key=lambda x:(-x["gain"],x["ambiguity"][2],x["capability"]))
best=scores[0]
if best["gain"]>0:
 status="RELATIONAL_CAPABILITY_ACQUIRED"
 residual={"name":"RECLOSE_RELATIONAL","capability":best,
  "next":"retain this capability, reclose, then expand only the surviving conflict"}
else:
 status="EXPAND_AGAIN"
 residual={"name":"NO_ONE_STEP_RELATIONAL_SEPARATOR",
  "next":"promote temporal composition: block/event relation over multiple transitions"}
print(json.dumps({"schema":"COLLATZ_CRYSTAL_TRANSITION_CAPABILITY_V1","rows":len(rows),
 "base":base,"scores":scores,"status":status,"residual":residual,"global_collatz":"UNKNOWN"},indent=2))
