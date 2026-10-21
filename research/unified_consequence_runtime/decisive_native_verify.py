"""Fixed full-pytest native verifier; research isolation is not a sandbox proof.

The contract is externally supplied authority, never candidate supplied. PASS
means only that a nonempty original native suite passed in this exact scope.
Standard python_files/testpaths declarations are immutable verifier inputs;
nonempty addopts is unsupported and refused as UNKNOWN_INTERFACE. Arbitrary
collection hooks and hostile in-process behavior require separate authority.
"""
from __future__ import annotations
import argparse
import ast
import configparser
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET

SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V1'
HORIZON_SECONDS = 7
PYTEST_VERSION = '8.3.5'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(value):
    return sha256(canonical(value).encode())


def _git(repo, *args):
    return subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE)


def _path(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('unsafe source path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != value:
        raise ValueError('unsafe source path')
    return path


def _snapshot(repo, commit):
    root = Path(repo).absolute()
    if root.resolve() != root or not root.is_dir():
        raise ValueError('repository path must be canonical, not a symlink')
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('exact commit required')
    try:
        if _git(root, 'rev-parse', commit+'^{commit}').decode().strip() != commit:
            raise ValueError('wrong source commit')
        tree = _git(root, 'rev-parse', commit+'^{tree}').decode().strip()
        rows = _git(root, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0')
        files, manifest = {}, []
        for row in filter(None, rows):
            meta, name = row.split(b'\t', 1)
            mode, kind, blob = meta.decode().split()
            name = name.decode('utf-8'); _path(name)
            if mode not in ('100644', '100755') or kind != 'blob':
                raise ValueError('only regular tracked files supported; no symlinks or submodules')
            raw = _git(root, 'cat-file', 'blob', blob)
            files[name] = raw
            manifest.append({'path':name, 'mode':mode, 'blob':blob, 'sha256':sha256(raw)})
        identity = {'git_tree':tree, 'tracked_tree_sha256':fingerprint(manifest), 'file_count':len(files)}
        return identity, files, manifest
    except subprocess.CalledProcessError as error:
        raise ValueError('wrong or unavailable immutable source commit') from error


def source_identity(repo, commit):
    return _snapshot(repo, commit)[0]


_ENVIRONMENT = r'''
import hashlib, importlib.metadata as md, json, pathlib, sys
def h(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
rows=[]
for dist in sorted(md.distributions(), key=lambda d:(d.metadata['Name'] or '').lower()):
    files=[]
    for entry in sorted(dist.files or [], key=str):
        path=pathlib.Path(dist.locate_file(entry))
        if path.is_file():
            files.append([str(entry),h(path)])
    rows.append([dist.metadata['Name'],dist.version,files])
import pytest
location=pathlib.Path(pytest.__file__).resolve()
if location != pathlib.Path(md.distribution('pytest').locate_file('pytest/__init__.py')).resolve():
    raise RuntimeError('pytest import is outside its independent distribution')
print(json.dumps({'executable':sys.executable,'executable_sha256':h(sys.executable),
 'version':sys.version,'prefix':sys.prefix,'base_prefix':sys.base_prefix,
 'pytest_version':md.version('pytest'),
 'pytest_import':{'path':str(location),'sha256':h(location)},
 'distributions_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
 'distribution_count':len(rows)},sort_keys=True))
'''


def _env(home):
    return {'PATH':os.environ.get('PATH','/usr/bin:/bin'), 'HOME':str(home),
            'LANG':'C.UTF-8', 'PYTHONHASHSEED':'0', 'PYTHONDONTWRITEBYTECODE':'1',
            'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1', 'GIT_NO_REPLACE_OBJECTS':'1'}


def environment_identity(interpreter):
    result = subprocess.run([str(interpreter), '-I', '-B', '-c', _ENVIRONMENT],
                            env=_env('/nonexistent'), capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError('native environment identity unavailable: '+result.stderr[-1000:])
    return json.loads(result.stdout)


_BOOTSTRAP = r'''
import hashlib,json,pathlib,sys
world=pathlib.Path(sys.argv[1]).resolve()
import pytest
location=pathlib.Path(pytest.__file__).resolve()
verified_pytest={'path':str(location),'sha256':hashlib.sha256(location.read_bytes()).hexdigest()}
if verified_pytest != json.loads(sys.argv[4]): raise RuntimeError('independent pytest source mismatch')
sys.path[:0]=[str(world/'src'),str(world)]
class NativeExecutionMonitor:
    def __init__(self): self.reports=[]; self.deselected=[]
    def pytest_runtest_logreport(self,report):
        if report.when=='call': self.reports.append({'nodeid':report.nodeid,'outcome':report.outcome})
    def pytest_deselected(self,items): self.deselected.extend(item.nodeid for item in items)
monitor=NativeExecutionMonitor()
code=pytest.main(['-q','-p','no:cacheprovider','--junitxml='+sys.argv[2]],plugins=[monitor])
manifest=[]
for module in tuple(sys.modules.values()):
    location=getattr(module,'__file__',None)
    if location:
        path=pathlib.Path(location).resolve()
        if path.is_relative_to(world) and path.is_file():
            manifest.append({'path':str(path.relative_to(world)),
              'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pathlib.Path(sys.argv[3]).write_text(json.dumps({'project':sorted(manifest,key=lambda x:x['path']),
 'pytest_import':verified_pytest,'executed_test_reports':monitor.reports,
 'deselected_test_nodes':sorted(monitor.deselected)},sort_keys=True))
raise SystemExit(code)
'''


NATIVE_CONFIG_FILES = ('pytest.ini','.pytest.ini','tox.ini','setup.cfg','pyproject.toml')
NATIVE_SUITE_SCHEMA = 'UDM_NATIVE_SUITE_AUTHORITY_V1'


def _declared_addopts(value):
    """Support immutable reporting/selection flags, never new test authority."""
    args=shlex.split(value) if isinstance(value,str) else value
    if not isinstance(args,list) or any(not isinstance(arg,str) for arg in args):
        raise ValueError('unsupported declared addopts')
    index=0
    while index<len(args):
        arg=args[index]
        if arg in ('-k','-m'):
            index+=2
            if index>len(args):raise ValueError('missing native selection expression')
            continue
        if (re.fullmatch(r'-(?:q+|v+|r[A-Za-z]+)',arg) or arg in ('--strict-config','--strict-markers',
                '--strict','--disable-warnings','--showlocals','-l','--full-trace','--no-header','--no-summary')
                or re.fullmatch(r'--(?:tb=(?:auto|long|short|line|native|no)|color=(?:yes|no|auto)|durations=[0-9]+|import-mode=(?:importlib|prepend|append))',arg)):
            index+=1;continue
        raise ValueError('unsupported addopts collection/authority option: '+arg)


def _test_patterns(files, *, allow_declared_addopts=False):
    patterns=['test_*.py','*_test.py']
    for name,section in (('pytest.ini','pytest'),('.pytest.ini','pytest'),
                         ('tox.ini','pytest'),('setup.cfg','tool:pytest'),('pyproject.toml',None)):
        if name not in files: continue
        try:
            if section is None:
                options=tomllib.loads(files[name].decode()).get('tool',{}).get('pytest',{}).get('ini_options',{})
            else:
                config=configparser.ConfigParser(interpolation=None);config.read_string(files[name].decode())
                options=dict(config.items(section)) if config.has_section(section) else {}
            if options.get('addopts') and not allow_declared_addopts:
                raise ValueError('nonempty addopts can change independent collection authority')
            if options.get('addopts') and allow_declared_addopts:
                _declared_addopts(options['addopts'])
            for key in ('python_files','testpaths'):
                value=options.get(key,[])
                values=shlex.split(value) if isinstance(value,str) else value
                if not isinstance(values,list) or any(not isinstance(x,str) or not x for x in values):
                    raise ValueError('invalid '+key)
                for value in values:
                    if key=='python_files': patterns.append(value)
                    else:
                        path=_path(value.rstrip('/')).as_posix()
                        patterns.extend(['*'] if path=='.' else [path,path+'/*'])
        except (ValueError,AttributeError,UnicodeError,configparser.Error) as error:
            raise ValueError('UNKNOWN_INTERFACE: unsupported native test configuration') from error
    return patterns


def _test_nodes(path, source):
    """Static prefixes; dynamic/uncollectable obligations remain UNKNOWN."""
    try:tree=ast.parse(source,filename=path)
    except (SyntaxError,UnicodeError) as error:raise ValueError('UNKNOWN_NATIVE_SUITE_AST') from error
    result=[]; declared=set()
    def visit(nodes,prefix):
        for node in nodes:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                result.append(prefix+'::'+node.name)
                declared.add(id(node))
            elif isinstance(node,ast.ClassDef):visit(node.body,prefix+'::'+node.name)
            elif not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if (isinstance(child,ast.Call) and isinstance(child.func,ast.Name)
                            and child.func.id in ('globals','locals','setattr','exec','eval')):
                        raise ValueError('UNKNOWN_SUITE_CONTRACT: dynamic test registration unsupported')
                    if isinstance(child,(ast.Assign,ast.AnnAssign,ast.NamedExpr)):
                        targets=child.targets if isinstance(child,ast.Assign) else [child.target]
                        if any(isinstance(target,ast.Name) and target.id.startswith('test_') for target in targets):
                            # Constant source data cannot register executable pytest tests.
                            # All names remain in the original AST/source identity.
                            if len(targets) != 1 or not isinstance(node,(ast.Assign,ast.AnnAssign)):
                                raise ValueError('UNKNOWN_SUITE_CONTRACT: dynamic test alias unsupported')
                            try:
                                ast.literal_eval(node.value)
                            except (ValueError,TypeError,MemoryError,RecursionError):
                                raise ValueError('UNKNOWN_SUITE_CONTRACT: dynamic test alias unsupported')
    visit(tree.body,path)
    if any(isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_')
            and id(node) not in declared for node in ast.walk(tree)):
        raise ValueError('UNKNOWN_SUITE_CONTRACT: conditional or nested test definition unsupported')
    return tree,result


def derive_native_suite_authority(repo, base_commit, augmented_commit, protocol_binding, *, repository):
    """Bind externally supplied native assertions from immutable Git AST deltas.

    Meaningful changes conservatively require all static test functions in the
    affected module, including class/parameter cases. This checks transport and
    actual execution, not semantic assertion strength or universal correctness.
    """
    if (not isinstance(repository,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository)
            or not isinstance(protocol_binding,str) or not re.fullmatch('[0-9a-f]{64}',protocol_binding)):
        raise ValueError('wrong native suite repository or protocol')
    _,old,_=_snapshot(repo,base_commit);_,files,_=_snapshot(repo,augmented_commit)
    patterns=_test_patterns(files,allow_declared_addopts=True)
    changed={};required=[]
    for name,raw in sorted(files.items()):
        if not name.endswith('.py') or not any(fnmatch.fnmatch(PurePosixPath(name).name,p)
                or fnmatch.fnmatch(name,p) for p in patterns):continue
        if old.get(name)==raw:continue
        tree,nodes=_test_nodes(name,raw)
        if name in old:
            previous,_=_test_nodes(name,old[name])
            if ast.dump(tree,include_attributes=False)==ast.dump(previous,include_attributes=False):continue
        if not nodes:raise ValueError('UNKNOWN_NATIVE_SUITE_DELTA: changed test module has no static test nodes')
        changed[name]=sha256(raw);required.extend(nodes)
    if not required:raise ValueError('UNKNOWN_NATIVE_SUITE_DELTA: no changed native test assertions')
    return {'schema':NATIVE_SUITE_SCHEMA,'derivation':'NATIVE_TEST_AST_DELTA_V1',
        'repository':repository,'baseline_commit':base_commit,'source_commit':augmented_commit,
        'protocol_binding':protocol_binding,'config_sha256':{name:sha256(files[name])
            for name in NATIVE_CONFIG_FILES if name in files},
        'test_source_sha256':changed,'required_test_nodes':sorted(set(required))}


def validate_native_suite_authority(contract, authority):
    if not isinstance(authority,dict) or authority.get('schema')!=NATIVE_SUITE_SCHEMA:
        raise ValueError('wrong native suite authority schema')
    expected=derive_native_suite_authority(contract['repo_path'],authority.get('baseline_commit'),
        contract['commit'],contract['protocol_binding'],repository=contract['repository'])
    if authority!=expected:raise ValueError('native suite authority source, config, assertions or protocol mismatch')
    return fingerprint(expected)


def required_assertions_satisfied(authority, executed, deselected, reports, counts, *, require_pass=True):
    """Only successful actual call reports discharge all protected prefixes."""
    if (not isinstance(executed,list) or not isinstance(deselected,list) or not isinstance(reports,list)
            or any(not isinstance(x,str) for x in executed+deselected)
            or any(not isinstance(row,dict) or set(row)!={'nodeid','outcome'} or
                not isinstance(row['nodeid'],str) or row['outcome'] not in ('passed','failed') for row in reports)
            or executed!=[row['nodeid'] for row in reports]
            or len(reports)!=counts.get('passed',0)+counts.get('failures',0)):return False
    if require_pass and (any(row['outcome']!='passed' for row in reports) or counts.get('errors')
            or counts.get('failures') or counts.get('skipped')):return False
    def match(node,prefix):return node==prefix or node.startswith(prefix+'[') or node.startswith(prefix+'::')
    if any(node.split('::',1)[0] in authority['test_source_sha256'] for node in deselected):return False
    return all(any(match(node,prefix) for node in executed) and not any(match(node,prefix) for node in deselected)
        for prefix in authority['required_test_nodes'])


def _candidate(candidate, files, *, allow_declared_addopts=False):
    if not isinstance(candidate, dict) or set(candidate) != {'replacements'} or not isinstance(candidate['replacements'], list):
        raise ValueError('invalid candidate schema')
    seen = set(); patterns=_test_patterns(files,allow_declared_addopts=allow_declared_addopts)
    for row in candidate['replacements']:
        if not isinstance(row, dict) or set(row) != {'path','original_sha256','replacement'}:
            raise ValueError('invalid replacement schema')
        path = _path(row['path']); name = path.as_posix()
        if name in seen:
            raise ValueError('duplicate candidate path')
        seen.add(name)
        if (name not in files or path.suffix != '.py' or path.name in ('conftest.py','setup.py','pytest.py')
                or any(fnmatch.fnmatchcase(path.name,p) or fnmatch.fnmatchcase(name,p) for p in patterns)
                or any(p.startswith('.') or p in ('test','tests','testing') or p.startswith('test_')
                       for p in path.parts)):
            raise ValueError('candidate must replace a tracked production Python file')
        if row['original_sha256'] != sha256(files[name]):
            raise ValueError('candidate original blob mismatch')
        if not isinstance(row['replacement'], str):
            raise ValueError('candidate source must be text')
        if row['replacement'].encode('utf-8') == files[name]:
            raise ValueError('unchanged candidate replacement is not development')
        compile(row['replacement'], name, 'exec')


def _junit(path):
    summary = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    if not path.is_file():
        return summary
    for case in ET.parse(path).getroot().iter('testcase'):
        summary['tests'] += 1
        status = next((key for key, tag in (('errors','error'),('failures','failure'),('skipped','skipped'))
                       if case.find(tag) is not None), 'passed')
        summary[status] += 1
    return summary


def verify(contract, candidate, output_dir, *, generated_wheel_evidence=None, native_suite_authority=None):
    start = time.monotonic()
    required = {'schema','repository','repo_path','commit','git_tree','tracked_tree_sha256',
                'file_count','interpreter','environment_sha256','protocol_binding','horizon_seconds'}
    if not isinstance(contract, dict) or set(contract) != required:
        raise ValueError('wrong native contract configuration')
    if contract['schema'] != SCHEMA or type(contract['horizon_seconds']) is not int or contract['horizon_seconds'] != 7:
        raise ValueError('wrong native verifier schema or horizon')
    for key in ('protocol_binding','environment_sha256','tracked_tree_sha256'):
        if not isinstance(contract[key],str) or not re.fullmatch('[0-9a-f]{64}',contract[key]):
            raise ValueError('wrong contract digest: '+key)
    source, files, manifest = _snapshot(contract['repo_path'], contract['commit'])
    if any(contract[key] != value for key, value in source.items()):
        raise ValueError('immutable source identity mismatch')
    suite_digest=validate_native_suite_authority(contract,native_suite_authority) if native_suite_authority is not None else None
    _candidate(candidate, files,allow_declared_addopts=suite_digest is not None)
    out = Path(output_dir).absolute()
    repository_path=Path(contract['repo_path']).absolute()
    if out.resolve() != out or out == repository_path or out.is_relative_to(repository_path):
        raise ValueError('output must be canonical and outside source')
    out.mkdir(parents=True, exist_ok=True)
    for name in ('receipt.json','tracked-source-manifest.json','stdout.log','stderr.log','native.xml'):
        path=out/name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError('redirected or invalid output file')
    receipt = {'schema':SCHEMA, 'repository':contract['repository'], 'commit':contract['commit'],
        'source':source, 'candidate_sha256':fingerprint(candidate), 'contract_sha256':fingerprint(contract),
        'protocol_binding':contract['protocol_binding'], 'runner_sha256':sha256(Path(__file__).read_bytes()),
        'authority':'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH_ONLY', 'external_enforcement':'UNKNOWN_NONBYPASSABILITY',
        'junit':dict(tests=0,passed=0,failures=0,errors=0,skipped=0), 'import_manifest':[],
        'costs':{'native_calls':0,'horizon_seconds':7,'native_seconds':0}}
    if suite_digest is not None:
        receipt.update(native_suite_authority_sha256=suite_digest,
            required_test_nodes=list(native_suite_authority['required_test_nodes']),
            executed_test_nodes=[],deselected_test_nodes=[],executed_test_reports=[])
    try:
        environment = environment_identity(contract['interpreter'])
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
        receipt.update(status='UNKNOWN_ENVIRONMENT', error=str(error))
    else:
        if fingerprint(environment) != contract['environment_sha256']:
            raise ValueError('native environment identity mismatch')
        if environment['pytest_version'] != PYTEST_VERSION:
            raise ValueError('native pytest version mismatch')
        receipt.update(environment=environment, environment_sha256=fingerprint(environment))
        generated_modules = {}
        if generated_wheel_evidence is not None:
            from .generated_wheel_evidence import authenticated_generated_modules, evidence_digest
            build_started = time.monotonic()
            try:
                generated_modules, built = authenticated_generated_modules(files, generated_wheel_evidence,
                    source_commit=contract['commit'], source_tree_sha256=source['tracked_tree_sha256'],
                    interpreter=contract['interpreter'], environment_sha256=contract['environment_sha256'],
                    output_dir=out/'build-verification', source_manifest=manifest,
                    allow_declared_addopts=suite_digest is not None)
            except (RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
                invalid = isinstance(error,ValueError)
                receipt.update(status='UNKNOWN_BUILD_AUTHENTICATION' if invalid else 'UNKNOWN_BUILD_MATERIALIZATION', error=str(error))
                attempt = out/'build-verification/build-attempt.json'
                receipt['costs'].update(build_calls=1 if attempt.is_file() else 0,
                    build_seconds=time.monotonic()-build_started,
                    total_seconds=time.monotonic()-start)
                (out/'receipt.json').write_text(canonical(receipt)+'\n')
                (out/'tracked-source-manifest.json').write_text(canonical(manifest)+'\n')
                if invalid:
                    raise  # Invalid evidence remains a fail-closed API error, with retained charged evidence.
                return receipt
            receipt.update(generated_wheel_evidence_sha256=evidence_digest(generated_wheel_evidence),
                generated_modules_sha256=fingerprint({k:sha256(v) for k,v in sorted(generated_modules.items())}),
                generated_module_count=len(generated_modules),
                generated_wheel_content_sha256=generated_wheel_evidence['wheel_content_sha256'],
                build_verification_sha256=sha256((out/'build-verification/build-receipt.json').read_bytes()))
            receipt['costs'].update(build_calls=1, build_seconds=time.monotonic()-build_started,
                build_artifact_bytes=built['costs']['wheel_bytes'])
        with tempfile.TemporaryDirectory(prefix='udm-native-') as folder:
            temporary = Path(folder); world=temporary/'world'; world.mkdir()
            expected=dict(files)
            for name, raw in files.items():
                path=world/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
                if name.endswith(('.pyc','.pyo')):
                    path.unlink()  # Frozen source never grants executable stale bytecode.
                    del expected[name]
            for row in manifest:
                if row['path'] in expected:
                    (world/row['path']).chmod(int(row['mode'],8) & 0o777)
            for name, raw in generated_modules.items():
                path=world/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
                expected[name]=raw
            for row in candidate['replacements']:
                (world/row['path']).write_text(row['replacement'], encoding='utf-8')
                expected[row['path']]=row['replacement'].encode('utf-8')
            bootstrap=temporary/'trusted_runner.py'; bootstrap.write_text(_BOOTSTRAP)
            junit=temporary/'native.xml'; imports=temporary/'imports.json'
            command=[contract['interpreter'],'-I','-B',str(bootstrap),str(world),str(junit),str(imports),canonical(environment['pytest_import'])]
            before=time.monotonic(); receipt['costs']['native_calls']=1
            with (temporary/'stdout').open('wb') as stdout, (temporary/'stderr').open('wb') as stderr:
                process=subprocess.Popen(command,cwd=world,env=_env(temporary),stdout=stdout,stderr=stderr,start_new_session=True)
                try:
                    process.wait(timeout=7)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL); process.wait()
                    receipt['status']='UNKNOWN_TIMEOUT'
            receipt['costs']['native_seconds']=time.monotonic()-before
            for name in ('stdout','stderr'):
                raw=(temporary/name).read_bytes()
                receipt[name+'_sha256']=sha256(raw); receipt['costs'][name+'_bytes']=len(raw)
                (out/(name+'.log')).write_bytes(raw)
            receipt['exit_code']=process.returncode
            if junit.exists():
                raw=junit.read_bytes(); (out/'native.xml').write_bytes(raw)
                receipt['junit_sha256']=sha256(raw)
                try: receipt['junit']=_junit(junit)
                except (ET.ParseError,ValueError): receipt['status']='UNKNOWN_NATIVE_ERROR'
            if imports.exists():
                imported=json.loads(imports.read_text())
                receipt['import_manifest']=imported['project'];receipt['pytest_import']=imported['pytest_import']
                if suite_digest is not None:
                    receipt['executed_test_reports']=imported['executed_test_reports']
                    receipt['executed_test_nodes']=[row['nodeid'] for row in imported['executed_test_reports']]
                    receipt['deselected_test_nodes']=imported['deselected_test_nodes']
            mutations=[name for name,raw in expected.items() if not (world/name).is_file()
                       or (world/name).resolve() != world/name or (world/name).read_bytes() != raw]
            mutations += [row['path'] for row in receipt['import_manifest']
                          if row['path'] not in expected or row['sha256'] != sha256(expected[row['path']])]
            if mutations:
                receipt.update(status='UNKNOWN_SOURCE_MUTATION',source_mutations=sorted(set(mutations)))
            count=receipt['junit']
            if suite_digest is not None and 'status' not in receipt and not required_assertions_satisfied(
                    native_suite_authority,receipt['executed_test_nodes'],receipt['deselected_test_nodes'],
                    receipt['executed_test_reports'],count,require_pass=False):
                receipt['status']='UNKNOWN_REQUIRED_ASSERTION'
            if 'status' not in receipt:
                receipt['status']=('UNKNOWN_NATIVE_ERROR' if count['errors'] or process.returncode not in (0,1,5) else
                    'UNKNOWN_NO_TEST_EXECUTION' if not count['passed']+count['failures'] else
                    'UNKNOWN_PARTIAL_SKIP' if count['skipped'] else
                    'FAIL_NATIVE' if process.returncode==1 and count['failures'] else
                    'PASS_NATIVE' if process.returncode==0 and not count['failures'] else 'UNKNOWN_NATIVE_ERROR')
    receipt['costs']['total_seconds']=time.monotonic()-start
    (out/'receipt.json').write_text(canonical(receipt)+'\n')
    (out/'tracked-source-manifest.json').write_text(canonical(manifest)+'\n')
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--contract',required=True); parser.add_argument('--candidate',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=verify(json.loads(Path(args.contract).read_text()),json.loads(Path(args.candidate).read_text()),args.out)
    print(canonical(result))


if __name__ == '__main__':
    main()
