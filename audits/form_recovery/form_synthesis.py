"""Bounded expression generation, with no access to the protected target.

The grammar is frozen in PROTOCOL.md. This module knows the derivative of
arctan, but does not import proof_bridge, the source theorem, or an oracle.
Failure of this coefficientwise certificate is not mathematical impossibility.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product

SLOPES = (Q(0), Q(1,4), Q(1,2), Q(3,4), Q(1))
EXPONENTS = (2,3,4,5)
DEN = {0: Q(1), 2: Q(1)}

def add(a,b):
    return {k:a.get(k,Q(0))+b.get(k,Q(0)) for k in a.keys()|b.keys()
            if a.get(k,Q(0))+b.get(k,Q(0))}
def scale(a,c):
    return {k:v*c for k,v in a.items() if v*c}
def mul(a,b):
    out={}
    for i,x in a.items():
        for j,y in b.items(): out[i+j]=out.get(i+j,Q(0))+x*y
    return {k:v for k,v in out.items() if v}
def deriv(a):
    return {k-1:k*v for k,v in a.items() if k and v}

def solve_linear_certificate(base,direction):
    """Solve base+c*direction >= 0 coefficientwise, c >= 0, exactly."""
    lo=Q(0); hi=None
    for degree in sorted(base.keys()|direction.keys()):
        a=base.get(degree,Q(0)); b=direction.get(degree,Q(0))
        if b>0: lo=max(lo,-a/b)
        elif b<0: hi=min(hi,-a/b) if hi is not None else -a/b
        elif a<0: return None
    if hi is not None and lo>hi: return None
    p=add(base,scale(direction,lo))
    assert all(v>=0 for v in p.values())
    return lo,p

@dataclass(frozen=True)
class Candidate:
    slope: Q
    exponent: int
    coefficient: Q
    certificate: tuple
    @property
    def name(self):
        return 'form_'+str(self.slope).replace('/','_')+'_'+str(self.exponent)
    def polynomial(self):
        return add({1:self.slope},{self.exponent:-self.coefficient})
    def evaluate(self,x):
        return self.slope*x-self.coefficient*x**self.exponent
    def lower(self,state):
        x,y=state
        return y>=self.evaluate(x)
    def record(self):
        def encoded(p):return {str(k):str(v) for k,v in sorted(p.items())}
        return {'name':self.name,'slope':str(self.slope),'exponent':self.exponent,
                'coefficient':str(self.coefficient),
                'expression':encoded(self.polynomial()),
                'certificate':encoded(dict(self.certificate))}

def certify(slope,exponent):
    # P = (1+x²)*(atan' - L') = 1 - (1+x²)*L'.
    # Here L=a*x-c*x^n, with c not supplied or enumerated.
    linear={1:slope}; correction={exponent:Q(1)}
    base=add({0:Q(1)},scale(mul(DEN,deriv(linear)),Q(-1)))
    direction=mul(DEN,deriv(correction))
    result=solve_linear_certificate(base,direction)
    if result is None:return None
    c,p=result
    return Candidate(slope,exponent,c,tuple(sorted(p.items())))

def validate(candidate):
    p=add({0:Q(1)},scale(mul(DEN,deriv(candidate.polynomial())),Q(-1)))
    return p==dict(candidate.certificate) and all(v>=0 for v in p.values())

def generate():
    candidates=[]; rejected=[]; duplicates=[]; seen=set()
    for slope,exponent in product(SLOPES,EXPONENTS):
        candidate=certify(slope,exponent)
        if candidate is None:
            rejected.append({'slope':str(slope),'exponent':exponent,'reason':'COEFFICIENT_CERTIFICATE_INSUFFICIENT'})
            continue
        assert validate(candidate)
        key=tuple(sorted(candidate.polynomial().items()))
        if key in seen:
            duplicates.append({'slope':str(slope),'exponent':exponent,'reason':'SAME_EXPRESSION'})
            continue
        seen.add(key); candidates.append(candidate)
    return candidates,rejected,duplicates
