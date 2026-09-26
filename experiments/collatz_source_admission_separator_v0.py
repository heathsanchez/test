#!/usr/bin/env python3
"""Falsify 'coefficient persistence alone determines the endpoint 3^20 cell'.

Construct two abstract parity-count schedules with the same first contraction
(t1,q1):
  EARLY: all q1 odd steps occur first, then all even;
  LATEST: the already-certified latest-odd mechanical suffix.
EARLY satisfies the coefficient inequalities because q ln3 is still above
(t-1) ln2 but below t ln2. The two schedules compile different endpoint
residues mod 3^20. Therefore coefficient-count persistence alone cannot be the
missing source-admission binding; the small-source/parity-realizability
constraint is consequential.

This is a symbolic count/suffix falsifier, not a claim that the EARLY schedule
has a source in the live <2^72 interval.
"""
import json
import collatz_transfer_farey as f
import collatz_reverse_trit_separator_v0 as v0

T=f.t1;Q=f.q1;B=20;P=3**B
# Exact rational log bounds certify:
# q ln3 < t ln2 and q ln3 > (t-1) ln2.
assert f.eps1_lo>0
assert f.eps1_hi < f.ln2_lo

acts,cums,positions=v0.extremal_reverse_actions(B)
latest_residue=v0.terminal_residue(tuple(acts))

# EARLY's last 20 odd positions are Q-20,...,Q-1.
last=list(range(Q-B,Q))
A=0
for j in last:
    A=(3*A+pow(2,j,P))%P
early_residue=A*pow(pow(2,T,P),-1,P)%P
assert early_residue!=latest_residue

result={
 "schema":"COLLATZ_SOURCE_ADMISSION_SEPARATOR_V0",
 "same_first_contraction":{"t":T,"q":Q},
 "early_schedule":{
   "coefficient_persistent_through_t_minus_1":True,
   "contracts_at_t":True,
   "last20_first":last[0],"last20_last":last[-1],
   "endpoint_residue_mod_3pow20":early_residue
 },
 "latest_mechanical_schedule":{
   "reverse_actions":acts,
   "endpoint_residue_mod_3pow20":latest_residue
 },
 "separator":"endpoint residue mod 3^20 differs",
 "conclusion":"coefficient-count persistence alone does not determine the protected endpoint trit cell",
 "missing_condition":"small-source (<2^72) parity-word realizability / exact source admission",
 "scope":"abstract parity-count schedules; EARLY is not asserted to have a live source below 2^72",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
