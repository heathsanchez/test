"""Independent exact replay of the frozen certificate language.

This module does not import the generator, controller or benchmark oracle.
A certificate is data, not executable Python. Every identity and side condition
is reconstructed from rational arithmetic. The Lean gate checks the corresponding
universal mathematical rules separately.
"""
from fractions import Fraction as Q


def norm(p):
    return {int(k): Q(v) for k, v in p.items() if Q(v)}


def add(a, b):
    a, b = norm(a), norm(b)
    return norm({k: a.get(k, Q(0)) + b.get(k, Q(0)) for k in a.keys() | b.keys()})


def mul(a, b):
    out = {}
    for i, x in norm(a).items():
        for j, y in norm(b).items():
            out[i+j] = out.get(i+j, Q(0)) + x*y
    return norm(out)


def scale(a, c):
    return norm({k: v*Q(c) for k, v in norm(a).items()})


def encode(p):
    return {str(k): str(v) for k, v in sorted(norm(p).items())}


def evaluate(p, x):
    return sum((v*Q(x)**k for k, v in norm(p).items()), Q(0))


def replay(c, domain):
    """Return the certified polynomial, or raise ValueError.

    Domains are ('ray',) and ('interval', lower, upper). All coefficients,
    endpoints, factors and claimed identities must be exact rationals.
    """
    kind = c['kind']
    if kind == 'coeff':
        p = norm(c['polynomial'])
        if any(k < 0 or v < 0 for k, v in p.items()): raise ValueError('coefficients')
        if domain[0] == 'interval' and Q(domain[1]) < 0: raise ValueError('negative domain')
        return p
    if kind == 'square':
        k, a, r, d = int(c['power']), Q(c['A']), Q(c['r']), Q(c['D'])
        if k < 0 or a < 0 or d < 0: raise ValueError('square side condition')
        if domain[0] == 'interval' and Q(domain[1]) < 0: raise ValueError('negative domain')
        return norm({j+k: v for j, v in {0:a*r*r+d, 1:-2*a*r, 2:a}.items()})
    if kind == 'affine':
        if domain[0] != 'interval': raise ValueError('affine requires interval')
        l, u = Q(domain[1]), Q(domain[2])
        if l > u: raise ValueError('reversed interval')
        a, b = Q(c['a']), Q(c['b'])
        if a*l+b < 0 or a*u+b < 0: raise ValueError('endpoint positivity')
        return norm({0:b,1:a})
    if kind in ('sum', 'product'):
        children = c['children']
        if not children: raise ValueError('empty combination')
        result = {} if kind == 'sum' else {0:Q(1)}
        for child in children:
            p = replay(child, domain)
            result = add(result,p) if kind == 'sum' else mul(result,p)
        return result
    raise ValueError('unknown constructor')


def verify(p, domain, certificate):
    try:
        return replay(certificate, domain) == norm(p)
    except (ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError):
        return False
