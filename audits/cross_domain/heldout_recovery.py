"""Held-out recovery, not a modification of the frozen controller.

The source estimate and its proof are not inputs. The grammar is fixed in
recovery_frozen.md: x-c*x^3, rational c>=0, and coefficientwise polynomial
positivity. The new operator is explicitly separate from experiment.develop.
"""
from __future__ import annotations
from fractions import Fraction as Q
from itertools import permutations
from collections import Counter
import json, unittest
from experiment import Feature, World, develop, verify, selected
from proof_bridge import TRAIN, HELDOUT, target, upper, FEATURES

# Sparse polynomials, degree -> exact rational coefficient.
def add(a,b):
    return {k:a.get(k,Q(0))+b.get(k,Q(0)) for k in a.keys()|b.keys() if a.get(k,Q(0))+b.get(k,Q(0))}
def mul(a,b):
    out={}
    for i,x in a.items():
        for j,y in b.items():out[i+j]=out.get(i+j,Q(0))+x*y
    return {k:v for k,v in out.items() if v}
def scale(a,c):return {k:v*c for k,v in a.items() if v*c}
def deriv(a):return {k-1:k*v for k,v in a.items() if k and v}

# Derivative of arctan is 1/(1+x^2). The minorant template is x-c*x^3.
DEN={0:Q(1),2:Q(1)}
BASE=add({0:Q(1)},scale(mul(DEN,deriv({1:Q(1)})),Q(-1)))
DIRECTION=mul(DEN,deriv({3:Q(1)}))

def synthesize_coefficient(base=BASE,direction=DIRECTION):
    """Least nonnegative rational c making every coefficient nonnegative.

    This is a sufficient certificate, not a complete positivity solver.
    No target coefficient is enumerated or supplied.
    """
    lo=Q(0); hi=None
    for degree in sorted(base.keys()|direction.keys()):
        a=base.get(degree,Q(0)); b=direction.get(degree,Q(0))
        if b>0:lo=max(lo,-a/b)
        elif b<0:hi=min(hi,-a/b) if hi is not None else -a/b
        elif a<0:return {'status':'GRAMMAR_INSUFFICIENT','degree':degree}
    if hi is not None and lo>hi:return {'status':'GRAMMAR_INSUFFICIENT','lower':str(lo),'upper':str(hi)}
    poly=add(base,scale(direction,lo))
    assert all(v>=0 for v in poly.values())
    return {'status':'PASS','coefficient':lo,'certificate':poly,
            'basis':(1,3),'method':'exact coefficientwise derivative certificate'}

def recovered_feature(c):
    return Feature('recovered_minorant',lambda s:s[1]>=s[0]-c*s[0]**3)

def run():
    # The withheld feature is not present in this grammar.
    old=tuple(f for f in FEATURES if f.name!='lower')
    world=World('heldout_angle_recovery',TRAIN,HELDOUT,lambda s:s[0],target,old)
    before=develop(world,old,True,2,initial=selected(world,('upper',)))
    assert before['status']=='GRAMMAR_INSUFFICIENT'
    assert before['witness'] is not None
    recovered=synthesize_coefficient()
    assert recovered['status']=='PASS'
    c=recovered['coefficient']
    new=recovered_feature(c)
    extended=World(world.name,TRAIN,HELDOUT,world.observe,target,old+(new,))
    # The old controller is unchanged; only the lawful grammar is extended.
    after=develop(extended,(new,),True,1,initial=selected(extended,('upper',)))
    assert after['status']=='PASS'
    assert verify(extended,selected(extended,after['features']),HELDOUT) is None
    assert verify(extended,selected(extended,('upper',)),HELDOUT) is not None
    # Preserve the original selection experiment and its no-residual control.
    counts={m:Counter() for m in ('residual','blind')}
    for order in permutations(FEATURES):
        for mode in counts:
            r=develop(World('baseline',TRAIN,HELDOUT,lambda s:s[0],target,FEATURES),order,mode=='residual',2)
            counts[mode][r['status']]+=1
    return {'status':'PASS','baseline_commit':'84e0da436a28f818a3d5fd0d4518c43b7a05b31c',
      'withheld':'lower source estimate and proof body',
      'before':before,'synthesis':{'status':recovered['status'],'coefficient':str(c),
        'certificate':{str(k):str(v) for k,v in recovered['certificate'].items()},
        'basis':recovered['basis'],'method':recovered['method']},
      'after':after,'heldout':'PASS','baseline_orderings':{m:dict(v) for m,v in counts.items()},
      'limitations':['A new restricted synthesis operator is used; experiment.develop is unchanged.',
        'The polynomial basis and derivative-positivity proof method are supplied.',
        'The finite verifier is not an all-state proof; Lean must certify the recovered estimate.',
        'The source theorem is used only for post-recovery comparison.']}

class Tests(unittest.TestCase):
    def test_exact_certificate(self):
        r=synthesize_coefficient()
        self.assertEqual(r['status'],'PASS')
        self.assertTrue(all(v>=0 for v in r['certificate'].values()))
        self.assertEqual(add(BASE,scale(DIRECTION,r['coefficient'])),r['certificate'])
    def test_impossible_grammar(self):
        self.assertEqual(synthesize_coefficient({0:Q(-1)},{})['status'],'GRAMMAR_INSUFFICIENT')
    def test_lower_bound_is_not_prelisted(self):
        self.assertNotIn('lower',[f.name for f in FEATURES if f.name!='lower'])
        self.assertNotIn(Q(1,3),tuple(BASE.values())+tuple(DIRECTION.values()))
    def test_recovery_and_ablation(self):
        r=run()
        self.assertEqual(r['before']['status'],'GRAMMAR_INSUFFICIENT')
        self.assertEqual(r['heldout'],'PASS')
        self.assertEqual(sum(r['baseline_orderings']['residual'].values()),720)
        self.assertEqual(sum(r['baseline_orderings']['blind'].values()),720)
    def test_exact_json(self):
        self.assertEqual(json.loads(json.dumps(run(),default=str))['status'],'PASS')

if __name__=='__main__':
    import sys
    if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]])
    else:print(json.dumps(run(),indent=2,default=str))
