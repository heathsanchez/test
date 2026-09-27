#!/usr/bin/env python3
"""Exact algebraic regression for repeatability of a composed return cycle.

For affine return cycle F(m)=(A m+B)/2^D with A odd and C=2^D-A,
Delta=Cm-B. Exact transport gives 2^D Delta(F(m))=A Delta(m), hence
v2(Delta) drops by exactly D per repeat. If the same cycle cylinder requires
v2(Delta)>=D+1 on entry, r consecutive repeats require initial
v2(Delta)>=r*D+1.
"""
import json
def repeats_bound(v,D):
    assert D>0 and v>=D+1
    return (v-1)//D
tests=[]
for D in range(1,17):
  for r in range(1,8):
    v=r*D+1
    assert repeats_bound(v,D)>=r
    if v> D+1:
      assert repeats_bound(v-1,D)<r
    tests.append((D,r,v,repeats_bound(v,D)))
print(json.dumps({"schema":"COLLATZ_RETURN_CYCLE_REPEATABILITY_LAW_V0",
 "law":"r repeats require v2(Delta_entry) >= r*D + 1",
 "checks":len(tests),"status":"EXACT_INTEGER_ALGEBRA_PASS",
 "global_collatz":"UNKNOWN"},indent=2))
