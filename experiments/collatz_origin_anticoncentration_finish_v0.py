#!/usr/bin/env python3
"""Archive-synthesis implication: weak origin anti-concentration closes P28.

This does NOT prove the missing anti-concentration hypothesis. It certifies that
a much weaker theorem than full mixing is sufficient after the new source-product
reduction.
"""
import json, math
alpha=math.log(2)/math.log(3)
def H(p): return -p*math.log2(p)-(1-p)*math.log2(1-p)
assert max(H(alpha-.002),H(alpha+.002),H(alpha)) < .952
eta=.04
gap=1-.952-eta
assert gap>.007999
J=None
for j in range(500,200000):
    if 15*math.log2(j)-gap*j < 0:
        J=j;break
assert J is not None
result={
 "schema":"COLLATZ_ORIGIN_ANTICONCENTRATION_FINISH_IMPLICATION_V0",
 "alpha":alpha,
 "binary_entropy_at_alpha":H(alpha),
 "entropy_loss_bits_per_step":1-H(alpha),
 "safe_entropy_upper_for_j_ge_500":.952,
 "sufficient_origin_distortion_exponent":eta,
 "net_exponential_decay":gap,
 "coarse_integer_threshold_using_X_lt_j^15":J,
 "hypothesis":"C_j(X) <= 2^(0.04 j) * |L_j| * X / 2^j for X=(3/4)j^14.3 eventually",
 "conclusion":"then C_j((3/4)j^14.3)=0 eventually, so P28 closes; combined with the qualified canonical M/source-product spine this excludes the remaining first-crossing counterexample class",
 "not_proved":"the origin anti-concentration/distortion hypothesis itself",
 "archive_join":[
   "P4-P8 exact legal Fourier/cancellation/majorant line",
   "Machine-Insight origin pushforward/carry line",
   "P28 polynomial seed cap",
   "September Lean source-product -> canonical M>=0 -> u=0/n=R reduction"
 ],
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
