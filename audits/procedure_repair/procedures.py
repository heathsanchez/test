"""Frozen, target-name-blind certificate procedure builders.

The four candidates are fixed by IMPLEMENTATION.md. Their output is checked
independently by certcheck; no target-specific coefficient or theorem is stored.
"""
from fractions import Fraction as Q
from certcheck import norm, add, mul, scale, verify

NAMES = ('coefficientwise', 'half_line_square', 'interval_affine', 'coefficient_sham')


def coefficientwise(p, domain):
    p = norm(p)
    if any(k < 0 or v < 0 for k,v in p.items()): return None
    return {'kind':'coeff','polynomial':{str(k):str(v) for k,v in p.items()}}


def half_line_square(p, domain):
    if domain[0] != 'ray': return None
    p = norm(p)
    if not p: return coefficientwise(p,domain)
    k = min(p)
    q = {j-k:v for j,v in p.items()}
    if any(j not in (0,1,2) for j in q): return None
    a,b,d = q.get(2,Q(0)),q.get(1,Q(0)),q.get(0,Q(0))
    if a <= 0: return None
    r = -b/(2*a)
    D = d-b*b/(4*a)
    if D < 0: return None
    return {'kind':'square','power':k,'A':str(a),'r':str(r),'D':str(D)}


def interval_affine(p, domain):
    if domain[0] != 'interval': return None
    l,u = Q(domain[1]),Q(domain[2])
    p = norm(p)
    # Exact rational linear-factor extraction by rational-root theorem.
    # This is deliberately bounded to degree <= 2 and rational coefficients.
    if not p: return coefficientwise(p,domain)
    degree=max(p)
    if degree > 2: return None
    if degree == 1:
        a,b=p.get(1,Q(0)),p.get(0,Q(0))
        return {'kind':'affine','a':str(a),'b':str(b)} if a*l+b>=0 and a*u+b>=0 else None
    if degree == 0: return coefficientwise(p,domain)
    a,b,c=p[2],p.get(1,Q(0)),p.get(0,Q(0))
    disc=b*b-4*a*c
    if disc<0:return None
    from math import isqrt
    n,d=isqrt(disc.numerator),isqrt(disc.denominator)
    if n*n!=disc.numerator or d*d!=disc.denominator:return None
    root=Q(n,d)
    r1=(-b+root)/(2*a);r2=(-b-root)/(2*a)
    # Both signs of the scalar are considered; only endpoint-valid factors survive.
    for first,second in (({0:-a*r1,1:a},{0:-r2,1:Q(1)}),
                         ({0:-a*r2,1:a},{0:-r1,1:Q(1)}),
                         ({0:a*r1,1:-a},{0:r2,1:Q(-1)}),
                         ({0:a*r2,1:-a},{0:r1,1:Q(-1)})):
        if mul(first,second)!=p:continue
        children=[{'kind':'affine','a':str(f[1]),'b':str(f[0])} for f in (first,second)]
        if all(Q(f['a'])*l+Q(f['b'])>=0 and Q(f['a'])*u+Q(f['b'])>=0 for f in children):
            return {'kind':'product','children':children}
    return None


def coefficient_sham(p,domain):
    return coefficientwise(p,domain)

BUILDERS=(coefficientwise,half_line_square,interval_affine,coefficient_sham)


def build(name,p,domain):
    c=BUILDERS[NAMES.index(name)](p,domain)
    return c if c is not None and verify(p,domain,c) else None
