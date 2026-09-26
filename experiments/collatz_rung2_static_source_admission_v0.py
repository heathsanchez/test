#!/usr/bin/env python3
"""Constructive static compatibility of Ansari source language with rung2 residuals.

Tests whether the explicit necessary source language
  n = 4*z+3, z has base-3 digits only 0/1
plus the rung2 source interval and near-return gap can by itself eliminate any
intrinsic residual bicell. For each residual, emit a concrete source n in the
language and an even delta<=G whose endpoint has the required Q3 residue and
odd parity. These are arithmetic compatibility witnesses, not Collatz orbits.
"""
import json
from functools import lru_cache
import collatz_rung2_bicell_v1 as b
import collatz_rung2_reverse_trit_v0 as r2

L=r2.L;G=r2.G
U=51_012_555_828_807_148_352_153

def next01(x,maxdigits=60):
    if x<0:return 0
    ds=[]
    y=x
    while y:ds.append(y%3);y//=3
    ds += [0]*(maxdigits-len(ds))
    @lru_cache(None)
    def rec(pos,greater):
        if pos<0:return 0
        xd=ds[pos];best=None
        for d in (0,1):
            if not greater and d<xd:continue
            sub=rec(pos-1,greater or d>xd)
            if sub is not None:
                val=d*3**pos+sub
                if best is None or val<best:best=val
        return best
    return rec(maxdigits-1,False)

def digits01(x):
    while x:
        if x%3 not in (0,1):return False
        x//=3
    return True

def extend(j,zlow):
    M=3**j
    Zlo=(L-3+3)//4; Zhi=(U-3)//4
    klo=max(0,(Zlo-zlow+M-1)//M);khi=(Zhi-zlow)//M
    k=next01(klo)
    if k is None or k>khi:return None
    assert digits01(k) and digits01(zlow)
    z=zlow+M*k
    assert digits01(z)
    n=4*z+3
    assert L<=n<=U
    return n

def even_delta(r,s,M):
    d=(r-s)%M
    candidates=[d]
    if d+M<=G:candidates.append(d+M)
    good=[x for x in candidates if x<=G and x%2==0]
    return min(good) if good else None

def low_candidate(j,r):
    M=3**j;zmax=(M-1)//2
    # Search intervals induced by d or d+M in [0,G]. Use ternary rounding,
    # plus exact verification. Candidate interval endpoints suffice because
    # next01 returns the first language member.
    dmax=min(G,2*M-1)
    # allowed s for delta d in [0,dmax] wraps; split by integer lift h=0,1.
    intervals=[]
    for h in (0,1):
        dlo=max(0,h*M);dhi=min(G,(h+1)*M-1)
        if dlo>dhi:continue
        # d=r-s mod M; residue range of d covers circular interval.
        # Generate conservative s intervals by splitting circular endpoints.
        lo=(r-(dhi%M))%M; hi=(r-(dlo%M))%M
        if dlo//M==dhi//M:
            if lo<=hi: intervals.append((lo,hi))
            else: intervals.extend(((0,hi),(lo,M-1)))
    # Also fall back to full residue interval when G>=M-1.
    if G>=M-1: intervals.append((0,M-1))
    for sa,sb in intervals:
        for kshift in (0,1,2):
            lo=(kshift*M+sa-3 +3)//4
            hi=(kshift*M+sb-3)//4
            lo=max(0,lo);hi=min(zmax,hi)
            if lo>hi:continue
            z=next01(lo,j+2)
            if z is None or z>hi or not digits01(z):continue
            s=(4*z+3)%M;d=even_delta(r,s,M)
            if d is not None:
                n=extend(j,z)
                if n is not None:
                    y=n+d
                    assert y%M==r and y%2==1 and 0<=d<=G
                    return n,d,z
    # Exact fallback over a few recursively generated language boundary points
    # is unnecessary if interval method is complete; signal failure explicitly.
    return None

# Reconstruct rung2 residuals.
acts,_=r2.reverse_actions(r2.DEPTH);centre=[];res=[]
for j in range(1,r2.DEPTH+1):
    qj=r2.terminal(tuple(acts[:j]));centre.append(qj)
    base=qj%(3**(j-1)) if j>1 else 0;cd=(qj//(3**(j-1)))%3
    for alt in range(3):
        if alt==cd:continue
        rr=base+alt*3**(j-1);direct=r2.cert(rr,j)
        for parity in (0,1):
            closed=direct is not None or rr%3==0 or b.one_step(rr,j,parity) is not None
            if not closed:res.append((j,rr,parity))
assert len(res)==31 and all(p==1 for _,_,p in res)
rows=[]
for j,r,p in res:
    w=low_candidate(j,r)
    rows.append(dict(depth=j,residue=r,compatible=w is not None,
                     source=(w[0] if w else None),delta=(w[1] if w else None)))
compatible=sum(x["compatible"] for x in rows)
result={
 "schema":"COLLATZ_RUNG2_STATIC_SOURCE_ADMISSION_V0",
 "residual_cells":len(rows),"statically_compatible":compatible,
 "eliminated_by_static_ansari_language":len(rows)-compatible,
 "rows":rows,
 "interpretation":"static recursively-sufficient source membership plus interval/gap is not the dynamic source-admission theorem unless cells are eliminated",
 "next_cycle":"if all survive, couple the source language to coefficient-persistence/parity dynamics rather than endpoint congruence alone",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
