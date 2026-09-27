#!/usr/bin/env python3
"""Crystal EXPAND: acquire one new observable from the exact first-descent residual.

The previous bank failed completely. Generate theorem-shaped source-product
observables from exact affine identities, score only by protected-future
ambiguity reduction, promote the cheapest positive separator, and return the
remaining residual. Bounded discovery only.
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
 s=initial(n);trace=[]
 for k in range(DEPTH+1):
  if k and s.endpoint<n:break
  trace.append(s);s=advance(s)
 first=len(trace)
 for s in trace:
  # New capability bank: exact affine/source-coupled distances, not old labels.
  gap=s.endpoint-s.source
  coeff=(1<<s.depth)-3**s.odd_steps
  # signed affine margin is exactly 2^j(endpoint-source)
  margin=(1<<s.depth)*gap
  rows.append({"remaining":first-s.depth,
    "endpoint_gap":gap,
    "gap_sign":(gap>0)-(gap<0),
    "gap_bits":abs(gap).bit_length(),
    "coeff_sign":(coeff>0)-(coeff<0),
    "coeff_bits":abs(coeff).bit_length(),
    "bias_bits":s.intercept.bit_length(),
    "tail_bits":s.tail.bit_length(),
    "residue_gap":s.endpoint_residue-s.source_residue,
    "residue_gap_bits":abs(s.endpoint_residue-s.source_residue).bit_length(),
    "margin_bits":abs(margin).bit_length(),
    "depth_minus_source_bits":s.depth-n.bit_length(),
    "odd_deficit":s.depth-s.odd_steps})
features=[k for k in rows[0] if k!="remaining"]
def ambiguity(feature=None):
 g=defaultdict(set)
 for r in rows:g[r[feature] if feature else 0].add(r["remaining"])
 return sum(len(v)-1 for v in g.values()),sum(len(v)>1 for v in g.values()),len(g)
base=ambiguity()
scores=[]
for f in features:
 a=ambiguity(f);scores.append({"feature":f,"ambiguity":a,"gain":base[0]-a[0]})
scores.sort(key=lambda x:(-x["gain"],x["ambiguity"][2],x["feature"]))
best=scores[0]
if best["gain"]<=0:
 status="EXPAND_AGAIN";residual={"name":"NO_AFFINE_SEPARATOR","next":"derive a new relational/transition capability, not another scalar snapshot"}
else:
 status="CAPABILITY_ACQUIRED";residual={"name":"RECLOSE_WITH_"+best["feature"].upper(),
  "capability":best,"next":"add only this earned observable to Crystal and reclose the same protected future"}
print(json.dumps({"schema":"COLLATZ_CRYSTAL_FIRST_DESCENT_CAPABILITY_V1","rows":len(rows),
 "base_ambiguity":base,"scores":scores,"status":status,"residual":residual,
 "global_collatz":"UNKNOWN"},indent=2))
