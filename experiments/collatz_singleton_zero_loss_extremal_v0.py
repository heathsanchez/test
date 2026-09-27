#!/usr/bin/env python3
"""Extract exact singleton zero-loss extremals and their forced terminating word."""
import json
from collatz_live_origin_bridge_v1 import language_counts, first_crossing
BITS=24; DEPTH=2000
qmin,_,_=language_counts(DEPTH)
# Find exact sources whose first crossing is 287 and the unique survivor at j=249.
rows=[]
for n in range(1,1<<BITS,2):
    z=first_crossing(n,qmin)
    if z is not None:
        d,y,q=z
        if d>=249:
            rows.append((d,n,y,q))
rows.sort(reverse=True)
surv=[r for r in rows if r[0]>249]
assert len(surv)==1, len(surv)
d,n,y,q=surv[0]
# Replay exact trajectory and parity/threshold slack from 249 through crossing.
v=n; oq=0; trace=[]
for j in range(1,d+1):
    bit=v&1
    if bit: v=(3*v+1)//2; oq+=1
    else: v//=2
    if j>=249:
        trace.append({"j":j,"bit":bit,"q":oq,"qmin":qmin[j],
                      "slack":oq-qmin[j],"y":v})
assert d==287
# Exact affine identity 2^j y = 3^q n + A_j.
A=(v*(1<<d))-(3**oq)*n
out={"schema":"COLLATZ_SINGLETON_ZERO_LOSS_EXTREMAL_V0",
 "source_bits":BITS,"unique_source":n,"start_depth":249,"crossing_depth":d,
 "zero_loss_steps":d-249-1,"endpoint":y,"odd_count":q,
 "affine_additive_term":str(A),"trace":trace,
 "target":"derive impossibility of infinite legal extension from exact threshold/carry recurrence",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
