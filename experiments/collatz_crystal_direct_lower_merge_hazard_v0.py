#!/usr/bin/env python3
"""Crystal: test direct inverse-odd lower-merge hazard on hard stationary survivors."""
import json
from collatz_live_origin_bridge_v1 import language_counts
BITS=24; DEPTH=2000
qmin,_,_=language_counts(DEPTH)
records=[13421671,14378779,8088063,12132095,9280639,13774695,1126015,2252031,1689023,6206655]
def audit(n):
    y=n;q=0; first_merge=None; cross=None; min_ratio_num=None
    for j in range(1,DEPTH+1):
        bit=y&1
        if bit:y=(3*y+1)//2;q+=1
        else:y//=2
        if first_merge is None and y%3==2:
            p=(2*y-1)//3
            assert (3*p+1)//2==y
            if 0<p<n:first_merge={"j":j,"y":y,"p":p,"gap":n-p}
        if q<qmin[j]:
            cross=j;break
    return {"n":n,"crossing":cross,"first_direct_lower_merge":first_merge,
            "merge_before_cross": first_merge is not None and (cross is None or first_merge["j"]<cross)}
hard=[audit(n) for n in records]
# deterministic broad odd sample
sample=[]; step=max(1,(1<<BITS)//200000)
for n in range(3,1<<BITS,2*step):
    a=audit(n|1)
    if a["crossing"] and a["crossing"]>=n.bit_length(): sample.append(a)
out={"schema":"COLLATZ_CRYSTAL_DIRECT_LOWER_MERGE_HAZARD_V0",
 "hard":hard,"sampled_stationary_live":len(sample),
 "sample_merge_before_cross":sum(x["merge_before_cross"] for x in sample),
 "sample_no_merge_before_cross":sum(not x["merge_before_cross"] for x in sample),
 "first_no_merge":[x for x in sample if not x["merge_before_cross"]][:20],
 "candidate":"eternal threshold-live fixed source must avoid y≡2 mod3 throughout source-relative band n<=y<(3n+1)/2",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
