#!/usr/bin/env python3
"""Audit ten candidate Collatz bridge lemmas against qualified exact evidence.

This is a falsifier/triage gate. It does not prove Collatz.
"""
import json
import collatz_symbolic_frontier as sf
import collatz_reverse_trit_separator_v0 as v0
import collatz_reverse_trit_bicell_v1 as v1
import collatz_transfer_farey as farey

T=farey.t1
G=farey.live_gap_ceiling
U=farey.dk_live_ceiling_int
assert T==114_208_327_604
assert U < 2**72
assert G==4_142_380_787

# At the first live resonance the universal source-product common tail is zero:
# floor(n/2^T)=0 for every live n<=U.
assert T > 72

# Depth-20 endpoint prefix information plus the gap still cannot constrain
# source residues: every delta class mod 2^20 occurs inside [0,G].
assert G >= 2**20-1

# Exact coefficient-persistence source-prefix language through depth 20.
_,src_residual,_=sf.compile_frontier(20)
sf.verify_cover(*sf.compile_frontier(20)[:2])
source_count=len(src_residual)
assert source_count==27328

# Re-run the exact reverse-trit first-difference and one-Q2-bit audits.
acts,_,_=v0.extremal_reverse_actions()
v0_rows=[]
v0_closed=0
for j in range(1,v0.DEPTH+1):
    qj=v0.terminal_residue(tuple(acts[:j]))
    base=qj%(3**(j-1)) if j>1 else 0
    qdigit=(qj//(3**(j-1)))%3
    for digit in range(3):
        if digit==qdigit: continue
        r=base+digit*3**(j-1)
        cert=v0.best_contracting_prefix(r,j)
        v0_closed += cert is not None
        v0_rows.append((j,r,cert is not None))
assert (len(v0_rows),v0_closed)==(40,12)

v1_cells=0; v1_closed=0
for j,r,direct_closed in v0_rows:
    for parity in (0,1):
        v1_cells+=1
        if direct_closed or r%3==0 or v1.one_step_reverse_cert(r,j,parity) is not None:
            v1_closed+=1
assert (v1_cells,v1_closed,v1_cells-v1_closed)==(80,53,27)

# Frozen qualified V3 depth-20 authority: run 36211158868,
# artifact sha256:629c874e...; all 27 Q3 parents share one language.
endpoint_depth20_count=15870
assert endpoint_depth20_count>0

routes=[
 {"id":1,"name":"SOURCE_LANGUAGE_EQUALS_V3","status":"REJECTED_AS_STATED",
  "reason":"source and endpoint prefixes live at different times; at resonance common tail is already zero; source depth-20 persistence count 27328 vs V3 endpoint count 15870"},
 {"id":2,"name":"EMPTY_OFF_DIAGONAL_FIBER_FROM_GAP","status":"REJECTED_FROM_CURRENT_PREMISES",
  "reason":"G >= 2^20-1, so the gap permits every source residue mod 2^20"},
 {"id":3,"name":"GAP_PLUS_BIADIC_DIVISIBILITY","status":"CANDIDATE",
  "reason":"would close by squeeze, but required divisibility of y-n is not supplied by common-tail cells"},
 {"id":4,"name":"TWENTY_TRIT_ADMISSION","status":"REJECTED_AS_UNCONDITIONAL",
  "reason":"exact V0 closes only 12/40 arbitrary first-difference Q3 cylinders"},
 {"id":5,"name":"SOURCE_ADMISSIBLE_FIRST_DIFFERENCE_MERGES","status":"CANDIDATE_PRIMARY",
  "reason":"V1 leaves exactly 27 bicells; proving source admission excludes/closes them would discharge the live first-resonance residual"},
 {"id":6,"name":"FINITE_SOURCE_FUTURE_QUOTIENT","status":"CANDIDATE",
  "reason":"needs a universal source-admission quotient; current depth-20 source persistence language remains nonempty"},
 {"id":7,"name":"UNIQUE_COMMON_TAIL_LIFT","status":"REJECTED_AT_RESONANCE",
  "reason":"T>72 while every live source <2^72, hence the common tail is identically zero"},
 {"id":8,"name":"SOURCE_ENDPOINT_LANGUAGE_INCOMPATIBILITY","status":"CANDIDATE_REFORMULATION",
  "reason":"must use the full affine/source-admission relation, not equality/intersection of low-bit languages"},
 {"id":9,"name":"RESONANCE_PROGRESS_RANK","status":"CANDIDATE_GLOBAL",
  "reason":"exactly matches the checked kernel interface once source admission and successor preservation are earned"},
 {"id":10,"name":"NO_INFINITE_ADMISSIBLE_WORD","status":"CANDIDATE_MASTER",
  "reason":"compactness-style master form; finite depth 20 does not establish it because both exact source and endpoint residual languages are nonempty"}
]
result={
 "schema":"COLLATZ_TEN_BRIDGE_AUDIT_V0",
 "first_live_resonance":{"t":T,"live_seed_upper":U,"near_return_gap":G},
 "facts":{"common_tail_zero_before_resonance":True,"gap_saturates_mod_2pow20":True,
          "source_persistence_depth20":source_count,
          "v0_first_difference_closed":"12/40","v1_bicell_closed":"53/80",
          "v1_bicell_residual":27,"v3_endpoint_depth20":endpoint_depth20_count,
          "v3_q3_parent_languages":1},
 "routes":routes,
 "smallest_live_residual":"SOURCE_ADMISSIBLE_FIRST_DIFFERENCE_MERGES",
 "master_reformulation":"NO_INFINITE_SOURCE_ADMISSIBLE_OFF_DIAGONAL_WORD",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
