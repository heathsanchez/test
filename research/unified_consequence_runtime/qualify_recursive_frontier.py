"""Generic native maintenance after the preserved failed prospective probe.

The native upstream suite supplies the protected obligation. UNKNOWN setup or
execution and an already satisfied suite never manufacture a developmental
residual. Historical finite genesis examples are not native acquisitions.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

from .developmental_machine import Machine, canonical, digest
from .generic_native_verify import source_identity, environment_identity, fingerprint

HERE=Path(__file__).resolve().parent
RECORDS=HERE/'archaeology/recursive-frontier'
PROTOCOL=RECORDS/'EXPERIMENT.json'
PINS=json.loads(PROTOCOL.read_text())
FREEZE_FILES=[
    'research/unified_consequence_runtime/'+name for name in
    ('generic_native_verify.py','native_frontier.py','qualify_recursive_frontier.py',
     'cross_frontier.py','developmental_machine.py',
     'archaeology/recursive-frontier/EXPERIMENT.json',
     'archaeology/recursive-frontier/MAINTENANCE_BOUNDARY.md','capability_index.json',
     'test_generic_native_verify.py','test_native_frontier.py',
     'test_qualify_recursive_frontier.py','test_native_frontier_activation.py',
     'test_recursive_restart_retention.py')
]+['.github/workflows/udm-recursive-native-frontier.yml']


def development_route(receipt):
    if receipt['status']=='PASS_NATIVE':return 'SATISFIED_NO_DEVELOPMENTAL_RESIDUAL'
    if receipt['status']=='FAIL_NATIVE':return 'SEARCH_EXISTING_LANGUAGE'
    return 'UNKNOWN_NATIVE_OBLIGATION'


def original_candidates(source_repo, source, cap=320):
    """Unchanged authenticated V104 generator; no old-language completeness."""
    if type(cap) is not int or not 0<cap<=320:raise ValueError('frozen positive cap required')
    pin=PINS['constructor_language']
    raw=subprocess.check_output(['git','--no-replace-objects','-C',str(source_repo),
        'show',pin['commit']+':'+pin['path']],stderr=subprocess.PIPE)
    if digest(raw)!=pin['sha256']:raise ValueError('original V104 source changed')
    tree=ast.parse(raw)
    definitions=[node for node in tree.body if
        isinstance(node,ast.FunctionDef) and node.name in pin['definitions'] or
        isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in pin['assignments'] for t in node.targets)]
    names={node.name for node in definitions if isinstance(node,ast.FunctionDef)}
    if names!=set(pin['definitions']):raise ValueError('original generator definitions missing')
    namespace={'ast':ast,'copy':copy,'hashlib':hashlib}
    exec(compile(ast.Module(body=definitions,type_ignores=[]),pin['path'],'exec'),namespace)
    return namespace['program_candidates'](source,cap=cap)


def freeze(repo,out,*,maintenance_only=False):
    if not maintenance_only:
        raise ValueError('original target probe is closed; use maintenance-only or freeze a new independent frontier')
    repo=Path(repo).resolve()
    if subprocess.check_output(['git','-C',str(repo),'diff','--name-only','HEAD']).strip():
        raise ValueError('commit implementation before source freeze')
    manifest={name:digest((repo/name).read_bytes()) for name in FREEZE_FILES}
    for name,expected in manifest.items():
        committed=subprocess.check_output(['git','--no-replace-objects','-C',str(repo),'show','HEAD:'+name],stderr=subprocess.PIPE)
        if digest(committed)!=expected:raise ValueError('freeze source is not exact committed bytes: '+name)
    result={'schema':'udm.recursive-native.freeze.v1',
        'source_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
        'frozen_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'files':manifest,'protocol_sha256':digest(PROTOCOL.read_bytes()),
        'qualification_mode':'MAINTENANCE_ONLY_NO_NEW_TARGET_EXECUTION',
        'target_prior_probe':'KNOWN_NATIVE_IMPORT_ERROR_UNDER_B450; PROSPECTIVE_UNKNOWN',
        'original_freeze_sha256':'aec93ebcaed7f4d4c0eff6c0d921acd297dffa3172827503dc1bb5a2c5c7d5a7'}
    original=HERE/'archaeology/v54-continuation/PROSPECTIVE_FRONTIER_FROZEN.json'
    if digest(original.read_bytes())!=result['original_freeze_sha256']:raise ValueError('original freeze changed')
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(canonical(result)+'\n')
    return result


def check_freeze(repo,path):
    result=json.loads(Path(path).read_text());repo=Path(repo)
    actual=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if result['source_commit']!=actual:raise ValueError('freeze source commit differs from exact checkout')
    if set(result['files'])!=set(FREEZE_FILES):raise ValueError('freeze file set differs')
    for name,expected in result['files'].items():
        if digest((repo/name).read_bytes())!=expected:raise ValueError('frozen implementation changed: '+name)
    if result['protocol_sha256']!=digest(PROTOCOL.read_bytes()):raise ValueError('frozen protocol changed')
    original=HERE/'archaeology/v54-continuation/PROSPECTIVE_FRONTIER_FROZEN.json'
    if digest(original.read_bytes())!=result['original_freeze_sha256']:raise ValueError('original frontier freeze changed')
    return result


def _command(command,out,*,cwd=None,timeout=240):
    started=time.monotonic();out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('wb') as log:
        try:
            process=subprocess.run([str(x) for x in command],cwd=cwd,stdout=log,
                stderr=subprocess.STDOUT,timeout=timeout,check=False)
            result={'exit_code':process.returncode,'status':'PASS' if process.returncode==0 else 'UNKNOWN_SETUP'}
        except subprocess.TimeoutExpired:result={'status':'UNKNOWN_SETUP_TIMEOUT'}
    return {**result,'seconds':time.monotonic()-started,'log_sha256':digest(out.read_bytes()),'log':str(out)}


def provision(name,root,protocol_binding):
    """Same precommitted recipe for control/target; no human dependency repair."""
    pin=PINS[name];root=Path(root);root.mkdir(parents=True,exist_ok=True)
    repo=root/'source';venv=root/'venv'
    commands=[(['git','init','-q',str(repo)],'init'),
        (['git','-C',str(repo),'fetch','--depth=1','https://github.com/'+pin['repository']+'.git',pin['commit']],'fetch'),
        (['git','-C',str(repo),'checkout','--detach','FETCH_HEAD'],'checkout'),
        ([sys.executable,'-m','venv',str(venv)],'venv'),
        ([venv/'bin/python','-m','pip','install','--disable-pip-version-check','--no-input',
          'pip==24.3.1','pytest==8.3.5'],'pytest'),
        ([venv/'bin/python','-m','pip','install','--disable-pip-version-check','--no-input',str(repo)+'[test]'],'project'),
        ([venv/'bin/python','-m','pip','freeze','--all'],'environment-packages')]
    costs=[];archive_identity=None
    for command,phase in commands:
        value=_command(command,root/(phase+'.log'));costs.append({'phase':phase,**value})
        if value['status']!='PASS':return {'status':'UNKNOWN_ENVIRONMENT','costs':costs,'phase':phase,
            'pinned_source_archive':archive_identity}
        if phase=='checkout':
            raw_archive=subprocess.check_output(['git','--no-replace-objects','-C',str(repo),'archive',
                '--format=tar.gz',pin['commit']])
            (root/'pinned-source.tar.gz').write_bytes(raw_archive)
            archive_identity={'path':str(root/'pinned-source.tar.gz'),'sha256':digest(raw_archive),'bytes':len(raw_archive)}
    identity=source_identity(repo,pin['commit']);environment=environment_identity(venv/'bin/python')
    contract={'schema':'UDM_GENERIC_NATIVE_PYTEST_V1','repository':pin['repository'],
        'repo_path':str(repo),'commit':pin['commit'],**identity,
        'interpreter':str(venv/'bin/python'),'environment_sha256':fingerprint(environment),
        'protocol_binding':protocol_binding,'horizon_seconds':7}
    (root/'contract.json').write_text(canonical(contract)+'\n')
    (root/'environment.json').write_text(canonical(environment)+'\n')
    return {'status':'PREPARED','costs':costs,'contract':contract,
        'pinned_source_archive':archive_identity}


def machine(components,state):
    return Machine(Path(components),Path(state),Path(components)/'evaluator',Path(state)/'unused-native-config.json')


def resume_after_restart(parent,result):
    """Reload the single canonical log before the parent writes after a child."""
    charged=list(parent.costs)
    reloaded=Machine(parent.components,parent.state,parent.evaluator,parent.config)
    reloaded.costs[:0]=charged
    if result['consequence'] not in {node.id for node in reloaded.log}:
        raise AssertionError('native restart consequence missing from canonical ledger')
    return reloaded


def _copy_qualified_state(output):
    archive=HERE/'archaeology/programme-closure/QUALIFIED_NATIVE_STATE.tar.gz'
    if digest(archive.read_bytes())!='5086b999e3f11b08524ea201cb8c2ac24842e6e288a56d17ef3c06c2c281a09d':
        raise ValueError('qualified input state archive changed')
    with tarfile.open(archive) as packet:
        for member in packet.getmembers():
            name=Path(member.name)
            if name.is_absolute() or '..' in name.parts or member.issym() or member.islnk():raise ValueError('unsafe state snapshot')
        packet.extractall(output,filter='data')


def _publish(m,runtime,cap):
    from .cross_frontier import publish_frontier_route
    payload=runtime.projection_payload(cap)
    return publish_frontier_route(m,cap,contract=payload['contract'],profiles=payload['profiles'],
        verification_id=payload['verification_id'],validate=runtime._validated)


def _search(runtime,source_repo,output,*,admit=True):
    """Bounded unchanged-language search; no supplied O1/O3 substitutes."""
    started=time.monotonic();calls=[];pin=runtime.contract
    rows=subprocess.check_output(['git','--no-replace-objects','-C',pin['repo_path'],
        'ls-tree','-r','--name-only',pin['commit']],text=True).splitlines()
    from .generic_native_verify import verify
    for name in sorted(rows):
        path=Path(name)
        if path.suffix!='.py' or path.name in ('setup.py','conftest.py') or path.name.endswith('_test.py') or any(
            part.startswith('.') or part in ('test','tests','testing') or part.startswith('test_') for part in path.parts):continue
        raw=subprocess.check_output(['git','--no-replace-objects','-C',pin['repo_path'],'show',pin['commit']+':'+name])
        for selector,builder,text in original_candidates(source_repo,raw.decode(),cap=320):
            if len(calls)>=541 or time.monotonic()-started>=180:
                return {'status':'UNKNOWN_SEARCH','calls':calls,'seconds':time.monotonic()-started}
            candidate={'replacements':[{'path':name,'original_sha256':digest(raw),'replacement':text}]}
            try:receipt=verify(pin,candidate,Path(output)/str(len(calls)))
            except (ValueError,SyntaxError) as error:
                calls.append({'selector':selector,'builder':builder,'path':name,
                    'status':'UNKNOWN_CANDIDATE_SCOPE','reason':str(error),'native_calls':0})
                continue
            calls.append({'selector':selector,'builder':builder,'path':name,'receipt':receipt})
            if receipt['status']=='PASS_NATIVE':
                if not any(row['path']==name for row in receipt['import_manifest']):
                    calls[-1]['promotion']='UNKNOWN_CANDIDATE_NOT_EXERCISED';continue
                cap=runtime.admit(candidate) if admit else None
                return {'status':'WARRANTED_BOUNDED_NATIVE_METHOD_ONLY','capability':cap,'calls':calls,
                    'seconds':time.monotonic()-started,'O1_causal_discoverability':'UNKNOWN',
                    'O3_developmental_change':'UNKNOWN'}
    return {'status':'UNKNOWN_SEARCH','calls':calls,'seconds':time.monotonic()-started,
        'complete_old_language_obstruction':'NOT_PROVIDED'}


def restart(spec,out):
    from .native_frontier import NativeFrontierRuntime
    m=machine(spec['components'],spec['state'])
    runtime=NativeFrontierRuntime(m,spec['contract'],Path(out).parent/'restart-native')
    receipt,consequence=runtime.execute(spec['capability'])
    result={'status':'PASS' if receipt['status']=='PASS_NATIVE' else 'UNKNOWN',
        'native':receipt,'consequence':consequence,'process_id':os.getpid()}
    Path(out).write_text(canonical(result)+'\n');return result


def qualify(args):
    from .native_frontier import NativeFrontierRuntime,FRONTIER_CONTRACT
    from .cross_frontier import register_frontier,require_frontier_route
    out=Path(args.out).absolute();out.mkdir(parents=True,exist_ok=False)
    frozen=check_freeze(args.repo,args.freeze);binding=digest(Path(args.freeze).read_bytes())
    if frozen.get('qualification_mode')!='MAINTENANCE_ONLY_NO_NEW_TARGET_EXECUTION':
        raise ValueError('closed prospective protocol cannot be rerun by maintenance code')
    report={'schema':'udm.recursive-native.result.v1','source_commit':frozen['source_commit'],
        'freeze':frozen,'freeze_sha256':binding,'started_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'verdicts':{'GENERIC_ADMISSION':'UNKNOWN','PROSPECTIVE_NATIVE_DISCOVERY':'UNKNOWN',
        'O1_O2_O3_RECURSIVE_CAUSALITY':'UNKNOWN','COMPARATIVE_ADVANTAGE':'UNKNOWN',
        'EXTERNAL_ENFORCEMENT':'UNKNOWN'},'conditions':{name:{'status':'NOT_RUN_PREREQUISITE_NOT_ESTABLISHED'}
            for name in PINS['conditions']},'process_id':os.getpid()}
    started=time.monotonic()
    m=None;original=()
    def save():
        report['total_wall_seconds']=time.monotonic()-started
        if m is not None:
            report['machine_costs']=m.costs
            report['retention']={'original_records_retained':len(original),'final_records':len(m.log),
                'ledger_sha256':digest((out/'state/metatron-ledger.jsonl').read_bytes()),
                'persistent_bytes':sum(p.stat().st_size for p in (out/'state').rglob('*') if p.is_file())}
        (out/'RESULT.json').write_text(canonical(report)+'\n')
    try:
        _copy_qualified_state(out);m=machine(args.components,out/'state')
        original=tuple(node.id for node in m.log);report['historical_records']=len(original)
        control=provision('control',out/'control',binding);report['control_setup']=control;save()
        if control['status']!='PREPARED':
            report.update(status='UNKNOWN_PREREQUISITE',smallest_obstruction='UNKNOWN_GENERIC_CONTROL_ENVIRONMENT');save();return report
        runtime=NativeFrontierRuntime(m,control['contract'],out/'control-evidence')
        receipt=runtime.observe();report['control_native']=receipt
        if receipt['status']!='PASS_NATIVE':
            report.update(status='UNKNOWN_PREREQUISITE',smallest_obstruction='UNKNOWN_GENERIC_CONTROL_NATIVE_VERIFIER');save();return report
        cap=runtime.admit({'replacements':[]});payload=runtime.projection_payload(cap)
        frontier='generic:'+payload['profiles'][0]
        register_frontier(m,frontier,contract=FRONTIER_CONTRACT,profile=payload['profiles'][0],
            request={'repository':control['contract']['repository'],'commit':control['contract']['commit']})
        register_frontier(m,'generic-wrong-authority',
            contract={**FRONTIER_CONTRACT,'verifier_id':'wrong-independent-verifier'},
            profile=payload['profiles'][0],request={'repository':control['contract']['repository'],
                'commit':control['contract']['commit']})
        _publish(m,runtime,cap)
        report['control_admission']={'capability':cap,'route':require_frontier_route(m,frontier,validate=runtime._validated),
            'native':m.select_and_execute_frontier(frontier,runtime)}
        report['wrong_authority_control']=require_frontier_route(m,'generic-wrong-authority')
        if report['wrong_authority_control']['status']!='UNKNOWN_SEARCH':raise AssertionError('wrong authority gained native route')
        inherited_live=set(m.mt.live_ids(m.log))
        # Causal controls qualify admission only: no acquired O1/O2/O3 exists here.
        unrelated=m.append('independent_control_support',{'kind':'unrelated-local-control'})
        m.flush();m.append('revoke',{'target':unrelated,'reason':'unrelated controlled withdrawal'});m.flush()
        report['unrelated_withdrawal_native']=runtime.execute(cap)[0]
        m.withdraw(cap,'exact generic native control source support')
        blocked=False
        try:runtime.execute(cap)
        except PermissionError:blocked=True
        if not blocked:raise AssertionError('ancestor withdrawal failed to block native execution')
        if not (set(original)&inherited_live)<=set(m.mt.live_ids(m.log)):
            raise AssertionError('native control withdrawal damaged unrelated inherited state')
        report['ancestor_withdrawal']={'blocked':blocked,'route':require_frontier_route(m,frontier,validate=runtime._validated)}
        restored=runtime.restore(cap);_publish(m,runtime,restored)
        spec={'components':str(Path(args.components).resolve()),'state':str(out/'state'),
              'contract':control['contract'],'capability':restored}
        (out/'restart-spec.json').write_text(canonical(spec)+'\n')
        process=_command([sys.executable,'-B','-m',__spec__.name,'--restart',out/'restart-spec.json',
            '--restart-out',out/'cold-restart.json'],out/'restart.log',cwd=args.repo)
        report['restart_process_cost']=process
        if process['status']!='PASS':raise AssertionError('native separate-process restart failed')
        report['cold_restart']=json.loads((out/'cold-restart.json').read_text())
        if report['cold_restart']['status']!='PASS' or report['cold_restart']['process_id']==os.getpid():
            raise AssertionError('restart did not independently execute native suite')
        m=resume_after_restart(m,report['cold_restart'])
        report['verdicts']['GENERIC_ADMISSION']='WARRANTED_BOUNDED_NATIVE_CONTROL'
        if frozen.get('qualification_mode')=='MAINTENANCE_ONLY_NO_NEW_TARGET_EXECUTION':
            marker=m.append('maintenance_continuation',{'restart_consequence':report['cold_restart']['consequence']})
            m.flush()
            if report['cold_restart']['consequence'] not in {node.id for node in m.log}:
                raise AssertionError('parent continuation lost child restart consequence')
            report['restart_retention']={'status':'PASS','consequence':report['cold_restart']['consequence'],
                'parent_continuation':marker,'final_ledger_contains_both':True}
            report['status']='WARRANTED_BOUNDED_MAINTENANCE_CONTROL_RECURSIVE_UNKNOWN'
            report['smallest_obstruction']='ORIGINAL_PROSPECTIVE_NATIVE_BUILD_MATERIALIZATION_AND_NATIVE_O1_O3_BINDINGS_UNCLOSED'
            report['target_reexecuted']=False
            save();return report
        save()
        # First target materialization is after exact freeze and native control.
        target=provision('target',out/'target',binding);report['target_setup']=target;save()
        if target['status']!='PREPARED':
            report.update(status='UNKNOWN_PREREQUISITE',smallest_obstruction='UNKNOWN_FROZEN_GENERIC_TARGET_ENVIRONMENT');save();return report
        future=NativeFrontierRuntime(m,target['contract'],out/'target-evidence')
        cold=future.observe();event=cold['observation_id'];route=development_route(cold)
        report['conditions']['cold']={'native':cold,'observation':event,'route':route}
        # Matched no-acquisition sham and equally informed ledger use actual verifier.
        for condition in ('sham','equally_informed_executable_ledger'):
            value=future.observe();event=value['observation_id'];report['conditions'][condition]={'native':value,'observation':event,
                'information':'SAME_SOURCE_ENVIRONMENT_SUPPLIED_OPERATORS_OBSERVATIONS_AND_EVIDENCE',
                'route':development_route(value),'acquisitions':0}
        if route=='SEARCH_EXISTING_LANGUAGE':
            report['cold_existing_language_search']=_search(future,args.constructor_source,out/'cold-search')
            report['ledger_existing_language_search']=_search(future,args.constructor_source,out/'ledger-search',admit=False)
        else:report['smallest_obstruction']=route
        for condition in ('O1_only','O1_O2','O1_O2_O3'):
            report['conditions'][condition]={'status':'NOT_RUN_MISSING_INDEPENDENTLY_WARRANTED_NATIVE_ACQUISITION',
                'reason':'No historical finite mechanism or supplied native bridge is relabeled as acquired developmental machinery.'}
        report['baseline_comparison']={'status':'NO_DEVELOPMENTAL_ADVANTAGE_DEMONSTRATED',
            'cold':cold['status'],'ledger':report['conditions']['equally_informed_executable_ledger']['native']['status'],
            'budget_equal':True,'comparison_scope':'SUPPLIED_NATIVE_VERIFIER_AND_EXISTING_LANGUAGE_ONLY',
            'full_lifecycle_advantage':'UNKNOWN','live_agent_comparator':'NOT_RUN'}
        if report['baseline_comparison']['cold']==report['baseline_comparison']['ledger']:
            report['verdicts']['COMPARATIVE_ADVANTAGE']='REJECTED_MEASURED_NATIVE_OBSERVATION_TIE_ONLY'
        if tuple(node.id for node in m.log[:len(original)])!=original:raise AssertionError('historical state changed')
        report['retention']={'original_records_retained':len(original),'final_records':len(m.log),
            'ledger_sha256':digest((out/'state/metatron-ledger.jsonl').read_bytes()),
            'persistent_bytes':sum(p.stat().st_size for p in (out/'state').rglob('*') if p.is_file())}
        report['machine_costs']=m.costs
        report['status']='QUALIFIED_BOUNDED_ADMISSION_RECURSIVE_RESULT_UNKNOWN'
        save();return report
    except Exception as error:
        report.update(status='FAILED_OR_UNKNOWN',error={'type':type(error).__name__,'reason':str(error)})
        save();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('repo','freeze','out','components','constructor-source','restart','restart-out'):
        parser.add_argument('--'+key,type=Path)
    parser.add_argument('--write-freeze',action='store_true')
    parser.add_argument('--maintenance-only',action='store_true')
    args=parser.parse_args()
    if args.write_freeze:result=freeze(args.repo,args.out,maintenance_only=args.maintenance_only)
    elif args.restart:result=restart(json.loads(args.restart.read_text()),args.restart_out)
    else:result=qualify(args)
    print(canonical({'status':result.get('status','FROZEN'),'source_commit':result.get('source_commit')}))

if __name__=='__main__':main()
