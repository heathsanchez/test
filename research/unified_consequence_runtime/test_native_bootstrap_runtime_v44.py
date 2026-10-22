"""Preimplementation V44 metadata-instrument contracts; infrastructure only.

The disposable original backend is an acceptance fixture, never a prospective
scientific task. No metadata receipt is substituted for a native assertion.
"""
from __future__ import annotations

import copy
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from . import decisive_native_verify as original
from . import native_source_v42 as source


HERE = Path(__file__).resolve().parent
FIXTURE = HERE/'archaeology/native-bootstrap-v44/preimplementation/original_backend_fixture'
PYTHON = '/workspace/qualification/native-authority-v41-profile-preparation/modern-runtime-final/venv/bin/python'
PROTOCOL = original.sha256(b'V44 frozen metadata instrument acceptance; not prospective G2')
MODULES = ('native_bootstrap_runtime_v44', 'cross_frontier_v44', 'developmental_machine_v44')


def implementation(name):
    return importlib.import_module(__package__+'.'+name)


def git(repo, *args):
    return subprocess.check_output(['git','--no-replace-objects','-C',str(repo),*args],
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1'),
        text=True,stderr=subprocess.PIPE).strip()


def fixture_source(root):
    assert FIXTURE.is_dir(), 'the preimplementation frozen original backend fixture is required'
    shutil.copytree(FIXTURE,root)
    git(root,'init','-q')
    git(root,'add','.')
    git(root,'-c','user.name=V44 Fixture','-c','user.email=v44@example.invalid',
        'commit','-qm','frozen original backend acceptance source')
    return root,git(root,'rev-parse','HEAD')


def stack(root):
    runtime=implementation('native_bootstrap_runtime_v44')
    machine=implementation('developmental_machine_v44').Machine(
        Path(os.environ.get('UDM_COMPONENTS','/workspace/components')),
        root/'state',root/'evaluator',root/'unused.json')
    return runtime,machine,runtime.MetadataRuntime(machine,root/'metadata')


def make_request(module,repo,commit):
    environment=original.environment_identity(PYTHON)
    return module.request(repo,commit,PYTHON,environment_sha256=original.fingerprint(environment),
                          protocol_binding=PROTOCOL,horizon_seconds=60)


def test_required_metadata_runtime_modules_exist_before_any_native_launch():
    missing=[name for name in MODULES if not (HERE/(name+'.py')).is_file()]
    assert not missing, 'V44 source-native metadata causal instrument missing: '+', '.join(missing)


def test_strict_request_scope_and_absent_route_never_execute_backend(tmp_path,monkeypatch):
    module,machine,runtime=stack(tmp_path)
    repo,commit=fixture_source(tmp_path/'source')
    request=make_request(module,repo,commit)
    runtime.register('native-metadata-obligation',request)
    metadata=implementation('native_metadata_v44')
    def forbidden(*args,**kwargs):
        pytest.fail('an unwarranted or invalid route reached native source execution')
    monkeypatch.setattr(metadata,'observe',forbidden)
    assert machine.select_and_execute_frontier('native-metadata-obligation',runtime)['status']=='UNKNOWN_SEARCH'
    assert not machine.active_capabilities()
    invalid=copy.deepcopy(request);invalid['environment_sha256']='0'*64
    with pytest.raises((ValueError,PermissionError)):
        runtime.register('forged-environment',invalid)
    invalid=copy.deepcopy(request);invalid['authority_ceiling']={'external_effects':'self-granted'}
    with pytest.raises((ValueError,PermissionError)):
        runtime.register('forged-permission',invalid)
    assert set(machine.mt.live_ids(machine.log))==machine.flash_live_ids()


def test_real_metadata_instrument_revocation_fresh_restore_and_process_restart(tmp_path):
    module,machine,runtime=stack(tmp_path)
    repo,commit=fixture_source(tmp_path/'source')
    before=source.snapshot(repo,commit)
    request=make_request(module,repo,commit)
    registration=runtime.register('protected-metadata',request)
    unrelated=machine.append('source_support',{'family':'independent-original-acceptance-input'})
    machine.flush()
    cap=runtime.admit(request)
    descriptor=machine.descriptor(cap)
    assert descriptor.operation=='source.observe_native_metadata'
    assert descriptor.generation==1
    assert registration in {n.id for n in machine.log}
    assert machine.frontiers['frontiers']['protected-metadata']['status']=='READY'
    execution=machine.select_and_execute_frontier('protected-metadata',runtime)
    assert execution['status']=='READY'
    observation=execution['metadata_observation']
    assert observation['status']=='VERIFIED_SOURCE_NATIVE_METADATA_OBSERVATION'
    assert observation['metadata']['name']=='native-bootstrap-alpha'
    binding=runtime.bind(cap,execution['consequence'])
    retained_request,retained_observation=runtime.preflight(binding)
    assert retained_request==request
    assert retained_observation==dict(observation)
    downstream=machine.append('verified_consequence',{'family':'acceptance-only-metadata-dependent'},
                               (cap,execution['consequence']))
    machine.flush()
    corrupt=dict(binding,generation=999)
    with pytest.raises((ValueError,PermissionError)):
        runtime.preflight(corrupt)
    machine.withdraw(cap,'V44 exact metadata ancestor withdrawal acceptance')
    live=set(machine.mt.live_ids(machine.log))
    assert cap not in live and execution['consequence'] not in live and downstream not in live
    assert unrelated in live
    assert machine.frontiers['frontiers']['protected-metadata']['status']=='UNKNOWN_SEARCH'
    with pytest.raises(PermissionError):
        runtime.execute(cap,request)
    with pytest.raises(PermissionError):
        runtime.preflight(binding)
    restored=runtime.restore(cap,request)
    assert machine.descriptor(restored).generation==2
    assert machine.descriptor(restored).supersedes==cap
    assert source.snapshot(repo,commit)==before
    spec={'components':str(machine.components),'state':str(machine.state),
          'evaluator':str(tmp_path/'child-evaluator'),'config':str(tmp_path/'unused.json'),
          'request':request,'capability':restored,'output':str(tmp_path/'child-output')}
    spec_path=tmp_path/'RESTART_SPEC.json';spec_path.write_text(json.dumps(spec,sort_keys=True)+'\n')
    child='''import json,sys\nfrom pathlib import Path\nfrom research.unified_consequence_runtime.developmental_machine_v44 import Machine\nfrom research.unified_consequence_runtime.native_bootstrap_runtime_v44 import MetadataRuntime\ns=json.loads(Path(sys.argv[1]).read_text())\nm=Machine(Path(s['components']),Path(s['state']),Path(s['evaluator']),Path(s['config']))\nr=MetadataRuntime(m,Path(s['output']))\no,c=r.execute(s['capability'],s['request'])\nb=r.bind(s['capability'],c);r.preflight(b)\nassert o['metadata']['name']=='native-bootstrap-alpha'\nassert set(m.mt.live_ids(m.log))==m.flash_live_ids()\nPath(sys.argv[2]).write_text(json.dumps({'status':'PASS_SEPARATE_PROCESS_NATIVE_METADATA_REBUILD','observation':dict(o),'consequence':c,'binding':b,'costs':m.costs},sort_keys=True)+'\\n')\n'''
    child_result=tmp_path/'RESTART_RESULT.json'
    completed=subprocess.run([sys.executable,'-B','-c',child,str(spec_path),str(child_result)],
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1'),
        capture_output=True,text=True,timeout=240)
    (tmp_path/'RESTART_STDOUT.log').write_text(completed.stdout)
    (tmp_path/'RESTART_STDERR.log').write_text(completed.stderr)
    assert completed.returncode==0,completed.stdout+completed.stderr
    restart=json.loads(child_result.read_text())
    assert restart['status']=='PASS_SEPARATE_PROCESS_NATIVE_METADATA_REBUILD'
    assert restart['observation']['costs']['build_calls']>=1
    assert source.snapshot(repo,commit)==before
    assert downstream not in set(machine.mt.live_ids(machine.log))
