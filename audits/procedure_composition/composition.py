"""Bounded synthesis of reusable certificate programs from lower-level primitives.
No finished repair builder or target-name dispatch is available to the generator.
"""
from __future__ import annotations
from fractions import Fraction as Q
from dataclasses import dataclass
from pathlib import Path
from time import process_time
import json, math, sys, unittest
import sympy as sp
import checker
from experiment import Feature, World, develop

ROOT=Path(__file__).resolve().parent
LIMITS=json.loads((ROOT/'LIMITS.json').read_text())
X=sp.Symbol('x')
PRIMS=tuple(LIMITS['primitive_order'])
OPS=tuple(LIMITS['combinator_order'])
replay=checker.replay

def norm(p):return {int(k):Q(v) for k,v in p.items() if Q(v)}
def add(a,b):
    a,b=norm(a),norm(b)
    return norm({k:a.get(k,Q(0))+b.get(k,Q(0)) for k in a.keys()|b.keys()})
def mul(a,b):
    out={}
    for i,x in norm(a).items():
        for j,y in norm(b).items():out[i+j]=out.get(i+j,Q(0))+x*y
    return norm(out)
def scale(p,c):return norm({k:v*Q(c) for k,v in norm(p).items()})
def encode(p):return {str(k):str(v) for k,v in sorted(norm(p).items())}
def degree(p):return max(norm(p),default=0)
def coeff(p,k):return norm(p).get(k,Q(0))
def to_sym(p):return sum(sp.Rational(v.numerator,v.denominator)*X**k for k,v in norm(p).items())
def from_sym(e):
    p=sp.Poly(sp.expand(e),X,domain=sp.QQ)
    return norm({int(k[0]):Q(int(v.p),int(v.q)) for k,v in p.terms()})
def rational_sqrt(q):
    q=Q(q)
    if q<0:return None
    a,b=math.isqrt(q.numerator),math.isqrt(q.denominator)
    return Q(a,b) if a*a==q.numerator and b*b==q.denominator else None

def nodes(t):return 1 if len(t)==1 else 1+nodes(t[1])+nodes(t[2])
def leaves(t):return (t[0],) if len(t)==1 else leaves(t[1])+leaves(t[2])
def shapes(domain):
    leaves_=tuple((n,) for n in PRIMS if n!='affine' or domain[0]=='interval')
    trees=list(leaves_)
    for op in OPS:
        for i,a in enumerate(leaves_):
            for b in leaves_[i:]:trees.append((op,a,b))
    assert all(nodes(t)<=LIMITS['maximum_tree_nodes'] for t in trees)
    return tuple(trees)
def possible_degrees(t,domain):
    if len(t)==1:
        return {'constant':{0},'monomial':set(range(5)),'square':{0,2},'affine':{0,1}}[t[0]]
    a,b=possible_degrees(t[1],domain),possible_degrees(t[2],domain)
    if t[0]=='product':return {i+j for i in a for j in b if i+j<=4}
    return ({max(i,j) for i in a for j in b} if domain[0]=='ray'
            else set(range(max(max(a),max(b))+1)))
def forced_zero(t):
    return False if len(t)==1 else (t[0]=='product' and (forced_zero(t[1]) or forced_zero(t[2])))
def necessity(t,p,domain):
    p=norm(p);d=degree(p)
    if d not in possible_degrees(t,domain):return 'degree'
    if coeff(p,0)!=0 and forced_zero(t):return 'nonzero_constant'
    if any(v<0 for v in p.values()) and not set(leaves(t))&{'square','affine'}:
        return 'negative_coefficient'
    return None

class Budget(Exception):pass
class Meter:
    def __init__(self,limit=None):
        self.limit=LIMITS['total_semantic_checks'] if limit is None else limit
        self.calls=0;self.events=[]
    def reserve(self,n):
        if self.calls+n>self.limit:raise Budget()
    def charge(self,kind,**data):
        if self.calls>=self.limit:raise Budget()
        self.calls+=1;self.events.append({'check':self.calls,'kind':kind,**data})

def factor_options(p):
    """Exact rational factor partitions, bounded by the frozen algebraic limit."""
    p=norm(p)
    if not p:return []
    c,fs=sp.factor_list(to_sym(p),X)
    factors=[]
    for f,m in fs:factors += [sp.expand(f)]*int(m)
    out=[];seen=set()
    for mask in range(1<<len(factors)):
        a=sp.Integer(1);b=sp.Integer(1)
        for i,f in enumerate(factors):
            if mask>>i&1:a*=f
            else:b*=f
        for sign in (1,-1):
            for left,right in ((sign*c*a,sign*b),(sign*a,sign*c*b)):
                pair=(tuple(sorted(from_sym(left).items())),tuple(sorted(from_sym(right).items())))
                if pair not in seen:
                    seen.add(pair);out.append((dict(pair[0]),dict(pair[1])))
    return out[:LIMITS['maximum_factor_options']]
def sum_options(p):
    p=norm(p);out=[]
    for k,v in sorted(p.items()):
        if v>0:out.append(({k:v},add(p,{k:-v})))
    for a,b in factor_options(p):
        for f in (a,b):
            if degree(f)==2 and rational_sqrt(coeff(f,2)) is not None:
                out.append((f,add(p,scale(f,-1))))
    seen=set();unique=[]
    for a,b in out:
        key=(tuple(sorted(a.items())),tuple(sorted(b.items())))
        if key not in seen and a and b:seen.add(key);unique.append((a,b))
    return unique[:LIMITS['maximum_sum_options']]

def solve(t,p,domain,meter):
    p=norm(p);meter.charge('candidate_solve',shape=t,polynomial=encode(p))
    kind=t[0]
    if len(t)==1:
        d=degree(p)
        if kind=='constant':
            return {'kind':'constant','c':str(coeff(p,0))} if d==0 and coeff(p,0)>=0 else None
        if kind=='monomial':
            return {'kind':'monomial','power':d,'c':str(coeff(p,d))} if (domain[0]=='ray' or Q(domain[1])>=0) and len(p)==1 and coeff(p,d)>0 else None
        if kind=='square':
            if d not in (0,2):return None
            if d==0:a=Q(0);b=rational_sqrt(coeff(p,0))
            else:
                a=rational_sqrt(coeff(p,2))
                if a is None or a==0:return None
                b=coeff(p,1)/(2*a)
                if b*b!=coeff(p,0):return None
            return {'kind':'square','a':str(a),'b':str(b)} if b is not None else None
        if kind=='affine':
            if domain[0]!='interval' or d>1:return None
            a,b=coeff(p,1),coeff(p,0);l,u=Q(domain[1]),Q(domain[2])
            return {'kind':'affine','a':str(a),'b':str(b)} if l<=u and a*l+b>=0 and a*u+b>=0 else None
        raise ValueError(kind)
    options=factor_options(p) if kind=='product' else sum_options(p)
    for a,b in options:
        if necessity(t[1],a,domain) or necessity(t[2],b,domain):continue
        left=solve(t[1],a,domain,meter)
        if left is None:continue
        right=solve(t[2],b,domain,meter)
        if right is not None:return {'kind':kind,'children':[left,right]}
    return None

def checked(c,p,domain,meter):
    meter.charge('independent_replay',polynomial=encode(p))
    return checker.verify(c,p,domain)
def baseline(p,domain,meter):
    meter.charge('initial_verifier',polynomial=encode(p));p=norm(p)
    return None if all(v>=0 for v in p.values()) and (domain[0]=='ray' or Q(domain[1])>=0) else {'polynomial':encode(p),'domain':[str(x) for x in domain],'degree':degree(p),'negative_coefficients':[k for k,v in p.items() if v<0],'constant':str(coeff(p,0))}
@dataclass(frozen=True)
class Program:
    tree:tuple
    def __call__(self,p,domain,meter):return solve(self.tree,p,domain,meter)
def stages():
    return (({1:Q(1,2),2:Q(-1),3:Q(1,2)},('ray',)),({0:Q(1),2:Q(-1)},('interval',Q(0),Q(1))))
def heldouts(i):
    return ((({0:Q(2),1:Q(-4),2:Q(2)},('ray',)),({1:Q(3),2:Q(-6),3:Q(3)},('ray',))),
            (({0:Q(4),1:Q(-4)},('interval',Q(0),Q(1))),({0:Q(-6),1:Q(5),2:Q(-1)},('interval',Q(2),Q(3)))))[i]

def propose(remaining,p,domain,residuals,meter):
    # This adapter proposes a structural candidate; it does not prebuild a proof.
    meter.reserve(2)
    fs=tuple(Feature(str(i),lambda state,t=t:bool(state[1] and necessity(t,p,domain) is None)) for i,t in enumerate(remaining))
    w=World('structural_repair_proposal',((0,False),(0,True)),((0,False),(0,True)),lambda s:s[0],lambda s:s[1],fs)
    r=develop(w,fs,residuals,1)
    for _ in range(r['calls']):meter.charge('controller_verifier',status=r['status'])
    return remaining[int(r['features'][0])] if r['features'] else None

def run(residuals=True,order=None):
    meter=Meter();installed=[];reports=[];start=process_time()
    try:
        for i,(p,domain) in enumerate(stages()):
            initial=baseline(p,domain,meter)
            assert initial is not None
            if installed:
                for prog in installed:
                    c=prog(p,domain,meter)
                    if c is not None and checked(c,p,domain,meter):raise AssertionError('prior procedure already sufficient')
            candidates=shapes(domain)
            if order is not None:candidates=tuple(t for t in order if t in candidates)
            pruned=[];chosen=None;certificate=None;remaining=list(candidates)
            while remaining:
                if residuals:
                    for t in remaining:
                        reason=necessity(t,p,domain)
                        if reason:pruned.append({'tree':t,'reason':reason})
                t=propose(tuple(remaining),p,domain,residuals,meter)
                if t is None:break
                remaining.remove(t)
                c=Program(t)(p,domain,meter)
                if c is not None and checked(c,p,domain,meter):chosen=Program(t);certificate=c;break
            if chosen is None:return {'status':'NOT_FINISHED','stage':i,'completed_stages':reports,'checks':meter.calls,'trace':meter.events,'pruned':pruned,'cpu_seconds':process_time()-start}
            if not checked(certificate,p,domain,meter):raise AssertionError('promotion replay')
            installed.append(chosen)
            reuse=[]
            for hp,hd in heldouts(i):
                c=chosen(hp,hd,meter)
                if c is None or not checked(c,hp,hd,meter):raise AssertionError('heldout failure')
                reuse.append({'polynomial':encode(hp),'domain':[str(x) for x in hd],'certificate':c})
            witness=baseline(p,domain,meter)
            if witness is None:raise AssertionError('ablation unexpectedly sufficient')
            for prog in installed[:-1]:
                c=prog(p,domain,meter)
                if c is not None and checked(c,p,domain,meter):raise AssertionError('ablation unexpectedly sufficient')
            reports.append({'polynomial':encode(p),'domain':[str(x) for x in domain],'before':initial,'program':chosen.tree,'certificate':certificate,'reuse':reuse,'ablation':'FAIL_WITHOUT_NEW_PROGRAM','pruned':pruned})
        return {'status':'PASS','stages':reports,'checks':meter.calls,'trace':meter.events,'cpu_seconds':process_time()-start}
    except Budget:
        return {'status':'BUDGET','stage':len(reports),'completed_stages':reports,'checks':meter.calls,'trace':meter.events,'cpu_seconds':process_time()-start}

def qualification():
    r=run(True);b=run(False)
    return {'status':r['status'],'scope':'bounded constructor composition','limits':LIMITS,'residual':r,'blind':b,'controller_blob':'5d28426f2ce50032a5b291d20c93bc7acd0ff4b5','limitations':['The supplied algebraic solver and primitive grammar are not invented.','The budget counts semantic checks, not equal CPU time.','The unchanged selector proposes structural candidates; the new bounded solver constructs and certifies them.','The Python synthesizer is not formally verified.','No essential blow-up lemma is repaired.']}
class Tests(unittest.TestCase):
    def test_grammar(self):
        self.assertEqual(len(shapes(('ray',))),15);self.assertEqual(len(shapes(('interval',Q(0),Q(1)))),24)
    def test_replay_rejects_forgery(self):
        self.assertEqual(replay({'kind':'square','a':'1','b':'-1'},('ray',)),{0:Q(1),1:Q(-2),2:Q(1)})
        with self.assertRaises(ValueError):replay({'kind':'affine','a':'-1','b':'0'},('interval',Q(0),Q(1)))
    def test_generic_reuse(self):
        for t,p,d in [(('product',('monomial',),('square',)),{1:Q(3),2:Q(-6),3:Q(3)},('ray',)),(('product',('affine',),('affine',)),{0:Q(1),2:Q(-1)},('interval',Q(0),Q(1)))]:
            m=Meter();c=Program(t)(p,d,m)
            self.assertIsNotNone(c);self.assertTrue(checked(c,p,d,m))
    def test_qualification(self):
        r=qualification();self.assertIn(r['status'],('PASS','BUDGET','NOT_FINISHED'))
        if r['status']=='PASS':self.assertEqual(len(r['residual']['stages']),2)
        self.assertLessEqual(r['residual']['checks'],LIMITS['total_semantic_checks'])
        self.assertLessEqual(r['blind']['checks'],LIMITS['total_semantic_checks'])
if __name__=='__main__':
    if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]])
    else:print(json.dumps(qualification(),indent=2,default=str))
