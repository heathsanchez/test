#!/usr/bin/env python3
"""Crystal audit: can the origin anti-concentration theorem be derived from
the exact source-lift recurrence without assuming fixed-source progress?

Key exact fact: for X < 2^(j-1), any canonical child with 0<R<X must have
terminal source-lift bit e=0, since e=1 adds 2^(j-1) to R. Hence the origin
window evolves by deterministic zero-lift filtering of its previous origin
window. This script verifies that identity symbolically and constructs the
sharp obstruction to any purely one-step multiplicative contraction:
arbitrarily long all-odd source cylinders retain their source in the origin
window while remaining coefficient-live. Thus an exponential origin envelope
cannot follow from local lift geometry/counting alone; it needs an all-depth
source-coupled progress input.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts

D=18
qmin,F,_=language_counts(D)
states=[(0,0,0)]
checks=0
plateau=[]
for j in range(1,D+1):
    prev=states; nxt=[]
    for q,R,Y in prev:
        for b in (0,1):
            e=(b-Y)&1
            Rp=R+(e<<(j-1))
            z=Y+e*3**q
            Yp=(3*z+1)//2 if b else z//2
            qp=q+b
            if qp>=qmin[j]: nxt.append((qp,Rp,Yp))
    # exact origin transfer for every dyadic X=2^m strictly below new lift.
    for m in range(1,j):
        X=1<<m
        lhs={(q,R,Y) for q,R,Y in nxt if 0<R<X}
        rhs=set()
        for q,R,Y in prev:
            if not (0<R<X): continue
            b=Y&1 # unique e=0 child
            Yp=(3*Y+1)//2 if b else Y//2
            qp=q+b
            if qp>=qmin[j]: rhs.add((qp,R,Yp))
        assert lhs==rhs; checks+=1
    states=nxt

# Explicit arbitrarily-long local obstruction family from OriginPhaseBarrier:
# n=2^J-1 has first J shortcut bits odd and coefficient survives all k<=J.
# Its source is fixed; therefore any theorem forcing a uniform local loss from
# lift geometry alone is false. Check finite representatives exactly.
for J in range(1,65):
    n=(1<<J)-1;y=n;q=0
    for k in range(1,J+1):
        assert y&1
        y=(3*y+1)//2;q+=1
        assert 3**q>=2**k
    plateau.append({"J":J,"source_bits":J,"survival":J})

out={
 "schema":"COLLATZ_CRYSTAL_ORIGIN_THEOREM_AUDIT_V1",
 "symbolic_depth":D,
 "exact_origin_transfer_checks":checks,
 "transfer_law":"for X<2^(j-1), low-R children are exactly coefficient-live e=0 children of low-R parents",
 "arbitrary_local_plateau_family":"n=2^J-1 survives coefficient threshold for every k<=J",
 "plateau_checked_through":64,
 "decision":"ORIGIN_ANTICONCENTRATION_NOT_DERIVABLE_FROM_LOCAL_LIFT_AND_LANGUAGE_COUNT_ALONE",
 "reason":"the exact transfer has no intrinsic contraction factor; contraction is precisely loss of actual low-R sources at the coefficient boundary",
 "remaining_nonlocal_input":"prove quantitative cumulative boundary loss for fixed-origin sources (or a lower-source coalescence constructor); this is source-coupled progress, not a counting corollary",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
