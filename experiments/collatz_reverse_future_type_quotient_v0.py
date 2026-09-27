#!/usr/bin/env python3
"""Crystal future-type quotient of the source-valid reverse survivor tree.

At each event, partition parent residues by the complete protected child mask.
Then refine backwards by the tuple of child future-types (Myhill-Nerode style).
This asks how many consequential future types the finite Q<=13 tree actually
needs; it does not extrapolate beyond Q=13.
"""
import json
from collections import Counter
from collatz_reverse_target_audit import enumerate_target,coverage
EVENTS=[3,5,6,8,10,11,13]
tabs={}; surv={}
for q in EVENTS:
 t,_=coverage(enumerate_target(q),q);tabs[q]=t
 surv[q]=[r for r in range(1,3**q,3) if not t[r]]
# terminal type at last event: all current survivors equivalent until more future is exposed.
types={EVENTS[-1]:{r:0 for r in surv[EVENTS[-1]]}}
stats=[]
for idx in range(len(EVENTS)-2,-1,-1):
 q,q1=EVENTS[idx],EVENTS[idx+1]; M=3**q; scale=3**(q1-q)
 signatures={}; sig_to_type={}
 for r in surv[q]:
  child=[]
  for k in range(scale):
   y=r+k*M
   if y%3!=1: continue
   if tabs[q1][y]: child.append(-1) # EXIT
   else: child.append(types[q1][y])
  sig=tuple(child);signatures[r]=sig
  if sig not in sig_to_type:sig_to_type[sig]=len(sig_to_type)
 types[q]={r:sig_to_type[s] for r,s in signatures.items()}
 hist=Counter(types[q].values())
 stats.append({"Q":q,"next":q1,"future_types":len(sig_to_type),
               "type_sizes":sorted(hist.values(),reverse=True)[:20],
               "signatures":[{"type":t,"signature":list(sig)} for sig,t in list(sig_to_type.items())[:30]]})
stats.reverse()
print(json.dumps({"schema":"COLLATZ_REVERSE_FUTURE_TYPE_QUOTIENT_V0",
 "events":EVENTS,"stats":stats,
 "root_type_count":len(set(types[EVENTS[0]].values())),
 "boundary":"finite future quotient only through Q=13; no all-depth automaton claim",
 "global_collatz":"UNKNOWN"},indent=2))
