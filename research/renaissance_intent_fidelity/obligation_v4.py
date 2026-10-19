#!/usr/bin/env python3
"""Exposed finite V4: separately compare premise and conclusion, not implication truth."""
from itertools import product
D=range(3); xs=list(product(D,repeat=4))
def ab(a,b,c,d):return a<=b
def cd(a,b,c,d):return c<=d
def zero(a,b,c,d):return a==0
def taut(a,b,c,d):return a==a
def conclusion(a,b,c,d):return a*c<=b*d
def reversed_(a,b,c,d):return b*d<=a*c
cases={
 "original":([ab,cd],conclusion,True),
 "swapped_premises":([cd,ab],conclusion,True),
 "missing_premise":([ab,ab],conclusion,False),
 "reversed_conclusion":([ab,cd],reversed_,False),
 "extra_premise":([ab,cd,zero],conclusion,False),
 "tautology":([ab,cd,taut],conclusion,True),
}
def signature(predicates):
    return tuple(all(p(*x) for p in predicates) for x in xs)
ref_pre=signature([ab,cd]); ref_con=signature([conclusion])
for name,(pre,con,expected) in cases.items():
    equal_pre=signature(pre)==ref_pre
    equal_con=signature([con])==ref_con
    got=equal_pre and equal_con
    assert got==expected,(name,got,expected)
    print(f"{name}: obligation_equivalent={got}; premise_equal={equal_pre}; conclusion_equal={equal_con}")
# Exhaustively reject source-specific oracle shortcuts: permutation and duplication invariant.
assert signature([ab,cd])==signature([cd,ab,ab])
# Scientific boundary: a full implication can be true even when its premise differs.
def implication(pre,con):
    return tuple((not p) or q for p,q in zip(signature(pre),signature([con])))
assert implication([ab,cd],conclusion)==implication([ab,cd,zero],conclusion)
assert signature([ab,cd])!=signature([ab,cd,zero])
print("V4_EXPOSED_PASS: 6/6, premise-strengthening separated; no expert superiority")
