"""One precommitted prospective experiment over original native regressions.

The harness never imports upstream repaired production code. Unsupported native
contracts stop development. A green evidence workflow can preserve a scientific
negative; its G2/G3/G4 verdicts are read from RESULT.json, never its exit color.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tarfile
import time

from .developmental_machine import Machine,canonical,digest
from . import decisive_native_verify as verifier
from .decisive_native_frontier import NativeFrontierRuntime
from .native_meta_decision import choose_meta_decision,invoke_meta_policy
from .decisive_native import catalog,orders,passed,reconstruct_profiles,task_roles,is_test,checked_constructor_context,checked_native_receipt

HERE=Path(__file__).resolve().parent
RECORDS=HERE/'archaeology/decisive-native'
PROTOCOL=RECORDS/'PROTOCOL.json'
MODULE='research.unified_consequence_runtime.qualify_decisive_native'


def write_freeze(repo,out):
    repo=Path(repo).resolve();protocol=json.loads(PROTOCOL.read_text())
    if subprocess.check_output(['git','-C',str(repo),'status','--porcelain']).strip():
        raise ValueError('commit all implementation/protocol bytes before native exposure')
    paths=protocol['freeze_files'];files={}
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    for name in paths:
        raw=subprocess.check_output(['git','--no-replace-objects','-C',str(repo),'show',head+':'+name])
        if raw!=(repo/name).read_bytes(): raise ValueError('working source differs')
        files[name]=digest(raw)
    result={'schema':'UDM_DECISIVE_NATIVE_FREEZE_V1','source_commit':head,
        'frozen_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'files':files,'protocol_sha256':digest(PROTOCOL.read_bytes()),
        'target_source_or_outcome_access_before_protocol_authorship':(
            'ORIGINAL_A02_PROTOCOL_ONLY; THREE_ADMISSION_REFUSALS_KNOWN_BEFORE_SOURCE_IDENTITY_MAINTENANCE'
            if protocol.get('qualification_mode')=='SOURCE_IDENTITY_MAINTENANCE'
            else 'DECLARED_NONE_BY_IMPLEMENTATION_TEAM; METADATA_ONLY_CURATOR'),
        'replay_boundary':'Only the original pre-outcome protocol authorship is prospective; later executions never reestablish untouchedness.',
        'original_protocol_source':protocol.get('original_protocol_source'),
        'qualification_mode':protocol.get('qualification_mode','ORIGINAL_PRE_OUTCOME_PROTOCOL'),
        'authority':'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH; NONBYPASSABILITY_UNKNOWN'}
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(canonical(result)+'\n')
    return result


def check_freeze(repo,path):
    result=json.loads(Path(path).read_text());repo=Path(repo)
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if head!=result['source_commit']:raise ValueError('freeze/execution source differs')
    for name,value in result['files'].items():
        if digest((repo/name).read_bytes())!=value:raise ValueError('frozen implementation changed')
    if result['protocol_sha256']!=digest(PROTOCOL.read_bytes()):raise ValueError('protocol changed')
    return result


def copy_state(out):
    receipt=json.loads((HERE/'RECURSIVE_QUALIFICATION_RECEIPT.json').read_text())
    archive=HERE/receipt['state_snapshot']['path']
    if digest(archive.read_bytes())!=receipt['state_snapshot']['sha256']:
        raise ValueError('qualified 246-record source state changed')
    with tarfile.open(archive) as packet:
        members=[]
        for entry in packet.getmembers():
            p=Path(entry.name)
            if p.is_absolute() or '..' in p.parts or not (entry.isdir() or entry.isfile()):
                raise ValueError('unsafe immutable input state')
            if p.parts[0]=='state':members.append(entry)
        packet.extractall(out,members=members,filter='data')


def native_probe(machine,runtime,candidate,label):
    started=time.monotonic();before=len(machine.costs)
    try:
        receipt=runtime._verify(candidate)
        folder=machine.costs[-1]['output']
        record={'receipt':receipt,'contract':runtime.contract,'candidate':candidate,'evidence_dir':folder,
            'native_suite_authority':runtime.native_suite_authority}
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
        outputs=[row.get('output') for row in machine.costs[before:] if row.get('output')]
        folder=outputs[-1] if outputs else ''
        retained=Path(folder)/'receipt.json' if folder else None
        if retained is not None and retained.is_file():
            receipt=json.loads(retained.read_text())
        else:
            receipt={'status':'UNKNOWN_ADMISSION_INTERFACE','error':str(error),
                'costs':{'native_calls':0,'total_seconds':time.monotonic()-started},
                'junit':dict(tests=0,passed=0,errors=0,failures=0,skipped=0)}
        record={'receipt':receipt,'contract':runtime.contract,'candidate':candidate,'evidence_dir':folder,
            'native_suite_authority':runtime.native_suite_authority}
    packet={'schema':'UDM_DECISIVE_NATIVE_PACKET_V1','files':{}}
    if record['evidence_dir']:
        for name in ('receipt.json','tracked-source-manifest.json','stdout.log','stderr.log','native.xml',
                     'build-verification/build-receipt.json','build-verification/build-attempt.json'):
            path=Path(record['evidence_dir'])/name
            if path.is_file() and not path.is_symlink():
                packet['files'][name]=base64.b64encode(path.read_bytes()).decode('ascii')
    record['packet']=machine.put(packet)
    key=machine.put(record)
    evidence=machine.append('decisive_native_probe',{'receipt':key,'label':label},(runtime.source,runtime.authority))
    machine.costs.append({'phase':'decisive_probe_envelope','seconds':time.monotonic()-started,
        'inclusive_not_additive':True,'native_calls':receipt['costs']['native_calls'],'status':receipt['status']})
    machine.flush()
    return {'record':key,'evidence':evidence,**record}


def search(machine,runtime,catalog_rows,order,budget,cache,label,*,reuse=False,unique_ceiling=None,deadline=None):
    started=time.monotonic();attempts=[];winner=None;ids={r['id']:r for r in catalog_rows}
    for ident in order[:budget]:
        if time.monotonic()-started>=180 or deadline is not None and time.monotonic()>=deadline:break
        if reuse and ident in cache:
            probe=cache[ident]
        else:
            if unique_ceiling is not None and len(cache)>=unique_ceiling:break
            probe=native_probe(machine,runtime,ids[ident]['candidate'],label+':'+ident)
            cache[ident]=probe
        attempts.append(probe['record'])
        if passed(probe['receipt']):winner=ident;break
    return {'status':'PASS_BOUNDED_SEARCH' if winner else 'UNKNOWN_SEARCH','winner':winner,
        'attempts':attempts,'seconds':time.monotonic()-started,'budget':budget,
        'complete_old_language_obstruction':'NOT_ESTABLISHED'}


def verified_failed_prefix(machine,episode,order,budget):
    """A truncated or UNKNOWN native trace cannot promote causal expansion."""
    return (bool(order) and not episode['winner'] and len(episode['attempts'])==min(budget,len(order))
        and all(verifier.fingerprint(machine.get(key)['candidate'])==order[index]
            and checked_native_receipt(machine.get(key),machine)['status']=='FAIL_NATIVE'
            for index,key in enumerate(episode['attempts'])))


def bounded_catalog(spec,out,timeout,machine):
    specpath=Path(out).with_suffix('.spec.json');specpath.write_text(canonical(spec)+'\n')
    started=time.monotonic()
    try:
        subprocess.run([sys.executable,'-m',MODULE,'--catalog-spec',str(specpath),'--out',str(out)],
            check=True,timeout=timeout)
        return json.loads(Path(out).read_text())
    finally:
        machine.costs.append({'phase':'original_v104_catalog_construction','seconds':time.monotonic()-started,
            'horizon_seconds':timeout,'native_calls':0})


def restart(spec,out):
    started=time.monotonic()
    machine=Machine(Path(spec['components']),Path(spec['state']),Path(spec['components'])/'evaluator',
        Path(spec['state'])/'unused-native-config.json')
    policy=invoke_meta_policy(machine,spec['policy'],protocol_binding=spec['protocol_binding'],
        candidate_catalog_sha256=spec['candidate_catalog_sha256'])
    runtime=NativeFrontierRuntime(machine,spec['contract'],Path(out).parent/'restart-native',
        generated_wheel_evidence=spec.get('generated_wheel_evidence'),
        native_suite_authority=spec.get('native_suite_authority'))
    if spec.get('constructor'):
        from .decisive_constructor import invoke_constructor
        constructor=invoke_constructor(machine,spec['constructor'],protocol_binding=spec['protocol_binding'],
            source_repo=spec['constructor_source'],independent_check=checked_constructor_context)
        signatures=constructor['signatures']
        candidate=machine.get(machine.descriptor(spec['capability']).program)
        generated=catalog(**spec['constructor_catalog_spec'],allowed=signatures)
        if verifier.fingerprint(candidate) not in {row['id'] for row in generated}:
            raise ValueError('restarted native method is not generated by retained original constructor')
    native,consequence=runtime.execute(spec['capability'])
    result={'status':'PASS' if passed(native) else 'UNKNOWN','selected':policy,
        'native':native,'consequence':consequence,'process_id':os.getpid(),'costs':machine.costs,
        'total_wall_seconds':time.monotonic()-started}
    Path(out).write_text(canonical(result)+'\n')
    return result


def constructor_trial(machine,train,first,training_rows,cache,training_context,first_result,
                      policy_id,scope,args,out,binding,protocol,prepare):
    """Original two-source V104 retention, followed by a still-unopened future."""
    from .decisive_constructor import retain_constructor,invoke_constructor
    from .qualify_recursive_frontier import resume_after_restart
    source=Path(args.source_repos)/'triskelion'
    first_context=machine.put({'contract':first['setup']['contract'],'catalog':first['catalog'],
        'orders':first['orders'],'catalog_spec':first['catalog_spec'],
        'baseline_record':first['baseline']['record'],'protocol_sha256':digest(PROTOCOL.read_bytes()),
        'native_suite_authority':first['setup'].get('native_suite_authority'),
        'source_boundaries':first['setup']['source_boundaries']})
    supports=[]
    def support(context_id,row,probe):
        return {'context':context_id,'record':probe['record'],'evidence':probe['evidence'],
            'signature':[row['selector'],row['builder']]}
    for row in training_rows:
        probe=cache.get(row['id'])
        if probe is not None and passed(probe['receipt']):supports.append(support(training_context,row,probe))
    winner=first_result['warm']['winner']
    first_row=next(row for row in first['catalog'] if row['id']==winner)
    first_record=first_result['warm']['attempts'][-1]
    event=next(node for node in machine.log if node.kind=='decisive_native_probe' and node.payload['receipt']==first_record)
    supports.append(support(first_context,first_row,{'record':first_record,'evidence':event.id}))
    dependencies=(policy_id,first_result['active_capability'])
    retained=retain_constructor(machine,supports,protocol_binding=binding,source_repo=source,
        independent_check=checked_constructor_context,dependencies=dependencies)
    result={'retention':retained,'supports':supports,'future_source_access_before_retention':'NONE'}
    if retained['status']!='WARRANTED_BOUNDED_CONSTRUCTOR':
        return machine,{**result,'status':'UNKNOWN_CONSTRUCTOR_SUPPORT',
            'smallest_obstruction':retained.get('reason','No original constructor program has the required source-distinct native support')}
    constructor_id=retained['constructor_id']
    live=invoke_constructor(machine,constructor_id,protocol_binding=binding,source_repo=source,
        independent_check=checked_constructor_context)
    future=prepare(2)
    if future is None or future['baseline']['receipt']['status']!='FAIL_NATIVE':
        return machine,{**result,'status':'UNKNOWN_FUTURE_NATIVE_RESIDUAL'}
    # prepare closes over the current canonical Machine; all new events and
    # invocations below use that same parent after its previous child restart.
    paths=[row['filename'] for row in task_roles(json.loads((RECORDS/'FRESH_TASK_METADATA.json').read_text())['selected'])[2]['files']
        if row['filename'].endswith('.py') and not is_test(row['filename'])]
    spec={'repo':future['setup']['contract']['repo_path'],'commit':future['setup']['contract']['commit'],
        'production_paths':paths,'triskelion':str(source),
        'observation':dict(future['baseline']['receipt'],evidence_dir=future['baseline']['evidence_dir']),
        'cap':protocol['candidate_cap_per_file']}
    cold_rows=bounded_catalog(spec,out/'recursive-cold-catalog.json',protocol['catalog_seconds'],machine)
    warm_rows=bounded_catalog(dict(spec,allowed=live['signatures']),out/'recursive-warm-catalog.json',protocol['catalog_seconds'],machine)
    sham_rows=bounded_catalog(dict(spec,allowed=live['null_signatures']),out/'recursive-sham-catalog.json',protocol['catalog_seconds'],machine)
    cold_orders=orders(cold_rows,Path(args.source_repos)/'msi')
    warm_orders=orders(warm_rows,Path(args.source_repos)/'msi')
    sham_orders=orders(sham_rows,Path(args.source_repos)/'msi')
    selected=invoke_meta_policy(machine,policy_id,protocol_binding=binding,candidate_catalog_sha256=scope['candidate_catalog_sha256'])
    runtime=future['runtime'];budget=scope['budget']
    cold=search(machine,runtime,cold_rows,cold_orders['COLD_V104_ORDER'],budget,{},'recursive-original')
    policy_only=search(machine,runtime,cold_rows,cold_orders[selected],budget,{},'recursive-policy-only')
    warm=search(machine,runtime,warm_rows,warm_orders[selected],budget,{},'recursive-constructor')
    ledger=search(machine,runtime,warm_rows,warm_orders[selected],budget,{},'recursive-informed-ledger')
    sham=search(machine,runtime,sham_rows,sham_orders[selected],budget,{},'recursive-original-null-constructor')
    result.update(cold=cold,policy_only=policy_only,warm=warm,ledger=ledger,sham=sham)
    if not warm['winner']:
        return machine,{**result,'status':'UNKNOWN_NO_CONSTRUCTOR_NATIVE_WINNER'}
    candidate=next(row['candidate'] for row in warm_rows if row['id']==warm['winner'])
    cap=runtime.admit(candidate,dependencies=(policy_id,constructor_id,first_result['active_capability']))
    native,consequence=runtime.execute(cap)
    # Physical program removal must block the actual constructor invocation;
    # a fresh unchanged-language search then tests the predicted lost reach.
    program_path=machine.state/'objects'/machine.descriptor(constructor_id).program
    raw=program_path.read_bytes();program_path.unlink();physical=False
    try:
        try:invoke_constructor(machine,constructor_id,protocol_binding=binding,source_repo=source,
            independent_check=checked_constructor_context)
        except (ValueError,KeyError,OSError,PermissionError):physical=True
        removed=search(machine,runtime,cold_rows,cold_orders[selected],budget,{},'recursive-physical-removal')
    finally:program_path.write_bytes(raw)
    unrelated=machine.append('recursive_unrelated_support',{'control':True})
    machine.append('revoke',{'target':unrelated,'reason':'recursive unrelated withdrawal control'});machine.flush()
    unrelated_native,_=runtime.execute(cap)
    before=set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    machine.append('revoke',{'target':constructor_id,'reason':'exact retained constructor ancestor withdrawal'});machine.flush()
    after=set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids();blocked=False
    try:runtime.execute(cap)
    except PermissionError:blocked=True
    if not blocked or constructor_id in after or cap in after or any(key not in after for key in dependencies):
        raise AssertionError('constructor withdrawal failed selective causal reclosure')
    # Fresh support qualification on every source used by retained programs;
    # original unrelated alternatives remain preserved, never overwritten.
    wanted={canonical(sig) for sig in live['signatures']};fresh_support=[]
    for index,old in enumerate(supports):
        if canonical(old['signature']) not in wanted:continue
        old_record=machine.get(old['record']);context=machine.get(old['context'])
        is_train=context['contract']['repository']==train['setup']['contract']['repository']
        runtime_source=train if is_train else first
        fresh_runtime=NativeFrontierRuntime(machine,context['contract'],out/('constructor-reverify-'+str(index)),
            generated_wheel_evidence=runtime_source.get('generated_wheel_evidence'),
            native_suite_authority=context.get('native_suite_authority'))
        probe=native_probe(machine,fresh_runtime,old_record['candidate'],'constructor-fresh-support-'+str(index))
        fresh_support.append(dict(old,record=probe['record'],evidence=probe['evidence']))
    restored=retain_constructor(machine,fresh_support,protocol_binding=binding,source_repo=source,
        independent_check=checked_constructor_context,dependencies=dependencies,supersedes=constructor_id)
    if restored['status']!='WARRANTED_BOUNDED_CONSTRUCTOR' or restored['constructor_id']==constructor_id:
        raise AssertionError('fresh constructor support did not establish new lineage')
    restored_id=restored['constructor_id']
    invoke_constructor(machine,restored_id,protocol_binding=binding,source_repo=source,
        independent_check=checked_constructor_context)
    restored_cap=runtime.admit(candidate,dependencies=(policy_id,restored_id,first_result['active_capability']),supersedes=cap)
    restored_native,_=runtime.execute(restored_cap)
    restart_spec={'components':str(Path(args.components).resolve()),'state':str(out/'state'),
        'policy':policy_id,'protocol_binding':binding,'candidate_catalog_sha256':scope['candidate_catalog_sha256'],
        'capability':restored_cap,'contract':runtime.contract,'constructor':restored_id,
        'constructor_source':str(source),'constructor_catalog_spec':spec,
        'native_suite_authority':runtime.native_suite_authority,
        'generated_wheel_evidence':future.get('generated_wheel_evidence')}
    (out/'recursive-restart-spec.json').write_text(canonical(restart_spec)+'\n')
    subprocess.run([sys.executable,'-m',MODULE,'--restart-spec',str(out/'recursive-restart-spec.json'),
        '--out',str(out/'recursive-cold-restart.json')],check=True,timeout=180)
    child=json.loads((out/'recursive-cold-restart.json').read_text())
    machine=resume_after_restart(machine,child)
    marker=machine.append('recursive_parent_continuation',{'restart_consequence':child['consequence']});machine.flush()
    independent={node.id for node in machine.log[:246]} & before
    causal=(physical and blocked and independent<=after and all(key in after for key in dependencies)
        and passed(native) and passed(unrelated_native) and passed(restored_native) and child['status']=='PASS'
        and passed(child['native']) and child['process_id']!=os.getpid())
    if not causal:raise AssertionError('constructor physical/causal/restoration/restart gate failed')
    # A bounded failure requires every frozen candidate in the declared prefix;
    # incomplete time/budget traces never establish new discoverability.
    def closed_failure(episode,order):return verified_failed_prefix(machine,episode,order,budget)
    first_expansion=not first_result['cold']['winner'] and first_result['warm']['winner'] is not None
    first_complete=closed_failure(first_result['cold'],first['orders']['COLD_V104_ORDER'])
    growth=(first_expansion and first_complete and closed_failure(cold,cold_orders['COLD_V104_ORDER'])
        and closed_failure(policy_only,cold_orders[selected]) and closed_failure(removed,cold_orders[selected])
        and closed_failure(sham,sham_orders[selected]) and ledger['winner'] is not None)
    result.update(status='WARRANTED_BOUNDED_RECURSIVE_DISCOVERABILITY' if growth else 'UNKNOWN_STRICT_RECURSIVE_GROWTH',
        physical_removal_blocks=physical,ancestor_blocks=blocked,original_independent_ids_preserved=independent<=after,
        removed=removed,native=native,consequence=consequence,unrelated_native=unrelated_native,
        restored_constructor=restored,restored_capability=restored_cap,restored_native=restored_native,
        cold_restart=child,parent_continuation=marker,
        expressivity='BOUNDED_SEARCH_CHANGE_WITHIN_SUPPLIED_ORIGINAL_AST_GRAMMAR; NOT_COMPLETE_OLD_LANGUAGE_IMPOSSIBILITY',
        comparative='Equal-information ledger has the same retained constructor; no superiority inferred')
    return machine,result


def qualify(args):
    from .decisive_task_admission import prepare_task
    from .generic_build_materialization import materialize
    protocol=json.loads(PROTOCOL.read_text());out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    frozen=check_freeze(args.repo,args.freeze);binding=digest(Path(args.freeze).read_bytes())
    result={'schema':'UDM_DECISIVE_NATIVE_RESULT_V1','source_commit':frozen['source_commit'],
        'freeze':frozen,'freeze_sha256':binding,'started_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'verdicts':{'G0_G1':'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY','G2':'UNKNOWN','G3':'UNKNOWN',
            'G4':'UNKNOWN','G5':'UNKNOWN','G6':'UNKNOWN'},'tasks':[],
        'conditions':{},'full_cost_boundary':'All controller phases retained; nested times are not additive. Engineering/model token cost is separately UNKNOWN.',
        'agent_comparator':{'status':'NOT_RUN_CI_CREDENTIALS_UNAVAILABLE',
            'local_cli_smoke':'401 Unauthorized: token refresh unavailable; smoke is not a comparator'}}
    started=time.monotonic();machine=None
    def save():
        result['total_wall_seconds']=time.monotonic()-started
        if machine is not None:
            result['machine_costs']=machine.costs
            raw=(out/'state/metatron-ledger.jsonl').read_bytes()
            result['retention']={'records':len(machine.log),'ledger_sha256':digest(raw),
                'original_prefix_preserved':raw.startswith(original),
                'persistent_bytes':sum(p.stat().st_size for p in (out/'state').rglob('*') if p.is_file())}
        (out/'RESULT.json').write_text(canonical(result)+'\n')
    try:
        copy_state(out)
        original=(out/'state/metatron-ledger.jsonl').read_bytes()
        machine=Machine(Path(args.components),out/'state',Path(args.components)/'evaluator',out/'state/unused-native-config.json')
        result['original_records']=len(machine.log)
        metadata=json.loads((RECORDS/'FRESH_TASK_METADATA.json').read_text())
        tasks=task_roles(metadata['selected'])
        if len(tasks)<3:
            result.update(status='UNKNOWN_TASK_FRONTIER_SHORTFALL',smallest_obstruction='Fewer than one training and two future sources');save();return result
        result['tasks']=[{'repository':s['repo'],'pr':s['pr'],'role':s['role']} for s in tasks]
        contexts=[None]*len(tasks)
        # A future is first transported only after training choice is settled.
        # This includes its baseline failure/trace; it is not training information.
        def prepare(i):
            spec=tasks[i];item=result['tasks'][i]
            setup=prepare_task(spec,out/('task-'+str(i)),binding,protocol['packages']);item['setup']=setup;save()
            if setup['status']!='PREPARED':
                item['status']='UNKNOWN_SETUP';return None
            runtime=NativeFrontierRuntime(machine,setup['contract'],out/('task-'+str(i))/'native-evidence',
                native_suite_authority=setup.get('native_suite_authority'))
            baseline=native_probe(machine,runtime,{'replacements':[]},'baseline-'+str(i))
            item['baseline']={k:v for k,v in baseline.items() if k not in ('candidate','contract')}
            item['status']=baseline['receipt']['status'];context={'runtime':runtime,'setup':setup,'baseline':baseline}
            contexts[i]=context;save()
            if baseline['receipt']['status'].startswith('UNKNOWN_ADMISSION_'):
                item['minimum_justified_route']='UNKNOWN_UNSUPPORTED_SHARED_NATIVE_INTERFACE'
                item['grammar_expansion_licensed']=False
                return context
            if baseline['receipt']['status']=='UNKNOWN_NATIVE_ERROR':
                # Pre-existing build operation is tried before any new constructor.
                try:
                    before=time.monotonic()
                    build=materialize(setup['contract']['repo_path'],out/('task-'+str(i))/'build',
                        python=setup['contract']['interpreter'],source_commit=setup['contract']['commit'])
                    item['build']=build;item['build_wall_seconds']=time.monotonic()-before
                    built_runtime=NativeFrontierRuntime(machine,setup['contract'],out/('task-'+str(i))/'built-native-evidence',
                        generated_wheel_evidence=build['generated_wheel_evidence'],
                        native_suite_authority=setup.get('native_suite_authority'))
                    built=native_probe(machine,built_runtime,{'replacements':[]},'built-baseline-'+str(i))
                    item['built_baseline']=built
                    if built['receipt']['status'] in ('PASS_NATIVE','FAIL_NATIVE'):
                        context.update(runtime=built_runtime,baseline=built,generated_wheel_evidence=build['generated_wheel_evidence'])
                except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
                    item['build_obstruction']={'status':'UNKNOWN_BUILD','error':str(error),'seconds':time.monotonic()-before}
                save()
            return context
        train=prepare(0)
        if train is None or train['baseline']['receipt']['status']!='FAIL_NATIVE':
            result.update(status='UNKNOWN_NO_NATIVE_ACQUISITION_RESIDUAL',
                smallest_obstruction=('Training native contract was already satisfied' if train and passed(train['baseline']['receipt'])
                    else 'No independently executable failing training obligation under the frozen native interface'))
            # The matched ledger actually invokes the same original operation on
            # every prepared subject; UNKNOWN parity is not a protected-outcome tie.
            ledger=[]
            for i in range(len(contexts)):
                context=contexts[i] if i==0 else prepare(i)
                if context is None:ledger.append({'status':'UNKNOWN_SETUP'});continue
                ledger.append(native_probe(machine,context['runtime'],{'replacements':[]},'informed-ledger-'+str(i)))
            result['conditions']['fully_informed_executable_ledger']=ledger
            result['conditions']['original_system']=[item.get('baseline',{'status':'UNKNOWN_SETUP'}) for item in result['tasks']]
            result['conditions']['developmental_machine']={'status':'UNKNOWN_NO_NATIVE_ACQUISITION_RESIDUAL'}
            result['conditions']['O1_O2_chain']={'status':'NOT_RUN_NO_VERIFIED_ACQUISITION'}
            result['conditions']['causal_withdrawal_restoration_restart']={
                'status':'NOT_RUN_NO_ACQUIRED_NATIVE_METHOD; PRIOR_G0_G1_AUTHORITY_PRESERVED'}
            result['status_parity_is_not_comparative_advantage']=True
            save();return result
        production=[r['filename'] for r in tasks[0]['files'] if r['filename'].endswith('.py') and not is_test(r['filename'])]
        # The authenticated original generator is itself bounded. Its process has
        # a separate wall limit, never upgraded into complete-language closure.
        catalog_spec={'repo':train['setup']['contract']['repo_path'],'commit':train['setup']['contract']['commit'],
            'production_paths':production,'triskelion':str(Path(args.source_repos)/'triskelion'),
            'observation':dict(train['baseline']['receipt'],evidence_dir=train['baseline']['evidence_dir']),
            'cap':protocol['candidate_cap_per_file']}
        try:
            rows=bounded_catalog(catalog_spec,out/'catalog.json',protocol['catalog_seconds'],machine)
        except (OSError,subprocess.SubprocessError) as error:
            result.update(status='UNKNOWN_CATALOG',smallest_obstruction=str(error));save();return result
        all_orders=orders(rows,Path(args.source_repos)/'msi')
        context_id=machine.put({'contract':train['setup']['contract'],'catalog':rows,'orders':all_orders,
            'catalog_spec':catalog_spec,'baseline_record':train['baseline']['record'],
            'protocol_sha256':digest(PROTOCOL.read_bytes()),
            'native_suite_authority':train['setup'].get('native_suite_authority'),
            'source_boundaries':train['setup']['source_boundaries']})
        scope={'protocol_binding':binding,'candidate_catalog_sha256':digest(canonical(rows).encode()),
            'source_binding':digest(canonical(tasks).encode()),'budget':protocol['search_budget'],
            'protocol_sha256':digest(PROTOCOL.read_bytes()),
            'author_test_blobs_sha256':digest((RECORDS/'AUTHOR_TEST_BLOBS.json').read_bytes()),
            'contexts':{tasks[0]['repo']:context_id},'receipt_objects':[context_id,train['baseline']['record'],train['baseline']['packet']]}
        cache={};profile_ids=[];profiles={};train_name=tasks[0]['repo'];selection_start=time.monotonic()
        for policy,order in all_orders.items():
            if len(cache)>=protocol['training_unique_calls'] or time.monotonic()-selection_start>=protocol['training_seconds']:
                attempts=[]
                for ident in order[:scope['budget']]:
                    if ident not in cache:break
                    attempts.append(cache[ident]['record'])
                    if passed(cache[ident]['receipt']):break
                episode={'status':'UNKNOWN_PROFILE_BUDGET','attempts':attempts,'winner':None}
            else:
                episode=search(machine,train['runtime'],rows,order,scope['budget'],cache,'train:'+policy,reuse=True,
                    unique_ceiling=protocol['training_unique_calls'],deadline=selection_start+protocol['training_seconds'])
            for key in episode['attempts']:
                scope['receipt_objects'].extend([key,machine.get(key)['packet']])
        # The full evidence carrier is identical in every profile, not a growing
        # per-policy scope. Raw CAS packets remain independently replay-checkable.
        scope['receipt_objects']=sorted(set(scope['receipt_objects']))
        for policy,order in all_orders.items():
            attempts=[]
            for ident in order[:scope['budget']]:
                if ident not in cache:break
                attempts.append(cache[ident]['record'])
                if passed(cache[ident]['receipt']):break
            episode={'attempts':attempts,'status':'CACHED_NATIVE_PREFIX_ONLY'}
            report={'candidate':policy,'future':train_name,'scope':scope,'attempts':episode['attempts'],
                'status':episode['status'],'original_constructor':'PINNED_V104','order':order}
            eid=machine.append('native_acquisition_profile',{'report':machine.put(report)},
                tuple(cache[x]['evidence'] for x in order[:scope['budget']] if x in cache))
            profile_ids.append(eid)
            receipts=[machine.get(k)['receipt'] for k in episode['attempts']]
            profiles[policy]={train_name:[0 if any(passed(r) for r in receipts) else 1,sum(r['costs']['native_calls'] for r in receipts)]}
        machine.flush()
        decision=choose_meta_decision(machine,tuple(all_orders), (train_name,),profiles,tuple(profile_ids),
            independent_check=reconstruct_profiles,source_repo=Path(args.source_repos))
        result['meta_decision']=decision;result['training_profiles']=profiles;save()
        if decision['status']!='WARRANTED_BOUNDED_POLICY_SELECTION':
            result.update(status='UNKNOWN_META_CHOICE',smallest_obstruction=decision.get('reason',decision['status']))
            save();return result
        result['verdicts']['G2']='WARRANTED_BOUNDED_NATIVE_POLICY_SELECTION'
        selected=invoke_meta_policy(machine,decision['policy_id'],protocol_binding=binding,
            candidate_catalog_sha256=scope['candidate_catalog_sha256'])
        result['selected_policy']=selected
        # A selected policy does not establish the prospective chain. Each future
        # must independently fail cold, succeed warm and retain an executable method.
        future_results=[];first_qualified=None
        for i in range(1,2):
            context=prepare(i)
            if context is None or context['baseline']['receipt']['status']!='FAIL_NATIVE':
                future_results.append({'status':'UNKNOWN_NO_NATIVE_RESIDUAL'});continue
            paths=[r['filename'] for r in tasks[i]['files'] if r['filename'].endswith('.py') and not is_test(r['filename'])]
            future_spec={'repo':context['setup']['contract']['repo_path'],'commit':context['setup']['contract']['commit'],
                'production_paths':paths,'triskelion':str(Path(args.source_repos)/'triskelion'),
                'observation':dict(context['baseline']['receipt'],evidence_dir=context['baseline']['evidence_dir']),
                'cap':protocol['candidate_cap_per_file']}
            try:
                future_catalog=bounded_catalog(future_spec,out/('catalog-future-'+str(i)+'.json'),protocol['catalog_seconds'],machine)
            except (OSError,subprocess.SubprocessError) as error:
                future_results.append({'status':'UNKNOWN_CATALOG','error':str(error)});continue
            future_orders=orders(future_catalog,Path(args.source_repos)/'msi')
            context.update(catalog=future_catalog,orders=future_orders,catalog_spec=future_spec)
            cold=search(machine,context['runtime'],future_catalog,future_orders['COLD_V104_ORDER'],scope['budget'],{},'future-cold')
            warm=search(machine,context['runtime'],future_catalog,future_orders[selected],scope['budget'],{},'future-warm')
            ledger=search(machine,context['runtime'],future_catalog,future_orders[selected],scope['budget'],{},'future-ledger')
            entry={'cold':cold,'warm':warm,'ledger':ledger,'scope':scope}
            if warm['winner']:
                candidate=next(r['candidate'] for r in future_catalog if r['id']==warm['winner'])
                cap_id=context['runtime'].admit(candidate,dependencies=(decision['policy_id'],))
                native,consequence=context['runtime'].execute(cap_id)
                entry.update(capability=cap_id,active_capability=cap_id,native=native,consequence=consequence)
                if first_qualified is None:
                    first_qualified=(i,context,cap_id,candidate,future_catalog,future_orders)
            future_results.append(entry);result['future_results']=future_results;save()
        if first_qualified is not None:
            i,context,old_cap,candidate,future_catalog,future_orders=first_qualified
            from .qualify_recursive_frontier import resume_after_restart
            policy_id=decision['policy_id'];policy_node=next(n for n in machine.log if n.id==policy_id)
            program_path=machine.state/'objects'/policy_node.payload['program']
            raw_program=program_path.read_bytes();program_path.unlink()
            physically_blocked=False
            try:
                try:invoke_meta_policy(machine,policy_id,protocol_binding=binding,candidate_catalog_sha256=scope['candidate_catalog_sha256'])
                except (ValueError,KeyError,OSError,PermissionError):physically_blocked=True
                without=search(machine,context['runtime'],future_catalog,future_orders['COLD_V104_ORDER'],
                    scope['budget'],{},'physical-policy-removal-cold')
            finally:program_path.write_bytes(raw_program)
            sham_names=[key for key in future_orders if key not in ('COLD_V104_ORDER',selected)]
            sham_name=min(sham_names,key=lambda x:digest(('FROZEN_SHAM|'+x).encode()))
            sham=search(machine,context['runtime'],future_catalog,future_orders[sham_name],scope['budget'],{},'sham-policy')
            unrelated=machine.append('decisive_unrelated_support',{'independent':True})
            machine.append('revoke',{'target':unrelated,'reason':'unrelated control'});machine.flush()
            unrelated_native,_=context['runtime'].execute(old_cap)
            before=set(machine.mt.live_ids(machine.log))
            machine.append('revoke',{'target':policy_id,'reason':'exact acquired discovery-policy ancestor withdrawal'})
            machine.flush();after=set(machine.mt.live_ids(machine.log))
            blocked=False
            try:context['runtime'].execute(old_cap)
            except PermissionError:blocked=True
            if not blocked or policy_id in after or old_cap in after:
                raise AssertionError('exact discovery ancestor withdrawal failed')
            # Selected-policy traces are freshly executed; original alternative
            # evidence remains independently supported. New reports carry a fresh
            # evidence lineage, not a resurrection of the revoked policy record.
            fresh_cache={}
            fresh_episode=search(machine,train['runtime'],rows,all_orders[selected],scope['budget'],
                fresh_cache,'fresh-policy-requalification')
            new_scope=dict(scope,restoration_nonce=secrets.token_hex(16))
            new_scope['receipt_objects']=list(scope['receipt_objects'])
            for record in fresh_episode['attempts']:
                new_scope['receipt_objects'].extend([record,machine.get(record)['packet']])
            new_scope['receipt_objects']=sorted(set(new_scope['receipt_objects']))
            fresh_ids=[];fresh_profiles={}
            for policy,order in all_orders.items():
                attempts=(fresh_episode['attempts'] if policy==selected else
                    machine.get(next(n.payload['report'] for n in machine.log if n.id==profile_ids[list(all_orders).index(policy)]))['attempts'])
                report={'candidate':policy,'future':train_name,'scope':new_scope,'attempts':attempts,'order':order}
                eid=machine.append('native_acquisition_profile',{'report':machine.put(report)},
                    tuple(p['evidence'] for p in fresh_cache.values()) if policy==selected else (profile_ids[list(all_orders).index(policy)],))
                fresh_ids.append(eid)
                receipts=[machine.get(k)['receipt'] for k in attempts]
                fresh_profiles[policy]={train_name:[0 if any(passed(r) for r in receipts) else 1,
                    sum(r['costs']['native_calls'] for r in receipts)]}
            machine.flush()
            restored=choose_meta_decision(machine,tuple(all_orders),(train_name,),fresh_profiles,tuple(fresh_ids),
                independent_check=reconstruct_profiles,source_repo=Path(args.source_repos))
            if restored['status']!='WARRANTED_BOUNDED_POLICY_SELECTION' or restored['policy_id']==policy_id:
                raise AssertionError('fresh policy qualification did not restore new lineage')
            restored_cap=context['runtime'].admit(candidate,dependencies=(restored['policy_id'],),supersedes=old_cap)
            restored_native,_=context['runtime'].execute(restored_cap)
            restart_spec={'components':str(Path(args.components).resolve()),'state':str(out/'state'),
                'policy':restored['policy_id'],'protocol_binding':binding,
                'candidate_catalog_sha256':scope['candidate_catalog_sha256'],
                'capability':restored_cap,'contract':context['runtime'].contract,
                'native_suite_authority':context['runtime'].native_suite_authority,
                'generated_wheel_evidence':context.get('generated_wheel_evidence')}
            (out/'restart-spec.json').write_text(canonical(restart_spec)+'\n')
            subprocess.run([sys.executable,'-m',MODULE,'--restart-spec',str(out/'restart-spec.json'),
                '--out',str(out/'cold-restart.json')],check=True,timeout=180)
            cold_restart=json.loads((out/'cold-restart.json').read_text())
            machine=resume_after_restart(machine,cold_restart)
            future_results[0]['active_capability']=restored_cap
            marker=machine.append('decisive_parent_continuation',{'restart_consequence':cold_restart['consequence']})
            machine.flush()
            result['causal_controls']={'physical_program_removal_blocks_invocation':physically_blocked,
                'actual_cold_search_without_policy':without,'sham':sham,'sham_policy':sham_name,
                'unrelated_native':unrelated_native,'exact_ancestor_blocks_execution':blocked,
                'dependent_old_capability_removed':old_cap not in after,'original_independent_ids_preserved':
                    set(n.id for n in machine.log[:result['original_records']]) & before <= after,
                'restored_policy':restored,'restored_capability':restored_cap,'restored_native':restored_native,
                'cold_restart':cold_restart,'parent_continuation':marker}
            if (not physically_blocked or not result['causal_controls']['original_independent_ids_preserved']
                    or not passed(restored_native) or cold_restart['status']!='PASS'
                    or not passed(cold_restart['native']) or cold_restart['process_id']==os.getpid()):
                raise AssertionError('native causal restoration/restart integrity gate failed')
            machine,recursive=constructor_trial(machine,train,contexts[1],rows,cache,context_id,
                future_results[0],restored['policy_id'],scope,args,out,binding,protocol,prepare)
            result['recursive_constructor_trial']=recursive
            if recursive['status']=='WARRANTED_BOUNDED_RECURSIVE_DISCOVERABILITY':
                result.update(status=recursive['status'],smallest_obstruction='No fully charged advantage over the informed executable ledger established')
                result['verdicts']['G3']=('UNKNOWN_PREVIOUS_ADMISSION_EXPOSED' if
                    protocol.get('qualification_mode')=='SOURCE_IDENTITY_MAINTENANCE'
                    else 'WARRANTED_BOUNDED_PROSPECTIVE_RECURSIVE_DISCOVERABILITY')
                result['verdicts']['G4']='UNKNOWN_NO_FULL_LIFECYCLE_ADVANTAGE'
                save();return result
        # Shared policy dependence alone cannot establish O1→O2. Constructor
        # support and a second native causal expansion have separate gates.
        result.update(status='BOUNDED_META_SELECTION_ONLY',
            smallest_obstruction=result.get('recursive_constructor_trial',{}).get('smallest_obstruction',
                'Further independently warranted policy/constructor transition from O1 to O2 not established'))
        result['verdicts']['G3']='UNKNOWN_NOT_ESTABLISHED_BY_SHARED_POLICY_REUSE'
        result['verdicts']['G4']='UNKNOWN_NO_FULL_LIFECYCLE_ADVANTAGE'
        save();return result
    finally:
        save()



def main():
    p=argparse.ArgumentParser();p.add_argument('--repo');p.add_argument('--components');p.add_argument('--source-repos')
    p.add_argument('--freeze');p.add_argument('--write-freeze',action='store_true');p.add_argument('--out',required=True)
    p.add_argument('--catalog-spec');p.add_argument('--restart-spec');a=p.parse_args()
    if a.write_freeze: result=write_freeze(a.repo,a.out)
    elif a.catalog_spec:
        result=catalog(**json.loads(Path(a.catalog_spec).read_text()));Path(a.out).write_text(canonical(result)+'\n')
    elif a.restart_spec:result=restart(json.loads(Path(a.restart_spec).read_text()),a.out)
    else:
        try:result=qualify(a)
        except BaseException as error:
            out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
            partial=out/'RESULT.json'
            if partial.exists():
                report=json.loads(partial.read_text())
                report['verdicts_before_integration_error']=report['verdicts']
                report['verdicts']={**report['verdicts'],'G2':'UNKNOWN_INTEGRATION_NOT_QUALIFIED',
                    'G3':'UNKNOWN_INTEGRATION_NOT_QUALIFIED','G4':'UNKNOWN_INTEGRATION_NOT_QUALIFIED'}
                report['status']='INTEGRATION_ERROR_NOT_SCIENTIFIC_SUCCESS'
                partial.write_text(canonical(report)+'\n')
            (out/'ERROR.json').write_text(canonical({'status':'INTEGRATION_ERROR_NOT_SCIENTIFIC_SUCCESS',
                'type':type(error).__name__,'error':str(error)})+'\n')
            raise
    print(canonical({'status':result.get('status','FROZEN') if isinstance(result,dict) else 'CATALOG_WRITTEN',
        'verdicts':result.get('verdicts',{}) if isinstance(result,dict) else {}}))


if __name__=='__main__':main()
