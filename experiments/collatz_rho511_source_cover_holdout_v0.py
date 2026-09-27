#!/usr/bin/env python3
"""Independent rho=511/512 live-origin contraction check from a CST histogram.

Reads one exact full source-cover JSON for all odd sources < 2^B.  This tests
only the single origin window X=2^B, but B is deliberately larger than the
20-bit Crystal discovery corpus.
"""
import json,sys
from fractions import Fraction

RHO=Fraction(511,512)
BMAX=21
obj=json.load(sys.stdin)
B=obj["source_bits"]
hist=obj["first_crossing_histogram"]
D=max(len(hist)-1, 512)

def language_counts(depth):
    qmin=[0]*(depth+1); q=0;p3=1
    for j in range(1,depth+1):
        while p3 < (1<<j):
            p3*=3;q+=1
        qmin[j]=q
    counts={0:1};F=[1]
    for j in range(1,depth+1):
        nxt={}
        for q,c in counts.items():
            for bit in (0,1):
                if q+bit>=qmin[j]:
                    nxt[q+bit]=nxt.get(q+bit,0)+c
        counts=nxt;F.append(sum(counts.values()))
    return F

F=language_counts(D)
P=[0]*(D+1)
P[0]=1<<(B-1)
rem=P[0]
for j in range(1,D+1):
    if j < len(hist): rem-=hist[j]
    P[j]=rem

def ratio(j,b):
    if not P[j]: return Fraction(0)
    a=Fraction(P[j+b]*F[j],P[j]*F[j+b])
    e=(6*(j+b))//125-(6*j)//125-b
    return a / (Fraction(2**e) if e>=0 else Fraction(1,2**(-e)))

rows=[];bad=[]
for j in range(60,D-BMAX+1):
    if not P[j]: continue
    wins=[b for b in range(1,BMAX+1) if ratio(j,b)<=RHO]
    rows.append((j,P[j],wins[0] if wins else None))
    if not wins: bad.append((j,P[j],[str(ratio(j,b)) for b in range(1,BMAX+1)]))

out={
 "schema":"COLLATZ_RHO511_SOURCE_COVER_HOLDOUT_V0",
 "source_bits":B,
 "source_cover_unresolved":obj["unresolved"],
 "source_cover_max_first_crossing":obj["max_first_crossing"],
 "checked_nonempty_states":len(rows),
 "bad_roots":len(bad),
 "first_bad":bad[:3],
 "max_selected_block":max((b for _,_,b in rows if b is not None),default=0),
 "status":"HOLDOUT_BAD_KERNEL_EMPTY" if not bad else "HOLDOUT_BAD_ROOT_FOUND",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
if bad: raise SystemExit(1)
