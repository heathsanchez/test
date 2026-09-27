#!/usr/bin/env python3
"""Crystal deficit-one theorem probe.

At a first coefficient crossing q=qmin(d)-1. Test whether descent can be reduced
to a source-prefix bound on the affine intercept. Search all canonical crossing
cylinders to find nondescending deficit-one examples, then ask whether singleton
uniqueness excludes them by source rank within the cylinder.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
qmin,F,H=language_counts(DEPTH)
def aff(n,d):
 y=n;q=0;b=0
 for k in range(d):
  if y&1:b=3*b+(1<<k);q+=1;y=(3*y+1)//2
  else:y//=2
 return y,q,b
rows=[];hard=[];def1=0
for n in range(3,1<<BITS,2):
 z=first_crossing(n,qmin)
 if not z:continue
 d,y,_=z; yy,q,b=aff(n,d)
 if qmin[d]-q!=1:continue
 def1+=1
 if y>=n:
  hard.append({"n":n,"d":d,"y":y,"q":q,"b":b,
    "budget":((1<<d)-3**q)*n-b})
# exact singleton sources from all windows
cross={n:first_crossing(n,qmin) for n in range(1,1<<BITS,2)}
single=set()
for m in range(1,BITS+1):
 pool=[n for n in cross if n<(1<<m)]
 for j in range(1,DEPTH):
  live=[n for n in pool if cross[n] is None or cross[n][0]>j]
  if len(live)==1:single.add(live[0])
hardset={r["n"] for r in hard}
result={"schema":"COLLATZ_CRYSTAL_DEFICIT_ONE_V1",
 "deficit_one_crossings":def1,"nondescending_deficit_one":len(hard),
 "singleton_sources":sorted(single),"singleton_hard_intersection":sorted(single&hardset),
 "first_hard":hard[:30],
 "conclusion":("DEFICIT_ONE_ALONE_INSUFFICIENT" if hard else "DEFICIT_ONE_SUFFICIENT_BOUNDED"),
 "next":"if hard exists but singleton intersection empty, learn the minimum canonical-source uniqueness separator between hard deficit-one cylinders and singleton cylinders",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
