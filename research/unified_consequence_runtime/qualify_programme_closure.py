"""Native programme integration over qualified persisted E/D/V54 state.

No V54 acquisition or discovery is repeated. The primary new causal path is
native observation acquisition -> changed protected repair choice -> native
execution, with global FLASH readiness, exact support withdrawal and restart.
Collection repair construction is a separately verified path in the same log.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .consequence_selection import _state_digest, native_selectors
from .cross_frontier import register_frontier, publish_frontier_route, require_frontier_route
from .developmental_choice import choose_verified_profiles, profile_binding
from .developmental_machine import Machine, canonical, digest
from .native_observation import NativeObservationRuntime, CONTRACT
from .native_constructor import NativeConstructorRuntime, FRONTIER_CONTRACT, FRONTIER_PROFILES
from .qualify_v54_machine import Journal


def _publish(machine, runtime, capability):
    payload = runtime.projection_payload(capability)
    return publish_frontier_route(machine, capability, contract=payload['contract'],
        profiles=payload['profiles'], verification_id=payload['verification_id'],
        validate=runtime._validated)


def _initial_residual(machine, runtime):
    """Persist a native MSI pair residual before observation acquisition."""
    observed=runtime.observe('A')
    rows={version:{row['id']:row for row in observed[version]['rows']}
          for version in ('old','head')}
    futures=tuple(rows['old'])
    primitive=('mut_status','native','length')
    carrier=tuple(version+':'+key for version in ('old','head') for key in futures)
    def row(key):
        version,case=key.split(':',1)
        return rows[version][case]
    def observe(key):
        return canonical([row(key)['features'][field] for field in primitive])
    core=native_selectors()['core']
    representation=core.EquivalenceRelation.from_observation(carrier,observe)
    witnesses=[key for key in futures if representation.same('old:'+key,'head:'+key)
               and rows['old'][key]['label']!=rows['head'][key]['label']]
    if not witnesses:raise ValueError('native protected obligation has no supported pair residual')
    first=sorted(witnesses)[0]
    residual=core.PairResidual('old:'+first,'head:'+first,representation,
        rows['old'][first]['label'],rows['head'][first]['label'])
    from realitygraph.developmental_types import DevelopmentalResult,ResultKind
    from realitygraph.developmental_core import route_residual
    route=route_residual(DevelopmentalResult(ResultKind.UNKNOWN_IDENTITY,'native-source-A',
        'verified native consequence contradicts primitive observational identification'))
    candidates=('A:old','A:head')
    profiles={candidate:{future:[0] for future in futures} for candidate in candidates}
    scope={'observations':machine.put(observed),'native_pins':runtime.native.verifier.IDENTITY['A'],
           'available_observation_channels':list(primitive),'scope':'exact original source-A cases'}
    choice=choose_verified_profiles(runtime.source_repo,candidates,futures,profiles,
        evidence_binding=profile_binding(candidates,futures,profiles,scope=scope))
    if choice['status']!='UNKNOWN_CHOICE':raise ValueError('unresolved native choice was erased')
    payload={'kind':'PairResidual','witness':[residual.left,residual.right],
        'protected_outcomes':[residual.consequence_left,residual.consequence_right],
        'observations':scope['observations'],'carrier':list(carrier),
        'initial_choice':choice,'constitutional_route':route.value,
        'existing_method':'ORIGINAL_FLASH_V11_NATIVE_BASIS_CONSTRUCTOR',
        'grammar_expansion_licensed':False,'expressivity':'UNKNOWN',
        'boundary':'available but not yet selected observation; no old-language impossibility'}
    event=machine.append('native_typed_residual',payload,(runtime.source,))
    machine.flush()
    return {**payload,'event':event},representation,observed


def _choice(machine, runtime, result, consequence):
    """Original choice on actual independently checked native future vectors."""
    family = result['family']
    observed = machine.get(result['observations'])
    rows = {version:{row['id']:row for row in observed[version]['rows']}
            for version in ('old', 'head')}
    futures = tuple(rows['old'])
    if set(rows['head']) != set(futures):
        raise ValueError('independent native future carrier differs across candidates')
    candidates = tuple(family+':'+version for version in ('old', 'head'))
    primitive = ('mut_status', 'native', 'length')
    if any(canonical([rows['old'][key]['features'][col] for col in primitive]) !=
           canonical([rows['head'][key]['features'][col] for col in primitive]) for key in futures):
        raise ValueError('primitive observational collision control failed')
    # Primitive observation supplies no preference. Keep the entire frontier.
    before = {candidate:{future:[0] for future in futures} for candidate in candidates}
    receipt = machine.get(result['receipt'])
    scope = {'family':family, 'native_receipt':result['receipt'], 'program':result['program'],
             'consequence':consequence, 'complete_future_carrier':list(futures),
             'authority':'independently replayed native/tomllib finite contract'}
    unknown = choose_verified_profiles(runtime.source_repo, candidates, futures, before,
        evidence_binding=profile_binding(candidates, futures, before, scope=scope))
    if unknown['status'] != 'UNKNOWN_CHOICE' or unknown['candidates'] != list(candidates):
        raise ValueError('primitive evidence prematurely chose a repair')
    predictions = {(row['version'],row['id']):row for row in result['predictions']}
    profiles = {}
    for version, candidate in zip(('old', 'head'), candidates):
        profiles[candidate] = {}
        for future in futures:
            row = predictions[version, future]
            if row['predicted'] not in ('PASS', 'FAIL') or row['predicted'] != row['actual']:
                raise ValueError('UNKNOWN_EVIDENCE: new observation has unsupported native signature')
            profiles[candidate][future] = [0 if row['predicted']=='PASS' else 1]
    chosen = choose_verified_profiles(runtime.source_repo, candidates, futures, profiles,
        evidence_binding=profile_binding(candidates, futures, profiles, scope=scope))
    if chosen['status'] != 'AUTHORIZED_REPAIR' or chosen['selected'] != family+':head':
        raise ValueError('independent acquired observation did not select a native repair')
    if receipt['native_reexecuted'] is not True or consequence not in machine.flash_live_ids():
        raise ValueError('repair choice has no live independent native execution')
    # Gate subsequent actual execution on the original selector's returned ID.
    selected_version = chosen['selected'].split(':',1)[1]
    replay = runtime._native(family, selected_version, independent=True)
    if any(row['label']!='PASS' for row in replay['rows']):
        raise ValueError('selected native future failed independent re-execution')
    node = machine.append('native_consequential_choice', {
        'family':family, 'before':unknown, 'after':chosen,
        'selected_native_sha256':digest(canonical(replay).encode()),
        'boundary':'changed selection under supplied observation grammar; not expressivity genesis'},
        (consequence,))
    machine.flush()
    return {'before':unknown, 'after':chosen, 'choice_event':node,
            'selected_native_reexecuted':True, 'profiles':profiles, 'receipt':result['receipt']}


def _baseline(runtime, capability):
    """Original executable ledger, same policy, source, observations and verifier."""
    started = time.perf_counter()
    cap = runtime._validated(capability)
    program = runtime.machine.get(cap.program)
    results = {}
    for family in ('B','C'):
        observed = runtime.observe(family)
        # Re-execute equal native production and independent verification work.
        receipt = runtime._verify(program, observed, family)
        status, result = runtime.native.verifier.evaluate(program,
            {family:(observed['old'],observed['head'])})
        if status != 'QUALIFIED_BOUNDED_REPLAY' or result[family]['false']:
            raise ValueError('equally informed original executable-ledger verifier failed')
        results[family] = {'outcome':result[family], 'receipt':receipt}
        futures=tuple(row['id'] for row in observed['old']['rows'])
        candidates=(family+':old',family+':head')
        profiles={family+':'+version:{row['id']:[0 if program['source_compiled_lookup'].get(
            runtime.native.producer.key(row['features'],program['selected_channels']))=='PASS' else 1]
            for row in observed[version]['rows']} for version in ('old','head')}
        scope={'family':family,'program':cap.program,'native_receipt_sha256':digest(canonical(receipt).encode()),
               'comparison':'same original executable selector and native evidence'}
        choice=choose_verified_profiles(runtime.source_repo,candidates,futures,profiles,
            evidence_binding=profile_binding(candidates,futures,profiles,scope=scope))
        if choice['selected']!=family+':head':raise ValueError('baseline native repair choice differs')
        results[family]['repair_choice']=choice
    return {'status':'PASS', 'comparison':'TIE_SAME_POLICY_NATIVE_OUTCOMES_AND_INFORMATION',
        'same_available_operators':True, 'same_policy_program':cap.program,
        'same_native_and_verification_access':True, 'source':cap.source,
        'fresh_native_execution':True, 'results':results, 'seconds':time.perf_counter()-started,
        'comparison_scope':'same informed policy execution and native future selection; acquisition knowledge shared',
        'live_agent_comparator':'NOT_RUN', 'causal_support':'same live executable ledger supplied'}


def _machine(spec):
    return Machine(Path(spec['components']), Path(spec['state']),
                   Path(spec['evaluator']), Path(spec['config']))


def restart(spec, out):
    machine = _machine(spec)
    runtime = NativeObservationRuntime(machine, Path(spec['source_repo']),
        Path(spec['observation_worlds']), Path(out).parent/'restart-observation')
    results = {}
    for family in ('B','C'):
        route = require_frontier_route(machine, 'tomlkit:'+family, validate=runtime._validated)
        if route['status']!='READY' or route['capability_id']!=spec['observation_capability']:
            raise ValueError('cold restart failed to recover exact warranted observation route')
        activation=machine.select_and_execute_frontier('tomlkit:'+family,runtime)
        result,consequence=activation['native'],activation['consequence']
        results[family] = {'native':result, 'choice':_choice(machine,runtime,result,consequence)}
    compiler = NativeConstructorRuntime(machine, Path(spec['source_repo']),
        Path(spec['constructor_worlds']), Path(out).parent/'restart-constructor',
        native_python=Path(spec['native_python']))
    constructed = {}
    for name, capability in spec['constructor_capabilities'].items():
        for profile in FRONTIER_PROFILES[name]:
            route = require_frontier_route(machine, profile, validate=compiler._validated)
            if route['status']!='READY' or route['capability_id']!=capability:
                raise ValueError('cold restart constructor frontier is unavailable')
        activation=machine.select_and_execute_frontier(FRONTIER_PROFILES[name][0],compiler)
        result,consequence=activation['native'],activation['consequence']
        constructed[name] = {'native':result,'consequence':consequence}
    if any(old in machine.flash_live_ids() for old in spec['withdrawn_capabilities']):
        raise ValueError('cold restart resurrected withdrawn generations')
    if not set(spec['historical_ids']) <= set(machine.mt.ids(machine.log)):
        raise ValueError('cold restart lost original history')
    answer = {'status':'PASS_NATIVE_SEPARATE_PROCESS_RESTART', 'observation':results,
        'constructors':constructed, 'history_retained':True, 'old_generations_inactive':True,
        'costs':machine.costs, 'ledger_sha256':digest(machine.mt.dumps(machine.log).encode())}
    Path(out).write_text(json.dumps(answer,indent=2)+'\n')
    return answer


def qualify(args):
    out, base = args.out.resolve(), args.base_state.resolve()
    if out==base or out in base.parents or base in out.parents:
        raise ValueError('qualification must not overlap retained state')
    before_digest = _state_digest(base)
    out.mkdir(parents=True,exist_ok=False)
    journal = Journal(out)
    journal.update('schema','udm.programme.native-closure.v1')
    journal.update('claim_boundary',{
        'observation_constructor':'SUPPLIED_ORIGINAL_SEVEN_CHANNEL_128_MASK_FLASH_SELECTION',
        'native_repair_constructors':'TWO_SUPPLIED_ORIGINAL_SOURCE_AST_GRAMMARS',
        'future_choice':'COMPLETE_ORIGINAL_NATIVE_B_C_CASES_WITH_ORIGINAL_PARETO_SELECTOR',
        'new_observation_primitive_or_constructor_grammar':'NOT_ACQUIRED',
        'historical_targets':'EXPOSED_NOT_NEWLY_BLINDED',
        'unrestricted_nonreachability':'UNKNOWN','python_formal_refinement':'UNKNOWN',
        'reference_monitor':'UNKNOWN_NONBYPASSABILITY','external_execution_authority':'NONE',
        'retained_V54':'Original one-new-rewrite horizon remains separately qualified; acquisition/search not repeated'})
    journal.update('protocol','UDM_PROGRAMME_NATIVE_CLOSURE_INTEGRATION_V1')
    journal.update('boundaries',{'historical_targets':'EXPOSED', 'new_observation_vocabulary':'NOT_ACQUIRED',
        'constructor_grammars':'SUPPLIED_ORIGINAL', 'prospective_urllib3':'UNKNOWN_TYPED_NATIVE_FRONTIER_NOT_ADMITTED',
        'external_reference_monitor':'UNKNOWN_NONBYPASSABILITY', 'python_refinement':'UNKNOWN',
        'fresh_V54_acquisition_or_search':False})
    try:
        with journal.stage('load_preserved_qualified_state_and_activate_existing_methods'):
            shutil.copytree(base,out/'state')
            machine = Machine(args.components,out/'state',args.evaluator,args.config)
            historical = sorted(machine.mt.ids(machine.log))
            base_caps = set(machine.active_capabilities())
            if len(historical)<101:
                raise ValueError('canonical history missing')
            tasks = json.loads((args.config.parent/'full_no_eval.json').read_text())
            existing = [machine.select_and_execute(next(t for t in tasks if t['task_id']==tid))
                        for tid in (62,64,65,168,169,172)]
            if any(r['status']!='VERIFIED_EXISTING_METHOD_ACTIVATION' for r in existing):
                raise ValueError('retained existing-method native activation failed')
            journal.update('existing_method_activation',existing)
        with journal.stage('register_independent_native_frontiers_before_acquisition'):
            for family in ('B','C'):
                register_frontier(machine,'tomlkit:'+family,contract=CONTRACT,
                    profile='tomlkit:'+family,request={'family':family,'protocol':'ORIGINAL_NATIVE_TOML'})
            register_frontier(machine,'wrong-contract',contract={**CONTRACT,'verifier_id':'wrong-verifier'},
                profile='tomlkit:B',request={'negative_control':True})
            for name in ('cachetools','boltons'):
                for profile in FRONTIER_PROFILES[name]:
                    register_frontier(machine,profile,contract=FRONTIER_CONTRACT,
                        profile=profile,request={'subject':name,'protected_profile':profile})
            if any(row['status']=='READY' for row in machine.frontiers['frontiers'].values()):
                raise ValueError('frontier became ready without executable evidence')
            journal.update('initial_frontiers',deepcopy(machine.frontiers))
        with journal.stage('activate_original_constructor_acquire_native_observation_and_reclose'):
            runtime = NativeObservationRuntime(machine,args.source_repo,args.observation_worlds,out/'observation')
            residual,old_representation,initial_observations=_initial_residual(machine,runtime)
            journal.update('initial_native_residual',residual)
            cap = runtime.acquire()
            if runtime.acquire()!=cap:raise ValueError('existing observation operation was reconstructed')
            program=machine.get(machine.descriptor(cap).program)
            core=native_selectors()['core']
            def combined(key):
                version,case=key.split(':',1)
                row=next(r for r in initial_observations[version]['rows'] if r['id']==case)
                primitive=canonical([row['features'][field] for field in ('mut_status','native','length')])
                return primitive,runtime.native.producer.key(row['features'],program['selected_channels'])
            refined=core.EquivalenceRelation.from_observation(old_representation.carrier,combined)
            if not refined.strictly_refines(old_representation):
                raise ValueError('new observation did not preserve old distinctions on fixed native carrier')
            journal.update('native_representation_refinement',{'checked_by':'original MSI EquivalenceRelation',
                'strict':True,'fixed_carrier_size':len(refined.carrier),'raw_provenance_retained':True})
            publication = _publish(machine,runtime,cap)
            delta = deepcopy(machine.frontiers)
            if not {'tomlkit:B','tomlkit:C'} <= set(delta['changed_frontiers']):
                raise ValueError('one warranted event did not propagate to both native frontiers')
            if delta['frontiers']['wrong-contract']['status']=='READY':
                raise ValueError('wrong verifier received native authority')
            journal.update('observation_acquisition',{'capability':cap,'publication':publication,'flash':delta,
                'original_constructor':'ACTIVATED_EXISTING_NOT_INVENTED',
                'new_executable_object':machine.descriptor(cap).program})
        with journal.stage('native_future_observation_changes_developmental_choice'):
            results,choices = {},{}
            for family in ('B','C'):
                route = require_frontier_route(machine,'tomlkit:'+family,validate=runtime._validated)
                if route['status']!='READY':raise ValueError('native future is not enabled')
                activation=machine.select_and_execute_frontier('tomlkit:'+family,runtime)
                result,consequence=activation['native'],activation['consequence']
                results[family] = result
                choices[family] = _choice(machine,runtime,result,consequence)
            journal.update('native_futures',results)
            journal.update('changed_choice',choices)
        with journal.stage('strong_same_information_native_executable_ledger_comparison'):
            baseline = _baseline(runtime,cap)
            for family,result in results.items():
                expected={'repaired':result['native_repaired'],'detected':result['detected_repaired'],
                          'false':result['false_warrants']}
                if baseline['results'][family]['outcome']!=expected:
                    raise ValueError('native executable-ledger outcomes differ')
            journal.update('baseline',baseline)
        with journal.stage('original_source_observation_and_executable_repair_construction'):
            compiler = NativeConstructorRuntime(machine,args.source_repo,args.constructor_worlds,
                out/'constructor',native_python=args.native_python)
            compiler.prepare()
            constructed={}
            for name in ('cachetools','boltons'):
                residual=compiler.observe(name)
                constructor_cap=compiler.acquire(name)
                if compiler.acquire(name)!=constructor_cap:
                    raise ValueError('existing native repair was reconstructed instead of activated')
                pub=_publish(machine,compiler,constructor_cap)
                propagation=deepcopy(machine.frontiers)
                activation=machine.select_and_execute_frontier(FRONTIER_PROFILES[name][0],compiler)
                native,consequence=activation['native'],activation['consequence']
                constructed[name]={'capability':constructor_cap,'residual':residual,'publication':pub,
                    'flash':propagation,'native':native,'consequence':consequence}
            journal.update('native_construction',constructed)
            # An equally informed executable ledger can invoke the same original
            # supplied constructor and native verifier without UDM admission.
            construction_baseline={}
            for name,record in constructed.items():
                expected=machine.get(machine.descriptor(record['capability']).program)
                start=time.perf_counter()
                generated=compiler._call(name,'synthesize',subject=expected['subject'])
                if generated!={'source':expected['source'],'generator_receipt':expected['generator_receipt']}:
                    raise ValueError('same-informed original constructor baseline differs')
                checked=compiler._verify(name,expected)
                construction_baseline[name]={'same_executable_source':True,'native_receipt':checked,
                    'seconds':time.perf_counter()-start,'comparison':'TIE_SAME_AVAILABLE_CONSTRUCTOR'}
            journal.update('construction_baseline',construction_baseline)
        with journal.stage('exact_ancestor_withdrawal_preserves_unrelated_frontiers'):
            independent_caps={row['capability'] for row in constructed.values()}
            runtime.withdraw(cap)
            cut=deepcopy(machine.frontiers)
            for family in ('B','C'):
                if require_frontier_route(machine,'tomlkit:'+family)['status']=='READY':
                    raise ValueError('withdrawn observation route remained active')
                try:runtime.execute(cap,family)
                except PermissionError:pass
                else:raise ValueError('withdrawn capability executed')
            if not base_caps|independent_caps <= set(machine.flash_live_ids()):
                raise ValueError('unrelated existing executable capabilities lost support')
            for name in constructed:
                if any(machine.frontiers['frontiers'][p]['status']!='READY' for p in FRONTIER_PROFILES[name]):
                    raise ValueError('unrelated constructor frontier changed on observation withdrawal')
            old_constructor=constructed['cachetools']['capability']
            compiler.withdraw(old_constructor)
            for p in FRONTIER_PROFILES['cachetools']:
                if require_frontier_route(machine,p)['status']=='READY':
                    raise ValueError('constructor ancestor withdrawal did not propagate')
            if any(machine.frontiers['frontiers'][p]['status']!='READY' for p in FRONTIER_PROFILES['boltons']):
                raise ValueError('unrelated constructor frontier was invalidated')
            journal.update('withdrawal',{'observation':cap,'constructor':old_constructor,
                'flash_after_observation_cut':cut,'flash_after_constructor_cut':deepcopy(machine.frontiers),
                'original_capabilities_retained':sorted(base_caps)})
        with journal.stage('fresh_native_evidence_restoration_new_lineage'):
            restored=runtime.restore(cap)
            _publish(machine,runtime,restored)
            restored_constructor=compiler.restore(old_constructor)
            _publish(machine,compiler,restored_constructor)
            constructed['cachetools']['restored_capability']=restored_constructor
            if restored==cap or restored_constructor==old_constructor:
                raise ValueError('restoration reused revoked generation')
            journal.update('restoration',{'observation':restored,'cachetools':restored_constructor,
                'flash':deepcopy(machine.frontiers)})
        with journal.stage('separate_process_native_restart_and_selected_execution'):
            spec={key:str(getattr(args,key).resolve()) for key in
                ('components','evaluator','config','source_repo','observation_worlds','constructor_worlds')}
            spec.update(state=str(out/'state'),native_python=str(args.native_python.absolute()),
                historical_ids=historical,withdrawn_capabilities=[cap,old_constructor],
                observation_capability=restored,constructor_capabilities={
                    'cachetools':restored_constructor,'boltons':constructed['boltons']['capability']})
            (out/'restart-spec.json').write_text(json.dumps(spec,indent=2)+'\n')
            process=subprocess.run([sys.executable,'-B','-m',__spec__.name,'--restart',
                str(out/'restart-spec.json'),'--restart-out',str(out/'cold-restart.json')],
                capture_output=True,text=True,timeout=1200)
            (out/'restart-process.log').write_text(process.stdout+process.stderr)
            if process.returncode:raise ValueError('separate process failed; retained restart-process.log')
            journal.update('restart',json.loads((out/'cold-restart.json').read_text()))
        final=Machine(args.components,out/'state',args.evaluator,args.config)
        if not set(historical)<=set(final.mt.ids(final.log)) or not base_caps<=set(final.flash_live_ids()):
            raise ValueError('final history or qualified base capability regression')
        if _state_digest(base)!=before_digest:raise ValueError('retained input state mutated')
        journal.update('costs',machine.costs)
        journal.update('retention',{'historical_records':len(historical),'final_records':len(final.log),
            'input_state_unchanged':True,'ledger_sha256':digest(final.mt.dumps(final.log).encode()),
            'persistent_bytes':sum(p.stat().st_size for p in (out/'state').rglob('*') if p.is_file())})
        journal.update('status','WARRANTED_BOUNDED_NATIVE_OBSERVATION_CHOICE_CONSTRUCTION_AND_GLOBAL_RECLOSURE')
        return journal.result
    except BaseException as error:
        journal.update('status','FAILED_OR_UNKNOWN')
        journal.update('error',{'type':type(error).__name__,'reason':str(error),
            'input_state_unchanged':_state_digest(base)==before_digest})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart',type=Path)
    parser.add_argument('--restart-out',type=Path)
    for name in ('components','evaluator','config','base-state','source-repo',
                 'observation-worlds','constructor-worlds','native-python','out'):
        parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    if args.restart:
        restart(json.loads(args.restart.read_text()),args.restart_out)
    else:
        if any(getattr(args,key) is None for key in ('components','evaluator','config','base_state',
                'source_repo','observation_worlds','constructor_worlds','native_python','out')):
            parser.error('all native qualification paths are required')
        result=qualify(args)
        print(json.dumps({'status':result['status']}))


if __name__=='__main__':main()
