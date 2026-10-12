#!/usr/bin/env python3
"""Independent prospective V12b check; frozen source-only policy verified by SHA.

The protected source was frozen in GitHub before unbiased source selector repair.
No new synthesis or objective change after protected import. All costs scoped.
"""
import hashlib, importlib.util, json, random
from pathlib import Path
from protected_v12b import frozen_worlds
ROOT=Path(__file__).parent
EXPECTED={
 'synthesize_objective_v2.py':'deaaa46a36210dab62bd1dcd448cd9d4e4f70425605adb250b7c4019f52ac7a9',
 'learned_objective.py':'eb736c72c3acc5bc152fe811be8d3892d88ac0e1932bb2fb47ef5d562fe49a3f',
 'source_weighted.py':'8fa8df70b553224359ac3802ddc175d691d704991be2450988037ea079b89adf',
 'source_receipt.json':'d394d88879f28b78bbe7498d46abfbc42f67c2d59304bbd7a3f73de23428ac1f',
 'protected_v12b.py':'2b39b11d551206201cd3cc0145c732b3a572a91258f5a9d7b6387e5f18701a4a',
}
for name,sha in EXPECTED.items():
 actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
 assert actual==sha,(name,actual,sha)
spec=importlib.util.spec_from_file_location('frozen_learned_v12b',ROOT/'learned_objective.py')
learned=importlib.util.module_from_spec(spec);spec.loader.exec_module(learned)
assert learned.POLICY=={'topology':'both','objective':'sum_weights','bound':'positive_weights','include_first':True}

class Count:
 def __init__(self,truth):self.truth=truth;self.calls=0
 def __call__(self,m):self.calls+=1;return self.truth[m]

def hereditary(table,n):
 if not table[0]:return False,('empty',0)
 for m in range(1<<n):
  if not table[m]:continue
  for i in range(n):
   if m>>i&1 and not table[m^(1<<i)]:return False,(m,m^(1<<i))
 return True,None

def modularity(score,w):
 if any(x<0 for x in w):return False,('negative',next(i for i,x in enumerate(w) if x<0))
 for m,s in enumerate(score):
  expected=sum(w[i] for i in range(len(w)) if m>>i&1)
  if s!=expected:return False,(m,s,expected)
 return True,None

def strong(order,w,valid):
 """Separately implemented explicit-stack score-aware exact search."""
 pending=[(0,0,0)]; best=0
 while pending:
  i,mask,score=pending.pop()
  upper=score+sum(max(0,w[j]) for j in order[i:])
  if upper<=best:continue
  if i==len(order):
   if valid(mask):best=max(best,score)
   continue
  j=order[i]
  pending.append((i+1,mask,score))
  pending.append((i+1,mask|(1<<j),score+w[j]))
 return best

def oracle_best(table,score,allowed):
 mask=allowed;best=-10**10;cost=0
 while True:
  cost+=1
  if table[mask] and score[mask]>best:best=score[mask]
  if not mask:break
  mask=(mask-1)&allowed
 return best,cost

def orderings(mask,n):
 xs=tuple(i for i in range(n) if mask>>i&1)
 r=random.Random(20261012+mask*27)
 ys=list(xs);r.shuffle(ys)
 return tuple(dict.fromkeys((xs,tuple(reversed(xs)),tuple(ys))))

def cardinality_only(table,score,allowed):
 sub=allowed;best=-1;selected=None
 while True:
  if table[sub] and sub.bit_count()>best:
   best=sub.bit_count();selected=sub
  if sub==0:break
  sub=(sub-1)&allowed
 return score[selected]

def qualify(world):
 n=world.n;truth=tuple(bool(world.feasible(m)) for m in range(1<<n))
 scores=tuple(world.score(m) for m in range(1<<n))
 good_h,wit_h=hereditary(truth,n)
 good_m,wit_m=modularity(scores,world.weights)
 warranted=(good_h and good_m)
 expected=(world.boundary=='NONNEGATIVE_MODULAR')
 assert warranted==expected,(world.name,warranted,world.boundary,wit_h,wit_m)
 entry={'name':world.name,'n':n,'boundary':world.boundary,
    'hereditary':good_h,'modular_nonnegative':good_m,
    'counterexample':wit_h if not good_h else wit_m if not good_m else None,
    'guard_raw_reads':2*(1<<n),'executed_learned':warranted}
 if not warranted:
  entry['status']='UNKNOWN_UNSUPPORTED_BOUNDARY'
  return entry
 checks=0; reference_checks=0; learned_calls=0;stateless_calls=0
 old_witness=None; mutant_witness=None
 for allowed in range(1<<n):
  optimum,cost=oracle_best(truth,scores,allowed)
  reference_checks+=cost
  if old_witness is None:
   old=cardinality_only(truth,scores,allowed)
   if old!=optimum:old_witness={'mask':allowed,'cardinality_value':old,'weighted_optimum':optimum}
  for order in orderings(allowed,n):
   learned_q=Count(truth)
   observed=learned.developed_optimize(n,learned_q,world.weights,order)
   strong_q=Count(truth)
   independently=strong(order,world.weights,strong_q)
   checks+=1;learned_calls+=learned_q.calls;stateless_calls+=strong_q.calls
   assert observed==optimum==independently,(world.name,allowed,order,observed,optimum,independently)
   assert learned_q.calls==strong_q.calls,(world.name,learned_q.calls,strong_q.calls)
 assert old_witness,(world.name,'old cardinality rule unexpectedly sufficient')
 entry.update(status='PASS_PROSPECTIVE_WEIGHTED',protected_cases=checks,
  independent_reference_checks=reference_checks,
  learned_calls=learned_calls,stateless_calls=stateless_calls,
  old_objective_ablation=old_witness,
  final_optimum=oracle_best(truth,scores,(1<<n)-1)[0])
 return entry

def main():
 cases=[qualify(w) for w in frozen_worlds()]
 valid=[x for x in cases if x['status']=='PASS_PROSPECTIVE_WEIGHTED']
 invalid=[x for x in cases if x['status']=='UNKNOWN_UNSUPPORTED_BOUNDARY']
 assert len(valid)==6 and len(invalid)==3
 source=json.loads((ROOT/'source_receipt.json').read_text())
 assert source['selector_version']=='unbiased_v2_all_source_qualifying_candidates'
 assert len([x for x in source['warm']['tested_candidates'] if x['pass']])==8
 assert source['warm']['selected']['policy']==source['cold']['selected']['policy']==learned.POLICY
 savings=source['cold']['total_feasibility_calls']-source['warm']['total_feasibility_calls']
 assert savings==156240
 v11=6006234
 report={'status':'PASS_V12B_PROSPECTIVE_FINITE',
   'source_policy_sha256':EXPECTED['learned_objective.py'],
   'protected_source_sha256':EXPECTED['protected_v12b.py'],
   'valid_families':len(valid),'unsupported_families':len(invalid),'cases':cases,
   'totals':{'protected_comparisons':sum(x['protected_cases'] for x in valid),
     'learned_execution_calls':sum(x['learned_calls'] for x in valid),
     'stateless_execution_calls':sum(x['stateless_calls'] for x in valid),
     'guard_raw_reads':sum(x['guard_raw_reads'] for x in cases),
     'reference_subset_checks':sum(x['independent_reference_checks'] for x in valid)},
   'acquisition':{'warm_candidates':24,'cold_candidates':60,
     'warm_source_calls':source['warm']['total_feasibility_calls'],
     'cold_source_calls':source['cold']['total_feasibility_calls'],
     'source_calls_saved':savings,'source_saving_pct':round(savings/source['cold']['total_feasibility_calls']*100,4),
     'v11_source_calls_sunk':v11,'two_generation_net':savings-v11,
     'optimistic_repeat_jobs_to_offset_v11':(v11+savings-1)//savings,
     'note':'Cached truth-table accesses, not physical cost; baseline is differently acquisition-informed; saved candidate evaluation only, not execution or independent validation cost.'},
   'verdict':{'warranted':'Source-selected unprivileged score-aware branch optimizer passed newly frozen unrelated objective families after guarded transport.',
    'rejected':'Strict performance win over informed stateless; one-reuse lifetime amortization; unrestricted grammar invention.',
    'unknown':'Lifetime gain after complete provenance and validation costs, new third-class rule invention or open-ended recursion.'}}
 (ROOT/'v12b_results.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('status','valid_families','unsupported_families','totals','acquisition')},indent=2))

if __name__=='__main__':main()
