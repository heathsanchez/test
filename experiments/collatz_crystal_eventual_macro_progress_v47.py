#!/usr/bin/env python3
"""V47: bounded eventual macro-progress audit on the full V41 challenge.

For every post-zero same-anchor return event, use the anchor coordinate m as
the candidate local rank. Contracting events close immediately. From a
noncontracting event, extend through subsequent *contiguous same-anchor return
epochs* until either:
  (a) the cumulative endpoint m falls below the starting m; or
  (b) an already-certified ordinary D/S/M exit occurs.
Anything still live at the horizon is emitted as an exact separator.

This tests the precise eventual-progress shape required by V37, but only on
the frozen 31,104-source adversarial corpus. It is not a universal theorem.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from contextlib import redirect_stdout
import hashlib,io,json
with redirect_stdout(io.StringIO()):
 import collatz_crystal_paradoxical_return_audit_v45 as v45
 import collatz_crystal_parameter_quotient_v25 as v25
 import collatz_crystal_phase_normalized_return_v40 as v40

stats=Counter(); seps=[]; longest=[]; tested=0
for r in v45.LIVE:
 for a3 in range(v45.MOD3):
  for motif in v45.MOTIFS:
   t=v45.crt_parameter(r,a3,motif); n=v25.N0+v25.NC*t
   rr=v40.actual_episode_returns(f"r{r}-a{a3}-{motif}",n,v45.CAP)
   tested+=1
   if rr["note"]=="ordinary exit before zero-tail": continue
   by=defaultdict(list)
   for e in rr["events"]: by[e["anchor"]].append(e)
   for anchor,es in by.items():
    es.sort(key=lambda z:(z["k0"],z["k1"]))
    for i,e in enumerate(es):
     stats["RETURN_STATES"]+=1
     if e["m1"]<e["m0"]:
      stats["IMMEDIATE_PROGRESS"]+=1
      continue
     stats["NONCONTRACTING_STARTS"]+=1
     start_m=e["m0"]; j=i; hit=None
     # Current event is already executed; inspect cumulative later epochs.
     if e["m1"]<start_m:
      hit=(j,e["m1"])
     else:
      while j+1<len(es) and es[j]["k1"]==es[j+1]["k0"]:
       j+=1
       if es[j]["m1"]<start_m:
        hit=(j,es[j]["m1"]); break
     if hit is not None:
      wait=hit[0]-i+1
      stats["EVENTUAL_M_PROGRESS"]+=1
      stats["TOTAL_WAIT_RETURNS"]+=wait
      row={"wait_returns":wait,"wait_depth":es[hit[0]]["k1"]-e["k0"],
           "source":str(n),"t":str(t),"motif":motif,"anchor":anchor,
           "depth":[e["k0"],es[hit[0]]["k1"]],"m0":str(start_m),
           "m_end":str(hit[1])}
      longest.append(row); longest.sort(key=lambda z:(z["wait_returns"],z["wait_depth"]),reverse=True)
      del longest[20:]
      continue
     # If the source exits after the last reachable epoch, it is still closed.
     last=es[j]
     ex=rr["first_exit"]
     if ex is not None and ex["depth"]>=last["k1"]:
      stats["CLOSED_BY_ORDINARY_EXIT"]+=1
      continue
     stats["OPEN_EVENTUAL_PROGRESS_SEPARATOR"]+=1
     if len(seps)<30:
      seps.append({"source":str(n),"t":str(t),"motif":motif,"anchor":anchor,
       "start_depth":e["k0"],"last_depth":last["k1"],"m0":str(start_m),
       "last_m":str(last["m1"]),"first_exit":ex,
       "events":[{"depth":[z["k0"],z["k1"]],"A":str(z["cert"]["A"]),
                  "B":str(z["cert"]["B"]),"D":z["cert"]["D"],
                  "m0":str(z["m0"]),"m1":str(z["m1"])}
                 for z in es[i:j+1]]})

verdict=("EVENTUAL_PROGRESS_SEPARATOR_FOUND" if seps else
         "ALL_OBSERVED_RETURN_STATES_HAVE_EVENTUAL_PROGRESS")
res={"schema":"COLLATZ_CRYSTAL_EVENTUAL_MACRO_PROGRESS_V47",
 "parent":"collatz-crystal-paradoxical-return-audit-v45@6db3ed76d384af3623461e4db5b0d64f996d3768",
 "tested_sources":tested,"stats":dict(sorted(stats.items())),
 "separators":seps,"longest_progress_waits":longest,"verdict":verdict,
 "interpretation":"Direct bounded audit of the V37 eventual-rank premise using same-anchor m plus certified exits.",
 "promotion_boundary":"No QED: universal source-independent progress remains unproved even if this frozen corpus is green.",
 "global_collatz":"UNKNOWN"}
res["certificate_sha256"]=hashlib.sha256(json.dumps(res,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(res,indent=2,sort_keys=True))
