"""Qualify typed source transport without promoting a developmental claim.

The original native collection, protected-assertion and independent-replay
algorithms are executed against versioned V42 dependencies.  Every retained
fixture is an admission control, never a fresh prospective task.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import FunctionType, SimpleNamespace
import unittest

from . import native_environment_v42 as environment
from . import native_execution_v42 as execution
from . import qualify_environment_selection_v41 as previous
from .audit_index_v4 import snapshot_indexes, compare_indexes
from .decisive_native_verify import canonical, fingerprint, sha256

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECORDS = HERE/'archaeology/native-authority-v42'
CATALOG = HERE/'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
BASE = 'dc59c8fcee6efede520c531eba5e42e7b84a1a9f'
ACCEPTANCE_COMMIT = 'c547612c80307c7ad218e3f7986df918525e5e86'
SUPPLEMENTARY_COMMIT = '7dc52f864d885509b53c1712206c68d4264aa2ee'
FREEZE_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V42'
RESULT_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V42'
source_authority = previous.source_authority
RecordedResult = previous.RecordedResult
retained_temporary_outputs = previous.retained_temporary_outputs
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
_FROZEN_TEST_PATHS = tuple('research/unified_consequence_runtime/'+name for name in (
    'test_native_source_v42.py', 'test_native_execution_v42.py',
    'test_qualify_native_frontier_v42.py',
    'archaeology/native-authority-v42/ACCEPTANCE_PROTOCOL.json',
    'archaeology/native-authority-v42/ACCEPTANCE_TEST_FREEZE.json'))
_SUPPLEMENTARY_TEST_PATHS = tuple('research/unified_consequence_runtime/'+name for name in (
    'test_native_source_v42_regressions.py','test_native_execution_v42_regressions.py',
    'archaeology/native-authority-v42/SUPPLEMENTARY_REVIEW_FREEZE.json'))
SOURCE_GATE_FILES = tuple(dict.fromkeys((*previous.SOURCE_GATE_FILES,
    *(('research/unified_consequence_runtime/'+name) for name in (
        'native_source_v42.py', 'native_admission_v42.py', 'native_execution_v42.py',
        'native_environment_v42.py', 'native_runtime_v42.py',
        'qualify_native_authority_v42.py', 'qualify_native_frontier_v42.py',
        'test_qualify_native_frontier_v42.py',
        'test_native_source_v42_regressions.py',
        'test_native_execution_v42_regressions.py',
        'archaeology/native-authority-v42/SUPPLEMENTARY_REVIEW_FREEZE.json',
        'archaeology/native-authority-v42/curate_frontier.py',
        'archaeology/native-authority-v42/prepare_records.py')),
    *_FROZEN_TEST_PATHS, '.github/workflows/udm-native-authority-v42.yml',
    '.github/workflows/udm-prospective-native-selection-v42.yml')))


def _guard():
    if sha256(Path(__file__).read_bytes()) != _LOADED_SHA256:
        raise ValueError('UNKNOWN_V42_QUALIFICATION_SOURCE_CHANGED')
    execution._runner_hash()
    environment._guard()


def inputs():
    _guard()
    acceptance = json.loads((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_text())
    tests = json.loads((RECORDS/'ACCEPTANCE_TEST_FREEZE.json').read_text())
    if (acceptance.get('schema') != 'UDM_TYPED_NATIVE_SOURCE_ACCEPTANCE_V42'
            or acceptance.get('baseline') != BASE
            or tests.get('implementation_absent_at_freeze') is not True):
        raise ValueError('frozen V42 admission protocol differs')
    for name, row in tests['tests'].items():
        if sha256((HERE/name).read_bytes()) != row['sha256']:
            raise ValueError('frozen preimplementation V42 test changed: '+name)
    supplementary = json.loads((RECORDS/'SUPPLEMENTARY_REVIEW_FREEZE.json').read_text())
    for name,row in supplementary['tests'].items():
        if sha256((HERE/name).read_bytes()) != row['sha256']:
            raise ValueError('frozen supplementary adversarial test changed: '+name)
    catalog = json.loads(CATALOG.read_text())
    environment.selection._catalog(catalog)
    return catalog


def _retain_index_bytes(snapshot, destination):
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    for number, row in enumerate(snapshot['indexes']):
        if row['exists']:
            raw = Path(row['path']).read_bytes()
            if sha256(raw) != row['sha256'] or len(raw) != row['size_bytes']:
                raise ValueError('index changed while retaining pre-read bytes')
            (destination/('index-'+str(number)+'.bytes')).write_bytes(raw)
    (destination/'SNAPSHOT.json').write_text(canonical(snapshot)+'\n')


def _write_freeze(repo, out, runtime_paths):
    started = time.monotonic(); catalog = inputs()
    head = source_authority._git(repo, 'rev-parse', 'HEAD').decode().strip()
    paths = source_authority._git(repo, 'ls-tree', '-r', '--name-only', head).decode().splitlines()
    if not set(SOURCE_GATE_FILES) <= set(paths):
        raise ValueError('commit every V42 qualification and prospective authority file first')
    source_authority._git(repo, 'merge-base', '--is-ancestor', ACCEPTANCE_COMMIT, head)
    source_authority._git(repo, 'merge-base', '--is-ancestor', SUPPLEMENTARY_COMMIT, head)
    for commit, names in ((ACCEPTANCE_COMMIT,_FROZEN_TEST_PATHS),
                          (SUPPLEMENTARY_COMMIT,_SUPPLEMENTARY_TEST_PATHS)):
        for name in names:
            if source_authority._git(repo, 'show', commit+':'+name) != (Path(repo)/name).read_bytes():
                raise ValueError('frozen adversarial acceptance bytes changed: '+name)
    frozen = source_authority.freeze_source(repo, BASE, paths)
    profiles = {row['id']:row for row in catalog['profiles']}
    if not isinstance(runtime_paths, dict) or set(runtime_paths) != set(profiles):
        raise ValueError('complete independently supplied two-profile runtime inventory required')
    runtimes = {name:environment.freeze_runtime(runtime_paths[name]) for name in sorted(profiles)}
    identities = {}
    for name, profile in profiles.items():
        environment.validate_runtime(profile, runtimes[name])
        identities[name] = {'environment':execution.environment_identity(runtimes[name]['interpreter']),
            'package_files_sha256':fingerprint(environment.installed_package_identity(runtimes[name]['interpreter'], profile))}
    frozen.update(schema=FREEZE_SCHEMA, catalog_sha256=fingerprint(catalog),
        runtimes=runtimes, profile_identities=identities, mode='ADMISSION_ONLY',
        acceptance_commit=ACCEPTANCE_COMMIT,
        supplementary_commit=SUPPLEMENTARY_COMMIT,
        acceptance_sha256=sha256((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_bytes()),
        test_sha256={name:sha256((HERE/name).read_bytes()) for name in
                     ('test_native_source_v42.py','test_native_execution_v42.py')},
        freeze_wall_seconds=time.monotonic()-started)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(canonical(frozen)+'\n')
    return frozen


def write_freeze(repo, out, runtime_paths):
    before = snapshot_indexes(repo); os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    path = Path(out).absolute()
    destinations = [path, *(path.with_name(path.name+suffix) for suffix in
                           ('.INDEX_AUDIT.json','.INDEX_BEFORE','.INDEX_AFTER'))]
    if any(p.exists() for p in destinations):
        raise ValueError('refusing to replace prior V42 freeze or index evidence')
    with tempfile.TemporaryDirectory(prefix='udm-v42-prefreeze-index-') as scratch:
        retained = Path(scratch)/'before'; _retain_index_bytes(before, retained)
        try:
            return _write_freeze(repo, path, runtime_paths)
        finally:
            after = snapshot_indexes(repo)
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(retained, path.with_name(path.name+'.INDEX_BEFORE'))
            _retain_index_bytes(after, path.with_name(path.name+'.INDEX_AFTER'))
            audit = {'before':before,'after':after,'changes':compare_indexes(before,after)}
            path.with_name(path.name+'.INDEX_AUDIT.json').write_text(canonical(audit)+'\n')
            if audit['changes']:
                raise ValueError('Git index changed during V42 freeze; evidence retained')


def check_freeze(repo, path):
    catalog = inputs(); frozen = json.loads(Path(path).read_text())
    head = source_authority._git(repo, 'rev-parse', 'HEAD').decode().strip()
    paths = source_authority._git(repo, 'ls-tree', '-r', '--name-only', head).decode().splitlines()
    if (frozen.get('schema') != FREEZE_SCHEMA or frozen.get('source_commit') != head
            or frozen.get('baseline_commit') != BASE or frozen.get('mode') != 'ADMISSION_ONLY'
            or frozen.get('catalog_sha256') != fingerprint(catalog)
            or frozen.get('acceptance_commit') != ACCEPTANCE_COMMIT
            or frozen.get('supplementary_commit') != SUPPLEMENTARY_COMMIT
            or frozen.get('acceptance_sha256') != sha256((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_bytes())
            or frozen.get('test_sha256') != {name:sha256((HERE/name).read_bytes()) for name in
                                          ('test_native_source_v42.py','test_native_execution_v42.py')}
            or set(frozen.get('files',{})) != set(paths)
            or not set(SOURCE_GATE_FILES) <= set(paths)
            or frozen.get('all_baseline_files_preserved') is not True):
        raise ValueError('V42 source, acceptance or external catalog differs from freeze')
    source_authority._preserved_baseline(repo, BASE, head)
    for name, digest in frozen['files'].items():
        if sha256((Path(repo)/name).read_bytes()) != digest:
            raise ValueError('frozen authority source changed: '+name)
    profiles = {row['id']:row for row in catalog['profiles']}
    if set(frozen['runtimes']) != set(profiles):
        raise ValueError('V42 frozen runtime inventory differs')
    for name, profile in profiles.items():
        runtime = frozen['runtimes'][name]
        environment.validate_runtime(profile, runtime)
        expected = {'environment':execution.environment_identity(runtime['interpreter']),
            'package_files_sha256':fingerprint(environment.installed_package_identity(runtime['interpreter'], profile))}
        if frozen['profile_identities'].get(name) != expected:
            raise ValueError('frozen package/executable profile changed')
    return frozen


_CHILD_REPLAY = '''import json,pathlib,sys
from research.unified_consequence_runtime import native_execution_v42 as worker
from research.unified_consequence_runtime.decisive_native_verify import canonical
context=json.loads(pathlib.Path(sys.argv[1]).read_text())
before=worker.attempt_snapshot()
receipt=worker.validate_receipt(context['contract'],context['candidate'],context['authority'],
 context['certificate'],context['receipt'],policy=context['policy'],output_dir=sys.argv[2],independent=True)
after=worker.attempt_snapshot()
assert receipt['status']=='PASS_NATIVE' and receipt['junit']['passed']==2
result={'status':receipt['status'],'junit':receipt['junit'],
 'attempt_costs':{k:after[k]-before[k] for k in after},
 'independent_reexecution':receipt['independent_reexecution'],
 'controller_environment':worker.environment_identity(sys.executable)}
pathlib.Path(sys.argv[3]).write_text(canonical(result)+'\\n')
print(canonical({'status':result['status'],'attempt_costs':result['attempt_costs']}))
'''


def _retain_case(case):
    destination = os.environ.get('UDM_V42_NATIVE_EVIDENCE_ROOT')
    if not destination or not hasattr(case,'root'):
        return
    if (case.id().endswith('.test_actual_link_import_failure_success_and_independent_reexecution')
            and hasattr(case,'_v42_context')):
        contract, authority = case._v42_context
        candidate = case.candidate()
        receipts = [json.loads(path.read_text()) for path in sorted(case.root.glob('evidence-*/receipt.json'))]
        receipt = next((row for row in receipts if row['status']=='PASS_NATIVE'
                       and row['candidate_sha256']==fingerprint(candidate)),None)
        if receipt is None:
            shutil.copytree(case.root,Path(destination)/case.id(),symlinks=True)
            return
        certificate = json.loads((case.root/'evidence-1/admission-certificate.json').read_text())
        context = {'contract':contract,'authority':authority,'candidate':candidate,
                   'policy':case.policy,'certificate':certificate,'receipt':receipt}
        (case.root/'separate-process-context.json').write_text(canonical(context)+'\n')
        started = time.monotonic()
        replay = subprocess.run([sys.executable,'-B','-c',_CHILD_REPLAY,
            str(case.root/'separate-process-context.json'),str(case.root/'separate-process-replay'),
            str(case.root/'separate-process-result.json')],cwd=ROOT,
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0'),
            capture_output=True,timeout=180)
        (case.root/'separate-process-stdout.log').write_bytes(replay.stdout)
        (case.root/'separate-process-stderr.log').write_bytes(replay.stderr)
        (case.root/'separate-process-controller.json').write_text(canonical({
            'returncode':replay.returncode,'seconds':time.monotonic()-started,
            'controller_executable':sys.executable})+'\n')
        if replay.returncode:
            # Retain failure before unittest propagates this cleanup error.
            shutil.copytree(case.root,Path(destination)/case.id(),symlinks=True)
            raise ValueError('separate-process independent native replay failed: '+replay.stderr.decode(errors='replace')[-1000:])
    shutil.copytree(case.root,Path(destination)/case.id(),symlinks=True)


def _retained(cls):
    old_setup = cls.setUp
    def setup(case):
        old_setup(case)
        case.addCleanup(_retain_case,case)
    methods = {'__module__':cls.__module__,'setUp':setup}
    if callable(getattr(cls,'contract',None)):
        original_contract = cls.contract
        def contract(case,*args,**kwargs):
            result = original_contract(case,*args,**kwargs)
            case._v42_context = result
            return result
        methods['contract'] = contract
    return type(cls.__name__,(cls,),methods)


def _private_v4_class(cls):
    """Run preserved fixture statements with new explicit authority dependencies."""
    from . import test_native_authority_v4 as old
    realm_overrides = {'execution':execution,'worker':execution,'original':execution.original,
                       'frozen':execution.original,'admission':execution.admission}
    methods = {'__module__':old.__name__}
    for name, value in vars(cls).items():
        is_classmethod = isinstance(value,classmethod)
        value = value.__func__ if is_classmethod else value
        if name=='setUp' and isinstance(value,FunctionType) and 'set_up' in value.__code__.co_freevars:
            value = value.__closure__[value.__code__.co_freevars.index('set_up')].cell_contents
        if isinstance(value,FunctionType):
            namespace = dict(value.__globals__,**realm_overrides)
            rebound = FunctionType(value.__code__,namespace,value.__name__,value.__defaults__,value.__closure__)
            rebound.__kwdefaults__ = value.__kwdefaults__
            methods[name] = classmethod(rebound) if is_classmethod else rebound
    # The plugin fixture carries V3's two-stage refresh wrapper. Rebind the
    # original V2 refresh directly, then set only the versioned contract schema.
    if hasattr(cls,'refresh'):
        from .test_native_admission_v2_adversarial import NativeAdmissionV2AdversarialTests
        original_refresh = NativeAdmissionV2AdversarialTests.refresh
        realm = dict(original_refresh.__globals__,**realm_overrides)
        refresh_body = FunctionType(original_refresh.__code__,realm,'refresh')
        def refresh(case):
            refresh_body(case);case.contract['schema']=execution.SCHEMA
        methods['refresh'] = refresh
        def setup_class(target):
            target.environment=execution.environment_identity(sys.executable)
            target.policy={'schema':execution.POLICY_SCHEMA,'collection_seconds':15,
                'execution_seconds':15,'pytest_version':target.environment['pytest_version'],'plugins':[]}
        methods['setUpClass'] = classmethod(setup_class)
    return _retained(type(cls.__name__,(unittest.TestCase,),methods))


def _temporary_retained(cls):
    """Retain method-local review fixtures through explicit private bindings.

    The original statements, assertions, tempfile module, subprocess module and
    native worker globals are untouched. Only these test functions receive an
    observing tempfile/subprocess dependency in their own private namespace.
    """
    methods={'__module__':cls.__module__}
    for name,value in vars(cls).items():
        is_classmethod=isinstance(value,classmethod)
        function=value.__func__ if is_classmethod else value
        if not isinstance(function,FunctionType):
            continue
        state={'number':0,'active':None,'subprocesses':0}
        ident=cls.__module__+'.'+cls.__name__+'.'+name
        def retained_directory(*args,_state=state,_ident=ident,**kwargs):
            original=tempfile.TemporaryDirectory(*args,**kwargs)
            class ObservedDirectory:
                def __enter__(self):
                    folder=original.__enter__();_state['active']=Path(folder)
                    return folder
                def __exit__(self,*exc):
                    try:
                        destination=os.environ.get('UDM_V42_NATIVE_EVIDENCE_ROOT')
                        if destination:
                            _state['number']+=1
                            target=Path(destination)/'subcases'/_ident/f'{_state["number"]:04d}'
                            shutil.copytree(original.name,target,symlinks=True)
                    finally:
                        _state['active']=None
                        original.__exit__(*exc)
            return ObservedDirectory()
        def observed_run(*args,_state=state,**kwargs):
            started=time.monotonic();result=None;error=None
            try:
                result=subprocess.run(*args,**kwargs)
                return result
            except (OSError,subprocess.SubprocessError) as caught:
                error=type(caught).__name__+': '+str(caught)
                raise
            finally:
                if _state['active'] is not None:
                    _state['subprocesses']+=1
                    def encoded(raw):
                        if raw is None:return None
                        return base64.b64encode(raw.encode() if isinstance(raw,str) else raw).decode()
                    record={'argv':[str(x) for x in args[0]],'seconds':time.monotonic()-started,
                        'returncode':None if result is None else result.returncode,
                        'stdout_base64':None if result is None else encoded(result.stdout),
                        'stderr_base64':None if result is None else encoded(result.stderr),'error':error}
                    (_state['active']/f'test-controller-subprocess-{_state["subprocesses"]:04d}.json').write_text(canonical(record)+'\n')
        namespace=dict(function.__globals__,
            tempfile=SimpleNamespace(**dict(vars(tempfile),TemporaryDirectory=retained_directory)),
            subprocess=SimpleNamespace(**dict(vars(subprocess),run=observed_run)))
        rebound=FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)
        rebound.__kwdefaults__=function.__kwdefaults__
        methods[name]=classmethod(rebound) if is_classmethod else rebound
    return type(cls.__name__,(unittest.TestCase,),methods)


def _suite(legacy_only=False):
    from . import test_native_source_v42 as source_tests
    from . import test_native_execution_v42 as native_tests
    from . import test_native_source_v42_regressions as source_regressions
    from . import test_native_execution_v42_regressions as native_regressions
    from . import test_native_authority_v4 as old
    loader = unittest.defaultTestLoader
    selected = _retained(native_tests.NativeExecutionV42Contracts)
    if legacy_only:
        return unittest.TestSuite(selected(name) for name in (
            'test_actual_link_import_failure_success_and_independent_reexecution',
            'test_alias_candidate_is_refused_before_native_warrant'))
    return unittest.TestSuite((loader.loadTestsFromTestCase(_retained(source_tests.NativeSourceV42Contracts)),
        loader.loadTestsFromTestCase(selected),
        loader.loadTestsFromTestCase(_retained(native_tests.inherited_suite())),
        loader.loadTestsFromTestCase(_private_v4_class(old.MalformedPythonNativeAuthorityV4)),
        loader.loadTestsFromTestCase(_private_v4_class(old.LicensedPluginReplacementAuthorityV4)),
        *(loader.loadTestsFromTestCase(_temporary_retained(cls) if module is native_regressions else _retained(cls)) for module in
          (source_regressions,native_regressions) for cls in vars(module).values()
          if isinstance(cls,type) and issubclass(cls,unittest.TestCase)
          and cls is not unittest.TestCase and cls.__module__==module.__name__)))


def _ids(suite):
    result=[]
    for test in suite:
        result.extend(_ids(test) if isinstance(test,unittest.TestSuite) else [test.id()])
    return result


def qualify(repo, freeze, out, *, legacy_only=False):
    before = snapshot_indexes(repo);os.environ['GIT_OPTIONAL_LOCKS']='0'
    out=Path(out).absolute();out.mkdir(parents=True,exist_ok=False)
    _retain_index_bytes(before,out/'index-before')
    started=time.monotonic();attempts=execution.attempt_snapshot()
    result={'schema':RESULT_SCHEMA,'status':'UNKNOWN_ADMISSION','mode':'LEGACY_NATIVE_CONTROLS_ONLY' if legacy_only else 'ADMISSION_ONLY',
        'first_task_gate':{'status':'UNKNOWN'},'acquisitions':0,'candidates':0,
        'verdicts':{'G0_G1':'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY',**{f'G{i}':'UNKNOWN' for i in range(2,7)}},
        'cost_boundary':'Parent/child native and collection attempts and measured wall only; full lifecycle/model/tool/engineering costs remain UNKNOWN.'}
    names=('UDM_V42_NATIVE_EVIDENCE_ROOT','UDM_NATIVE_V42_INTERPRETER','UDM_NATIVE_V3_INTERPRETER','UDM_V4_NATIVE_EVIDENCE_ROOT')
    saved={name:os.environ.get(name) for name in names}
    try:
        frozen=check_freeze(repo,freeze)
        result.update(source_commit=frozen['source_commit'],freeze=frozen)
        selected=(min if legacy_only else max)(frozen['runtimes'].values(),key=lambda row:row['identity']['version_info'][:3])
        os.environ.update(UDM_V42_NATIVE_EVIDENCE_ROOT=str(out/'native-evidence'),
            UDM_NATIVE_V42_INTERPRETER=selected['interpreter'],UDM_NATIVE_V3_INTERPRETER=selected['interpreter'])
        os.environ.pop('UDM_V4_NATIVE_EVIDENCE_ROOT',None)
        suite=_suite(legacy_only);expected=_ids(suite)
        if len(expected)!=(2 if legacy_only else 60) or len(set(expected))!=len(expected):
            raise ValueError('exact 55 initial + 5 supplementary modern / 2 legacy admission controls required')
        with (out/'contracts.log').open('w') as stream,retained_temporary_outputs(out/'default-collection-evidence'):
            RecordedResult.ids=[]
            verdict=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResult).run(suite)
        result['contracts']={'run':verdict.testsRun,'ids':sorted(verdict.ids),'expected_ids':sorted(expected),
            'failures':len(verdict.failures),'errors':len(verdict.errors),'skipped':len(verdict.skipped),'successful':verdict.wasSuccessful()}
        result['control_scope']={'initial_frozen_controls':2 if legacy_only else 55,
                                 'supplementary_review_controls':0 if legacy_only else 5}
        positive=out/'native-evidence'/(native_test_id()+'.test_actual_link_import_failure_success_and_independent_reexecution')
        child=json.loads((positive/'separate-process-result.json').read_text())
        result['positive_independent_native']=child
        result['selected_profile_interpreter']=selected['interpreter']
        result['controller_environment']=execution.environment_identity(sys.executable)
        check_freeze(repo,freeze)
        current=execution.attempt_snapshot()
        if (verdict.wasSuccessful() and not verdict.skipped and sorted(verdict.ids)==sorted(expected)
                and child['status']=='PASS_NATIVE' and child['junit']['passed']==2
                and child['attempt_costs']['native_calls']>0 and child['attempt_costs']['collection_calls']>0
                and current['native_calls']>attempts['native_calls'] and current['collection_calls']>attempts['collection_calls']):
            result['status']='LEGACY_NATIVE_CONTROLS_VERIFIED' if legacy_only else 'ADMISSION_ONLY_QUALIFIED'
            if not legacy_only:
                result['first_task_gate']={'status':'PASS','boundary':'Frozen typed-source/native admission controls only; not G2'}
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,subprocess.SubprocessError) as error:
        result['error']=type(error).__name__+': '+str(error)
    finally:
        for name,value in saved.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
        after=snapshot_indexes(repo);_retain_index_bytes(after,out/'index-after')
        result['index_audit']={'before':before,'after':after,'changes':compare_indexes(before,after)}
        if result['index_audit']['changes']:
            result.update(status='UNKNOWN_ADMISSION',first_task_gate={'status':'UNKNOWN'})
        current=execution.attempt_snapshot()
        result['attempt_costs']={key:current[key]-attempts[key] for key in current}
        result['total_wall_seconds']=time.monotonic()-started
        (out/'RESULT.json').write_text(canonical(result)+'\n')
    return result


def native_test_id():
    return __package__+'.test_native_execution_v42.NativeExecutionV42Contracts'


def main():
    os.environ.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--runtimes');parser.add_argument('--freeze')
    parser.add_argument('--write-freeze',action='store_true')
    parser.add_argument('--legacy-native-controls',action='store_true')
    args=parser.parse_args()
    if args.write_freeze:
        result=write_freeze(args.repo,args.out,json.loads(Path(args.runtimes).read_text()))
    else:
        result=qualify(args.repo,args.freeze,args.out,legacy_only=args.legacy_native_controls)
    print(canonical({'status':result.get('status',result.get('schema')),'verdicts':result.get('verdicts',{})}))
    if not args.write_freeze and result['status']!=('LEGACY_NATIVE_CONTROLS_VERIFIED' if args.legacy_native_controls else 'ADMISSION_ONLY_QUALIFIED'):
        raise SystemExit(1)


if __name__=='__main__':
    main()
