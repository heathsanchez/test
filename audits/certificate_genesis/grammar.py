"""Bounded certificate-language completion. No target oracle or source theorem import.
The old coefficientwise solver is imported unchanged. Only its rejected records
are offered to the new, explicitly restricted square-certificate constructor.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from math import isqrt
from form_synthesis import SLOPES, EXPONENTS, DEN, Candidate, add, scale, mul, deriv, generate, validate


def rational_sqrt(q):
    q = Q(q)
    if q < 0: return None
    a,b = isqrt(q.numerator), isqrt(q.denominator)
    return Q(a,b) if a*a == q.numerator and b*b == q.denominator else None


def polynomial(c,slope,exponent):
    return add({1:Q(slope)},{exponent:-Q(c)})


def derivative_numerator(p):
    return add({0:Q(1)},scale(mul(DEN,deriv(p)),Q(-1)))


def factor_monomial(p):
    if not p: return 0,{}
    k=min(p)
    return k,{j-k:v for j,v in p.items()}


def complete_square(q):
    """Exact q=A*(x-r)^2+D, A>0 and D>=0."""
    if any(k not in (0,1,2) for k in q): return None
    a,b,d=q.get(2,Q(0)),q.get(1,Q(0)),q.get(0,Q(0))
    if a<=0:return None
    r=-b/(2*a); remainder=d-b*b/(4*a)
    if remainder<0:return None
    return {'A':a,'r':r,'D':remainder}


def expand_square(k,cert):
    a,r,d=cert['A'],cert['r'],cert['D']
    q=add(scale(mul({1:Q(1),0:-r},{1:Q(1),0:-r}),a),{0:d})
    return {j+k:v for j,v in q.items()}


@dataclass(frozen=True)
class Extension:
    candidate:Candidate
    k:int
    square:dict
    def record(self):
        def encode(p):return {str(k):str(v) for k,v in sorted(p.items())}
        return {**self.candidate.record(),'certificate_kind':'half_line_square',
                'factor_power':self.k,
                'square':{k:str(v) for k,v in self.square.items()},
                'derivative_numerator':encode(derivative_numerator(self.candidate.polynomial()))}


def validate_extension(e):
    return (e.k>=0 and e.square['A']>0 and e.square['D']>=0 and
            derivative_numerator(e.candidate.polynomial())==expand_square(e.k,e.square))


def solve_square_family(slope,exponent):
    """Solve the frozen residual family, not a target-specific coefficient list.

    After factoring x^k, P(c)=b*x+c*(d0+d2*x^2), where b<0 and d0,d2>0.
    The exact least nonnegative coefficient is -b/(2*sqrt(d0*d2)).
    Other polynomial families are outside this deliberately incomplete solver.
    """
    base=derivative_numerator(polynomial(Q(0),slope,exponent))
    direction=mul(DEN,deriv({exponent:Q(1)}))
    if not base or not direction:return None
    k=min(set(base)|set(direction))
    b={j-k:v for j,v in base.items()}
    d={j-k:v for j,v in direction.items()}
    if set(b)!={1} or b[1]>=0:return None
    if set(d)!={0,2} or d[0]<=0 or d[2]<=0:return None
    root=rational_sqrt(d[0]*d[2])
    if root is None or root==0:return None
    c=-b[1]/(2*root)
    p=derivative_numerator(polynomial(c,slope,exponent))
    k2,q=factor_monomial(p)
    cert=complete_square(q)
    if cert is None or k2!=k:return None
    e=Extension(Candidate(Q(slope),exponent,c,tuple(sorted(p.items()))),k,cert)
    assert validate_extension(e)
    return e


def generate_extensions():
    old,rejected,duplicates=generate()
    out=[];failures=[]
    for rec in rejected:
        e=solve_square_family(Q(rec['slope']),rec['exponent'])
        if e is None:
            failures.append({**rec,'reason':'SQUARE_META_GRAMMAR_INSUFFICIENT'})
        else:
            assert validate_extension(e)
            assert not validate(e.candidate)
            out.append(e)
    return old,rejected,duplicates,out,failures
