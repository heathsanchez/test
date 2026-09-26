#!/usr/bin/env python3
"""Compile the full local contracting chamber at the 12-odd / <=19-cost scale.

A reverse history becomes linearly contracting as soon as its first 12 odd
inverse steps consume S<=19 powers of two, since 2^19<3^12. Therefore it is
enough to enumerate all positive 12-part compositions with total cost 12..19.
This strictly contains the single 12/19 generator language.

The complement has an exact interpretation: no reverse history can accumulate
12 odd steps within total two-cost <=19 from that 3-adic context.
"""
from itertools import combinations
import json
O=12;MOD=3**O
def comps(total,parts):
    for cuts in combinations(range(1,total),parts-1):
        p=0;w=[]
        for c in cuts+(total,):w.append(c-p);p=c
        yield tuple(w)
def cocycle(w):
    C=0
    for i,a in enumerate(w):C=(1<<a)*C+3**i
    return C
A=set();shapes=0;byS={}
for S in range(12,20):
    AS=set()
    for w in comps(S,O):
        shapes+=1
        r=(cocycle(w)*pow(1<<S,-1,MOD))%MOD
        AS.add(r);A.add(r)
    byS[S]=len(AS)
domain={r for r in range(MOD) if r%3}
blocked=domain-A
# exclusion precision
mods={m:{r%(3**m) for r in A} for m in range(1,O+1)}
hist={}
for r in blocked:
    for m in range(1,O+1):
        if r%(3**m) not in mods[m]:
            hist[m]=hist.get(m,0)+1;break
result={
 "schema":"COLLATZ_FULL_LOCAL_CONTRACTING_CHAMBER_V0",
 "block_shapes":shapes,
 "unique_admissible_residues":len(A),
 "domain_nonzero_mod3":len(domain),
 "blocked":len(blocked),
 "coverage_fraction":len(A)/len(domain),
 "unique_by_total_cost":byS,
 "blocked_exclusion_precision_histogram":hist,
 "exact_blocked_meaning":"no reverse history reaches 12 odd inverse steps within total two-cost <=19",
 "consequence":"any reverse path staying in this blocked context has local odd-density strictly below 12/19 at the first 12 odds",
 "next":"test forward blocked-context recurrence using this full chamber; if recurrent, add exact canonical M register",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
