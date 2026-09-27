#!/usr/bin/env python3
"""Crystal singleton theorem falsifier across exact source windows.

Test the candidate:
  P_j(2^m)=1 -> the unique live source's first coefficient crossing descends.
Search all singleton live windows in the exact bounded corpus, not just equality
states. Emit first nondescending or unresolved source as separator.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
q,F,H=language_counts(DEPTH)
data=[]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,q); data.append((n,z))
bad=[];states=0;uniq=set();maxwait=0
for m in range(1,BITS+1):
 pool=[(n,z) for n,z in data if n < (1<<m)]
 # crossing depth DEPTH+1 if unresolved
 for j in range(1,DEPTH):
  live=[(n,z) for n,z in pool if z is None or z[0]>j]
  if len(live)!=1:continue
  states+=1;n,z=live[0];uniq.add(n)
  if z is None:
   bad.append({"m":m,"j":j,"source":n,"kind":"unresolved"});continue
  maxwait=max(maxwait,z[0]-j)
  if n != 1 and z[1]>=n:
   bad.append({"m":m,"j":j,"source":n,"kind":"nondescending","crossing":z})
result={"schema":"COLLATZ_CRYSTAL_SINGLETON_THEOREM_FALSIFIER_V1",
 "singleton_states":states,"unique_sources":len(uniq),"max_wait":maxwait,
 "violations":len(bad),"first_violations":bad[:30],
 "candidate":"P_j(2^m)=1 implies unique live source has terminal exit or finite descending first coefficient crossing",
 "status":"BOUNDED_SINGLETON_LAW" if not bad else "SINGLETON_SEPARATOR_REQUIRED",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
