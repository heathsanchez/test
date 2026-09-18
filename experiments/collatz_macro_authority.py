"""Independent, stdlib-only authority for guarded forward macros.

No imports from the discovery code. A path template is not a universal
lower-merge theorem: every application must replay and prove its own descent.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n'


def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def require(ok, message):
    if not ok: raise ValueError(message)


def contract():
    return {'schema':'guarded-forward-macro-v1','verifier':hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest(),
        'consequence':'positive exact shortcut path with a value below the fixed source',
        'scope':'bounded replay qualification; no universal Collatz claim'}


def capability(word):
    require(isinstance(word,(list,tuple)) and 0<len(word)<=12,'word size')
    word=[list(z) for z in word]
    require(all(len(z)==3 and all(type(x) is int and 1<=x<=256 for x in z)
                for z in word),'episode shape')
    require(all(x[2]==y[0] for x,y in zip(word,word[1:])),'anchor continuity')
    slope,offset=Fraction(1),Fraction(0)
    D=0
    for r,s,rp in word:
        factor=Fraction(3**r,2**(s+rp))
        slope,offset=factor*slope,factor*offset+Fraction(2**s-1,2**(s+rp))
        D+=s+rp
    c={'word':word,'r0':word[0][0],'r1':word[-1][2],
       'A':int(slope*2**D),'B':int(offset*2**D),'D':D,
       'steps':sum(r+s for r,s,rp in word)}
    c['id']=digest(c)
    return c


def verify_capability(c):
    require(c==capability(c['word']),'capability coefficient or identity mismatch')


def seal(caps,revocations=()):
    for c in caps: verify_capability(c)
    require(len({c['id'] for c in caps})==len(caps),'duplicate capability')
    require(set(revocations)<={c['id'] for c in caps},'unknown revocation')
    # Order is part of the policy: preserve the original discovery order.
    obj={'contract':contract(),'capabilities':caps,'revocations':sorted(set(revocations))}
    return dict(obj,digest=digest(obj))


def restore(text):
    obj=json.loads(text)
    require(set(obj)=={'contract','capabilities','revocations','digest'},'bank schema')
    require(text==canonical(obj),'noncanonical restart')
    require(obj['contract']==contract(),'stale authority or contract')
    require(obj==seal(obj['capabilities'],obj['revocations']),'bank digest or content mismatch')
    return obj


def active(bank):
    revoked=set(bank['revocations'])
    return [c for c in bank['capabilities'] if c['id'] not in revoked]


def step(x):
    require(type(x) is int and x>0,'positive ordinary integer required')
    return (3*x+1)//2 if x%2 else x//2


def valuation(x):
    require(x>0,'valuation domain')
    count=0
    while x%2==0:x//=2;count+=1
    return count


def replay(c,m):
    require(type(m) is int and m>0 and m%2==1,'odd positive parameter')
    x=2**c['r0']*m-1
    minimum=x;arg=0;steps=0
    for r,s,rp in c['word']:
        if x%2!=1 or valuation(x+1)!=r:
            return {'legal':False,'steps':steps}
        for parity,count in [(1,r),(0,s)]:
            for _ in range(count):
                if x%2!=parity:return {'legal':False,'steps':steps}
                x=step(x);steps+=1
                if x<minimum:minimum=x;arg=steps
        if x%2!=1 or valuation(x+1)!=rp:
            return {'legal':False,'steps':steps}
    require((x+1)//2**c['r1']*2**c['D']==c['A']*m+c['B'],
            'affine identity mismatch')
    return {'legal':True,'steps':steps,'minimum':minimum,'arg':arg,'endpoint':x}


def verify_descent(n,t,y):
    require(type(t) is int and 0<t<=100000,'certificate step bound')
    x=n
    for _ in range(t):x=step(x)
    require(x==y and 0<y<n,'invalid direct lower merge')
    return True
