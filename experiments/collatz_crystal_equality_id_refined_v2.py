#!/usr/bin/env python3
"""Refined exact identity for one-step normalized equality.

From F[j+1]+H[j+1]=2F[j], normalized one-step equality requires H[j+1]=0
and no +1 jump in floor(6j/125). Verify equivalence symbolically.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts
DEPTH=20000
_,F,H=language_counts(DEPTH)
bad=[]
for j in range(1,DEPTH):
 d=(6*(j+1))//125-(6*j)//125
 eq=(F[j+1]*(2**d)==2*F[j])
 rhs=(H[j+1]==0 and d==0)
 if eq!=rhs:bad.append({"j":j,"H":H[j+1],"d":d})
result={"schema":"COLLATZ_CRYSTAL_EQUALITY_ID_REFINED_V2","depth":DEPTH,
 "mismatches":len(bad),"first":bad[:20],
 "candidate_theorem":"one-step normalized equality iff H[j+1]=0 and phasejump=0",
 "proof":"F[j+1]+H[j+1]=2F[j]; phasejump d in {0,1}",
 "status":"SYMBOLIC_IDENTITY_CANDIDATE" if not bad else "SEPARATOR_REQUIRED",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
