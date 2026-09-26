#!/usr/bin/env python3
"""Stateful theorem certificate: a nondescending first crossing has zero common tail.

At depth j source-product normalization gives
  n = R + 2^j*u,  y = Y + 3^q*u,  D=2^j-3^q>0.
If y>=n then
  Y-R >= D*u,
so M=2^j(Y-R) >= 2^j*D*u.
Always M=B-D*R <= B. P14/P16 give B<=B*<=2^j*j/4 and Rhin gives
D>2^j/(3*j^13.3). For j>=94, exact arithmetic below certifies
  2^j > (3/4)*j^14.3,
hence B < 2^j*D. Therefore u>=1 is impossible.
P36 already gives M<0 for every certified feasible class through j=447, so
any hypothetical M>=0 class lies beyond the finite overlap.

This certificate does not independently reprove P16/P36/Rhin.
"""
import json
J0=94
base=2**(10*J0+20) > 3**10 * J0**143
mono=2**10 * J0**143 > (J0+1)**143
assert base and mono and J0<=447
result={
 "schema":"COLLATZ_FIRST_CROSSING_ZERO_TAIL_V0",
 "asymptotic_start":J0,
 "finite_negative_M_coverage_through":447,
 "exact_power10_inequality":base,
 "exact_monotonicity":mono,
 "theorem_shape":"first crossing + non-descent => common tail u=0 => actual source equals canonical residue R",
 "dependencies":["source-product normalization","P14/P16","P36","published Rhin bound"],
 "consequence":"the universal counterexample residual is exactly the canonical M>=0 cylinder problem; no separate source-admission layer remains",
 "next":"work only on canonical legal cylinders with zero terminal carry; derive a well-founded recursion on the preterminal doubling gap Y_parent-2R",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
