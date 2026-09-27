#!/usr/bin/env python3
"""Crystal EXPAND: temporal/block composition after one-step relations failed."""
from __future__ import annotations
import sys,json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
BITS=16;DEPTH=256;BLOCKS=(2,3,4,5,6,8,12,16)
traces=[]
for n in range(3,1<<BITS,2):
 s=initial(n);xs=[s]
 for k in range(DEPTH):
  s=advance(s);xs.append(s)
  if s.endpoint<n:break
 traces.append((n,xs))
rows=[]
for n,xs in traces:
 first=len(xs)-1
 for i in range(first):
  rows.append((n,xs,i,first-i))
def ambiguity(vals):
 g=defaultdict(set)
 for key,rem in vals:g[key].add(rem)
 return sum(len(v)-1 for v in g.values()),sum(len(v)>1 for v in g.values()),len(g)
base=ambiguity([(0,rem) for _,_,_,rem in rows])
scores=[]
for b in BLOCKS:
 vals=[]
 for n,xs,i,rem in rows:
  j=min(i+b,len(xs)-1); a=xs[i]; z=xs[j]
  ga=a.endpoint-a.source; gz=z.endpoint-z.source
  # block/event relations only
  key=(j-i,
       (gz>ga)-(gz<ga),
       abs(gz)<abs(ga),
       z.endpoint<a.endpoint,
       z.odd_steps-a.odd_steps,
       z.tail==0,
       z.endpoint_residue-z.source_residue==0)
  vals.append((key,rem))
 sc=ambiguity(vals); scores.append({"block":b,"ambiguity":sc,"gain":base[0]-sc[0]})
scores.sort(key=lambda x:(-x["gain"],x["ambiguity"][2],x["block"]))
best=scores[0]
if best["gain"]>0:
 status="TEMPORAL_CAPABILITY_ACQUIRED"
 residual={"name":"RECLOSE_TEMPORAL","capability":best,
  "next":"retain only this block relation and reclose protected first-descent futures"}
else:
 status="EXPAND_AGAIN"
 residual={"name":"NO_FIXED_BLOCK_SEPARATOR",
  "next":"move from fixed blocks to event-defined macro transitions; preserve all failed snapshot/one-step/fixed-block capabilities"}
print(json.dumps({"schema":"COLLATZ_CRYSTAL_TEMPORAL_COMPOSITION_V1","rows":len(rows),
 "base":base,"scores":scores,"status":status,"residual":residual,"global_collatz":"UNKNOWN"},indent=2))
