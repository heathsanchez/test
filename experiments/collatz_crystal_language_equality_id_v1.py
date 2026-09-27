#!/usr/bin/env python3
"""Identify equality credit with live-language zero-terminal phases.

Exact identities:
 F[j+1]+H[j+1]=2F[j].
 For b=1, normalized equality with no source loss is controlled by H and the
 floor(6j/125) phase. Audit equivalence on a long symbolic range and expose the
 remaining fixed-origin source-hit statement.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts
DEPTH=10000
q,F,H=language_counts(DEPTH)
zero=[]; phasepay=[]; mismatch=[]
for j in range(1,DEPTH):
 # envelope one-step multiplier target: (F[j+1]/F[j])*2^(floor6diff-1)
 d=(6*(j+1))//125-(6*j)//125
 # equality factor =1 iff F[j+1]*2^d == 2*F[j]
 eq=(F[j+1]*(2**d)==2*F[j])
 z=(H[j+1]==0)
 if z:zero.append(j)
 if eq:phasepay.append(j)
 if z!=eq:mismatch.append({"j":j,"Hnext":H[j+1],"phasejump":d})
result={"schema":"COLLATZ_CRYSTAL_LANGUAGE_EQUALITY_ID_V1",
 "depth":DEPTH,"zero_terminal_phases":len(zero),"one_step_equality_phases":len(phasepay),
 "equivalence_mismatches":len(mismatch),"first_mismatches":mismatch[:20],
 "identity":"F[j+1]+H[j+1]=2F[j]",
 "residual_if_equivalent":"At the next H>0 opportunity after an equality phase, prove the fixed-origin source window loses positive mass C>0 within a finite adaptive block.",
 "warning":"This is fixed-origin anti-concentration; translation-uniform phase-blind closure was already rejected by V12.",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
