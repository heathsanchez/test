#!/usr/bin/env python3
"""Crystal predecessor-gap residual.

For each actual return endpoint of prospective sources, apply the frozen global
map bank and record the minimum legal predecessor gap y-n. Protected consequence
is gap<0 (lower merge). Test whether best gap improves with endpoint depth and
whether a simple normalized gap is monotone across returns of one source/anchor.
"""
import json
from collections import defaultdict
import collatz_crystal_global_map_bank_v1 as gb

BANK=gb.compile_bank(3,8191,160)
rows=[]; by=defaultdict(list)
for n in range(8193,32768,2):
 for r,c,m,k in gb.returns(n,200):
  best=None;bestq=None
  for (rr,q),old in BANK.items():
   if rr!=r:continue
   p=gb.inv(old,m)
   if p is None:continue
   y=(1<<r)*p-1;gap=y-n
   if best is None or gap<best:best=gap;bestq=q
  if best is not None:
   row={"n":n,"r":r,"k":k,"m":m,"gap":best,"gap_over_n_num":best,
        "gap_over_n_den":n,"q":list(bestq)}
   rows.append(row);by[(n,r)].append(row)
trans=0;improve=0;viol=[]
for key,xs in by.items():
 xs.sort(key=lambda x:x["k"])
 for a,b in zip(xs,xs[1:]):
  trans+=1
  # exact normalized comparison b.gap/n < a.gap/n same n -> raw gap
  if b["gap"]<a["gap"]:improve+=1
  else:
   viol.append({"key":list(key),"a":a,"b":b})
neg=sum(x["gap"]<0 for x in rows);zero=sum(x["gap"]==0 for x in rows)
print(json.dumps({"schema":"COLLATZ_CRYSTAL_PREDECESSOR_GAP_V1",
 "rows":len(rows),"lower_merge_rows":neg,"zero_gap_rows":zero,
 "within_source_transitions":trans,"strict_gap_improvements":improve,
 "violations":len(viol),"first_violations":viol[:20],
 "best_positive_gaps":sorted([x for x in rows if x["gap"]>=0],key=lambda x:x["gap"])[:30],
 "candidate":"best legal bank predecessor gap as source-relative progress resource",
 "global_collatz":"UNKNOWN"},indent=2))
