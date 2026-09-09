"""Unknown-form qualification using the unchanged experiment.develop.

The generator has no protected-target import. This module is the evaluator:
it receives the oracle and compares residual versus pass/fail-only selection.
"""
from __future__ import annotations
from collections import Counter
from itertools import permutations
from dataclasses import replace
import json, unittest
from experiment import Feature, develop, verify, selected, minimal_subsets
from form_synthesis import generate, validate, certify, Candidate, solve_linear_certificate
from form_oracle import world, obstruction, UPPER, HELDOUT, TRAIN
from proof_bridge import report as baseline_report
from fractions import Fraction as Q

BUDGET=2

def qualification():
    candidates,rejected,duplicates=generate()
    features=tuple(Feature(c.name,c.lower) for c in candidates)
    w=world((UPPER,)+features)
    initial=(UPPER,)
    before=obstruction()
    residual=develop(w,features,True,BUDGET,initial)
    blind=develop(w,features,False,BUDGET,initial)
    learned=selected(w,residual['features'])
    heldout_witness=verify(w,learned,HELDOUT)
    ablation=[]
    for f in learned:
        if f.name==UPPER.name:continue
        rest=tuple(g for g in learned if g.name!=f.name)
        ablation.append({'feature':f.name,'witness':verify(w,rest,HELDOUT)})
    counts={m:Counter() for m in ('residual','blind')}
    for order in permutations(features):
        for mode in counts:
            r=develop(w,order,mode=='residual',BUDGET,initial)
            counts[mode][r['status']]+=1
    k,minimum=minimal_subsets(w)
    chosen=[c for c in candidates if c.name in residual['features']]
    return {'status':'PASS' if residual['status']=='PASS' and heldout_witness is None else 'NOT_QUALIFIED',
      'scope':'bounded expression and exact derivative-certificate grammar',
      'controller':'unchanged experiment.develop',
      'controller_blob':'5d28426f2ce50032a5b291d20c93bc7acd0ff4b5',
      'grammar':{'slopes':[str(x) for x in __import__('form_synthesis').SLOPES],
                 'exponents':list(__import__('form_synthesis').EXPONENTS),
                 'budget':BUDGET,'syntax_choices':20,'certified':len(candidates),
                 'rejected':rejected,'duplicates':duplicates},
      'candidates':[c.record() for c in candidates],
      'before':before,'residual':residual,'blind':blind,
      'selected':[c.record() for c in chosen],
      'training_states':len(TRAIN),'heldout_states':len(HELDOUT),
      'heldout_witness':heldout_witness,'ablation':ablation,
      'minimum_feature_count':k,'minimum_subsets':minimum,
      'orderings':{m:dict(c) for m,c in counts.items()},
      'limitations':['The benchmark designer knows the withheld source theorem.',
        'The expression grammar and derivative proof method are supplied.',
        'Coefficientwise positivity is sufficient, not a complete positivity decision procedure.',
        'The generator is new; the residual selector is unchanged.',
        'Finite predicate adequacy is distinct from universal Lean proof.',
        'No original blow-up lemma is repaired and no new Navier-Stokes theorem is claimed.']}

def report():
    r=qualification()
    r['previous_baseline']=baseline_report()['orderings']
    return r

class Tests(unittest.TestCase):
    def test_exact_synthesis_and_rejection(self):
        cs,rejected,duplicates=generate()
        self.assertEqual(len(cs)+len(rejected)+len(duplicates),20)
        self.assertTrue(all(validate(c) for c in cs))
        self.assertIsNone(solve_linear_certificate({0:Q(-1)},{}))
        for c in cs:
            self.assertEqual(certify(c.slope,c.exponent),c)
    def test_no_target_import_in_generator(self):
        import ast,inspect,form_synthesis
        names=[n.module for n in ast.walk(ast.parse(inspect.getsource(form_synthesis)))
               if isinstance(n,ast.ImportFrom)]
        self.assertNotIn('proof_bridge',names)
        self.assertNotIn('form_oracle',names)
        self.assertNotIn('heldout_recovery',names)
    def test_frozen_controller_and_ablation(self):
        r=qualification()
        self.assertEqual(r['controller_blob'],'5d28426f2ce50032a5b291d20c93bc7acd0ff4b5')
        self.assertEqual(r['before']['status'],'GRAMMAR_INSUFFICIENT')
        self.assertIsNone(r['heldout_witness'])
        self.assertTrue(all(a['witness'] is not None for a in r['ablation']))
    def test_all_orderings_and_fair_budget(self):
        r=qualification()
        n=r['grammar']['certified']
        import math
        self.assertEqual(sum(r['orderings']['residual'].values()),math.factorial(n))
        self.assertEqual(sum(r['orderings']['blind'].values()),math.factorial(n))
        self.assertEqual(r['grammar']['budget'],BUDGET)
    def test_exact_json(self):
        self.assertEqual(json.loads(json.dumps(report(),default=str))['status'],'PASS')

if __name__=='__main__':
    import sys
    if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]])
    else:print(json.dumps(report(),indent=2,default=str))
