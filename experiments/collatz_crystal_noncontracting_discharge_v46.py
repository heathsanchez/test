#!/usr/bin/env python3
"""V46: compose maximal same-anchor noncontracting streak + first discharge.

Discovery/falsifier only. Uses the exact V41 31,104-source corpus. For each
source and episode anchor, consecutive same-anchor return maps form a chain.
Whenever one or more coefficient-noncontracting maps are followed by the first
coefficient-contracting map, compose the whole block exactly and ask whether
it lowers the anchor coordinate m. A streak terminated by an already-certified
ordinary exit is counted separately as closed. Open CAP tails are separators.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib,io,json
with redirect_stdout(io.StringIO()):
 import collatz_crystal_paradoxical_return_audit_v45 as v45
 import collatz_crystal_parameter_quotient_v25 as v25
 import collatz_crystal_phase_normalized_return_v40 as v40

LIVE=v45.LIVE; MOD3=v45.MOD3; MOTIFS=v45.MOTIFS
stats=Counter(); bad=[]; open_tail=[]; examples=[]

def compose(es):
 A,B,D=1,0,0
 for e in es:
  c=e["cert"]
  B=c["A"]*B+c["B"]*(1<<D)
  A=c["A"]*A
  D+=c["D"]
 return A,B,D

tested=0
for r in LIVE:
 for a3 in range(MOD3):
  for motif in MOTIFS:
   t=v45.crt_parameter(r,a3,motif); n=v25.N0+v25.NC*t
   rr=v40.actual_episode_returns(f"r{r}-a{a3}-{motif}",n,v45.CAP)
   tested+=1
   if rr["note"]=="ordinary exit before zero-tail": continue
   by=defaultdict(list)
   for e in rr["events"]: by[e["anchor"]].append(e)
   for anchor,es in by.items():
    es.sort(key=lambda z:(z["k0"],z["k1"]))
    # V40 events for a given anchor are successive same-anchor return epochs.
    for x,y in zip(es,es[1:]):
     assert x["k1"]<=y["k0"]
     if x["k1"]==y["k0"]: assert x["m1"]==y["m0"]
    i=0
    while i<len(es):
     c=es[i]["cert"]
     if c["A"] < (1<<c["D"]): i+=1; continue
     j=i
     while j+1<len(es) and es[j+1]["cert"]["A"] >= (1<<es[j+1]["cert"]["D"]):
      # only compose contiguous return epochs
      if es[j]["k1"]!=es[j+1]["k0"]: break
      j+=1
     stats["NONCONTRACTING_STREAKS"]+=1
     stats["NONCONTRACTING_EVENTS_IN_STREAKS"]+=j-i+1
     # First same-anchor contracting discharge, only if contiguous.
     if j+1<len(es) and es[j]["k1"]==es[j+1]["k0"] and es[j+1]["cert"]["A"] < (1<<es[j+1]["cert"]["D"]):
      block=es[i:j+2]
      A,B,D=compose(block)
      m0,m1=block[0]["m0"],block[-1]["m1"]
      assert A*m0+B==(1<<D)*m1
      C=(1<<D)-A
      row={"source":str(n),"t":str(t),"motif":motif,"anchor":anchor,
           "streak_len":j-i+1,"block_len":len(block),"depth":[block[0]["k0"],block[-1]["k1"]],
           "A":str(A),"B":str(B),"D":D,"m0":str(m0),"m1":str(m1),
           "slope_contracting":C>0,"actual_contracting":m1<m0}
      if C>0:
       fp=Fraction(B,C); row["fixed_point"]=[fp.numerator,fp.denominator]
       row["m0_above_fixed_point"]=m0>fp
      stats["DISCHARGE_BLOCKS"]+=1
      if m1<m0: stats["DISCHARGE_BLOCKS_CONTRACT_M"]+=1
      else:
       stats["DISCHARGE_BLOCKS_FAIL"]+=1
       if len(bad)<20: bad.append(row)
      if len(examples)<20: examples.append(row)
      i=j+2
     else:
      # If no next same-anchor discharge, an ordinary D/S/M exit after this
      # final return is a certified close; otherwise this is an open CAP tail.
      last=es[j]
      ex=rr["first_exit"]
      if ex is not None and ex["depth"]>=last["k1"]:
       stats["STREAKS_CLOSED_BY_ORDINARY_EXIT"]+=1
      else:
       stats["OPEN_NONCONTRACTING_TAILS"]+=1
       if len(open_tail)<20:
        open_tail.append({"source":str(n),"t":str(t),"motif":motif,"anchor":anchor,
         "streak_len":j-i+1,"depth":[es[i]["k0"],last["k1"]],
         "last_m":str(last["m1"]),"first_exit":ex})
      i=j+1

verdict=("NONCONTRACTING_DISCHARGE_SEPARATOR" if bad else
         "OPEN_NONCONTRACTING_TAIL_SEPARATOR" if open_tail else
         "ALL_OBSERVED_NONCONTRACTING_STREAKS_DISCHARGE_WITH_PROGRESS")
res={"schema":"COLLATZ_CRYSTAL_NONCONTRACTING_DISCHARGE_V46",
 "parents":{"V45":"collatz-crystal-paradoxical-return-audit-v45@6db3ed76d384af3623461e4db5b0d64f996d3768"},
 "tested_sources":tested,"stats":dict(sorted(stats.items())),
 "bad_blocks":bad,"open_tails":open_tail,"examples":examples,"verdict":verdict,
 "interpretation":"Tests eventual macro progress without predicting intermediate return state.",
 "promotion_boundary":"Bounded corpus only; QED requires a symbolic all-depth discharge theorem or exact separator.",
 "global_collatz":"UNKNOWN"}
res["certificate_sha256"]=hashlib.sha256(json.dumps(res,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(res,indent=2,sort_keys=True))
