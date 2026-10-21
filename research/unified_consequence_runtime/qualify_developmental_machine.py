"""Run the real archived-world developmental integration and cold executable replay."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from .developmental_machine import Machine, PINS, EVIDENCE, canonical, digest

def recover_archive(path, expected, destination):
    raw = Path(path).read_bytes()
    if digest(raw) != expected:
        raise ValueError('original archive digest mismatch')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(n.startswith('/') or '..' in Path(n).parts for n in names):
            raise ValueError('unsafe original archive')
        archive.extractall(destination)

def run_cold_replay(spec, out):
    subprocess.run([sys.executable, '-B', '-m',
                    'research.unified_consequence_runtime.qualify_developmental_machine',
                    '--replay', str(spec), '--out', str(out)], check=True, capture_output=True)
    return json.loads(Path(out).read_text())

def replay(spec, out):
    started = time.perf_counter()
    spec = json.loads(Path(spec).read_text())
    m = Machine(Path(spec['components']), Path(spec['state']),
                Path(spec['evaluator']), Path(spec['config']))
    assets = Path(spec['assets'])
    tasks = json.loads((assets/'full_no_eval.json').read_text())
    outcomes = {}
    for kind, ids in (('grouping', (62,64,65)), ('stars', (168,169,172))):
        for task_id in ids:
            task = next(t for t in tasks if t['task_id']==task_id)
            response, warrant = m.execute(spec['capabilities'][kind], task)
            outcomes[str(task_id)] = {'response_sha256':digest(canonical(response).encode()),
                                      'warrant':warrant, 'native':'accepted'}
    if m.applicable(spec['withdrawn'], next(t for t in tasks if t['task_id']==62)):
        raise AssertionError('cold restart resurrected withdrawn generation')
    result = {'status':'PASS', 'outcomes':outcomes, 'costs':m.costs,
              'seconds':time.perf_counter()-started,
              'withdrawn_generation_inactive':True,
              'active_capabilities':m.active_capabilities()}
    Path(out).write_text(json.dumps(result, indent=2)+'\n')
    return result

def qualify(args):
    started = time.perf_counter()
    out, state = args.out.resolve(), args.state.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (state/'metatron-ledger.jsonl').exists():
        raise ValueError('qualification requires a new isolated state; use replay for retained execution')
    assets, history = out/'original-depth5', out/'original-runtime'
    recover_archive(args.depth5_archive, EVIDENCE['depth5']['sha256'], assets)
    recover_archive(args.runtime_archive, EVIDENCE['runtime']['sha256'], history)
    root = next(history.rglob('metatron-ledger.jsonl')).parent
    # Reuse the original independently qualified historical join boundary.
    from .compose_original_evidence import read_original, compose
    original_join = compose(read_original('depth5', args.depth5_archive),
                            read_original('runtime', args.runtime_archive))
    m = Machine(args.components, state, args.evaluator, assets/'config.json',
                root/'metatron-ledger.jsonl', root/'flash-state-bundle.json')
    original_ids = set(m.mt.ids(m.log))
    original_flash = json.loads((root/'flash-state-bundle.json').read_text())
    prior_active = {x for x in m.flash['summary']['active_capability_ids']
                    if not x.startswith('udm:warrant:')}
    if len(prior_active) != 11 or len(original_flash['events']) != 13:
        raise AssertionError('original source-qualified runtime boundary changed')
    tasks = json.loads((assets/'full_no_eval.json').read_text())
    task = lambda i:next(t for t in tasks if t['task_id']==i)
    observation = json.loads((assets/'e_obs.json').read_text())
    cap_e = m.acquire_grouping(task(63), observation)
    representation = m.get(m.descriptor(cap_e).program)
    if representation != json.loads((assets/'e_rep.json').read_text()):
        raise AssertionError('original induced executable representation changed')
    cap_d = m.activate_stars(json.loads((assets/'d_obs.json').read_text()),
                             json.loads((assets/'d_binding.json').read_text()), task(169))
    selected, warrants, independent = {}, [], []
    for i in (62,64,65):
        response, warrant = m.execute(cap_e, task(i))
        selected[str(i)] = digest(canonical(response).encode())
        warrants.append(warrant)
    for i in (168,169,172):
        _, warrant = m.execute(cap_d, task(i))
        independent.append(warrant)
    negatives = {}
    for i in (62,64,65):
        response = m.run_source('grouping', task(i), observation, representation, ablate=True)
        receipt = m.verify(response, i)
        if receipt['status'] != 'rejected' or receipt['score']==1:
            raise AssertionError('original grouping ablation failed to refute consequence')
        negatives[str(i)] = receipt
    forged = m.verify({'task_type':'RETRIEVE','status':'NOT_FOUND_ERROR',
                       'retrieved_data':None,'error_details':None},62)
    if forged['status'] != 'rejected':
        raise AssertionError('native verifier accepted forged missing consequence')
    m.append('negative_evidence', {'grouping_ablation':negatives, 'forged_response':forged,
                                 'impossibility_certificate':'NOT_PROVIDED'})
    m.flush()
    # Equal information and executable memory: identical code/program/inputs,
    # same three native checks, without the causal-maintenance layer.
    baseline_started = time.perf_counter()
    baseline_cost_start = len(m.costs)
    baseline = {}
    for i in (62,64,65):
        response = m.run_source('grouping', task(i), observation, representation)
        receipt = m.verify(response, i)
        if receipt['status'] != 'accepted':
            raise AssertionError('equally informed executable baseline failed')
        baseline[str(i)] = {'response_sha256':digest(canonical(response).encode()), 'receipt':receipt}
    baseline_seconds = time.perf_counter()-baseline_started
    if any(baseline[k]['response_sha256'] != v for k,v in selected.items()):
        raise AssertionError('equally informed baseline response differs')
    baseline_costs = m.costs[baseline_cost_start:]
    before = set(m.mt.live_ids(m.log))
    revoke = m.withdraw(cap_e, 'controlled exact E support withdrawal; original source evidence remains valid')
    after = set(m.mt.live_ids(m.log))
    if cap_e in after or any(w in after for w in warrants) or not set(independent)<=after:
        raise AssertionError('selective causal withdrawal is incorrect')
    if cap_d not in after:
        raise AssertionError('independent executable route was withdrawn')
    blocked = False
    try:
        m.execute(cap_e, task(62))
    except PermissionError:
        blocked = True
    if not blocked:
        raise AssertionError('withdrawn executable route still works')
    withdrawn_summary = m.flash['summary']
    if len({x for x in withdrawn_summary['active_capability_ids'] if not x.startswith('udm:warrant:')}) != 11:
        raise AssertionError('withdrawal changed unrelated original source capabilities')
    # Restoration rechecks original executable behavior before a new admission.
    restored = m.acquire_grouping(task(63), observation, supersedes=cap_e)
    for i in (62,64,65):
        response, _ = m.execute(restored, task(i))
        if digest(canonical(response).encode()) != selected[str(i)]:
            raise AssertionError('restoration changed original semantics')
    spec = {'components':str(args.components.resolve()), 'state':str(state),
            'evaluator':str(args.evaluator.resolve()), 'config':str(assets/'config.json'),
            'assets':str(assets), 'withdrawn':cap_e,
            'capabilities':{'grouping':restored, 'stars':cap_d}}
    (out/'replay-spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    before_replay_ids = set(m.mt.ids(m.log))
    cold = run_cold_replay(out/'replay-spec.json',out/'cold-replay.json')
    if cold['status'] != 'PASS' or any(cold['outcomes'][k]['response_sha256']!=v for k,v in selected.items()):
        raise AssertionError('cold replay did not recover executable behavior')
    final = Machine(args.components, state, args.evaluator, assets/'config.json')
    if not (original_ids | before_replay_ids) <= set(final.mt.ids(final.log)):
        raise AssertionError('append-only history lost across restart')
    result = {'schema':'metalogic.live-developmental-qualification.v1',
        'status':'WARRANTED_BOUNDED_INTEGRATED_EXECUTION',
        'source_pins':PINS, 'original_evidence':EVIDENCE,
        'coordinator_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'native_protected_successes':3, 'native_protected_total':3,
        'independent_domain_successes':3, 'grouping_ablation_successes':0,
        'representation_induced_by_original_code':True,
        'historical_join':original_join, 'original_ledger_nodes_retained':len(original_ids),
        'original_source_events_retained':13, 'original_active_capabilities_retained':11,
        'withdrawal':{'status':'PASS','revocation_node':revoke,'removed_ids':sorted(before-after),
                      'dependent_consequences':warrants,'independent_survivors':independent,
                      'old_route_blocked':blocked, 'upstream_revocation':False},
        'restoration':{'status':'PASS','new_generation':restored,'supersedes':cap_e,
                       'revoked_old_generation_remains_inactive':cap_e not in final.mt.live_ids(final.log)},
        'restart':cold, 'baseline':{'status':'TIE','equal_information':True,
                                  'same_source_same_program_same_tasks':True,'native_checks':3,
                                  'seconds':baseline_seconds,'outcomes':baseline,'costs':baseline_costs},
        'negative_controls':{'grouping':negatives,'forged_response':forged},
        'costs':m.costs, 'total_seconds':time.perf_counter()-started,
        'final_log_records':len(final.log),'final_live_records':len(final.mt.live_ids(final.log)),
        'final_ledger_sha256':digest((state/'metatron-ledger.jsonl').read_bytes()),
        'flash_closure':final.flash['summary'],
        'boundary':{'world':'ORIGINAL_ARCHIVED_WEB_ARENA_SNAPSHOT','fresh_browser_observation':'NOT_CHECKED',
                    'newly_blinded_discovery':'NOT_CLAIMED','prospective_second_generation':'UNKNOWN',
                    'source_distinct_representation_transfer':'UNKNOWN','autonomous_constructor_growth':'UNKNOWN',
                    'cross_model_transport':'UNKNOWN','competent_tool_using_agent_comparator':'NOT_RUN',
                    'complete_old_language_nonreachability':'NOT_PROVIDED','production_authorization':'NONE'}}
    (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--depth5-archive',type=Path)
    p.add_argument('--runtime-archive',type=Path)
    p.add_argument('--components',type=Path)
    p.add_argument('--evaluator',type=Path)
    p.add_argument('--state',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--replay',type=Path)
    args = p.parse_args()
    if args.replay:
        replay(args.replay,args.out)
    else:
        if any(getattr(args,k) is None for k in ('depth5_archive','runtime_archive','components','evaluator','state')):
            p.error('qualification requires both archives, components, evaluator, state and out')
        result = qualify(args)
        print(json.dumps({'status':result['status'],'protected':3,'ablation':0,
                          'baseline':result['baseline']['status'],'restart':result['restart']['status']}))

if __name__=='__main__':
    main()
