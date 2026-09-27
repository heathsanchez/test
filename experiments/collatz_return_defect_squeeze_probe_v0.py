#!/usr/bin/env python3
"""Crystal probe: compare exact return defect magnitude to its mandatory 2-adic modulus."""
import json, math
import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_coalescence_component_audit as base
from collections import defaultdict

def audit(lo,hi,K=128):
 ratios=[]; rows=0; zeros=0; squeezed=0; worst=None
 for n in range(lo|1,hi+1,2):
  survives,_=base.survives_to_q0(n)
  if not survives or base.birth_status(n)[0]!="RIGID" or not fk.completed_rigid_source(n,K): continue
  for r,seq in fk.return_sequences(n,K).items():
   for e in seq:
    c=e["cert"]; d=abs(fk.defect(c,e["m0"])); rows+=1
    if d==0: zeros+=1; continue
    mod=1<<(c["D"]+1)
    assert d%mod==0
    q=d//mod
    if d<mod:squeezed+=1
    # normalized quotient after mandatory divisibility; inspect vs source and m.
    rec={"n":n,"r":r,"D":c["D"],"m":e["m0"],"defect":d,"units":q,
         "units_over_n":q/n,"units_over_m":q/e["m0"]}
    if worst is None or rec["units_over_n"]>worst["units_over_n"]:worst=rec
    ratios.append(rec)
 return {"range":[lo,hi],"rows":rows,"zeros":zeros,"squeezed_nonzero":squeezed,
         "max_units_over_n":None if not ratios else max(x["units_over_n"] for x in ratios),
         "max_units_over_m":None if not ratios else max(x["units_over_m"] for x in ratios),
         "min_units":None if not ratios else min(x["units"] for x in ratios),
         "max_units":None if not ratios else max(x["units"] for x in ratios),
         "worst":worst}
print(json.dumps({"schema":"COLLATZ_RETURN_DEFECT_SQUEEZE_PROBE_V0",
 "rows":[audit(3,8191),audit(8193,32767)],
 "interpretation":"nonzero exact-domain defect is at least 2^(D+1); need independent magnitude bound below modulus to force zero",
 "global_collatz":"UNKNOWN"},indent=2))

# trigger
