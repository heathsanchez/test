#!/usr/bin/env python3
"""Exact arithmetic handoff from the now-covered first Farey rung to rung 2.

External premise boundary:
  Ansari 2025 Proposition 3.2 + Barina verified base imply convergence through
  V = 4*3^44+2.
This script does not prove that external premise. It verifies its numerical
coverage of rung 1 and derives exact rational rung-2 coefficient/gap bounds
using the already-qualified log enclosures and the coarse intercept bound
A/3^q < q/3.

No global Collatz claim.
"""
from fractions import Fraction
import json
import collatz_transfer_farey as f

V=4*3**44+2
U1=f.dk_live_ceiling_int
assert V>U1

# q1/t1 is the first live lower mediant. The same upper Farey neighbor remains.
q1,t1=f.q1,f.t1
qu,tu=f.qu,f.tu
assert qu*t1-q1*tu==1

# Next lower mediant; Farey determinant certifies no fraction strictly between
# q1/t1 and qu/tu has denominator below t2.
q2,t2=q1+qu,t1+tu
assert (q2,t2)==(137_528_045_312,217_976_794_617)
assert Fraction(q1,t1)<Fraction(q2,t2)<f.alpha_lo
assert f.alpha_hi<Fraction(qu,tu)
assert qu*t2-q2*tu==1

eps2_lo=t2*f.ln2_lo-q2*f.ln3_hi
eps2_hi=t2*f.ln2_hi-q2*f.ln3_lo
assert 0<eps2_lo<eps2_hi

# Coarse exact intercept bound from the qualified transfer argument:
# A/3^q < q/3. Therefore a surviving first contraction at rung 2 must have
# n < q/(3*epsilon).
rescue_hi=Fraction(q2,1)/(3*eps2_lo)
U2=(rescue_hi.numerator+rescue_hi.denominator-1)//rescue_hi.denominator
assert U2>V

# For any n>=V surviving rung 2:
# delta <= q/3 - epsilon*n <= q/3-eps_lo*V.
gap_hi=Fraction(q2,3)-eps2_lo*V
assert gap_hi>0
G2=(gap_hi.numerator+gap_hi.denominator-1)//gap_hi.denominator
assert 3**22 < G2 < 3**23
assert 2**35 < G2 < 2**36

result={
 "schema":"COLLATZ_FAREY_RUNG2_HANDOFF_V0",
 "external_premise":{
   "verified_through":V,
   "source":"Ansari 2025 Prop 3.2 applied to Barina 2^71 base",
   "status":"EXTERNAL_PREMISE_NOT_FORMALIZED_HERE"
 },
 "rung1":{"rescue_ceiling":U1,"covered_by_external_premise":V>U1},
 "rung2":{
   "q":q2,"t":t2,"rescue_ceiling_coarse":U2,
   "live_lower":V,"near_return_gap_coarse":G2,
   "first_injective_q3_depth":23,
   "first_injective_q2_depth":36
 },
 "farey_boundary":{
   "lower":[q1,t1],"upper":[qu,tu],"next_mediant":[q2,t2],
   "determinant":1
 },
 "source_admission":{
   "necessary_language":"Ansari recursively-sufficient intersection F",
   "form":"n=4*z+3 where z has finite base-3 expansion using only digits 0,1",
   "reason":"a minimal bad source outside F has a lower merge by recursive sufficiency"
 },
 "next_cycle":"compile F source trits directly into the rung-2 reverse-trit/near-return quotient",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
