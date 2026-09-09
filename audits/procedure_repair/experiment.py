"""Frozen-controller qualification of two successive procedure repairs.

The adapter is explicitly a capability test, not a physical-state quotient.
The generator sees polynomial coefficients and domains, never task names.
"""
from __future__ import annotations
from fractions import Fraction as Q
from itertools import permutations
from collections import Counter
from pathlib import Path
import json,sys,hashlib,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cross_domain'))
from experiment import Feature,World,develop,verify,selected
from certcheck import encode,verify as replay
from procedures import NAMES,build

TASKS=(
 {'name':'arctangent_derivative','polynomial':{1:Q(1,2),2:Q(-1),3:Q(1,2)},'domain':('ray',)},
 {'name':'interval_positivity','polynomial':{0:Q(1),2:Q(-1)},'domain':('interval',Q(0),Q(1))},
)
INITIAL=('coefficientwise',)
BUDGET=2


def attempts(task):
    return {n:build(n,task['polynomial'],task['domain']) for n in NAMES}


def world(task,certificates):
    features=tuple(Feature(n,lambda s,valid=certificates[n] is not None:bool(s[1] and valid)) for n in NAMES)
    return World('procedure_capability',((0,False),(0,True)),((0,False),(0,True)),lambda s:s[0],lambda s:s[1],features)


def run_stage(task,order,residuals,initial):
    certificates=attempts(task)
    w=world(task,certificates)
    chosen=selected(w,initial)
    result=develop(w,selected(w,order),residuals,BUDGET,initial=chosen)
    result['certificate_attempts']=len(NAMES)
    result['accepted']=[n for n in NAMES if certificates[n] is not None]
    result['initial']=list(initial)
    result['heldout_witness']=verify(w,selected(w,result['features']),w.heldout)
    result['ablation']=[{'removed':n,'witness':verify(w,selected(w,tuple(f for f in result['features'] if f!=n)),w.heldout)} for n in result['features'] if n not in INITIAL and certificates[n] is not None]
    result['promoted_certificates']={n:certificates[n] for n in result['features'] if n not in initial and certificates[n] is not None}
    return result


def qualification():
    stages=[]
    installed=INITIAL
    for task in TASKS:
        before=run_stage(task,(),True,installed)
        # The baseline failure is checked before extending the active library.
        if not stages:
            assert attempts(task)[INITIAL[0]] is None
        else:
            assert all(attempts(task)[n] is None for n in installed)
        residual=run_stage(task,NAMES,True,installed)
        blind=run_stage(task,NAMES,False,installed)
        if residual['status']!='PASS':raise AssertionError((task['name'],residual))
        stages.append({'name':task['name'],'polynomial':encode(task['polynomial']),
          'domain':[str(x) for x in task['domain']],'before':before,
          'residual':residual,'blind':blind})
        installed=tuple(dict.fromkeys(residual['features']))
    counts=Counter();stage_counts=[{'residual':Counter(),'blind':Counter()} for _ in TASKS]
    for order in permutations(NAMES):
        for mode in ('residual','blind'):
            installed=INITIAL;statuses=[]
            for i,task in enumerate(TASKS):
                r=run_stage(task,order,mode=='residual',installed)
                statuses.append(r['status']);stage_counts[i][mode][r['status']]+=1
                installed=tuple(dict.fromkeys(r['features']))
                if r['status']!='PASS':break
            counts[(mode,'PASS' if len(statuses)==len(TASKS) and all(s=='PASS' for s in statuses) else 'NOT_FINISHED')]+=1
    return {'status':'PASS','scope':'bounded certificate-procedure repair',
      'controller_blob':'5d28426f2ce50032a5b291d20c93bc7acd0ff4b5',
      'candidate_order':list(NAMES),'budget_per_task':BUDGET,
      'stages':stages,'orderings':{mode:{s:counts[(mode,s)] for s in ('PASS','NOT_FINISHED')} for mode in ('residual','blind')},
      'stage_orderings':[{m:dict(c) for m,c in sc.items()} for sc in stage_counts],
      'limitations':['The constructor primitives and two obligations are supplied.',
      'The adapter tests certificate availability, not a physical-state quotient.',
      'The residual arm may spend more certificate checks than the blind arm.',
      'One successful candidate per task limits the causal interpretation.',
      'Generic mathematical soundness is checked separately from Python code correctness.',
      'No missing blow-up lemma is repaired.']}

class Tests(unittest.TestCase):
    def test_old_failure_and_distinct_repairs(self):
        a,b=TASKS
        self.assertIsNone(attempts(a)['coefficientwise'])
        self.assertIsNotNone(attempts(a)['half_line_square'])
        self.assertIsNone(attempts(b)['half_line_square'])
        self.assertIsNone(attempts(b)['coefficientwise'])
        self.assertIsNotNone(attempts(b)['interval_affine'])
    def test_exact_replay_and_forgery(self):
        from certcheck import verify
        from copy import deepcopy
        for t in TASKS:
            for n,c in attempts(t).items():
                if c is not None:self.assertTrue(verify(t['polynomial'],t['domain'],c))
        c=deepcopy(attempts(TASKS[0])['half_line_square']);c['D']='-1'
        self.assertFalse(verify(TASKS[0]['polynomial'],TASKS[0]['domain'],c))
        c=deepcopy(attempts(TASKS[1])['interval_affine']);c['children'][0]['b']='2'
        self.assertFalse(verify(TASKS[1]['polynomial'],TASKS[1]['domain'],c))
        self.assertFalse(verify({0:-1},('ray',),{'kind':'coeff','polynomial':{'0':'-1'}}))
    def test_transfer_and_ablation(self):
        r=qualification()
        for stage in r['stages']:
            self.assertEqual(stage['residual']['status'],'PASS')
            self.assertIsNone(stage['residual']['heldout_witness'])
            self.assertTrue(all(x['witness'] is not None for x in stage['residual']['ablation']))
        self.assertEqual(r['orderings']['residual']['PASS'],24)
    def test_generic_heldout_families(self):
        # The promoted procedures are callable on unlisted rational inputs.
        for t in [
          {'polynomial':{0:Q(2),1:Q(-4),2:Q(2)},'domain':('ray',)},
          {'polynomial':{0:Q(4),1:Q(-4)},'domain':('interval',Q(0),Q(1))},
          {'polynomial':{0:Q(-6),1:Q(5),2:Q(-1)},'domain':('interval',Q(2),Q(3))},
        ]:
            self.assertTrue(any(build(n,t['polynomial'],t['domain']) for n in NAMES))
    def test_no_target_dispatch(self):
        import ast,inspect,procedures
        tree=ast.parse(inspect.getsource(procedures))
        self.assertNotIn('arctangent_derivative',inspect.getsource(procedures))
        self.assertNotIn('interval_positivity',inspect.getsource(procedures))
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module in ('experiment','form_oracle','proof_bridge') for n in ast.walk(tree)))
    def test_json(self):
        self.assertEqual(json.loads(json.dumps(qualification(),default=str))['status'],'PASS')

if __name__=='__main__':
    if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]])
    else:print(json.dumps(qualification(),indent=2,default=str))
