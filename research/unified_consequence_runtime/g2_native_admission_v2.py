#!/usr/bin/env python3
"""V16 source-owned native admission calibration. Never a scientific G2 warrant.

Expected pin is an external, predeclared test authority. All original code is
trusted within this bounded experiment. This does not sandbox hostile Python.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

SCHEMA = 'UDM_NATIVE_ADMISSION_V16'
SHA = re.compile(r'[0-9a-f]{40}\Z')
RUNNER = r'''
import json, pathlib, sys, pytest
class Monitor:
    def __init__(self):
        self.collected=[]; self.calls=[]; self.deselected=[]; self.collection_errors=[]
    def pytest_collection_finish(self, session):
        self.collected=[x.nodeid for x in session.items]
    def pytest_deselected(self, items):
        self.deselected.extend(x.nodeid for x in items)
    def pytest_collectreport(self, report):
        if report.failed:self.collection_errors.append(str(report.nodeid))
    def pytest_runtest_logreport(self, report):
        if report.when=='call':
            self.calls.append({'nodeid':report.nodeid,'outcome':report.outcome,
                               'xfail':bool(getattr(report,'wasxfail',False))})
m=Monitor()
rc=int(pytest.main(['-q','-p','no:cacheprovider','--junitxml='+sys.argv[2],*json.loads(sys.argv[3])],plugins=[m]))
pathlib.Path(sys.argv[1]).write_text(json.dumps({'returncode':rc,'collected':m.collected,
 'calls':m.calls,'deselected':m.deselected,'collection_errors':m.collection_errors},sort_keys=True))
sys.exit(rc)
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), '--no-replace-objects', *args],
                          check=True, capture_output=True).stdout


def source_inventory(root, commit):
    if not isinstance(commit, str) or not SHA.fullmatch(commit):
        raise ValueError('UNKNOWN_SOURCE_PIN')
    if git(root, 'rev-parse', 'HEAD').decode().strip() != commit:
        raise ValueError('UNKNOWN_SOURCE_COMMIT')
    if git(root, 'status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError('UNKNOWN_TRACKED_SOURCE_DIRTY')
    extras=(git(root,'ls-files','-z','--others','--exclude-standard').split(b'\0')
            +git(root,'ls-files','-z','--others','--ignored','--exclude-standard').split(b'\0'))
    if any(name.startswith((b'tests/',b'src/')) or name.endswith((b'.py',b'.pyc',b'.so',b'.pyd'))
           for name in extras if name):
        raise ValueError('UNKNOWN_UNTRACKED_EXECUTABLE_SOURCE')
    entries=[]
    for item in filter(None, git(root,'ls-tree','-rz','--full-tree',commit).split(b'\0')):
        meta, raw_name=item.split(b'\t',1)
        mode, kind, oid=meta.decode('ascii').split()
        name=raw_name.decode('utf-8','strict')
        path=Path(name)
        if (path.is_absolute() or '..' in path.parts or '\\' in name or '\x00' in name
                or name!=path.as_posix() or mode not in ('100644','100755') or kind!='blob'):
            raise ValueError('UNKNOWN_NONREGULAR_OR_UNSAFE_SOURCE')
        actual=root/path
        if (not stat.S_ISREG(actual.lstat().st_mode) or actual.is_symlink()
                or digest(actual.read_bytes())!=digest(git(root,'cat-file','blob',oid))):
            raise ValueError('UNKNOWN_TRACKED_SOURCE_BYTES')
        entries.append({'path':name,'mode':mode,'oid':oid,'sha256':digest(actual.read_bytes())})
    if not entries:
        raise ValueError('UNKNOWN_EMPTY_SOURCE')
    return {'git_tree':git(root,'rev-parse',commit+'^{tree}').decode().strip(),
            'files':len(entries),'manifest_sha256':digest(json.dumps(entries,sort_keys=True).encode()),
            'entries':entries}


def authorized_assertion(root, prefix):
    """Original asserted test declaration, not a proof that every branch asserted."""
    if not isinstance(prefix,str) or '::' not in prefix or '[' in prefix:
        return False
    path, *names=prefix.split('::')
    if (not path.startswith('tests/') or not path.endswith('.py')
            or '..' in Path(path).parts or not all(n.isidentifier() for n in names)):
        return False
    try:
        tree=ast.parse((root/path).read_bytes(),filename=path)
    except (OSError,SyntaxError,UnicodeError,ValueError):
        return False
    body=tree.body
    for name in names:
        nodes=[n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))
               and n.name==name]
        if len(nodes)!=1:return False
        body=nodes[0].body
    # A nested/dormant assertion cannot establish execution merely because pytest called this test.
    return any(isinstance(stmt,ast.Assert) for stmt in body)


def matches(node,prefix):
    return node==prefix or node.startswith(prefix+'[')


def execute(source,out):
    started=time.monotonic()
    summary={'schema':SCHEMA,'status':'UNKNOWN_ADMISSION','G2':'UNKNOWN','G3':'UNKNOWN',
             'G4':'UNKNOWN','scope':'CALIBRATION_ONLY','native_calls':0}
    try:
        source=Path(source).absolute();out=Path(out).absolute()
        if (source.resolve()!=source or not source.is_dir() or source.is_symlink()
                or out.resolve()!=out or out==source or out.is_relative_to(source)):
            raise ValueError('UNKNOWN_PATH_AUTHORITY')
        if not out.is_dir() or (out/'admission.json').exists():
            raise ValueError('UNKNOWN_EVIDENCE_OUTPUT')
        pin_raw=(out/'pin.json').read_bytes()
        pin=json.loads(pin_raw)
        summary['pin_sha256']=digest(pin_raw)
        if set(pin)!={'repository','sha','test_paths','required_test_prefixes','requirements_blob','scope'}:
            raise ValueError('UNKNOWN_PIN_SCHEMA')
        if (pin['scope']!='CALIBRATION_ONLY' or pin['test_paths']!=['tests']
                or not isinstance(pin['required_test_prefixes'],list)
                or not pin['required_test_prefixes']
                or len(set(pin['required_test_prefixes']))!=len(pin['required_test_prefixes'])):
            raise ValueError('UNKNOWN_TEST_AUTHORITY')
        if git(source,'rev-parse','HEAD').decode().strip()!=pin['sha']:
            raise ValueError('UNKNOWN_SOURCE_COMMIT')
        if git(source,'rev-parse','HEAD:requirements/tests.txt').decode().strip()!=pin['requirements_blob']:
            raise ValueError('UNKNOWN_TEST_DEPENDENCY_LOCK')
        summary['source_identity']=source_inventory(source,pin['sha'])
        summary['repository']=pin['repository'];summary['source_sha']=pin['sha']
        if not all(authorized_assertion(source,p) for p in pin['required_test_prefixes']):
            raise ValueError('UNKNOWN_PROTECTED_ASSERTION_SOURCE')
        for output_name in ('native.xml','events.json','native.stdout','native.stderr'):
            if (out/output_name).exists():
                raise ValueError('UNKNOWN_EXISTING_NATIVE_EVIDENCE')
        cmd=[sys.executable,'-I','-B','-c',RUNNER,str(out/'events.json'),
             str(out/'native.xml'),json.dumps(pin['test_paths'])]
        env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1')
        before=time.monotonic();summary['native_calls']=1
        try:
            attempt=subprocess.run(cmd,cwd=source,env=env,capture_output=True,timeout=180)
        except subprocess.TimeoutExpired as exc:
            (out/'native.stdout').write_bytes(exc.stdout or b'')
            (out/'native.stderr').write_bytes(exc.stderr or b'')
            raise ValueError('UNKNOWN_NATIVE_TIMEOUT') from exc
        summary['native_seconds']=time.monotonic()-before
        summary['returncode']=attempt.returncode
        (out/'native.stdout').write_bytes(attempt.stdout)
        (out/'native.stderr').write_bytes(attempt.stderr)
        if (out/'pin.json').read_bytes()!=pin_raw:
            raise ValueError('UNKNOWN_EXTERNAL_PIN_MUTATION')
        if source_inventory(source,pin['sha'])!=summary['source_identity']:
            raise ValueError('UNKNOWN_SOURCE_MUTATION')
        events=json.loads((out/'events.json').read_text())
        cases=list(ET.parse(out/'native.xml').getroot().iter('testcase'))
        counts={'cases':len(cases), 'failed':sum(bool(list(c.iter('failure'))) for c in cases),
                'errors':sum(bool(list(c.iter('error'))) for c in cases),
                'skipped':sum(bool(list(c.iter('skipped'))) for c in cases)}
        summary['counts']=counts
        summary['observed_call_nodes']=events['calls']
        summary['deselected']=events['deselected'];summary['collection_errors']=events['collection_errors']
        if (not events['calls'] or counts['cases']!=len(events['calls'])
                or len(events['collected'])!=len(events['calls'])
                or any(x['xfail'] or x['outcome'] not in ('passed','failed') for x in events['calls'])
                or events['deselected'] or events['collection_errors'] or counts['errors'] or counts['skipped']):
            raise ValueError('UNKNOWN_COLLECTION_OR_INCOMPLETE_ASSERTION')
        required=pin['required_test_prefixes']
        if any(not any(matches(c['nodeid'],p) for c in events['calls']) for p in required):
            raise ValueError('UNKNOWN_PROTECTED_TEST_NOT_EXECUTED')
        failed=[c['nodeid'] for c in events['calls'] if c['outcome']=='failed']
        if len(failed)!=counts['failed']:
            raise ValueError('UNKNOWN_JUNIT_CALL_MISMATCH')
        if attempt.returncode==0 and not failed:
            summary['status']='ADMITTED_NATIVE_PASS_CALIBRATION'
        elif (attempt.returncode==1 and failed
              and all(any(matches(node,p) for p in required) for node in failed)):
            summary['status']='ADMITTED_NATIVE_FAIL_PROTECTED_CALIBRATION'
        else:
            raise ValueError('UNKNOWN_UNPROTECTED_FAILURE_OR_NATIVE_EXIT')
    except (OSError,ValueError,KeyError,TypeError,IndexError,ET.ParseError,
            json.JSONDecodeError,subprocess.CalledProcessError) as exc:
        summary['status']='UNKNOWN_ADMISSION'
        summary['reason']=str(exc)
    finally:
        summary['wall_seconds']=time.monotonic()-started
        if isinstance(out,Path) and out.is_dir():
            receipt=out/'admission.json'
            if not receipt.exists():
                receipt.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    return summary


if __name__=='__main__':
    report=execute(sys.argv[1],sys.argv[2])
    print(json.dumps({'status':report['status'],'reason':report.get('reason'),
                      'G2':'UNKNOWN','native_calls':report['native_calls']}))
    raise SystemExit(0 if report['status'].startswith('ADMITTED_NATIVE_') else 2)
