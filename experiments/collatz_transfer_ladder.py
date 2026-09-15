#!/usr/bin/env python3
"""
Exact two-rung Collatz transfer ladder.

This extends the first dangerous-resonance certificate without enumerating
the ~10^11 crossing depths between resonances.

All transcendental claims use rational atanh-series enclosures.

Rung 1:
  r1 = q1/t1 = 72057431991 / 114208327604
is the first lower semiconvergent after the previously safe Farey neighbor.
Its extremal intercept gets a 2-block Denjoy-Koksma error <= 2/3.

Bridge:
  r1 and the upper neighbor ru are Farey neighbors and
  t2=t1+tu < 2*t1.  Therefore for t1 < t < t2:
    * there is no lower q/t in (r1, alpha);
    * equality q/t=r1 is impossible (the next multiple has denominator 2*t1);
    * hence d=q1*t-t1*q >= 1.
  The determinant gives an additive epsilon gap large enough that the coarse
  intercept bound A < q*3^(q-1) already forces descent above the rung-1
  verified ceiling.

Rung 2:
  r2=(q1+qu)/(t1+tu)
is the next lower convergent.  Its numerator q2 is a convergent denominator
for beta=log_2(3), so one Denjoy-Koksma block gives error <= 1/3.
"""
from fractions import Fraction

# Current published/computational base used by rung 1.
L0 = 2075 * (1 << 60)

# Last lower convergent before rung 1 and its upper Farey neighbor.
q0,t0 = 6586818670,10439860591
qu,tu = 65470613321,103768467013
q1,t1 = q0+qu,t0+tu
q2,t2 = q1+qu,t1+tu

def ceil_frac(x: Fraction) -> int:
    return (x.numerator + x.denominator - 1)//x.denominator

def ln_bounds_atanh(x: Fraction, terms: int=220):
    assert 0 < x < 1
    s=Fraction(0)
    x2=x*x
    p=x
    for k in range(terms):
        s += p/(2*k+1)
        p *= x2
    N=terms
    tail=2*(x**(2*N+1))/((2*N+1)*(1-x2))
    return 2*s, 2*s+tail

def common_cf(lo: Fraction, hi: Fraction, limit=64):
    """Common continued-fraction prefix certified by a rational interval."""
    assert 0 < lo < hi
    out=[]
    for _ in range(limit):
        a=lo.numerator//lo.denominator
        b=hi.numerator//hi.denominator
        if a != b:
            break
        out.append(a)
        lo -= a
        hi -= a
        if lo == 0 or hi == 0:
            break
        lo,hi = 1/hi,1/lo
    return out

def convergents(cf):
    p0,p1=0,1
    q0_,q1_=1,0
    out=[]
    for a in cf:
        p=a*p1+p0
        q=a*q1_+q0_
        out.append((p,q))
        p0,p1=p1,p
        q0_,q1_=q1_,q
    return out

ln2_lo,ln2_hi=ln_bounds_atanh(Fraction(1,3))
ln3_lo,ln3_hi=ln_bounds_atanh(Fraction(1,2))
alpha_lo=ln2_lo/ln3_hi
alpha_hi=ln2_hi/ln3_lo
beta_lo=ln3_lo/ln2_hi
beta_hi=ln3_hi/ln2_lo

r0=Fraction(q0,t0)
ru=Fraction(qu,tu)
r1=Fraction(q1,t1)
r2=Fraction(q2,t2)

# Exact brackets and Farey structure.
assert r0 < r1 < r2 < alpha_lo < alpha_hi < ru
assert qu*t0-q0*tu == 1
assert qu*t1-q1*tu == 1
assert (q1,t1)==(72057431991,114208327604)
assert (q2,t2)==(137528045312,217976794617)
assert t2 < 2*t1

# Certify the relevant continued-fraction denominators of beta=log_2 3.
cf=common_cf(beta_lo,beta_hi,40)
conv=convergents(cf)
denoms=[q for _,q in conv]
assert 6586818670 in denoms
assert 65470613321 in denoms
i21=denoms.index(6586818670)
i22=denoms.index(65470613321)
assert i22==i21+1
assert q1==denoms[i21]+denoms[i22]
assert q2 in denoms
assert denoms.index(q2)==i22+1

# Rung 1 exact epsilon and two-block DK ceiling.
eps1_lo=t1*ln2_lo-q1*ln3_hi
eps1_hi=t1*ln2_hi-q1*ln3_lo
assert 0 < eps1_lo < eps1_hi
dk1_num_hi=Fraction(q1,1)/(6*ln2_lo)+Fraction(2,3)
B1=ceil_frac(dk1_num_hi/eps1_lo)
assert B1==3143983941795894239301
assert B1 > L0

# Bridge all strict lower crossings t1 < t < t2.
# If q/t < r1 then d=q1*t-t1*q>=1.  Exactly:
# eps=(t/t1)*eps1 + (d/t1)*ln3.
# Also q/t<r1 => q < r1*t.  Since t/(a*t+b) is increasing,
# the coarse rescue q/(3 eps) is maximized safely at t=t2-1.
tm=t2-1
bridge_eps_lo=Fraction(tm,t1)*eps1_lo + Fraction(ln3_lo,t1)
bridge_rescue_hi=Fraction(r1*tm,1)/(3*bridge_eps_lo)
bridge_ceiling=ceil_frac(bridge_rescue_hi)
assert bridge_ceiling==2276494896546098592457
assert bridge_ceiling < B1

# Equality q/t=r1 cannot recur before t2 because r1 is reduced and 2*t1>t2.
assert Fraction(q1,t1).denominator==t1
assert 2*t1 > t2

# Rung 2 is a single beta-convergent block: DK error <= Var(f)=1/3.
eps2_lo=t2*ln2_lo-q2*ln3_hi
eps2_hi=t2*ln2_hi-q2*ln3_lo
assert 0 < eps2_lo < eps2_hi
dk2_num_hi=Fraction(q2,1)/(6*ln2_lo)+Fraction(1,3)
B2=ceil_frac(dk2_num_hi/eps2_lo)
assert B2==36797780659016653495980
assert B2 > B1

print("BETA_CF_PREFIX",",".join(map(str,cf[:25])))
print("RUNG1",q1,t1,B1)
print("BRIDGE_STRICT_LOWER_CEILING",bridge_ceiling)
print("RUNG2",q2,t2,B2)
print("CONDITIONAL_THEOREM",
      f"once all n < {B1} are verified, every first coefficient contraction "
      f"with t < {t2} forces descent for n >= {B1}; at t={t2}, "
      f"any additive rescue requires n <= {B2}")
