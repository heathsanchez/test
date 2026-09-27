#!/usr/bin/env python3
"""Crystal: speak only from actual pre-first-descent source-product futures."""
from __future__ import annotations
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
BITS=16;DEPTH=256
rows=[]; horizons=[]
for n in range(3,1<<BITS,2):
 s=initial(n); trace=[]
 for k in range(DEPTH+1):
  if k>0 and s.endpoint<n: break
  trace.append(s)
  s=advance(s)
 else:
  horizons.append(n)
 first=len(trace)
 for s in trace:
  rows.append({"source":n,"depth":s.depth,"remaining":first-s.depth,
   "Msign":((s.endpoint_residue-s.source_residue)>0)-((s.endpoint_residue-s.source_residue)<0),
   "Mzero":s.endpoint_residue==s.source_residue,"parity":s.endpoint&1,
   "tail_zero":s.tail==0,"tail_parity":s.tail&1,
   "Rparity":s.source_residue&1,"Yparity":s.endpoint_residue&1,
   "source_bits":n.bit_length()})
# Protected future is exact remaining actions to first strict descent.
features=["Msign","Mzero","parity","tail_zero","tail_parity","Rparity","Yparity","source_bits"]
classes={i:0 for i in range(len(rows))}; admitted=[];cycles=[]
def ambiguity(cls):
 g=defaultdict(set)
 for i,c in cls.items():g[c].add(rows[i]["remaining"])
 return sum(len(v)-1 for v in g.values()),sum(len(v)>1 for v in g.values())
base=ambiguity(classes)
for cyc in range(len(features)):
 best=None
 for f in features:
  if f in admitted:continue
  sig={(classes[i],rows[i][f]) for i in classes}; ids={s:k for k,s in enumerate(sorted(sig,key=repr))}
  trial={i:ids[(classes[i],rows[i][f])] for i in classes}; score=ambiguity(trial); gain=base[0]-score[0]
  if gain>0 and (best is None or gain>best[0]):best=(gain,f,trial,score)
 if best is None:break
 gain,f,classes,score=best;admitted.append(f)
 cycles.append({"cycle":cyc+1,"split":f,"gain":gain,"before":base,"after":score,"classes":len(set(classes.values()))})
 base=score
 if base[0]==0:break
groups=defaultdict(list)
for i,c in classes.items():groups[c].append(i)
res=[]
for c,ix in groups.items():
 vals=sorted({rows[i]["remaining"] for i in ix})
 if len(vals)>1:res.append({"class":c,"remaining":vals[:40],"examples":[rows[i] for i in ix[:12]]})
out={"schema":"COLLATZ_CRYSTAL_FIRST_DESCENT_RESIDUAL_V1","authority":"source_product_v1.initial/advance",
 "sources":(1<<15)-1,"prefix_states":len(rows),"horizon_unknown_sources":horizons[:40],"horizon_unknown_count":len(horizons),
 "cycles":cycles,"admitted":admitted,"ambiguity":base,
 "residual":{"name":"FIRST_DESCENT_FUTURE_CONFLICT","classes":res[:20]} if res else
 {"name":"COMPILED_FIRST_DESCENT_FUTURE","next":"universalize only the earned capability"},
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
