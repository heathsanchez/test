#!/usr/bin/env python3
"""V14 exact-source producer/consumer integration verification.

The target source protected_domains.py was committed before this adapter.
Scientific claims are conditional on exact producer and task source hashes.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
from protected_domains import tasks
from source_consumer import Gate,PROTECTED_SHA,SOURCE_EXPECTED,V12
from independent_reference import optimum,strong_weighted,old_cardinality_witness
ROOT=Path(__file__).parent
RUN_V12=38202495321
RUN_V13=38203812704


def condition(group,rows):
    relevant=[x for x in rows if x['family'] in group]
    return all(x['status']=='SOURCE_AUTHORIZED_OUTPUT' for x in relevant)


def main():
    assert hashlib.sha256((ROOT/'protected_domains.py').read_bytes()).hexdigest()==PROTECTED_SHA
    # Real executable source qualification is re-run before any promotion.
    process=subprocess.run([sys.executable,str(V12/'verify_v12b.py')],cwd=V12,
      check=True,capture_output=True,text=True)
    assert 'PASS_V12B_PROSPECTIVE_FINITE' in process.stdout
    worlds=tasks()
    assert len(worlds)==8
    positive=[w for w in worlds if w.declared=='MODULAR_POSITIVE_HEREDITARY']
    negative=[w for w in worlds if w not in positive]
    assert len(positive)==5 and len(negative)==3
    g=Gate()
    init=[g.evaluate(w) for w in worlds]
    assert all(x['status']=='UNKNOWN_NO_ACTIVE_SOURCE_WARRANT' for x in init[:5])
    assert all(x['status']=='UNKNOWN_UNSUPPORTED_INTERFACE' for x in init[5:])
    unrelated_before={x:g.engine.frontiers[x] for x in ('F_unrelated_control','F_matroid','F_nonmatroid')}
    e0=g.independently_attest_producer()
    promote=g.promote_after_attestation()
    assert 'cap_weighted' in promote['changed_facts']
    assert 'F_weighted' in promote['changed_frontiers']
    active=[g.evaluate(w) for w in worlds]
    assert all(x['status']=='SOURCE_AUTHORIZED_OUTPUT' for x in active[:5])
    assert all(x['status']=='UNKNOWN_UNSUPPORTED_INTERFACE' for x in active[5:])
    graphgroup={'graph','intervals','matroid'}
    resourcegroup={'resources','packing'}
    assert condition(graphgroup,active) and condition(resourcegroup,active)
    assert all(g.engine.frontiers[x]==before for x,before in unrelated_before.items())
    comparisons=[];old_obstruction=[];stateless_calls=0;raw_guard=0;source_exec_calls=0;truth_calls=0
    for w,ex in zip(worlds,active):
        raw_guard+=ex['raw_feasibility_reads']+ex['raw_score_reads']
        if w in positive:
            brute=optimum(w)
            strong=strong_weighted(w)
            assert brute['value']==strong['value']==ex['checked_value']
            assert strong['feasible_calls']==ex['source_feasibility_execution_calls']
            old=old_cardinality_witness(w)
            if old['canonical_example_weight']!=brute['value']:
                old_obstruction.append({'name':w.name,'max_cardinality':old['cardinality'],
                  'canonical_rank_witness_score':old['canonical_example_weight'],
                  'weighted_optimum':brute['value']})
            comparisons.append({'name':w.name,'class':w.family,
              'optimum':brute['value'],'complete_enumeration_feasibility_calls':brute['feasible_calls'],
              'source_learned_feasibility_calls':ex['source_feasibility_execution_calls'],
              'informed_stateless_feasibility_calls':strong['feasible_calls']})
            stateless_calls+=strong['feasible_calls']
            source_exec_calls+=ex['source_feasibility_execution_calls']
            truth_calls+=brute['feasible_calls']
    assert len(old_obstruction)>=2,(len(old_obstruction),old_obstruction)
    assert source_exec_calls==stateless_calls
    # Restart from the compiled present without replay of the historical
    # source candidate synthesis or re-running V12 qualification.
    snapshot=g.snapshot()
    restarted=Gate.restore(json.loads(json.dumps(snapshot)))
    assert restarted.engine.state()==g.engine.state()
    restored=[restarted.evaluate(w) for w in worlds]
    assert restored==active
    # Simulated revocation retracts both target frontiers but preserves source bytes.
    changed=restarted.simulated_revoke()
    assert 'cap_weighted' in changed['changed_facts']
    revoked=[restarted.evaluate(w) for w in worlds]
    assert all(x['status']=='UNKNOWN_NO_ACTIVE_SOURCE_WARRANT' for x in revoked[:5])
    assert all(x['status']=='UNKNOWN_UNSUPPORTED_INTERFACE' for x in revoked[5:])
    assert restarted.source_evidence==e0
    assert len(restarted.archive)>=3
    assert all(restarted.engine.frontiers[x]==before for x,before in unrelated_before.items())
    # Reinstatement requires unchanged source attestation, not rescoring or
    # a new human-authored program. For real revocation, new source verifier
    # would be required; this is a simulation.
    refreshed=restarted.promote_after_attestation()
    assert 'cap_weighted' in refreshed['changed_facts']
    final=[restarted.evaluate(w) for w in worlds]
    assert final==active
    # Evidence disappearance cannot be overwritten by a forged event in adapter.
    untrusted=Gate()
    try:untrusted.promote_after_attestation()
    except Exception:pass
    else:raise AssertionError('source was promoted without exact attestation')
    assert all(row['status']!='SOURCE_AUTHORIZED_OUTPUT' for row in [untrusted.evaluate(w) for w in positive])
    report={
     'status':'PASS_V14_SOURCE_TO_CONSUMER_FINITE',
     'source_protocol_run':RUN_V12,'closure_protocol_run':RUN_V13,
     'qualified_producer_sha256':e0['read_only_source_sha256'],
     'frozen_protected_sha256':PROTECTED_SHA,
     'protected_positive_families':len(positive),'protected_negative_families':len(negative),
     'protected_consumer_groups':{'graph_and_schedule':len([w for w in positive if w.family in graphgroup]),
                                  'resources_and_packing':len([w for w in positive if w.family in resourcegroup])},
     'capability_events':{'initial_no_warrant':True,'promoted_source_changes_real_consumer_output':True,
                          'compiled_restart_preserved':True,'simulated_revocation_retracts':True,
                          'reattest_restores':True,'unsupported_fails_closed':True,
                          'unrelated_frontiers_unchanged':True},
     'source_attestation':e0,'producer_replay_status':'QUALIFIED_EXACT_SOURCE_RERUN',
     'results':comparisons,'old_objective_ablation_examples':old_obstruction,
     'costs':{'consumer_guard_raw_evaluations':raw_guard,
         'source_learned_execution_feasibility_calls':source_exec_calls,
         'informed_stateless_feasibility_calls':stateless_calls,
         'complete_reference_feasibility_calls':truth_calls,
         'producer_source_verification_excluded_from_incremental_runtime':True,
         'historic_v11_acquisition_source_calls':6006234,
         'guard_validation_expensive_vs_task_execution':raw_guard>source_exec_calls},
     'constraints':{'source_is_actual_independently_checked_program':True,
       'dependent_tasks_are_separately_frozen_synthetic_mathematical_families':True,
       'revocation_is_simulated_not_real_github_warrant_withdrawal':True,
       'matched_stateless_execution_ties':True,
       'no_unrestricted_autonomous_new_grammar':True,
       'no_full_lifecycle_cost_win':True,
       'not_cross_repository_producer_consumer':True},
     'final_engine_chain_sha256':restarted.engine.event_chain,
     'source_event_ledger':restarted.archive,
    }
    (ROOT/'results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('status','protected_positive_families','protected_negative_families','protected_consumer_groups','capability_events','costs','constraints')},indent=2))

if __name__=='__main__':main()
