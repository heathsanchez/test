#!/usr/bin/env python3
"""Crystal residual cycle: universal post-equality source-hit structure.

Do not enlarge depth to claim universality.  Starting from the warranted local
identity, inspect the exact language/source events that make the next hit occur
and quotient them by the smallest phase/carry description.  Emit either a
counterexample, a finite-state recurrence candidate, or the irreducible
fixed-origin theorem obligation.
"""
from __future__ import annotations
import json
from collections import Counter,defaultdict
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
q,F,H=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
 z=first_crossing(n,q)
 if z:hist[z[0]][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
 for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
 P[0][m]=1<<(m-1)
 for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]
def phasejump(j):return (6*(j+1))//125-(6*j)//125

# Exact equality states from the proved algebraic characterization.
states=[]
for j in range(60,DEPTH-1):
 if H[j+1] or phasejump(j):continue
 for m in range(1,BITS+1):
  if P[j][m] and C[j+1][m]==0:states.append((j,m))

cycles=[]
# C1 find the actual first hit and classify by the unrestricted language event.
rows=[];miss=[]
for j,m in states:
 hit=None
 for t in range(j+2,DEPTH+1):
  if C[t][m]>0:
   hit=t;break
 if hit is None:miss.append((j,m));continue
 rows.append({"j":j,"m":m,"wait":hit-(j+1),"hit":hit,
              "phase0":j%125,"hit_phase":(hit-1)%125,
              "Hhit":H[hit],"qmin_jump":q[hit]-q[hit-1],
              "C":C[hit][m]})
cycles.append({"cycle":1,"capability":"EXACT_FIRST_POST_EQUALITY_HIT",
 "states":len(states),"hits":len(rows),"misses":len(miss),
 "max_wait":max((r["wait"] for r in rows),default=None),"first_miss":miss[:20]})

# C2 consequential quotient: which small observables determine the wait on the
# realized set? Refine phase -> phase+qminjump pattern -> m only if required.
def audit(key):
 g=defaultdict(set)
 for r in rows:g[key(r)].add(r["wait"])
 return len(g),sum(len(v)>1 for v in g.values()),max((len(v) for v in g.values()),default=0)
audits={
 "phase":audit(lambda r:(r["phase0"],)),
 "phase_m":audit(lambda r:(r["phase0"],r["m"])),
 "phase_hitphase":audit(lambda r:(r["phase0"],r["hit_phase"])),
 "phase_m_hitphase":audit(lambda r:(r["phase0"],r["m"],r["hit_phase"]))
}
cycles.append({"cycle":2,"capability":"MINIMUM_HIT_QUOTIENT","audits":audits})

# C3 identify whether source hit coincides with an unrestricted language
# terminal opportunity H>0. If every actual hit has H>0, language availability
# is necessary in the observed set; fixed-origin realization remains the issue.
badH=[r for r in rows if r["Hhit"]<=0]
wait_hist=Counter(r["wait"] for r in rows)
phase_wait=Counter((r["phase0"],r["wait"]) for r in rows)
cycles.append({"cycle":3,"capability":"LANGUAGE_TO_ORIGIN_BRIDGE",
 "hit_with_H_zero":len(badH),"first_bad":badH[:20],
 "wait_hist":dict(wait_hist),
 "phase_wait_top":[{"phase":k[0],"wait":k[1],"count":v} for k,v in phase_wait.most_common(30)]})

if miss:
 status="BOUNDED_COUNTEREXAMPLE"; residual={"name":"POST_EQUALITY_HIT_MISS","examples":miss[:20]}
elif badH:
 status="SEPARATOR_REQUIRED"; residual={"name":"SOURCE_HIT_WITHOUT_LANGUAGE_TERMINAL","examples":badH[:20]}
else:
 status="BOUNDED_BRIDGE_PATTERN"; residual={
  "name":"FIXED_ORIGIN_TERMINAL_REALIZATION",
  "statement":"after an equality phase, prove that a future legal-language terminal cylinder intersects the fixed-origin source interval before the adaptive contraction deadline",
  "warning":"translation-uniform/Fourier-magnitude closure is already formally obstructed; proof must use origin-sensitive canonical source/carry structure",
  "bounded_max_wait":max((r["wait"] for r in rows),default=None),
  "next":"derive an origin-sensitive congruence/interval lemma for canonical source residues at the next H>0 opportunities; reject phase-only claims if quotient audit conflicts"}

print(json.dumps({"schema":"COLLATZ_CRYSTAL_POST_EQUALITY_SOURCE_HIT_V1",
 "cycles":cycles,"status":status,"residual":residual,"global_collatz":"UNKNOWN"},indent=2))
