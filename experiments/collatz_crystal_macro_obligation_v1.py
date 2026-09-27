#!/usr/bin/env python3
"""Crystal macro-obligation discovery on actual record-survivor trajectories.

Intermediate shortcut states are quotiented away. Events are independently
defined coefficient-sign crossings of 3^q versus 2^k (not descent-defined).
At successive events, test exact source-anchored obligation coordinates for
strict lexicographic descent. Bounded falsification only.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
SOURCES=[27,703,10087,35655,270271,362343,381727,626331,1027431]
DEPTH=4096
def sign(s):
 a=3**s.odd_steps; b=2**s.depth
 return (a>b)-(a<b)
def obligation(s):
 n=s.source;y=s.endpoint
 A=3**s.odd_steps; D=2**s.depth-A
 # Exact coordinates only; no future/descent information.
 return {"depth":s.depth,"odds":s.odd_steps,"endpoint":y,
   "gap":y-n,"abs_gap":abs(y-n),"D":D,"Dabs":abs(D),
   "intercept":s.intercept}
out=[]; failures={k:[] for k in ["abs_gap","Dabs","intercept"]}
lex_fail=[]
for n in SOURCES:
 s=initial(n); prevsign=sign(s); events=[]
 for k in range(DEPTH):
  t=advance(s); sg=sign(t)
  if sg!=prevsign:
   events.append(obligation(t)); prevsign=sg
  if k and t.endpoint<n: break
  s=t
 for a,b in zip(events,events[1:]):
  for key in failures:
   if not b[key]<a[key] and len(failures[key])<12:
    failures[key].append({"source":n,"a":a,"b":b})
  # Search a few theorem-shaped lex orders.
  pairs=[("Dabs","abs_gap"),("abs_gap","Dabs"),("Dabs","intercept")]
  for p in pairs:
   va=(a[p[0]],a[p[1]]); vb=(b[p[0]],b[p[1]])
   if not vb<va and len(lex_fail)<30: lex_fail.append({"source":n,"pair":p,"a":va,"b":vb})
 out.append({"source":n,"event_count":len(events),"events":events[:20]})
print(json.dumps({"schema":"COLLATZ_CRYSTAL_MACRO_OBLIGATION_V1",
 "event":"coefficient_sign_change","sources":SOURCES,"traces":out,
 "scalar_failures":failures,"lex_failures":lex_fail,
 "status":"MACRO_OBLIGATION_RESIDUAL",
 "next":"retain only event coordinates whose failure pattern is consequential; if no strict order survives, expand event definition using already-warranted return/carry events rather than trajectory snapshots",
 "global_collatz":"UNKNOWN"},indent=2))
