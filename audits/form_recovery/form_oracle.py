"""Private benchmark oracle. Never imported by form_synthesis or emit_form.

The original source-derived target is deliberately available to the verifier,
not to the expression generator. This is a reproducible benchmark boundary,
not a claim that the benchmark designer is blind to the known theorem.
"""
from fractions import Fraction as Q
from itertools import product
from experiment import Feature, World, develop, selected
from proof_bridge import target, upper, FEATURES

TRAIN=((Q(1),Q(2,3)),(Q(1),Q(7,12)),(Q(1),Q(2)))
HELDOUT=tuple(product((Q(0),Q(1,2),Q(1),Q(2)),
    (Q(0),Q(1,4),Q(1,2),Q(7,12),Q(2,3),Q(3,4),Q(1),Q(3,2),Q(2),Q(3))))
UPPER=Feature('upper',upper)

def world(features):
    return World('unknown_form_angle',TRAIN,HELDOUT,lambda s:s[0],target,tuple(features))

def obstruction():
    old=tuple(f for f in FEATURES if f.name!='lower')
    w=world(old)
    return develop(w,old,True,2,initial=selected(w,('upper',)))
