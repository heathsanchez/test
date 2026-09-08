"""Bounded proof-interface selection, not unrestricted theorem discovery.

The grammar contains the two actual AB arctangent bounds and four weaker
or irrelevant candidate predicates. The target is a conjunction of bounds.
The frozen controller from experiment.py sees only counterexample pairs;
the no-residual control sees the same pass/fail oracle and candidate order.
The chosen source lemmas are subsequently checked on actual Lean source types.
"""
from fractions import Fraction as Q
from itertools import permutations
from collections import Counter
import json, unittest
from experiment import Feature, World, develop, verify, selected

def lower(s):
    x,a=s
    return a >= x-x**3/3

def upper(s):
    x,a=s
    return a <= x

def target(s): return lower(s) and upper(s)

FEATURES=(
    Feature('nonnegative',lambda s:s[1]>=0),
    Feature('coarse_upper',lambda s:s[1]<=2*s[0]),
    Feature('lower',lower),
    Feature('upper_plus_one',lambda s:s[1]<=s[0]+1),
    Feature('coarse_lower',lambda s:s[1]>=-s[0]),
    Feature('upper',upper))

# Three predeclared separating valuations, not approximate arctan samples.
# The actual arctangent theorem is a separate universal Lean obligation.
TRAIN=((Q(1),Q(1)),(Q(1),Q(0)),(Q(1),Q(2)))
HELDOUT=tuple((x,a) for x in (Q(0),Q(1,2),Q(1),Q(2))
    for a in (Q(0),Q(1,4),Q(1,2),Q(1),Q(3,2),Q(2),Q(3)))
WORLD=World('source_angle_bounds',TRAIN,HELDOUT,lambda s:s[0],target,FEATURES)

def report():
    r=develop(WORLD,FEATURES,True,2)
    b=develop(WORLD,FEATURES,False,2)
    assert r['status']=='PASS'
    assert set(r['features'])=={'lower','upper'}
    assert verify(WORLD,selected(WORLD,r['features']),HELDOUT) is None
    assert verify(WORLD,selected(WORLD,('lower',)),HELDOUT) is not None
    assert verify(WORLD,selected(WORLD,('upper',)),HELDOUT) is not None
    counts={m:Counter() for m in ('residual','blind')}
    for order in permutations(FEATURES):
        for mode in counts:
            rr=develop(WORLD,order,mode=='residual',2)
            counts[mode][rr['status']]+=1
    return {'scope':'finite candidate-axiom selection; source estimates supplied',
      'source':'tristanbuckmaster/fluid_lean@d0124689230b58b4f86e7b90ac59de06404b3b6b',
      'target':'openai/NavierStokesAndEuler@8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538/NavierStokes/PolarCharts.lean',
      'controller':'unchanged experiment.develop', 'budget':2,
      'training_states':len(TRAIN),'heldout_states':len(HELDOUT),
      'residual':r,'blind':b,'orderings':{m:dict(c) for m,c in counts.items()},
      'selected_capabilities':list(r['features']),
      'limitations':['The candidate grammar includes the known source estimates.',
        'The finite predicate test is not a proof of the arctangent inequalities.',
        'The Lean target is a new local-chart bound, not a missing blow-up lemma.',
        'The selection experiment does not prove that the target cannot be derived by another method.']}

class Tests(unittest.TestCase):
    def test_frozen_controller(self):
        self.assertEqual(set(report()['selected_capabilities']),{'lower','upper'})
    def test_heldout_and_ablation(self):
        fs=selected(WORLD,('lower','upper'))
        self.assertIsNone(verify(WORLD,fs,HELDOUT))
        for f in fs:
            self.assertIsNotNone(verify(WORLD,tuple(g for g in fs if g!=f),HELDOUT))
    def test_all_orderings(self):
        r=report()
        self.assertEqual(sum(r['orderings']['residual'].values()),720)
        self.assertEqual(sum(r['orderings']['blind'].values()),720)

if __name__=='__main__':
    import sys
    if '--test' in sys.argv: unittest.main(argv=[sys.argv[0]])
    else: print(json.dumps(report(),indent=2,default=list))
