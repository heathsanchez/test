#!/usr/bin/env python3
"""Crystal singleton residual: identify the last live source exactly.

For every equality-origin state with P=1, recover the unique odd source <2^m
having no coefficient crossing through j, then follow its actual crossing.
This turns aggregate origin misses into source-coupled singleton obligations.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
q,F,H=language_counts(DEPTH)
cross={}
for n in range(1,1<<BITS,2):
 z=first_crossing(n,q); cross[n]=z[0] if z else DEPTH+1
# P via exact condition cross>j
rows=[]
for m in range(1,BITS+1):
 sources=[n for n in range(1,1<<m,2)]
 for j in range(60,DEPTH-1):
  live=[n for n in sources if cross[n]>j]
  if len(live)!=1:continue
  n=live[0]
  # equality one-step requires it also survive j+1 and language equality condition
  d=(6*(j+1))//125-(6*j)//125
  if cross[n]>j+1 and H[j+1]==0 and d==0:
   z=first_crossing(n,q)
   rows.append({"j":j,"m":m,"source":n,"first_crossing":z[0] if z else None,
                "wait":(z[0]-j if z else None),"endpoint":z[1] if z else None,
                "descending":(z[1]<n if z else None)})
uniq=sorted(set(r["source"] for r in rows))
result={"schema":"COLLATZ_CRYSTAL_SINGLETON_RESIDUAL_V1","states":len(rows),
 "unique_sources":uniq,"source_count":len(uniq),
 "max_wait":max((r["wait"] for r in rows if r["wait"] is not None),default=None),
 "unresolved":sum(r["first_crossing"] is None for r in rows),
 "nondescending_crossings":[r for r in rows if r["descending"] is False][:30],
 "first_rows":rows[:40],
 "candidate":"singleton aggregate residual reduces to finitely many actual source-coupled trajectories in this bounded window",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
