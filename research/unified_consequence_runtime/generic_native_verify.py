"""Fixed full-pytest native verifier; research isolation is not a sandbox proof.

The contract is externally supplied authority, never candidate supplied. PASS
means only that a nonempty original native suite passed in this exact scope.
Standard python_files/testpaths declarations are immutable verifier inputs;
nonempty addopts is unsupported and refused as UNKNOWN_INTERFACE. Arbitrary
collection hooks and hostile in-process behavior require separate authority.
"""
from __future__ import annotations
import argparse
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
code=pytest.main(['-q','-p','no:cacheprovider','--junitxml='+sys.argv[2]])
manifest=[]
for module in tuple(sys.modules.values()):
    location=getattr(module,'__file__',None)
    if location:
        path=pathlib.Path(location).resolve()
        if path.is_relative_to(world) and path.is_file():
            manifest.append({'path':str(path.relative_to(world)),
              'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pathlib.Path(sys.argv[3]).write_text(json.dumps({'project':sorted(manifest,key=lambda x:x['path']),
 'pytest_import':verified_pytest},sort_keys=True))
raise SystemExit(code)
'''


def _test_patterns(files):
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
            if options.get('addopts'):
                raise ValueError('nonempty addopts can change independent collection authority')
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


def _candidate(candidate, files):
    if not isinstance(candidate, dict) or set(candidate) != {'replacements'} or not isinstance(candidate['replacements'], list):
        raise ValueError('invalid candidate schema')
    seen = set(); patterns=_test_patterns(files)
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


def verify(contract, candidate, output_dir):
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
    _candidate(candidate, files)
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
            mutations=[name for name,raw in expected.items() if not (world/name).is_file()
                       or (world/name).resolve() != world/name or (world/name).read_bytes() != raw]
            mutations += [row['path'] for row in receipt['import_manifest']
                          if row['path'] not in expected or row['sha256'] != sha256(expected[row['path']])]
            if mutations:
                receipt.update(status='UNKNOWN_SOURCE_MUTATION',source_mutations=sorted(set(mutations)))
            count=receipt['junit']
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
