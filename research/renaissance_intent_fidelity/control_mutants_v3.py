#!/usr/bin/env python3
"""Exposed finite Nat model. Tests frozen V3 mutations; no prospective/AI claim."""
from itertools import product
D=range(3)
def impl(p,q): return (not p) or q
def orig(a,b,c,d): return impl(a<=b and c<=d,a*c<=b*d)
def swap(a,b,c,d): return impl(c<=d and a<=b,a*c<=b*d)
def missing(a,b,c,d): return impl(a<=b and a<=b,a*c<=b*d)
def reversed_(a,b,c,d): return impl(a<=b and c<=d,b*d<=a*c)
def extra(a,b,c,d): return impl(a<=b and c<=d and a==0,a*c<=b*d)
def taut(a,b,c,d): return impl(a<=b and c<=d and a==a,a*c<=b*d)
fs={'original':orig,'swapped_premises':swap,'missing_premise':missing,
    'reversed_conclusion':reversed_,'extra_premise':extra,'tautology':taut}
samples=list(product(D,repeat=4))
base=[orig(*x) for x in samples]
for name,f in fs.items():
    observed=[f(*x) for x in samples]
    witness=next((x for x,y,z in zip(samples,base,observed) if y!=z),None)
    print(f'{name}: equivalent_on_81={witness is None}; witness={witness}')
assert all(base), 'source inequality must hold on Nat domain'
assert next((x for x in samples if orig(*x)!=missing(*x)),None) is not None
assert next((x for x in samples if orig(*x)!=reversed_(*x)),None) is not None
# IMPORTANT negative: since source theorem is universally true in this model,
# strengthening its antecedent remains equally true: fidelity not decidable.
assert all(extra(*x)==orig(*x) for x in samples)
print('SCIENTIFIC_NEGATIVE: premise-strengthening is undetectable by Nat truth-table equivalence')
