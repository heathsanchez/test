"""Finite, exact, consequence-driven recovery of quadratic flux observables.
This is a controlled two-cell model, not a Navier--Stokes solver.
"""
from itertools import product, combinations
from fractions import Fraction
import json, hashlib, unittest, argparse
from pathlib import Path

VALUES = range(-2, 3)
STATES = tuple(product(VALUES, repeat=4))
FEATURES = ((0,0),(0,1),(1,1))

def mean(s): return (s[0]+s[2], s[1]+s[3])
def flux(s): return tuple(s[i]*s[j]+s[i+2]*s[j+2] for i,j in FEATURES)
def feature(s, ij):
    i,j=ij
    return s[i]*s[j]+s[i+2]*s[j+2]
def observation(s, chosen): return mean(s)+tuple(feature(s,c) for c in chosen)
def residual(states, chosen):
    seen={}
    for s in states:
        k=observation(s,chosen)
        if k in seen and flux(seen[k])!=flux(s): return seen[k],s
        seen.setdefault(k,s)
    return None

def discover(states=STATES):
    # Fixed grammar: raw symmetric quadratic moments. No stress names or target-specific policy.
    # Search by arity; use the verifier's first separating pair to reject each insufficient interface.
    rejected=[]
    for size in range(len(FEATURES)+1):
        for chosen in combinations(FEATURES,size):
            witness=residual(states,chosen)
            if witness is None:
                return chosen,rejected
            rejected.append({'features':chosen,'witness':witness,'consequences':[flux(x) for x in witness]})
    raise RuntimeError('No sufficient interface in grammar')

def burg_derivative(u):
    return tuple(-(u[i]**2-u[(i-1)%3]**2) for i in range(3))
def burg_moments(u): return sum(u),sum(x*x for x in u)
def burg_q_derivative(u): return 2*sum(x*d for x,d in zip(u,burg_derivative(u)))

def report():
    selected,rejected=discover()
    heldout=tuple(product(range(-3,4),repeat=4))
    assert residual(heldout,selected) is None
    ablation=[]
    for f in selected:
        r=residual(STATES,tuple(x for x in selected if x!=f))
        assert r is not None
        ablation.append({'removed':f,'witness':r,'consequences':[flux(x) for x in r]})
    a=(1,1,-2); b=(-1,-1,2)
    assert burg_moments(a)==burg_moments(b)
    assert burg_q_derivative(a)!=burg_q_derivative(b)
    result={'scope':'two-cell quadratic flux; three-cell semidiscrete Burgers boundary',
       'training_states':len(STATES),'heldout_states':len(heldout),
       'grammar':FEATURES,'selected':selected,'rejected':rejected,'ablation':ablation,
       'dynamic_boundary':{'a':a,'b':b,'moments':burg_moments(a),'derivatives':[burg_q_derivative(a),burg_q_derivative(b)]},
       'claims':['finite-grammar minimality','held-out exact replay','ablation','higher-moment closure obstruction'],
       'not_claimed':['arbitrary grammar discovery','Navier-Stokes existence or blow-up','full dynamical closure']}
    return result

class Qualification(unittest.TestCase):
    def test_discovery(self): self.assertEqual(discover()[0],FEATURES)
    def test_all_smaller_interfaces_fail(self):
        for n in range(3):
            for c in combinations(FEATURES,n): self.assertIsNotNone(residual(STATES,c))
    def test_heldout(self):
        self.assertIsNone(residual(tuple(product(range(-3,4),repeat=4)),FEATURES))
    def test_ablation(self):
        for f in FEATURES: self.assertIsNotNone(residual(STATES,tuple(x for x in FEATURES if x!=f)))
    def test_no_unearned_capability(self): self.assertIsNotNone(residual(STATES,()))
    def test_dynamic_boundary(self):
        a=(1,1,-2);b=(-1,-1,2)
        self.assertEqual(burg_moments(a),burg_moments(b))
        self.assertEqual((burg_q_derivative(a),burg_q_derivative(b)),(18,-18))
    def test_conservation(self):
        for u in product(range(-2,3),repeat=3): self.assertEqual(sum(burg_derivative(u)),0)
    def test_exact_identity(self):
        for s in STATES:
            m=mean(s)
            for i,j in FEATURES:
                self.assertEqual(2*feature(s,(i,j))-m[i]*m[j],(s[i]-s[i+2])*(s[j]-s[j+2]))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',action='store_true');args=p.parse_args()
    if args.report:
        r=report();Path('result.json').write_text(json.dumps(r,indent=2)+'\n')
        print('DISCOVERY_PASS',r['selected']);print('REJECTED',len(r['rejected']));print('HELDOUT',r['heldout_states']);print('ABLATION',len(r['ablation']));print('DYNAMIC_BOUNDARY',r['dynamic_boundary']);print('RESULT_SHA256',hashlib.sha256(Path('result.json').read_bytes()).hexdigest())
    else: unittest.main()
