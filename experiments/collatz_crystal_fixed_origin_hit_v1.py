#!/usr/bin/env python3
"""Fixed-origin hit residual after an equality step.

For each realized one-step equality state, find the first subsequent depth t
with unrestricted terminal mass H[t]>0 and no envelope phase-jump obstruction;
test whether the fixed-origin window has C[t][m]>0 there. Emit misses and waiting.
Bounded discovery; a miss is a separator, not a refutation of Collatz.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
q,F,H=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,q)
 if z:hist[z[0]][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
# P conservation
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
def phasejump(j):return (6*(j+1))//125-(6*j)//125
states=[];miss=[];waits=[]
for j in range(60,DEPTH-1):
 if not (H[j+1]==0 and phasejump(j)==0):continue
 for m in range(1,BITS+1):
  if not P[j][m] or P[j+1][m]!=P[j][m]:continue
  states.append((j,m))
  found=None
  for t in range(j+2,DEPTH+1):
   if H[t]>0 and phasejump(t-1)==0:
    if C[t][m]>0:found=t;break
  if found is None:miss.append({"j":j,"m":m})
  else:waits.append(found-(j+1))
result={"schema":"COLLATZ_CRYSTAL_FIXED_ORIGIN_HIT_V1",
 "equality_origin_states":len(states),"misses":len(miss),"first_misses":miss[:20],
 "max_wait_to_eligible_positive_origin_hit":max(waits,default=None),
 "candidate":"after zero-terminal/no-phasejump equality, a later eligible language terminal event hits the fixed-origin live window",
 "status":"BOUNDED_FIXED_ORIGIN_HIT" if not miss else "ORIGIN_SEPARATOR_REQUIRED",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
