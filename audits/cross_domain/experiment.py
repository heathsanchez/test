"""Frozen finite residual-repair qualification across algebra and fluid fluxes.

Only a declared feature grammar is searched. The verifier sees the complete
finite universe; the controller sees no domain-specific feature names. A
no-residual control receives the same pass/fail oracle and candidate order.
Finite adequacy is not an all-state theorem or unrestricted discovery.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product, combinations, permutations
from collections import Counter
import json, unittest

@dataclass(frozen=True)
class Feature:
    name: str
    fn: object

@dataclass(frozen=True)
class World:
    name: str
    train: tuple
    heldout: tuple
    observe: object
    consequence: object
    features: tuple

def observation(world, chosen, state):
    return (world.observe(state),) + tuple(f.fn(state) for f in chosen)

def verify(world, chosen, states=None):
    """First exact counterexample, or None. No target-specific branch."""
    seen = {}
    for state in world.train if states is None else states:
        key = observation(world, chosen, state)
        value = world.consequence(state)
        if key in seen and seen[key][1] != value:
            return seen[key][0], state
        seen.setdefault(key, (state, value))
    return None

def develop(world, order, residuals=True, budget=None, initial=()):
    """Same verifier and feature budget. Only returned information differs."""
    chosen = list(initial)
    calls = 0
    trace = []
    budget = len(order) if budget is None else budget
    while True:
        w = verify(world, chosen)
        calls += 1
        if w is None:
            return {'status':'PASS', 'features':tuple(f.name for f in chosen),
                    'calls':calls,'trace':trace}
        if len(chosen) - len(initial) >= budget:
            return {'status':'BUDGET', 'features':tuple(f.name for f in chosen),
                    'calls':calls,'trace':trace}
        unused = [f for f in order if f not in chosen]
        if residuals:
            available = [f for f in unused if f.fn(w[0]) != f.fn(w[1])]
            if not available:
                return {'status':'GRAMMAR_INSUFFICIENT','features':tuple(f.name for f in chosen),
                        'calls':calls,'trace':trace,'witness':w}
            f = available[0]
        else:
            if not unused:
                return {'status':'GRAMMAR_INSUFFICIENT','features':tuple(f.name for f in chosen),
                        'calls':calls,'trace':trace}
            f = unused[0]
        trace.append({'feature':f.name,'witness':w if residuals else None})
        chosen.append(f)

def selected(world, names):
    return tuple(f for n in names for f in world.features if f.name == n)

def minimal_subsets(world):
    for k in range(len(world.features)+1):
        found = [tuple(f.name for f in fs) for fs in combinations(world.features,k)
                 if verify(world,fs) is None]
        if found: return k,found
    return None,[]

# Terms over {a0, f, g}, with variables x and y. The source's head/child
# grammar is extended by raw atomic identity, not a target-specific answer.
def atom(i): return ('var',i)
def node(op,a,b): return (op,a,b)
A=('a0',); X=atom(0); Y=atom(1)
def arity(t): return 2 if t[0] in ('f','g') else 0
def head(t): return t[0]
def child(t,i): return t[i+1] if arity(t)==2 else None
def atomic(t): return t if arity(t)==0 else None
ALG_FEATURES=(Feature('arity',arity),Feature('head',head),
    Feature('child0',lambda t:child(t,0)),Feature('child1',lambda t:child(t,1)),
    Feature('atom',atomic),Feature('is_f',lambda t:t[0]=='f'))
ALG_TRAIN=(A,X,Y,node('f',X,A),node('f',Y,A),node('g',X,A),node('g',Y,A))
ALG_HELDOUT=ALG_TRAIN+(node('f',X,Y),node('f',Y,X),node('g',X,Y),
    node('f',node('g',X,A),Y),node('g',node('f',Y,X),A))
ALG=World('term_structure',ALG_TRAIN,ALG_HELDOUT,arity,lambda t:t,ALG_FEATURES)

# Unnormalised two-cell quadratic flux. The feature grammar contains
# elementary symmetric quadratic components and their linear combinations.
def mean(s): return (s[0]+s[2],s[1]+s[3])
def flux(s): return (s[0]**2+s[2]**2,s[0]*s[1]+s[2]*s[3],s[1]**2+s[3]**2)
FLUID_FEATURES=(Feature('mean_x',lambda s:mean(s)[0]),
    Feature('trace',lambda s:flux(s)[0]+flux(s)[2]),
    Feature('xx',lambda s:flux(s)[0]),Feature('xy',lambda s:flux(s)[1]),
    Feature('yy',lambda s:flux(s)[2]),Feature('difference',lambda s:flux(s)[0]-flux(s)[2]))
FLUID=World('quadratic_flux',tuple(product(range(-2,3),repeat=4)),
    tuple(product(range(-3,4),repeat=4)),mean,flux,FLUID_FEATURES)

def qualification(world, budget=4):
    order=world.features
    residual=develop(world,order,True,budget)
    blind=develop(world,order,False,budget)
    assert residual['status']=='PASS'
    learned=selected(world,residual['features'])
    heldout_witness=verify(world,learned,world.heldout)
    continuation=None
    final=learned
    if heldout_witness is not None:
        heldout_world=World(world.name+'_heldout',world.heldout,world.heldout,
                            world.observe,world.consequence,world.features)
        continuation=develop(heldout_world,order,True,budget,initial=learned)
        if continuation['status']=='PASS':
            final=selected(world,continuation['features'])
    final_witness=verify(world,final,world.heldout)
    k,minimum=minimal_subsets(world)
    ablation=[]
    for f in learned:
        rest=tuple(g for g in learned if g!=f)
        w=verify(world,rest)
        ablation.append({'feature':f.name,'necessary_for_selected':w is not None,'witness':w})
    # Exhaust all 6! feature orders rather than reporting a favorable ordering.
    stats={m:Counter() for m in ('residual','blind')}
    for perm in permutations(order):
        for mode in stats:
            r=develop(world,perm,mode=='residual',budget)
            stats[mode][r['status']]+=1
    return {'world':world.name,'training_states':len(world.train),
        'heldout_states':len(world.heldout),'budget':budget,
        'residual':residual,'blind':blind,'minimum_feature_count':k,
        'minimum_subsets':minimum,'ablation':ablation,
        'heldout_initial_witness':heldout_witness,'continuation':continuation,
        'final_features':tuple(f.name for f in final),'final_witness':final_witness,
        'all_orderings':{m:dict(c) for m,c in stats.items()},
        'heldout':'PASS' if final_witness is None else 'FAIL','scope':'finite declared grammar'}

def report():
    return {'controller':'frozen first-separator refinement',
            'sources':{'msi':'1a8e59d40c21ae8f621e933c858e2d4f794da293',
                       'fluid':'29e6f954f7ae674802d4ad1e91e4c6e4c7a9ddbf'},
            'results':[qualification(ALG),qualification(FLUID)],
            'limitations':['Finite exact adequacy is not all-state adequacy.',
              'The feature grammar is supplied, including atomic identity.',
              'The no-residual control receives pass/fail rather than a counterexample.',
              'No new theorem about incompressible Navier--Stokes is claimed.',
              'No common blow-up mechanism from the two large proofs is established.']}

class Tests(unittest.TestCase):
    def test_generic_recovery(self):
        for w in (ALG,FLUID):
            r=develop(w,w.features)
            self.assertEqual(r['status'],'PASS')
            self.assertIsNone(verify(w,selected(w,r['features'])))
    def test_heldout(self):
        for w in (ALG,FLUID):
            r=develop(w,w.features)
            h=verify(w,selected(w,r['features']),w.heldout)
            if h is not None:
                ww=World(w.name+'_heldout',w.heldout,w.heldout,w.observe,w.consequence,w.features)
                r=develop(ww,w.features,True,initial=selected(w,r['features']))
                self.assertEqual(r['status'],'PASS')
                self.assertIsNone(verify(w,selected(w,r['features']),w.heldout))
    def test_ablation(self):
        for w in (ALG,FLUID):
            r=develop(w,w.features)
            fs=selected(w,r['features'])
            for f in fs:
                self.assertIsNotNone(verify(w,tuple(g for g in fs if g!=f)))
    def test_counterexample_soundness(self):
        for w in (ALG,FLUID):
            for f in w.features:
                pair=verify(w,(f,))
                if pair:
                    a,b=pair
                    self.assertEqual(observation(w,(f,),a),observation(w,(f,),b))
                    self.assertNotEqual(w.consequence(a),w.consequence(b))
    def test_complete_grammar(self):
        for w in (ALG,FLUID): self.assertIsNone(verify(w,w.features))
    def test_report(self):
        self.assertEqual(len(report()['results']),2)

if __name__=='__main__':
    import sys
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]])
    else:
        print(json.dumps(report(),indent=2,default=list))
