#!/usr/bin/env python3
"""Crystal: compile reverse EXIT certificates into necessary height barriers.

For each residue y mod 3^Q, all applicable first-contraction certificates imply
a*y >= d*n+c on a no-OrdinaryExit minimal-bad orbit.  We retain the strongest
asymptotic ratio d/a and report its residue kernel.  This is an exact capability
compilation; the finite Q bank is not universal.
"""
from fractions import Fraction
from collections import Counter,defaultdict
import json
from collatz_reverse_predecessor_tree import enumerate_first_contractions
Q=14; M=3**Q
certs=enumerate_first_contractions(Q)
# For each residue class 0..M-1, strongest ratio d/a among applicable certs.
best=[Fraction(1,1) for _ in range(M)]
best_cert=[None]*M
for c in certs:
    ratio=Fraction(c.d,c.a)
    for r in range(c.residue,M,c.d):
        if ratio>best[r]:
            best[r]=ratio;best_cert[r]=(c.word,c.a,c.c,c.d,c.residue)
# compress ratio distribution on odd-relevant residues by mod3
dist=Counter(best)
hard=Counter(best[r] for r in range(1,M,3))
# Threshold counts useful for forward contradiction search.
thresholds={}
for num,den in [(3,2),(4,3),(5,4),(6,5),(9,8),(1,1)]:
    t=Fraction(num,den)
    thresholds[f"{num}/{den}"]=sum(1 for r in range(M) if best[r]>=t)
print(json.dumps({"schema":"COLLATZ_REVERSE_HEIGHT_BARRIER_Q14_V0",
 "Q":Q,"modulus":M,"certificates":len(certs),
 "distinct_height_ratios":len(dist),
 "hard_mod3_1_dist":[{"ratio":[x.numerator,x.denominator],"count":n} for x,n in hard.most_common()],
 "all_threshold_counts":thresholds,
 "max_ratio":[max(best).numerator,max(best).denominator],
 "max_ratio_residue":best.index(max(best)),
 "max_ratio_cert":best_cert[best.index(max(best))],
 "interpretation":"no-exit requires y/n at least d/a (plus positive c/(a*n)) on every applicable certificate residue",
 "global_collatz":"UNKNOWN"},indent=2))

# trigger
