"""Finite qualification on the independently specified quantitative obligation.
The generator does not import this oracle. The selected universal estimate is
compiled to an entailed threshold feature; this is not raw estimate selection.
"""
from __future__ import annotations
from fractions import Fraction as Q
from itertools import permutations
from collections import Counter
import json,unittest,hashlib
from experiment import Feature,World,develop,verify,selected
from grammar import generate_extensions,validate_extension

THRESHOLD=Q(7,10)
TRAIN=tuple((Q(1),a) for a in (Q(7,10),Q(2,3),Q(1),Q(2)))
HELDOUT=tuple((Q(1),a) for a in (Q(0),Q(1,2),Q(7,12),Q(2,3),Q(7,10),Q(3,4),Q(1),Q(3,2),Q(2)))
UPPER=Feature('upper',lambda s:s[1]<=s[0])
def target(s):return s[1]>=THRESHOLD and s[1]<=s[0]
def world(features):return World('angle_quantitative_obligation',TRAIN,HELDOUT,lambda s:s[0],target,(UPPER,)+tuple(features))
def compiled_features(extensions):
    """Install only consequences certified by the universal lower estimate."""
    return tuple(Feature(e.candidate.name,lambda s,t=THRESHOLD:s[1]>=t)
        for e in extensions if e.candidate.evaluate(Q(1))>=THRESHOLD)

def qualification():
    old,rejected,duplicates,extensions,failures=generate_extensions()
    old_features=compiled_features([type('Old',(),{'candidate':c}) for c in old])
    before=develop(world(old_features),old_features,True,2,(UPPER,))
    assert before['status']=='GRAMMAR_INSUFFICIENT' and before['witness'] is not None
    features=compiled_features(extensions)
    w=world(features)
    residual=develop(w,features,True,2,(UPPER,))
    blind=develop(w,features,False,2,(UPPER,))
    learned=selected(w,residual['features'])
    heldout=verify(w,learned,HELDOUT)
    ablation=[{'feature':f.name,'witness':verify(w,tuple(g for g in learned if g!=f),HELDOUT)}
              for f in learned if f.name!=UPPER.name]
    counts={m:Counter() for m in ('residual','blind')}
    for order in permutations(features):
        for mode in counts:
            r=develop(w,order,mode=='residual',2,(UPPER,))
            counts[mode][r['status']]+=1
    return {'status':'PASS' if residual['status']=='PASS' and heldout is None else 'NOT_QUALIFIED',
        'scope':'bounded proof-certificate language extension',
        'controller_blob':'5d28426f2ce50032a5b291d20c93bc7acd0ff4b5',
        'before':before,'old_certified':len(old),'old_rejected':len(rejected),
        'old_duplicates':len(duplicates),'old_maximum_at_one':str(max(c.evaluate(Q(1)) for c in old)),
        'meta_grammar':'factor x^k; complete rational quadratic square',
        'extensions':[e.record() for e in extensions],'meta_failures':failures,
        'selected':[e.record() for e in extensions if e.candidate.name in residual['features']],
        'residual':residual,'blind':blind,'heldout_witness':heldout,'ablation':ablation,
        'orderings':{m:dict(c) for m,c in counts.items()},
        'training_states':len(TRAIN),'heldout_states':len(HELDOUT),
        'limitations':['The certificate meta-grammar is supplied, not invented without primitives.',
          'The protected threshold is supplied; synthesis does not infer the task.',
          'Universal lower estimates are compiled to an entailed threshold feature.',
          'A single certified extension does not establish a residual-versus-blind search advantage.',
          'The finite predicate test is distinct from the universal Lean theorem.',
          'No original blow-up lemma is repaired.']}

def report():return qualification()

class Tests(unittest.TestCase):
    def test_old_grammar_and_exact_certificate(self):
        from form_synthesis import generate,validate
        from grammar import derivative_numerator,expand_square
        old,rejected,duplicates,extensions,failures=generate_extensions()
        self.assertEqual(len(old)+len(rejected)+len(duplicates),20)
        self.assertEqual(len(extensions)+len(failures),len(rejected))
        self.assertTrue(all(validate_extension(e) and not validate(e.candidate) for e in extensions))
        for e in extensions:
            self.assertEqual(derivative_numerator(e.candidate.polynomial()),expand_square(e.k,e.square))
    def test_generic_square_and_forgery(self):
        from grammar import complete_square,expand_square,solve_square_family,Extension
        from dataclasses import replace
        self.assertEqual(complete_square({0:Q(1),1:Q(-2),2:Q(1)}),{'A':Q(1),'r':Q(1),'D':Q(0)})
        self.assertEqual(complete_square({0:Q(2),1:Q(-4),2:Q(2)}),{'A':Q(2),'r':Q(1),'D':Q(0)})
        self.assertIsNone(complete_square({0:Q(0),1:Q(1),2:Q(1)}))
        e=solve_square_family(Q(1),2)
        self.assertIsNotNone(e)
        self.assertFalse(validate_extension(replace(e,square={'A':Q(1),'r':Q(1),'D':Q(0)})))
    def test_exact_frozen_obstruction(self):
        r=qualification()
        self.assertEqual(r['controller_blob'],'5d28426f2ce50032a5b291d20c93bc7acd0ff4b5')
        self.assertEqual(r['before']['status'],'GRAMMAR_INSUFFICIENT')
        self.assertEqual(r['old_maximum_at_one'],'2/3')
        self.assertEqual(r['training_states'],4)
        self.assertEqual(r['heldout_states'],9)
    def test_heldout_ablation_and_controls(self):
        r=qualification()
        self.assertEqual(r['status'],'PASS')
        self.assertIsNone(r['heldout_witness'])
        self.assertTrue(all(a['witness'] is not None for a in r['ablation']))
        import math
        n=len(compiled_features(generate_extensions()[3]))
        self.assertEqual(sum(r['orderings']['residual'].values()),math.factorial(n))
        self.assertEqual(sum(r['orderings']['blind'].values()),math.factorial(n))
    def test_no_target_import(self):
        import ast,inspect,grammar
        modules=[n.module for n in ast.walk(ast.parse(inspect.getsource(grammar))) if isinstance(n,ast.ImportFrom)]
        for name in ('proof_bridge','form_oracle','genesis_experiment','source_compare'):
            self.assertNotIn(name,modules)
    def test_json(self):
        self.assertEqual(json.loads(json.dumps(report(),default=str))['status'],'PASS')

if __name__=='__main__':
    import sys
    if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]])
    else:print(json.dumps(report(),indent=2,default=str))
