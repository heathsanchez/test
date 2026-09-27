#!/usr/bin/env python3
"""Symbolic first-crossing margin falsifier.

Enumerate every canonical live source-product prefix, not sources below a
numeric cutoff. At the first coefficient crossing leaf, test Y<R for the
canonical source R. This isolates whether strict descent is a combinatorial
first-crossing theorem. Existence of a crossing for every fixed source is a
separate UNKNOWN.
"""
from __future__ import annotations
import json
from collatz_live_origin_bridge_v1 import language_counts
DEPTH=31
qmin,_,_=language_counts(DEPTH)
states=[(0,0,0)] # q,R,Y at depth 0
leaves=0; hard=[]; zero=[]; min_margin=None; per_depth=[]
for j in range(1,DEPTH+1):
    nxt=[]; dl=0; dh=0
    for q,R,Y in states:
        for orbit_bit in (0,1):
            lift=(orbit_bit-Y)&1
            Rp=R+(lift<<(j-1))
            z=Y+(3**q)*lift
            assert z&1==orbit_bit
            Yp=(3*z+1)//2 if orbit_bit else z//2
            qp=q+orbit_bit
            if qp<qmin[j]:
                leaves+=1;dl+=1
                m=Rp-Yp
                if Rp==0:
                    zero.append({"j":j,"q":qp,"R":Rp,"Y":Yp})
                elif m<=0:
                    dh+=1
                    if len(hard)<40:hard.append({"j":j,"q":qp,"R":Rp,"Y":Yp,"margin":m})
                elif min_margin is None or m<min_margin["margin"]:
                    min_margin={"j":j,"q":qp,"R":Rp,"Y":Yp,"margin":m}
            else:
                nxt.append((qp,Rp,Yp))
    per_depth.append({"j":j,"live":len(nxt),"first_crossing":dl,"nondescending":dh})
    states=nxt
out={"schema":"COLLATZ_FIRST_CROSSING_SYMBOLIC_MARGIN_V1","depth":DEPTH,
 "first_crossing_leaves":leaves,"live_at_depth":len(states),
 "nondescending_nonzero":len(hard),"first_nondescending":hard,
 "zero_source_leaves":zero[:20],"minimum_positive_R_minus_Y":min_margin,
 "per_depth":per_depth,
 "status":"BOUNDED_SYMBOLIC_MARGIN_SURVIVES" if not hard else "SYMBOLIC_MARGIN_COUNTEREXAMPLE",
 "boundary":"all canonical first-crossing words through declared depth; does not prove every fixed source eventually crosses",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
