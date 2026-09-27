#!/usr/bin/env python3
"""Crystal V3: quotient odd states by their common accelerated successor.

For odd x, s=v2(3x+1).  Strip pairs of powers of two from this valuation:
  k=floor((s-1)/2), C_k=(4^k-1)/3,
  p=(x-C_k)/4^k.
Then p is a positive odd integer, p<=x, v2(3p+1) is 1 or 2, and p and x
have exactly the same next odd Collatz successor.  This is one parametric
source-changing capability, not a constructor bank.

Protected consequence: if p<n for an odd x on n's orbit, p is an exact
lower-source coalescence certificate.
"""
import json

LIMIT=1<<20
H=1024
HARD=[13421671,14378779,8088063,12132095,9280639,13774695,
      1126015,2252031,1689023,6206655,63728127]

def T(x):
    return (3*x+1)//2 if x&1 else x//2

def v2(x):
    return (x & -x).bit_length()-1

def odd_successor(x):
    assert x&1
    s=v2(3*x+1)
    return (3*x+1)>>s, s

def pullback(x):
    u,s=odd_successor(x)
    k=(s-1)//2
    pow4=1<<(2*k)
    c=(pow4-1)//3
    assert (x-c)%pow4==0
    p=(x-c)//pow4
    assert p>0 and p&1 and p<=x
    up,sp=odd_successor(p)
    assert up==u
    assert sp in (1,2)
    return p,u,s,k,sp

# Parametric identity audit, independent of trajectory sampling.
identity=0
for x in range(1,LIMIT,2):
    p,u,s,k,sp=pullback(x)
    if k:
        assert p<x
    identity+=1

def first_hit(n):
    y=n
    for j in range(H+1):
        if y&1:
            p,u,s,k,sp=pullback(y)
            if p<n:
                # Original orbit reaches u after s shortcut steps from y.
                z=y
                for _ in range(s): z=T(z)
                assert z==u
                # Canonical pullback reaches same u after sp steps.
                z=p
                for _ in range(sp): z=T(z)
                assert z==u
                return dict(j=j,x=y,s=s,k=k,p=p,common=u,
                            original_a=j+s,p_b=sp)
        y=T(y)
    return None

hard=[{"n":n,"hit":first_hit(n)} for n in HARD]

# Bounded source qualification: every odd n below 2^18 gets a V3 certificate.
# This is deliberately a scale holdout from the identity audit and is not
# promoted to a universal statement.
BOUND=1<<18
uncovered=[]
max_a=0
for n in range(3,BOUND,2):
    h=first_hit(n)
    if h is None:
        uncovered.append(n)
        if len(uncovered)>=20: break
    else:
        max_a=max(max_a,h["original_a"])

out={
 "schema":"COLLATZ_CRYSTAL_VALUATION_PULLBACK_V3",
 "identity_odd_x_checked":identity,
 "identity_range_exclusive":LIMIT,
 "law":"k=floor((v2(3x+1)-1)/2), p=(x-(4^k-1)/3)/4^k; x and p have the same next odd successor and v2(3p+1) in {1,2}",
 "protected_consequence":"p<n => exact LOWER_SOURCE_CERTIFICATE for the original source n",
 "hard_holdouts":hard,
 "hard_covered":sum(r["hit"] is not None for r in hard),
 "bounded_source_floor_exclusive":BOUND,
 "bounded_uncovered_first20":uncovered,
 "bounded_max_certificate_forward_depth":max_a,
 "status":"PARAMETRIC_PULLBACK_IDENTITY_AND_BOUNDED_COVERAGE",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
