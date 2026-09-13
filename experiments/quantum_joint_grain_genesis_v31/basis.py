#!/usr/bin/env python3
"""Frozen V31 exact finite quantum substrate over Q(sqrt(2))."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import itertools
from typing import Any, Iterable, Iterator, Tuple


@dataclass(frozen=True)
class Q2:
    """Exact a + b*sqrt(2), a,b rational."""
    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    @staticmethod
    def of(x: int | Fraction | "Q2") -> "Q2":
        if isinstance(x, Q2):
            return x
        return Q2(Fraction(x), Fraction(0))

    def __add__(self, other):
        o=Q2.of(other); return Q2(self.a+o.a,self.b+o.b)
    __radd__=__add__

    def __sub__(self, other):
        o=Q2.of(other); return Q2(self.a-o.a,self.b-o.b)
    def __rsub__(self, other):
        return Q2.of(other).__sub__(self)

    def __neg__(self):
        return Q2(-self.a,-self.b)

    def __mul__(self, other):
        o=Q2.of(other)
        return Q2(self.a*o.a+2*self.b*o.b,self.a*o.b+self.b*o.a)
    __rmul__=__mul__

    def inv(self):
        den=self.a*self.a-2*self.b*self.b
        if den==0: raise ZeroDivisionError
        return Q2(self.a/den,-self.b/den)

    def __truediv__(self, other):
        return self*Q2.of(other).inv()

    def __rtruediv__(self, other):
        return Q2.of(other)/self

    def square(self):
        return self*self

    def sign(self) -> int:
        """Exact sign of a+b*sqrt(2)."""
        a,b=self.a,self.b
        if a==0 and b==0:return 0
        if b==0:return 1 if a>0 else -1
        if a>=0 and b>0:return 1
        if a<=0 and b<0:return -1
        # Opposite signs: compare |a| with |b|*sqrt(2) exactly.
        lhs=a*a
        rhs=2*b*b
        if lhs==rhs:return 0
        if a>0 and b<0:
            return 1 if lhs>rhs else -1
        if a<0 and b>0:
            return 1 if rhs>lhs else -1
        raise AssertionError

    def __lt__(self, other):
        return (self-Q2.of(other)).sign()<0
    def __le__(self, other):
        return (self-Q2.of(other)).sign()<=0
    def __gt__(self, other):
        return (self-Q2.of(other)).sign()>0
    def __ge__(self, other):
        return (self-Q2.of(other)).sign()>=0

    def abs(self):
        return self if self.sign()>=0 else -self

    def data(self) -> Any:
        def f(x: Fraction):
            return [x.numerator,x.denominator]
        return {"a":f(self.a),"b":f(self.b)}

    def approx(self) -> float:
        return float(self.a)+float(self.b)*(2.0**0.5)


ZERO=Q2.of(0); ONE=Q2.of(1); HALF=Q2(Fraction(1,2),Fraction(0))
SQRT2_OVER_2=Q2(Fraction(0),Fraction(1,2))


Matrix2=Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]]
Matrix4=Tuple[Tuple[Q2,Q2,Q2,Q2],...]
StateVec=Tuple[int,int,int,int]
OutcomeTable=Tuple[
    Tuple[Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]], Tuple[Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]], ...]],
    ...
]


I2:Matrix2=((ONE,ZERO),(ZERO,ONE))
X2:Matrix2=((ZERO,ONE),(ONE,ZERO))
Z2:Matrix2=((ONE,ZERO),(ZERO,-ONE))


def m2_add(a:Matrix2,b:Matrix2)->Matrix2:
    return tuple(tuple(a[i][j]+b[i][j] for j in range(2)) for i in range(2))  # type: ignore

def m2_scale(s:Q2,a:Matrix2)->Matrix2:
    return tuple(tuple(s*a[i][j] for j in range(2)) for i in range(2))  # type: ignore

def kron2(a:Matrix2,b:Matrix2)->Matrix4:
    rows=[]
    for i in range(2):
        for k in range(2):
            row=[]
            for j in range(2):
                for l in range(2):
                    row.append(a[i][j]*b[k][l])
            rows.append(tuple(row))
    return tuple(rows)  # type: ignore


@dataclass(frozen=True)
class BipartiteExperiment:
    a_observables: Tuple[Matrix2,Matrix2]
    b_observables: Tuple[Matrix2,Matrix2]
    probabilities: Tuple[
        Tuple[
            Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]],
            Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]]
        ],
        Tuple[
            Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]],
            Tuple[Tuple[Q2,Q2],Tuple[Q2,Q2]]
        ]
    ]
    complete: bool=True
    world_id: str=""

    def __post_init__(self):
        if len(self.a_observables)!=2 or len(self.b_observables)!=2:
            raise ValueError("2 settings per side required")


def canonical_state(v: Iterable[int]) -> StateVec | None:
    t=tuple(int(x) for x in v)
    if len(t)!=4 or all(x==0 for x in t):return None
    first=next(x for x in t if x!=0)
    if first<0:t=tuple(-x for x in t)
    return t  # type: ignore


def candidate_states() -> Tuple[StateVec,...]:
    out=set()
    for raw in itertools.product((-1,0,1),repeat=4):
        v=canonical_state(raw)
        if v is not None:out.add(v)
    return tuple(sorted(out))


def state_norm2(v:StateVec)->int:
    return sum(x*x for x in v)


def state_support(v:StateVec)->int:
    return sum(1 for x in v if x!=0)


def schmidt_rank(v:StateVec)->int:
    det=v[0]*v[3]-v[1]*v[2]
    return 1 if det==0 else 2


def expectation(v:StateVec,op:Matrix4)->Q2:
    n=state_norm2(v)
    acc=ZERO
    for i in range(4):
        for j in range(4):
            if v[i] and v[j]:
                acc=acc+Q2.of(v[i])*op[i][j]*Q2.of(v[j])
    return acc/Q2.of(n)


def born_table(
    v:StateVec,
    a_obs:Tuple[Matrix2,Matrix2],
    b_obs:Tuple[Matrix2,Matrix2],
):
    """Exact P(a,b|x,y), outcome indices 0->-1, 1->+1."""
    table=[]
    for x in range(2):
        row=[]
        for y in range(2):
            ea=expectation(v,kron2(a_obs[x],I2))
            eb=expectation(v,kron2(I2,b_obs[y]))
            eab=expectation(v,kron2(a_obs[x],b_obs[y]))
            probs=[]
            for av in (-1,1):
                prow=[]
                for bv in (-1,1):
                    p=(ONE+Q2.of(av)*ea+Q2.of(bv)*eb+Q2.of(av*bv)*eab)/Q2.of(4)
                    prow.append(p)
                probs.append(tuple(prow))
            row.append(tuple(probs))
        table.append(tuple(row))
    return tuple(table)


def table_equal(a,b)->bool:
    return a==b


def valid_probability_table(table)->bool:
    for x in range(2):
        for y in range(2):
            total=ZERO
            for ai in range(2):
                for bi in range(2):
                    p=table[x][y][ai][bi]
                    if p<ZERO:return False
                    total=total+p
            if total!=ONE:return False
    return True


def local_marginal_signature(table):
    out=[]
    # A marginals for each x; independence from y is also checked by caller.
    for x in range(2):
        vals=[]
        for ai in range(2):
            s=table[x][0][ai][0]+table[x][0][ai][1]
            vals.append(s)
        out.append(("A",x,tuple(vals)))
    for y in range(2):
        vals=[]
        for bi in range(2):
            s=table[0][y][0][bi]+table[0][y][1][bi]
            vals.append(s)
        out.append(("B",y,tuple(vals)))
    return tuple(out)


def correlators(table):
    out=[]
    for x in range(2):
        row=[]
        for y in range(2):
            e=ZERO
            for ai,av in enumerate((-1,1)):
                for bi,bv in enumerate((-1,1)):
                    e=e+Q2.of(av*bv)*table[x][y][ai][bi]
            row.append(e)
        out.append(tuple(row))
    return tuple(out)


def product_of_marginals(table):
    # Uses no-signalling local marginals from y=0/x=0.
    a=[]
    b=[]
    for x in range(2):
        a.append(tuple(table[x][0][ai][0]+table[x][0][ai][1] for ai in range(2)))
    for y in range(2):
        b.append(tuple(table[0][y][0][bi]+table[0][y][1][bi] for bi in range(2)))
    return tuple(tuple(tuple(tuple(a[x][ai]*b[y][bi] for bi in range(2)) for ai in range(2)) for y in range(2)) for x in range(2))
