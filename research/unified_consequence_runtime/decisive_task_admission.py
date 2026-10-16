"""Frozen generic source admission: base production plus independent author tests.

Only the base Git commit and head-revision test files are transported. No head
production object, reference patch, target-specific setup repair or native test
execution occurs here. This is contract preparation, never acquisition warrant.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote

from .generic_native_verify import SCHEMA, HORIZON_SECONDS, _path, _snapshot, canonical, environment_identity, fingerprint, sha256
from .qualify_recursive_frontier import _command


def is_test(name):
    try: path=_path(name)
    except ValueError:return False
    return path.suffix=='.py' and (any(part in {'test','tests','testing'} for part in path.parts)
        or path.name.startswith('test_') or path.name.endswith('_test.py') or path.name=='conftest.py')


def overlay_author_tests(base_files, author_tests):
    if not isinstance(author_tests,dict) or not author_tests:
        raise ValueError('nonempty author test bytes required')
    if any(not is_test(name) or not isinstance(raw,bytes) for name,raw in author_tests.items()):
        raise ValueError('overlay may contain canonical Python test paths and bytes only')
    return {**base_files,**author_tests}


def _validate_spec(spec):
    repo=spec.get('repo',spec.get('repository',''))
    base=spec.get('base_commit','');head=spec.get('head_commit','')
    if not isinstance(repo,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        raise ValueError('exact repository identity required')
    if any(not isinstance(value,str) or not re.fullmatch('[0-9a-f]{40}',value) for value in (base,head)):
        raise ValueError('exact base and head commits required')
    rows=spec.get('files',[])
    if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
        raise ValueError('frozen changed-file metadata required')
    for row in rows:
        _path(row.get('filename'))
        if row.get('status') not in {'modified','added'}:raise ValueError('renamed or deleted metadata unsupported')
    paths=sorted(row['filename'] for row in rows if is_test(row['filename']))
    if not paths or len(paths)!=len(set(paths)):raise ValueError('unique changed author tests required')
    return repo,base,head,paths


def _commit_overlay(repo,base,author_tests):
    _,base_files,_=_snapshot(repo,base)
    expected=overlay_author_tests(base_files,author_tests)
    for name,raw in author_tests.items():
        destination=Path(repo)/name
        if destination.is_symlink():raise ValueError('redirected test destination')
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    subprocess.check_call(['git','-C',str(repo),'-c','core.autocrlf=false','add','--',*sorted(author_tests)],stdout=subprocess.DEVNULL)
    tree=subprocess.check_output(['git','-C',str(repo),'write-tree']).decode().strip()
    env={**os.environ,'GIT_AUTHOR_NAME':'UDM Frozen Contract','GIT_AUTHOR_EMAIL':'udm@example.invalid',
         'GIT_COMMITTER_NAME':'UDM Frozen Contract','GIT_COMMITTER_EMAIL':'udm@example.invalid',
         'GIT_AUTHOR_DATE':'2000-01-01T00:00:00+0000','GIT_COMMITTER_DATE':'2000-01-01T00:00:00+0000'}
    commit=subprocess.check_output(['git','-C',str(repo),'commit-tree',tree,'-p',base,
        '-m','Frozen independent author-test overlay'],env=env).decode().strip()
    subprocess.check_call(['git','-C',str(repo),'checkout','-q','--detach',commit])
    if _snapshot(repo,commit)[1]!=expected:raise ValueError('overlay changed original production bytes')
    return commit


def prepare_task(spec,root,protocol_binding,packages):
    """Prepare a frozen native contract; setup failures remain UNKNOWN, not FAIL."""
    started=time.monotonic();root=Path(root).absolute();costs=[];boundaries={};authority=None
    if root.resolve()!=root or root.exists():raise ValueError('new canonical task directory required')
    if not isinstance(protocol_binding,str) or not re.fullmatch('[0-9a-f]{64}',protocol_binding):
        raise ValueError('exact frozen protocol binding required')
    if not isinstance(packages,(tuple,list)) or not packages or any(
            not isinstance(pin,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+',pin) for pin in packages):
        raise ValueError('predeclared exact package pins required')
    repository,base,head,test_paths=_validate_spec(spec)
    root.mkdir(parents=True);repo=root/'source';venv=root/'venv'
    def command(argv,phase):
        result=_command(argv,root/(phase+'.log'));costs.append({'phase':phase,'argv':[str(x) for x in argv],**result})
        if result['status']!='PASS':raise RuntimeError('UNKNOWN_SETUP:'+phase)
        return root/(phase+'.log')
    def save(status,reason=None,contract=None):
        value={'status':status,'contract':contract,'costs':costs,'source_boundaries':boundaries,
               'native_suite_authority':authority,'total_wall_seconds':time.monotonic()-started}
        if reason:value['reason']=reason
        (root/'admission.json').write_text(canonical(value)+'\n');return value
    try:
        command(['git','init','-q',repo],'git-init')
        command(['git','-C',repo,'fetch','--depth=1','https://github.com/'+repository+'.git',base],'base-fetch')
        command(['git','-C',repo,'checkout','-q','--detach','FETCH_HEAD'],'base-checkout')
        base_identity,base_files,base_manifest=_snapshot(repo,base)
        archive=subprocess.check_output(['git','--no-replace-objects','-C',str(repo),'archive','--format=tar.gz',base])
        (root/'base-source.tar.gz').write_bytes(archive)
        boundaries.update(repository=repository,base_commit=base,author_test_head_commit=head,
            base_identity=base_identity,base_manifest=base_manifest,
            base_source_archive={'path':str(root/'base-source.tar.gz'),'sha256':sha256(archive),'bytes':len(archive)},
            head_production_fetched=False,author_tests=[],production_preserved=False)
        author_tests={}
        for index,name in enumerate(test_paths):
            endpoint=f'repos/{repository}/contents/{quote(name,safe="/")}?ref={head}'
            response_path=command(['gh','api',endpoint],'author-test-'+str(index))
            response=json.loads(response_path.read_text())
            if response.get('path')!=name or response.get('type')!='file' or response.get('encoding')!='base64':
                raise ValueError('UNKNOWN_INTERFACE: author test response is not an exact file')
            raw=base64.b64decode(response['content'],validate=False)
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if blob!=response.get('sha') or len(raw)!=response.get('size'):raise ValueError('author test transport digest mismatch')
            author_tests[name]=raw
            boundaries['author_tests'].append({'path':name,'sha256':sha256(raw),'git_blob':blob,'bytes':len(raw),
                'endpoint':endpoint,'transport_json':str(response_path),'transport_sha256':sha256(response_path.read_bytes())})
        commit=_commit_overlay(repo,base,author_tests)
        identity,augmented_files,manifest=_snapshot(repo,commit)
        if augmented_files!=overlay_author_tests(base_files,author_tests):raise ValueError('source overlay mismatch')
        boundaries.update(augmented_commit=commit,augmented_identity=identity,augmented_manifest=manifest,production_preserved=True)
        (root/'source-boundaries.json').write_text(canonical(boundaries)+'\n')
        archive=subprocess.check_output(['git','--no-replace-objects','-C',str(repo),'archive','--format=tar.gz',commit])
        (root/'contract-source.tar.gz').write_bytes(archive)
        boundaries['contract_source_archive']={'path':str(root/'contract-source.tar.gz'),'sha256':sha256(archive),'bytes':len(archive)}
        (root/'source-boundaries.json').write_text(canonical(boundaries)+'\n')
        from .generic_native_verify import derive_native_suite_authority
        authority_started=time.monotonic()
        try:
            authority=derive_native_suite_authority(repo,base,commit,protocol_binding,repository=repository)
        except ValueError as error:
            costs.append({'phase':'native-suite-authority','seconds':time.monotonic()-authority_started,'status':'UNKNOWN_CONTRACT'})
            return save('UNKNOWN_CONTRACT',reason=str(error))
        costs.append({'phase':'native-suite-authority','seconds':time.monotonic()-authority_started,'status':'PASS'})
        (root/'native-suite-authority.json').write_text(canonical(authority)+'\n')
        command([sys.executable,'-m','venv',venv],'venv')
        command([venv/'bin/python','-m','pip','install','--disable-pip-version-check','--no-input',*packages],'fixed-packages')
        command([venv/'bin/python','-m','pip','install','--disable-pip-version-check','--no-input',str(repo)+'[test,tests]'],'project')
        command([venv/'bin/python','-m','pip','freeze','--all'],'pip-freeze')
        environment_started=time.monotonic();environment=environment_identity(venv/'bin/python')
        costs.append({'phase':'environment-identity','seconds':time.monotonic()-environment_started,'status':'PASS'})
        (root/'environment.json').write_text(canonical(environment)+'\n')
        contract={'schema':SCHEMA,'repository':repository,'repo_path':str(repo),'commit':commit,**identity,
            'interpreter':str(venv/'bin/python'),'environment_sha256':fingerprint(environment),
            'protocol_binding':protocol_binding,'horizon_seconds':HORIZON_SECONDS}
        (root/'contract.json').write_text(canonical(contract)+'\n')
        return save('PREPARED',contract=contract)
    except (RuntimeError,ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
        if (venv/'bin/python').is_file():
            result=_command([venv/'bin/python','-m','pip','freeze','--all'],root/'pip-freeze-after-failure.log')
            costs.append({'phase':'pip-freeze-after-failure',**result})
        return save('UNKNOWN_SETUP',reason=str(error))
