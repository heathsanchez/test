#!/usr/bin/env python3
"""Unified source-progress rank probe: predecessor gap + active-map 2-adic fuel.

For each prospective actual return endpoint, choose the frozen-bank legal inverse
with minimum source gap G=y-n. Let q=p/u be that map centre and E=u*m-p.
Use fuel=v2(E), the exact same-map resource already warranted in ROS.
Test lexicographic candidates on consecutive endpoints of a fixed source/anchor:
  (positive-part G, fuel) and (G, -fuel), while lower merge is terminal.
Emit first violations for Crystal refinement.
"""
import json
from collections import defaultdict
import collatz_crystal_global_map_bank_v1 as gb
BANK=gb.compile_bank(3,8191,160)
def v2(x):
 x=abs(x)
 if x==0:return 10**9
 k=0
 while x%2==0:k+=1;x//=2
 return k
rows=defaultdict(list)
for n in range(8193,32768,2):
 for r,c,m,k in gb.returns(n,200):
  best=None
  for (rr,q),old in BANK.items():
   if rr!=r:continue
   pred=gb.inv(old,m)
   if pred is None:continue
   y=(1<<r)*pred-1;g=y-n;p,u=q;E=u*m-p
   z={"n":n,"r":r,"k":k,"m":m,"gap":g,"q":list(q),"fuel":v2(E),"abs_defect":abs(E)}
   if best is None or (g,z["fuel"],z["abs_defect"])<(best["gap"],best["fuel"],best["abs_defect"]):best=z
  if best is not None:rows[(n,r)].append(best)
tests={
 "G_THEN_FUEL":lambda a,b:(max(b["gap"],-1),b["fuel"])<(max(a["gap"],-1),a["fuel"]),
 "G_THEN_NEGFUEL":lambda a,b:(max(b["gap"],-1),-b["fuel"])<(max(a["gap"],-1),-a["fuel"]),
 "FUEL_THEN_G":lambda a,b:(b["fuel"],max(b["gap"],-1))<(a["fuel"],max(a["gap"],-1)),
}
out={}
for name,fn in tests.items():
 good=0;bad=[]
 for key,xs in rows.items():
  xs.sort(key=lambda x:x["k"])
  for a,b in zip(xs,xs[1:]):
   if a["gap"]<0:continue
   if b["gap"]<0 or fn(a,b):good+=1
   elif len(bad)<30:bad.append({"key":list(key),"a":a,"b":b})
 out[name]={"strict_or_exit":good,"violations":len(bad),"first":bad}
print(json.dumps({"schema":"COLLATZ_CRYSTAL_UNIFIED_GAP_FUEL_V1","tests":out,
 "note":"fuel is exact active-centre v2 defect; same-map repetition consumes it, switches may recharge",
 "global_collatz":"UNKNOWN"},indent=2))
