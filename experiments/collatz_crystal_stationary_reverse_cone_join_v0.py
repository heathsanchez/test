#!/usr/bin/env python3
"""Intersect hard stationary-threshold trajectories with exact reverse-cone bank."""
import json
import collatz_reverse_predecessor_tree as pred
from collatz_live_origin_bridge_v1 import language_counts
BITS=24; H=2000; Q=14
qmin,_,_=language_counts(H)
records=[13421671,14378779,8088063,12132095,9280639,13774695,1126015,2252031,1689023,6206655]
cs=pred.enumerate_first_contractions(Q)
by={}
for c in cs: by.setdefault(c.d,{}).setdefault(c.residue,[]).append(c)
def T(x): return (3*x+1)//2 if x&1 else x//2
def best(y,n):
    hit=None
    for d,rows in by.items():
        for c in rows.get(y%d,()):
            num=c.a*y-c.c
            if num%d: continue
            p=num//d
            if 0<p<n:
                z=pred.reverse_apply(y,c.word)
                assert z==p
                cand=(p,c.steps,c.word)
                if hit is None or cand<hit: hit=cand
    return hit
def audit(n):
    y=n;q=0; first=None; cross=None
    for j in range(1,H+1):
        y=T(y); q += y*0 # placeholder no-op
        # odd count belongs to input parity; recompute separately below
        h=best(y,n)
        if h and first is None:first={"j":j,"y":y,"p":h[0],"steps":h[1],"word":h[2]}
        # threshold crossing from exact replay count:
    y=n;q=0
    for j in range(1,H+1):
        bit=y&1
        y=T(y); q+=bit
        if q<qmin[j]: cross=j;break
    return {"n":n,"crossing":cross,"first_reverse_merge":first,
            "merge_before_cross": first is not None and (cross is None or first["j"]<cross)}
hard=[audit(n) for n in records]
print(json.dumps({"schema":"COLLATZ_CRYSTAL_STATIONARY_REVERSE_CONE_JOIN_V0",
 "Q":Q,"certificates":len(cs),"hard":hard,
 "hard_closed_before_cross":sum(x["merge_before_cross"] for x in hard),
 "hard_residual":[x for x in hard if not x["merge_before_cross"]],
 "status":"BOUNDED_EXACT_JOIN","global_collatz":"UNKNOWN"},indent=2))
