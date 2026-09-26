#!/usr/bin/env python3
"""Exact arithmetic certificate for eliminating terminal lift carry e=1.

Mathematical inputs already present in the Collatz ledger:
  P14/P16: B(w) <= B*(j) and E*=B*/2^j <= q/4 <= j/4.
  Rhin lower bound (also used in P20):
      D=2^j-3^q > 2^j/(3*j^13.3).
  P36: every feasible class through j=447 has globally negative maximum M.

For e=1 at terminal depth j, canonical R >= 2^(j-1). Thus
  M = B-D*R <= B-D*2^(j-1).
For j>=95 the two analytic bounds imply D*2^(j-1)>2^j*j/4>=B.

The only numerical inequality with decimal exponent is certified exactly by
raising to the 10th power:
  2^(j+1) > 3*j^14.3
iff
  2^(10(j+1)) > 3^10*j^143.
Monotonicity follows from 2^10*j^143 > (j+1)^143 at j=95, whose LHS/RHS
ratio only increases with j.

This script certifies those integer inequalities. It does not independently
reprove P16, P36, or Rhin.
"""
import json
J0=95
base = 2**(10*(J0+1)) > 3**10 * J0**143
mono = 2**10 * J0**143 > (J0+1)**143
assert base and mono
assert J0 <= 447
result={
 "schema":"COLLATZ_TERMINAL_CARRY1_ELIMINATION_V0",
 "asymptotic_start":J0,
 "exact_power10_base_inequality":base,
 "exact_ratio_monotonicity_at_start":mono,
 "finite_coverage_through":447,
 "finite_authority":"P36 global negative M maxima for every certified feasible class through j=447",
 "analytic_inputs":[
   "P14/P16: B <= B* <= 2^j*j/4",
   "Rhin: D > 2^j/(3*j^13.3)"
 ],
 "conclusion":"terminal lift carry e=1 implies M<0 for every feasible class, conditional on the cited P16/P36/Rhin authorities",
 "residual":"any hypothetical M>=0 first-crossing cylinder must have terminal lift carry e=0",
 "next":"derive the zero-carry parent recursion: R is unchanged and terminal Y is preterminal Y/2, so M>=0 iff preterminal Y>=2R",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
