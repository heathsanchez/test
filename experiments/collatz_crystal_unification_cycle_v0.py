#!/usr/bin/env python3
"""Stateful unification cycle: exact M residual -> continued-fraction chamber bridge.

Reads the canonical campaign state.  It does not use superseded rung-2 coverage.
"""
import json
from pathlib import Path
import collatz_reverse_trit_separator_v0 as r

state=json.loads(Path("experiments/collatz_crystal_campaign_state_v1.json").read_text())
assert "joint margin" in state["canonical_residual"]

# Corrected recursive-sufficiency parity sieve is redundant on any prefix that
# is still above the coefficient boundary: 2^485 > 3^306 proves
# 306/485 < log(2)/log(3).
assert 2**485 > 3**306

# The old P39/P40 chamber generators are the two consecutive rational scales
# around beta=log(3)/log(2).
assert 2**19 < 3**12       # 19/12 < beta; reverse 2^19/3^12 is subunit
assert 3**5 < 2**8         # beta < 8/5; reverse 2^8/3^5 is superunit
assert 8*12 - 19*5 == 1    # Farey-neighbor / unimodular basis

acts,_,_=r.extremal_reverse_actions(20)
# Exact finite bridge into the current reverse mechanical word.
five=[]
twelve=[]
for i in range(len(acts)-5+1):
    if sum(acts[i:i+5])==8: five.append(i)
for i in range(len(acts)-12+1):
    if sum(acts[i:i+12])==19: twelve.append(i)
assert len(five)==15
assert len(twelve)==8

# The first 20 odd events tile into four superunit 5/8 blocks, while overlapping
# 12/19 subunit blocks exist but require the right 3-adic legality context.
assert all(sum(acts[i:i+5])==8 for i in (0,5,10,15))
assert 5 in twelve

result={
 "schema":"COLLATZ_CRYSTAL_UNIFICATION_CYCLE_V0",
 "input_residual":state["canonical_residual"],
 "reconciliations":{
   "corrected_RS_parity_sieve":"REDUNDANT_ON_NONCROSSING_PREFIX",
   "reason":"2^485 > 3^306",
   "superseded_rung2_handoff":"NOT_USED"
 },
 "continued_fraction_bridge":{
   "subunit_reverse_block":{"odd_steps":12,"two_cost":19,"factor":"2^19/3^12","windows_in_depth20":twelve},
   "superunit_reverse_block":{"odd_steps":5,"two_cost":8,"factor":"2^8/3^5","windows_in_depth20":five},
   "unimodular_determinant":1,
   "finite_current_word_actions":acts
 },
 "connection_to_august":{
   "P39":"the same exponent vectors generate the finite residual S-unit semigroup",
   "P40":"subunit vs superunit chamber is exactly the sign around the identity line",
   "P43_candidate":"survivor context blocks an available 12/19 subunit reverse block",
   "P44_boundary":"old 700-row success is discovery-only because that corpus was later audited M<0"
 },
 "next_exact_experiment":"on universal symbolic M>=0 cylinders, characterize the 3-adic legality condition for the 12/19 subunit block and test whether its failure necessarily advances context toward admissibility or a smaller M-cylinder",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
