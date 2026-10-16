"""Admission-only V4 qualification; no acquisition or prospective task outcome.

Run frozen real-native acceptance controls, retain every raw packet, reconcile
the seven exposed metadata diagnostics, and preserve all prior source bytes.
The original native verifier and its independent replay remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import time
import unittest

from . import native_environment_v4 as environment
from . import native_execution_v3 as execution
from . import qualify_environment_selection_v3 as source_authority
from .audit_index_v4 import snapshot_indexes, compare_indexes
from .decisive_native_verify import canonical, fingerprint, sha256

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECORDS = HERE/'archaeology/native-authority-v4'
CATALOG = HERE/'archaeology/native-environment-v3/ENVIRONMENT_CATALOG.json'
BASE = '95029db0d0b2122836bee7268299461bfbdb5a66'
FREEZE_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V4'
ACCEPTANCE_SHA256 = '652c2f5117be0e61d6953c509228580a7441e2a8bc23fa1b67c2b5fc240b8671'
TEST_SHA256 = 'dd23f7325bac1c4e0dd895a1f93f84ce122e3f58443bd8986f3cc1115070b564'
SOURCE_GATE_FILES = tuple('research/unified_consequence_runtime/'+name for name in (
    'native_environment_selection_v4.py', 'native_environment_v4.py',
    'qualify_environment_selection_v4.py', 'test_native_authority_v4.py',
    'test_native_environment_v4.py', 'native_execution_v3.py', 'native_environment_v3.py',
    'native_admission_v2.py', 'native_execution_v2.py', 'decisive_native_verify.py',
    'native_runtime_v3.py', 'audit_index_v4.py',
    'archaeology/native-authority-v4/ACCEPTANCE_PROTOCOL.json',
    'archaeology/native-environment-v3/ENVIRONMENT_CATALOG.json',
    'archaeology/native-environment-v3/PACKAGE_METADATA.json',
    'archaeology/native-environment-v3/bootstrap/prepare_runtimes.py',
    'archaeology/native-environment-v3/bootstrap/stdlib_cache.py',
    'archaeology/native-environment-v3/bootstrap/metadata_receipt.py',
    'archaeology/native-environment-v3/bootstrap/METADATA_RECEIPT.json',
    'archaeology/native-environment-v3/bootstrap/official-legacy-installer.json',
    'archaeology/native-environment-v3/bootstrap/legacy-pins.txt')) + (
        '.github/workflows/udm-native-authority-v4.yml',)


def inputs():
    if sha256((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_bytes()) != ACCEPTANCE_SHA256:
        raise ValueError('frozen acceptance protocol changed')
    if sha256((HERE/'test_native_authority_v4.py').read_bytes()) != TEST_SHA256:
        raise ValueError('frozen acceptance tests changed')
    return json.loads(CATALOG.read_text())


def _write_freeze(repo, out, runtime_paths):
    started = time.monotonic(); catalog = inputs()
    head = source_authority._git(repo, 'rev-parse', 'HEAD').decode().strip()
    paths=source_authority._git(repo,'ls-tree','-r','--name-only',head).decode().splitlines()
    frozen = source_authority.freeze_source(repo, BASE, paths)
    profiles = {p['id']: p for p in environment.selection._catalog(catalog)}
    if set(runtime_paths) != set(profiles):
        raise ValueError('complete externally supplied runtime inventory required')
    runtimes = {}
    for name in sorted(profiles):
        runtimes[name] = environment.freeze_runtime(runtime_paths[name])
        environment.validate_runtime(profiles[name], runtimes[name])
    frozen.update(schema=FREEZE_SCHEMA, catalog_sha256=fingerprint(catalog), runtimes=runtimes,
                  mode='ADMISSION_ONLY_EXPOSED_DIAGNOSTICS',
                  acceptance_sha256=ACCEPTANCE_SHA256, freeze_wall_seconds=time.monotonic()-started)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(canonical(frozen)+'\n'); return frozen


def check_freeze(repo, path):
    catalog = inputs(); frozen = json.loads(Path(path).read_text())
    head = source_authority._git(repo, 'rev-parse', 'HEAD').decode().strip()
    if (frozen.get('schema') != FREEZE_SCHEMA or frozen.get('source_commit') != head
            or frozen.get('baseline_commit') != BASE
            or frozen.get('catalog_sha256') != fingerprint(catalog)
            or frozen.get('acceptance_sha256') != ACCEPTANCE_SHA256
            or set(frozen.get('files', {})) != set(source_authority._git(
                repo,'ls-tree','-r','--name-only',head).decode().splitlines())):
        raise ValueError('qualification source/authority differs from freeze')
    source_authority._preserved_baseline(repo, BASE, head)
    for name, digest in frozen['files'].items():
        if sha256((Path(repo)/name).read_bytes()) != digest:
            raise ValueError('frozen qualification file changed: '+name)
    profiles = {p['id']: p for p in catalog['profiles']}
    if set(frozen['runtimes']) != set(profiles): raise ValueError('runtime inventory differs')
    for name, runtime in frozen['runtimes'].items(): environment.validate_runtime(profiles[name], runtime)
    return frozen


def exposed_diagnostics(out):
    """Re-infer from exact archived source bytes; never execute an old task."""
    raw = HERE/'archaeology/native-environment-v3/SEALED_SCREENING_EVIDENCE.tar.gz'
    if sha256(raw.read_bytes()) != '70c705018ffcc782c4dadd52b3b2f403e50b3ad93a4c18b2dbf530e703f3cfec':
        raise ValueError('original diagnostic archive changed')
    analysis = json.loads((RECORDS/'DIAGNOSTIC_ANALYSIS.json').read_text()); catalog=inputs(); rows=[]
    with tarfile.open(raw, 'r:gz') as packet:
        for case in analysis['cases']:
            name='screening/'+case['case_id']+'/source-environment/metadata-source.tar.gz'
            archive=packet.extractfile(name).read()
            expected=next(a for a in case['archives'] if a['path'].endswith('/metadata-source.tar.gz'))
            if sha256(archive)!=expected['sha256']: raise ValueError('original case archive differs')
            files={}
            with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as source:
                for member in source:
                    path=PurePosixPath(member.name)
                    if (not member.isfile() or path.is_absolute() or '..' in path.parts
                            or str(path)!=member.name or member.name in files):
                        raise ValueError('unsupported original source archive member')
                    files[member.name]=source.extractfile(member).read()
            chosen=environment.selection.select_profile(files,catalog)
            environment.selection.validate_selection(files,catalog,chosen)
            if chosen['constraints']['source_sha256'] != case['original_selector_source_sha256']:
                raise ValueError('all-byte source inventory changed')
            rows.append({'repository':case['repository'],'source_commits':case['source_commits'],
                'original':case['original'],'selection':chosen,'native_calls':0,'collection_calls':0,
                'status':'EXPOSED_DIAGNOSTIC_ONLY_NOT_NATIVE_ADMISSION'})
    (out/'EXPOSED_DIAGNOSTICS.json').write_text(canonical(rows)+'\n'); return rows


class RecordedResult(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test); self.ids.append(test.id())


def _qualify(repo, freeze, out):
    started=time.monotonic(); frozen=check_freeze(repo,freeze)
    out=Path(out).absolute();out.mkdir(parents=True,exist_ok=False)
    before=snapshot_indexes(repo);attempts=execution.attempt_snapshot()
    result={'schema':'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V4','status':'UNKNOWN_ADMISSION',
        'source_commit':frozen['source_commit'],'freeze':frozen,'mode':'ADMISSION_ONLY',
        'verdicts':{'G0_G1':'PRESERVED_EXACT_PRIOR_SOURCE_AUTHORITY',**{f'G{i}':'UNKNOWN' for i in range(2,7)}},
        'first_task_gate':{'status':'UNKNOWN'},'acquisitions':0,'candidates':0,
        'cost_boundary':'Native/collection attempts and observed wall only; full lifecycle/model/tool/engineering costs UNKNOWN.'}
    try:
        from . import test_native_authority_v4 as tests
        acceptance=json.loads((RECORDS/'ACCEPTANCE_PROTOCOL.json').read_text())
        expected={r['id'] for r in acceptance['tests']}
        os.environ['UDM_V4_NATIVE_EVIDENCE_ROOT']=str(out/'native-evidence')
        modern=max(frozen['runtimes'].values(),key=lambda r:r['identity']['version_info'][:3])
        os.environ['UDM_NATIVE_V3_INTERPRETER']=modern['interpreter']
        suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
        with (out/'contracts.log').open('w') as stream:
            runner=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResult)
            RecordedResult.ids=[]
            verdict=runner.run(suite)
        actual=set(verdict.ids)
        result['contracts']={'run':verdict.testsRun,'ids':sorted(actual),'failures':len(verdict.failures),
            'errors':len(verdict.errors),'skipped':len(verdict.skipped),'successful':verdict.wasSuccessful()}
        positive=out/'native-evidence'/(__package__+'.test_native_authority_v4.MalformedPythonNativeAuthorityV4.test_unimported_malformed_fixture_allows_real_native_pass')/'checked-independent-receipt.json'
        checked=json.loads(positive.read_text()) if positive.is_file() else {}
        result['positive_independent_native']={key:checked.get(key) for key in ('status','junit','costs','independent_reexecution')}
        result['exposed_diagnostics']=exposed_diagnostics(out)
        check_freeze(repo,freeze)
        after=snapshot_indexes(repo)
        result['index_audit']={'before':before,'after':after,'changes':compare_indexes(before,after)}
        if (verdict.wasSuccessful() and actual==expected and len(actual)==29 and not verdict.skipped
                and checked.get('status')=='PASS_NATIVE'
                and checked.get('independent_reexecution',{}).get('costs',{}).get('native_calls')==1
                and not result['index_audit']['changes']):
            result['first_task_gate']={'status':'PASS','boundary':'Frozen metadata/native adversarial controls only'}
            result['status']='ADMISSION_ONLY_QUALIFIED'
        return result
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,subprocess.SubprocessError) as error:
        result.update(status='UNKNOWN_ADMISSION',error=type(error).__name__+': '+str(error),
                      first_task_gate={'status':'UNKNOWN'})
        return result
    finally:
        result['total_wall_seconds']=time.monotonic()-started
        after=execution.attempt_snapshot()
        result['attempt_costs']={k:after[k]-attempts[k] for k in after}
        (out/'RESULT.json').write_text(canonical(result)+'\n')


def write_freeze(repo,out,runtime_paths):
    """Measure index bytes before the first Git read, including refusals."""
    before=snapshot_indexes(repo);os.environ['GIT_OPTIONAL_LOCKS']='0'
    path=Path(out)
    if path.exists():raise ValueError('refusing to replace existing freeze')
    try:
        value=_write_freeze(repo,out,runtime_paths)
        return value
    finally:
        after=snapshot_indexes(repo)
        audit={'before':before,'after':after,'changes':compare_indexes(before,after)}
        sidecar=path.with_name(path.name+'.INDEX_AUDIT.json')
        if sidecar.exists():raise ValueError('refusing to replace existing index audit')
        sidecar.parent.mkdir(parents=True,exist_ok=True)
        sidecar.write_text(canonical(audit)+'\n')
        if audit['changes']:raise ValueError('Git index changed during source freeze; evidence retained')


def qualify(repo,freeze,out):
    """Audit the whole interval, before check_freeze or any other Git read."""
    before=snapshot_indexes(repo);os.environ['GIT_OPTIONAL_LOCKS']='0'
    out=Path(out)
    if out.exists():raise ValueError('refusing to replace existing qualification')
    try:
        result=_qualify(repo,freeze,out)
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,subprocess.SubprocessError) as error:
        result={'schema':'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V4','status':'UNKNOWN_ADMISSION',
            'first_task_gate':{'status':'UNKNOWN'},'error':type(error).__name__+': '+str(error),
            'verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)}}
    after=snapshot_indexes(repo)
    result['index_audit']={'before':before,'after':after,'changes':compare_indexes(before,after)}
    if result['index_audit']['changes']:
        result.update(status='UNKNOWN_ADMISSION',first_task_gate={'status':'UNKNOWN'})
    out.mkdir(parents=True,exist_ok=True)
    (out/'RESULT.json').write_text(canonical(result)+'\n')
    return result


def main():
    os.environ['GIT_OPTIONAL_LOCKS']='0'
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    parser=argparse.ArgumentParser();parser.add_argument('--repo',required=True)
    parser.add_argument('--out',required=True);parser.add_argument('--runtimes')
    parser.add_argument('--freeze');parser.add_argument('--write-freeze',action='store_true')
    args=parser.parse_args()
    if args.write_freeze:
        result=write_freeze(args.repo,args.out,json.loads(Path(args.runtimes).read_text()))
    else:
        result=qualify(args.repo,args.freeze,args.out)
    print(canonical({'status':result.get('status',result.get('schema')),'verdicts':result.get('verdicts',{})}))
    if not args.write_freeze and result['status']!='ADMISSION_ONLY_QUALIFIED':raise SystemExit(1)


if __name__=='__main__':main()
