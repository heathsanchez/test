#!/usr/bin/env python3
"""Prospective FLASH V13 six-gate evidence over frozen synthetic episode.

Independent batch reference; changed-graph snapshots; event permutations;
negative malformed events; scope and economic countercontrol. All source refs
are labels to prior bounded qualifications, not new independent domain proofs.
"""
import hashlib, json, random, tempfile, time
from copy import deepcopy
from pathlib import Path
from flash_engine import RecloseEngine,EventRejected,wire_json
from reference_oracle import FullReference
ROOT=Path(__file__).parent
FIXTURE_SHA256='64060c4cbb419ef8ebe295449c19100a8b227ff07c8c12102096092c8bd2cbf9'


def exact_equal(engine,reference,context):
 a=engine.state();b=reference.current
 assert a==b,(context,a,b)
 return True


def expected_tests(fixture):
 engine=RecloseEngine(fixture);ref=FullReference(fixture)
 assert exact_equal(engine,ref,'initial')
 history=[];snap=None
 for i,event in enumerate(fixture['events']):
  old=engine.state()
  report=engine.apply(event)
  ref.apply(event)
  assert exact_equal(engine,ref,f'event_{i}:{event}')
  assert report['fixed_point']
  # A true semantic frontier change must be inside an explicitly watched cone.
  for fid in set(report['changed_frontiers']):
   assert fid in report['checked_frontiers']
   assert old['frontiers'][fid]!=engine.frontiers[fid]
  for fid in set(engine.frontiers)-set(report['checked_frontiers']):
   assert old['frontiers'][fid]==engine.frontiers[fid]
  history.append(report)
  if i==fixture['restart_after_event_index']:
   snap=engine.snapshot()
   encoded=wire_json(snap)
   # Fresh constructor/restart without replaying the prior events.
   restarted=RecloseEngine.restore(fixture,json.loads(encoded))
   assert restarted.state()==engine.state()
   assert restarted.event_count==i+1
   assert restarted.event_chain==engine.event_chain
   engine=restarted
 # Core original paper requirements
 assert engine.event_count==len(fixture['events'])
 assert snap is not None
 # Event0 activates the separate observation frontier, but not joint genesis.
 assert 'F_observation' in history[0]['changed_frontiers']
 assert 'F_joint_genesis' not in history[0]['changed_frontiers']
 # Event1 makes observation and viability jointly sufficient, changing multiple frontiers.
 assert {'F_joint_genesis','F_weighted_viability'}.issubset(history[1]['changed_frontiers'])
 # Event2 uses a dormant, already-source-qualified greedy capability in a new role.
 assert 'F_dormant_reuse' in history[2]['changed_frontiers']
 # Event3 is a verified separator, switching quotient from merged to split.
 assert 'F_quotient' in history[3]['changed_frontiers']
 assert 'cap_split' in engine.symbols
 # Event5 is an unrelated synthetic certificate; dependent fact changes, 0 frontiers.
 assert history[5]['dirty_facts']>0 and history[5]['checked_frontiers']==[]
 # Event6 is duplicate: no recomputation.
 assert history[6]['noop'] and history[6]['rule_checks']==0 and history[6]['checked_frontiers']==[]
 # Event7 revokes v11 and retracts complete search; direct v12 authority remains.
 assert 'cap_complete' in history[7]['changed_facts']
 assert 'cap_weighted' not in history[7]['changed_facts']
 assert engine.event_count>8
 # Event8 removes last surviving cap_weighted support, and must retract it.
 assert 'cap_weighted' in history[8]['changed_facts']
 # Event9 restores source-v11 path and thereby restores weighted even without v12direct.
 assert 'cap_weighted' in history[9]['changed_facts']
 # Negative separator removal event10 lets quotient merge again.
 assert 'F_quotient' in history[10]['changed_frontiers']
 # Later revocations invalidate/reinstate dormant reuse, equivalence and sensor-derived frontier.
 assert 'F_dormant_reuse' in history[11]['changed_frontiers']
 assert 'F_dormant_reuse' in history[12]['changed_frontiers']
 assert 'F_quotient' in history[13]['changed_frontiers']
 assert 'F_quotient' in history[14]['changed_frontiers']
 assert 'F_weighted' in history[15]['changed_frontiers']
 assert 'F_weighted' in history[16]['changed_frontiers']
 assert 'F_observation' in history[17]['changed_frontiers']
 assert 'F_observation' in history[18]['changed_frontiers']
 # No forged event can mutate the engine or its digest.
 for bad in fixture['adversarial_tests']:
  before=engine.snapshot()
  try:engine.apply(bad)
  except EventRejected:pass
  else:raise AssertionError(('forged_event_accepted',bad))
  assert engine.snapshot()==before
 # Tampered snapshot and cross-fixture snapshot must fail closed.
 corrupted=deepcopy(snap);corrupted['state']['base'].append('FORGED')
 try:RecloseEngine.restore(fixture,corrupted)
 except EventRejected:pass
 else:raise AssertionError('corrupted_snapshot_accepted')
 fixture_changed=deepcopy(fixture);fixture_changed['scope']='MUTATED'
 try:RecloseEngine.restore(fixture_changed,snap)
 except EventRejected:pass
 else:raise AssertionError('cross_fixture_snapshot_accepted')
 # Independent result for every *commuting* order of the first pair of events.
 def two_event_order(first,second):
  e=RecloseEngine(fixture);r=FullReference(fixture)
  for event in (first,second):
   e.apply(event);r.apply(event)
  assert exact_equal(e,r,'commuting')
  return e.state()
 assert two_event_order(*fixture['events'][:2])==two_event_order(*reversed(fixture['events'][:2]))
 # Strong batch semantic comparator MUST be exact; any speed claim cannot be reachability.
 incremental=engine.metrics
 baseline={'rule_evaluations':ref.checks,'frontier_evaluations':ref.frontier_checks,
   'rebuilds':ref.rebuilds}
 assert incremental['frontier_evaluations']<baseline['frontier_evaluations']
 assert incremental['rule_evaluations']<baseline['rule_evaluations']
 assert engine.frontiers['F_unrelated_control']['selected']=='constant'
 assert engine.frontiers['F_unreachable']['status']=='UNKNOWN'
 return {'history':history,'snapshot':snap,'final':engine.snapshot(),
  'incremental':incremental,'batch_baseline':baseline,
  'six_gates':{'cross_frontier':True,'dormant_revived':True,'negative_separator':True,
   'incremental_local_cone':True,'revocation_with_alternative_support':True,
   'restart_without_prior_event_replay':True},
  'controls':{'forged_events':len(fixture['adversarial_tests']),
   'tampered_snapshot_rejected':True,'cross_fixture_rejected':True,
   'order_invariance':True,'fixed_points_equivalent':len(history)+1}}


def randomized_sequences(fixture,number=120,steps=35):
 rng=random.Random(20261012)
 e=RecloseEngine(fixture);r=FullReference(fixture)
 sym=fixture['allowed_events']['promote']
 touched=0
 for j in range(number):
  for _ in range(steps):
   fact=rng.choice(sym)
   kind=rng.choice(('promote','revoke'))
   event={'kind':kind,'fact':fact,
    'authority':'synthetic_event' if kind=='promote' else 'synthetic_revoker'}
   response=e.apply(event);r.apply(event)
   assert exact_equal(e,r,f'random_{j}_{fact}_{kind}')
   touched+=len(response['checked_frontiers'])
  if j%10==0:
   snap=e.snapshot();e=RecloseEngine.restore(fixture,snap)
 assert e.metrics['events']==number*steps
 return {'randomized_events':number*steps,'randomized_restarts':12,
  'incremental_evaluated_frontiers':touched,
  'batch_evaluated_frontiers':number*steps*len(fixture['frontiers']),
  'incremental_rule_evaluations':e.metrics['rule_evaluations'],
  'batch_rule_evaluations':r.checks}


def main():
 assert hashlib.sha256((ROOT/'fixture.json').read_bytes()).hexdigest()==FIXTURE_SHA256
 fixture=json.loads((ROOT/'fixture.json').read_text())
 assert fixture['version']=='flash-v13-20261012'
 t0=time.perf_counter()
 first=expected_tests(fixture)
 second=randomized_sequences(fixture)
 generated=fuzz_generic_closure(seed=20261013,graphs=200,events_per_graph=30)
 elapsed=time.perf_counter()-t0
 data={'status':'PASS_FLASH_V13_FINITE_PROSPECTIVE',
  'frozen_fixture_sha256':FIXTURE_SHA256,
  'source_authority_claims':fixture['source_authorities'],
  'main_six_gates':first['six_gates'],
  'main_controls':first['controls'],
  'main_incremental':first['incremental'],
  'main_batch_baseline':first['batch_baseline'],
  'randomized_stress':second,
  'independent_generated_graphs':generated,
  'main_event_receipts':first['history'],
  'compiled_restart_snapshot':first['snapshot'],
  'final_compiled_snapshot':first['final'],
  'interpretation':{'warranted':'Finite synthetic source-pinned incremental consequence reclosure, exact batch equivalence, six operational gates, restart and safe revocation.',
     'not_warranted':'Unrestricted self-inventing research grammar, real cross-project causal dependency, universal productivity, strict semantic advantage over complete batch planner, external physical prediction.',
     'economic_boundary':'Dirty dependency-cone work is lower than full batch recomputation on this fixture; full system implementation and original acquisition costs excluded.'}}
 (ROOT/'results.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:data[k] for k in ('status','main_six_gates','main_controls','main_incremental','main_batch_baseline','randomized_stress','independent_generated_graphs')},indent=2))

# Independently generated cyclic/hypergraph adversarial validation.
def fuzz_generic_closure(seed=20261012,graphs=100,events_per_graph=24):
    """Adversarial independent DAG/cyclic hypergraph stress (not source claims)."""
    rng=random.Random(seed)
    events=0
    for gi in range(graphs):
        base_names=['b'+str(i) for i in range(5)]
        derived=['d'+str(i) for i in range(8)]
        symbols=base_names+derived
        rules=[]
        for ri in range(rng.randint(8,24)):
            conclusion=rng.choice(derived)
            candidates=[s for s in symbols if s!=conclusion]
            premises=rng.sample(candidates,rng.randint(1,3))
            rules.append({'id':f'r{ri}','when':premises,'then':conclusion})
        frontiers=[]
        for fi in range(5):
            options=[]
            for oi in range(3):
                ps=rng.sample(symbols,rng.randint(1,3))
                bs=rng.sample([x for x in symbols if x not in ps],rng.randint(0,2))
                options.append({'id':f'o{oi}','when':ps,'unless':bs,'cost':rng.randint(0,12)})
            frontiers.append({'id':f'f{fi}','budget':rng.randint(3,12),'options':options})
        fixture={'version':'flash-v13-20261012','scope':'adversarial_generated',
          'source_authorities':{},'base_facts':rng.sample(base_names,rng.randint(0,len(base_names))),
          'rules':rules,'frontiers':frontiers,
          'allowed_events':{'promote':base_names,'revoke':base_names},'events':[],
          'restart_after_event_index':0,'adversarial_tests':[]}
        e=RecloseEngine(fixture);r=FullReference(fixture)
        assert exact_equal(e,r,f'generated{gi}:base')
        for si in range(events_per_graph):
            kind=rng.choice(('promote','revoke'))
            ev={'kind':kind,'fact':rng.choice(base_names),
              'authority':'synthetic_event' if kind=='promote' else 'synthetic_revoker'}
            e.apply(ev);r.apply(ev)
            assert exact_equal(e,r,f'generated{gi}:event{si}')
            if si in (10,19):
                e=RecloseEngine.restore(fixture,e.snapshot())
            events+=1
    return {'generated_graphs':graphs,'independent_checks':events+graphs,
            'source_generated_cycles_allowed':True}

if __name__=='__main__':main()
