#!/usr/bin/env python3
"""Crystal V2: actual source-product residuals, consequences first.

Authority: experiments/source_product_v1/source_product.py advance/initial.
No parallel transition simulator is permitted.

Protected consequence for a state is the first future event among:
  DESCENT: actual endpoint < fixed original source;
  CROSS_DESCENT / CROSS_NONDESCENT: first coefficient crossing;
  HORIZON: bounded UNKNOWN.
Crystal begins with no feature identity. It admits a separator only if actual
protected futures differ inside a current class. The first admitted separator
is therefore earned by a witnessed consequence conflict.

Bounded evidence only. HORIZON is UNKNOWN, never an exit.
"""
from __future__ import annotations
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
from collatz_live_origin_bridge_v1 import language_counts
BITS=16;DEPTH=160
qmin,_,_=language_counts(DEPTH)

def event(s):
 if s.source==1:return "TERMINAL"
 if s.depth and s.endpoint<s.source:return "DESCENT"
 if s.depth and s.odd_steps<qmin[s.depth]:
  return "CROSS_DESCENT" if s.endpoint<s.source else "CROSS_NONDESCENT"
 return None

# Collect actual states and first-future protected consequence.
rows=[]
for n in range(1,1<<BITS,2):
 trace=[];s=initial(n)
 for _ in range(DEPTH+1):
  e=event(s)
  trace.append((s,e))
  if e:break
  s=advance(s)
 final=trace[-1][1] or "HORIZON"
 # Back-propagate the first actual protected future to every prefix.
 for s,e in trace:
  M=(1<<s.depth)*(s.endpoint_residue-s.source_residue)
  rows.append({"source":n,"depth":s.depth,"odd":s.odd_steps,"tail":s.tail,
   "R":s.source_residue,"Y":s.endpoint_residue,"Msign":(M>0)-(M<0),
   "Mzero":M==0,"parity":s.endpoint&1,
   "q_excess":s.odd_steps-qmin[s.depth] if s.depth else 0,
   "source_bits":n.bit_length(),"future":final})

# Crystal SPLIT: start one class, choose the first candidate observable that
# strictly reduces protected-future conflicts; repeat until no candidate helps.
features=["Msign","Mzero","parity","q_excess","tail","R","Y","source_bits","depth"]
classes={i:0 for i in range(len(rows))}
admitted=[];cycles=[]
def conflicts(cls):
 g=defaultdict(set)
 for i,c in cls.items():g[c].add(rows[i]["future"])
 return sum(len(v)-1 for v in g.values()),sum(len(v)>1 for v in g.values())
base=conflicts(classes)
for cycle in range(len(features)):
 best=None
 for f in features:
  if f in admitted:continue
  # split only within existing classes
  sig={(classes[i],rows[i][f]) for i in classes}
  ids={s:k for k,s in enumerate(sorted(sig,key=repr))}
  trial={i:ids[(classes[i],rows[i][f])] for i in classes}
  score=conflicts(trial)
  gain=base[0]-score[0]
  if gain>0 and (best is None or (gain,-len(set(trial.values())),f)>(best[0],best[1],best[2])):
   best=(gain,-len(set(trial.values())),f,trial,score)
 if best is None:break
 gain,_,f,classes,score=best
 admitted.append(f);cycles.append({"cycle":cycle+1,"split":f,"gain":gain,
   "before":base,"after":score,"classes":len(set(classes.values()))})
 base=score
 if base[0]==0:break

# Residuals are exactly unresolved future-conflict classes plus HORIZON states.
groups=defaultdict(list)
for i,c in classes.items():groups[c].append(i)
conflict=[]
for c,ix in groups.items():
 fut=sorted({rows[i]["future"] for i in ix})
 if len(fut)>1:
  conflict.append({"class":c,"futures":fut,"examples":[rows[i] for i in ix[:8]]})
horizon=[r for r in rows if r["future"]=="HORIZON"]
future_counts=Counter(r["future"] for r in rows)
if conflict:
 residual={"name":"PROTECTED_FUTURE_SEPARATOR","classes":conflict[:20],
  "next":"acquire only an exact observable that separates these witnessed future consequences"}
elif horizon:
 residual={"name":"SOURCE_PRODUCT_HORIZON_UNKNOWN","count":len(horizon),
  "examples":horizon[:20],
  "next":"act on these actual source-coupled paths; derive a theorem/capability, do not label them exits"}
else:
 residual={"name":"UNIVERSALIZE_COMPILED_QUOTIENT",
  "next":"prove admitted distinctions simulate every lawful source-product continuation"}

print(json.dumps({"schema":"COLLATZ_CRYSTAL_SOURCE_PRODUCT_KERNEL_V2",
 "authority":"source_product_v1.initial/advance","rows":len(rows),
 "protected_future_counts":dict(future_counts),"cycles":cycles,
 "admitted_separators":admitted,"remaining_conflicts":base,
 "residual":residual,"global_collatz":"UNKNOWN"},indent=2))
