#!/usr/bin/env python3
"""Exact polynomial experiment on a periodic scalar conservation-law grid.

This is a finite-volume Burgers analogue, NOT a Navier--Stokes theorem.
The constructor language (polynomials and boundary-flux contrasts) is supplied.
The residual is derived from the equations, not supplied as a target feature.
"""
from __future__ import annotations
from fractions import Fraction
from itertools import product
import json
import unittest

# Sparse polynomials: exponent tuple -> exact rational coefficient.
def add(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
        if not out[k]: del out[k]
    return out

def neg(a): return {k: -v for k, v in a.items()}
def sub(a, b): return add(a, neg(b))
def scale(a, c): return {k: c*v for k, v in a.items() if c*v}
def var(n, i): return {tuple(int(j == i) for j in range(n)): Fraction(1)}
def mul(a, b):
    out = {}
    for x, c in a.items():
        for y, d in b.items():
            k = tuple(i+j for i, j in zip(x, y))
            out[k] = out.get(k, 0) + c*d
    return {k:v for k,v in out.items() if v}
def power(a, k):
    n = len(next(iter(a)))
    out = {(0,)*n: Fraction(1)}
    for _ in range(k): out = mul(out, a)
    return out

def primitive(p):
    """Canonical rational polynomial, up to nonzero scalar."""
    if not p: return {}, Fraction(0)
    from math import gcd, lcm
    den = lcm(*(v.denominator for v in p.values()))
    nums = [int(v*den) for v in p.values()]
    g = gcd(*nums)
    first = p[sorted(p)[0]]
    factor = Fraction(g, den) * (1 if first > 0 else -1)
    return scale(p, 1/factor), factor

def basis_reduce(p, basis):
    """Exact elimination by leading monomial, retaining all coefficients."""
    q = dict(p)
    for b in basis:
        if not b: continue
        pivot = sorted(b)[0]
        if pivot in q:
            q = sub(q, scale(b, q[pivot]/b[pivot]))
    return q

def discover(n, exponent):
    assert n >= 4 and n % 2 == 0 and exponent >= 2
    m = n//2
    x = [var(n, i) for i in range(n)]
    flux = [power(v, exponent) for v in x]
    # A conservative semidiscrete law. Physical Burgers uses flux u^2/2;
    # the fixed positive scaling is immaterial to the closure obstruction.
    velocity = [sub(flux[(i-1)%n], flux[i]) for i in range(n)]
    old = [sum_poly(x[:m]), sum_poly(x[m:])]
    consequence = [sum_poly(velocity[:m]), sum_poly(velocity[m:])]
    # Reduce consequences modulo the existing coarse linear observations.
    basis = [primitive(p)[0] for p in old]
    learned = []
    coefficients = []
    for p in consequence:
        r = basis_reduce(p, basis + learned)
        if r:
            feature, _ = primitive(r)
            learned.append(feature)
        coefficients.append(p)
    assert len(learned) == 1, 'The frozen one-feature hypothesis failed'
    feature = learned[0]
    # Lift a discovered contrast to the supplied generic boundary-flux grammar.
    terms = [(k, c) for k,c in feature.items()]
    assert len(terms) == 2, 'No boundary contrast in the supplied grammar'
    assert sorted(abs(c) for _,c in terms) == [1,1]
    assert all(sum(k) == exponent and sum(v != 0 for v in k) == 1 for k,c in terms)
    ports = [next(i for i,v in enumerate(k) if v) for k,c in terms]
    assert set(ports) == {m-1,n-1}, 'The inferred feature is not a block-boundary contrast'
    return {'n':n, 'exponent':exponent, 'feature':feature, 'consequence':consequence,
            'ports':ports, 'rank':len(learned), 'old':old}

def sum_poly(ps):
    out = {}
    for p in ps: out = add(out, p)
    return out

def evaluate(p, values):
    return sum(c * product_value(values, k) for k,c in p.items())
def product_value(values, powers):
    r = 1
    for x, k in zip(values, powers): r *= x**k
    return r

def witness(n, exponent):
    # Same block sums; exchange a unit between a boundary and its neighbour.
    a = [0]*n; b = [0]*n
    a[n//2-1] = 1; b[0] = 1
    assert n//2 > 1
    return a,b

def report():
    train = discover(4,2)
    a,b = witness(4,2)
    assert all(evaluate(p,a) == evaluate(p,b) for p in train['old'])
    assert any(evaluate(p,a) != evaluate(p,b) for p in train['consequence'])
    # Exact polynomial equality is the all-state check, not finite sampling.
    f = train['feature']
    assert all(not basis_reduce(p,train['old']+[f]) for p in train['consequence'])
    assert any(basis_reduce(p,train['old']) for p in train['consequence'])
    # A fresh grid and a fresh nonlinear flux are evaluated only after learning.
    transfer = discover(6,3)
    c,d = witness(6,3)
    assert any(evaluate(p,c) != evaluate(p,d) for p in transfer['consequence'])
    assert set(transfer['ports']) == {2,5}
    # Negative control: a nonconservative local source defeats boundary-flux closure.
    n=4; x=[var(n,i) for i in range(n)]
    source = add(power(x[0],2),power(x[1],2))
    assert basis_reduce(source,train['old']+[train['feature']])
    result = {'scope':'bounded scalar finite-volume analogue; not incompressible Navier--Stokes',
        'train':{'cells':4,'flux_degree':2,'old_closure':'FAIL','learned_rank':1,
                 'feature':format_poly(f),'exact_polynomial_closure':'PASS','ablation':'FAIL'},
        'transfer':{'cells':6,'flux_degree':3,'boundary_ports':transfer['ports'],
                    'exact_polynomial_closure':'PASS'},
        'negative_control':'NONCONSERVATIVE_SOURCE_NOT_CLOSED',
        'limitations':['The polynomial/contrast grammar is supplied.',
                       'One-step projected dynamics, not a closed autonomous coarse evolution.',
                       'No transfer into either large fluid formalization is established.']}
    return result

def format_poly(p):
    return [{'exponents':list(k),'coefficient':str(v)} for k,v in sorted(p.items())]

class Qualification(unittest.TestCase):
    def test_old_obstruction(self):
        r=discover(4,2); a,b=witness(4,2)
        self.assertEqual([evaluate(p,a) for p in r['old']],[evaluate(p,b) for p in r['old']])
        self.assertNotEqual([evaluate(p,a) for p in r['consequence']],[evaluate(p,b) for p in r['consequence']])
    def test_exact_repair(self):
        r=discover(4,2)
        self.assertTrue(all(not basis_reduce(p,r['old']+r['feature'] and [r['feature']]) for p in r['consequence']))
    def test_transfer(self):
        r=discover(6,3)
        self.assertEqual(set(r['ports']),{2,5})
        self.assertTrue(all(not basis_reduce(p,r['old']+[r['feature']]) for p in r['consequence']))
    def test_ablation(self):
        r=discover(4,2)
        self.assertTrue(any(basis_reduce(p,r['old']) for p in r['consequence']))
    def test_negative_control(self):
        r=discover(4,2); x=[var(4,i) for i in range(4)]
        self.assertTrue(basis_reduce(add(power(x[0],2),power(x[1],2)),r['old']+[r['feature']]))
    def test_report(self): self.assertEqual(report()['train']['learned_rank'],1)

if __name__ == '__main__':
    unittest.main() if '--test' in __import__('sys').argv else print(json.dumps(report(),indent=2))
