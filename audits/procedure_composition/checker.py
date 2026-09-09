"""Independent, data-only exact certificate replay. No synthesis or task imports."""
from fractions import Fraction as Q

def norm(p):return {int(k):Q(v) for k,v in p.items() if Q(v)}
def add(a,b):
    a,b=norm(a),norm(b)
    return norm({k:a.get(k,Q(0))+b.get(k,Q(0)) for k in a.keys()|b.keys()})
def mul(a,b):
    out={}
    for i,x in norm(a).items():
        for j,y in norm(b).items():out[i+j]=out.get(i+j,Q(0))+x*y
    return norm(out)
def replay(c,domain):
    kind=c['kind']
    if kind=='constant':
        v=Q(c['c'])
        if v<0:raise ValueError('constant')
        return norm({0:v})
    if kind=='monomial':
        k,v=int(c['power']),Q(c['c'])
        if k<0 or k>4 or v<0 or (domain[0]=='interval' and Q(domain[1])<0):raise ValueError('monomial')
        return norm({k:v})
    if kind=='square':
        a,b=Q(c['a']),Q(c['b'])
        return norm({2:a*a,1:2*a*b,0:b*b})
    if kind=='affine':
        if domain[0]!='interval':raise ValueError('domain')
        a,b=Q(c['a']),Q(c['b']);l,u=Q(domain[1]),Q(domain[2])
        if l>u or a*l+b<0 or a*u+b<0:raise ValueError('endpoints')
        return norm({1:a,0:b})
    if kind in ('sum','product'):
        children=c['children']
        if len(children)!=2:raise ValueError('arity')
        a,b=(replay(x,domain) for x in children)
        return add(a,b) if kind=='sum' else mul(a,b)
    raise ValueError('constructor')
def verify(c,p,domain):
    try:return replay(c,domain)==norm(p)
    except (ValueError,KeyError,TypeError,ZeroDivisionError,OverflowError):return False
