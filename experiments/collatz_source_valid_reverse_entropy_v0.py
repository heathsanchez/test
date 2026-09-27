#!/usr/bin/env python3
"""Crystal block-budget audit for source-valid reverse pruning.

This does NOT assume block independence.  It computes the exact nested survivor
fractions for target-directed reverse banks Q=1..14 and tests the candidate
submultiplicative entropy gain needed by the combined origin+reverse finish.
"""
import json,math
from collatz_reverse_target_audit import enumerate_target,coverage

rows=[]
prev=None
for Q in range(1,15):
    certs=enumerate_target(Q)
    tab,st=coverage(certs,Q)
    f=st["uncovered"]/st["total"]
    eps=-math.log2(f)/Q if f else float("inf")
    rows.append({"Q":Q,"covered":st["covered"],"total":st["total"],
                 "survivor_fraction":f,"entropy_gain_per_step":eps,
                 "certificates":len(certs)})
Q14=rows[-1]
delta=0.05004447281166946
eta_target=0.04
budget=delta+Q14["entropy_gain_per_step"]
print(json.dumps({"schema":"COLLATZ_SOURCE_VALID_REVERSE_ENTROPY_V0",
 "rows":rows,
 "q14_entropy_gain":Q14["entropy_gain_per_step"],
 "binary_legal_entropy_gap":delta,
 "combined_origin_distortion_budget_if_recursive":budget,
 "origin_candidate_eta":eta_target,
 "candidate_margin":budget-eta_target,
 "critical_note":"Q-level residue coverage is nested certificate-family evidence, not proof that 14-block pruning multiplies along one source-coupled path.",
 "global_collatz":"UNKNOWN"},indent=2))
