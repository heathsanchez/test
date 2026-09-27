#!/usr/bin/env python3
"""Crystal joint squeeze: reverse height barrier -> q/source lower bound at hard first crossing.

If hard first crossing has y>=L*n from reverse no-exit and 3(y-n)<q,
then q > 3(L-1)n. Compile the exact finite Q14 barrier ratios into exact
q/n threshold classes. This is a consequence compiler, not a global proof.
"""
from fractions import Fraction
from collections import Counter
import json
from collatz_reverse_predecessor_tree import enumerate_first_contractions

Q=14; M=3**Q
certs=enumerate_first_contractions(Q)
bar=[Fraction(1,1) for _ in range(M)]
for c in certs:
    L=Fraction(c.d,c.a)
    for r in range(c.residue,M,c.d):
        if L>bar[r]: bar[r]=L
thr=[3*(L-1) for L in bar]
hard=Counter(thr[r] for r in range(1,M,3))
# Classes impossible under the conditional regime q<=n are thresholds >=1
impossible_q_le_n=sum(n for t,n in hard.items() if t>=1)
print(json.dumps({
 "schema":"COLLATZ_HARD_CROSSING_Q_SOURCE_SQUEEZE_Q14_V0",
 "Q":Q,"modulus":M,
 "hard_mod3_1_thresholds":[{"q_over_n_strict_lower":[t.numerator,t.denominator],"count":n}
                          for t,n in sorted(hard.items(),key=lambda z:z[0])],
 "hard_total":M//3,
 "conditional_q_le_n_impossible":impossible_q_le_n,
 "conditional_q_le_n_survivors":M//3-impossible_q_le_n,
 "max_q_over_n_lower":[max(thr).numerator,max(thr).denominator],
 "law":"Hard + reverse barrier L implies q > 3*(L-1)*n via 3*(y-n)<q",
 "global_collatz":"UNKNOWN"},indent=2))
