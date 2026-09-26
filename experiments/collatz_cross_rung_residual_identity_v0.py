#!/usr/bin/env python3
"""Exact cross-rung comparison of intrinsic residual bicells."""
import json
import collatz_reverse_trit_bicell_v2 as first
import collatz_rung2_bicell_v1 as second
import collatz_rung2_reverse_trit_v0 as r2

r1=sorted((x["depth"],x["residue"],x["parity"]) for x in first.parent_residuals())

# Reconstruct rung2 V1 residuals without importing its top-level result.
acts,_=r2.reverse_actions(r2.DEPTH);centre=[];r2res=[]
for j in range(1,r2.DEPTH+1):
    qj=r2.terminal(tuple(acts[:j]))
    centre.append(qj);base=qj%(3**(j-1)) if j>1 else 0
    cd=(qj//(3**(j-1)))%3
    for alt in range(3):
        if alt==cd:continue
        rr=base+alt*3**(j-1);direct=r2.cert(rr,j)
        for parity in (0,1):
            closed=direct is not None or rr%3==0 or second.one_step(rr,j,parity) is not None
            if not closed:r2res.append((j,rr,parity))
prefix=sorted(x for x in r2res if x[0]<=20)
new=sorted(x for x in r2res if x[0]>20)
assert prefix==r1
assert len(r1)==27 and len(new)==4
result={
 "schema":"COLLATZ_CROSS_RUNG_RESIDUAL_IDENTITY_V0",
 "rung1_depth20_residuals":len(r1),
 "rung2_prefix_depth20_residuals":len(prefix),
 "exact_prefix_identity":True,
 "rung2_new_depth21_23":new,
 "rung2_total":len(r2res),
 "interpretation":"the intrinsic protected residual is a single extending language, not a rung-specific 27-cell family",
 "next_cycle":"compile the survivor language independently of Farey rung and intersect it with recursively-sufficient source admission",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
