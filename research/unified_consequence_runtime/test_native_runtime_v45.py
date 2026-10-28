"""Existing-machine namespace qualification; G2–G6 remain UNKNOWN."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import FunctionType

import pytest

from .native_v45_test_support import project_factory, modern_environment, implementation, record_evidence
from . import developmental_machine_v44 as framework
from . import native_runtime_v2 as frozen
from . import native_runtime_v3 as portable


def runtime_module():
    return implementation('native_runtime_v45')


def machine(root):
    return framework.Machine(Path('/workspace/components'), root/'state', root/'evaluator', root/'config')


def costs(value):
    return [row for row in value.costs if row['phase'] == 'generic_native_v2_independent_verification']


def test_original_algorithms_are_privately_bound_to_typed_v45_and_existing_machine():
    module = runtime_module()
    assert issubclass(module.NativeRuntimeV45, frozen.NativeRuntimeV2)
    assert module.framework is framework
    assert module.AUTHORITY == frozen.AUTHORITY
    assert module.AUTHORITY is not frozen.AUTHORITY
    assert module.AUTHORITY['external_effects'] == 'NONE'
    for name, function in vars(frozen.NativeRuntimeV2).items():
        if not isinstance(function, FunctionType) or name in ('__init__', '_inputs', '_scope', '_expected_scope', '_verify', 'admit'):
            continue
        bound = vars(module.NativeRuntimeV45)[name]
        assert bound.__code__ is function.__code__
        assert bound.__closure__ is function.__closure__
        assert bound.__globals__ is not vars(frozen)
        assert bound.__globals__['verifier'] is module.verifier
        assert bound.__globals__['admission'] is module.admission
    assert module.NativeRuntimeV45._verify.__code__ is portable.NativeRuntimeV3._verify.__code__
    assert frozen.verifier.__name__.endswith('native_execution_v2')


def test_w01_native_admit_execute_ancestor_withdraw_fresh_restore_and_process_restart(project_factory, tmp_path):
    module = runtime_module()
    case = project_factory(control='W01_closed_production_wildcard')
    worker = implementation()
    certificate = worker.collect(case.contract, case.authority, tmp_path/'collection', policy=case.policy)
    state = tmp_path/'machine'
    state.mkdir()
    value = machine(state)
    dependency = value.append('qualification_prerequisite', {'engineering_only': True})
    unrelated = value.append('qualification_unrelated', {'engineering_only': True})
    value.flush()
    runtime = module.NativeRuntimeV45(value, case.contract, case.authority, certificate, case.policy, tmp_path/'native')
    cap = runtime.admit({'replacements': []}, dependencies=(dependency,))
    descriptor = value.descriptor(cap)
    assert descriptor.operation == 'native.pytest_suite'
    assert descriptor.scope['native_runtime_version'] == 45
    assert descriptor.scope['authority_ceiling'] == frozen.AUTHORITY
    assert value.get(descriptor.source['suite_authority']) == case.authority
    assert value.get(descriptor.source['suite_authority'])['namespace_certificate'] == case.authority['namespace_certificate']
    assert len(costs(value)) == 2
    assert all(row['accounting_complete'] and row['controller_attempts']['native_calls'] == 1 for row in costs(value))
    receipt, consequence = runtime.execute(cap)
    assert receipt['status'] == 'PASS_NATIVE'
    assert next(node for node in value.log if node.id == consequence).premises == (cap,)
    value.append('revoke', {'target': unrelated, 'reason': 'engineering unrelated withdrawal'})
    value.flush()
    assert cap in value.flash_live_ids() and consequence in value.flash_live_ids()
    assert dependency in value.flash_live_ids()
    before = worker.attempt_snapshot()
    value.append('revoke', {'target': runtime.source, 'reason': 'engineering exact source withdrawal'})
    value.flush()
    assert cap not in value.flash_live_ids() and consequence not in value.flash_live_ids()
    assert dependency in value.flash_live_ids()
    with pytest.raises(PermissionError):
        runtime.execute(cap)
    assert worker.attempt_snapshot() == before
    with pytest.raises((ValueError, PermissionError)):
        runtime.restore(cap)
    fresh = worker.collect(case.contract, case.authority, tmp_path/'fresh-collection', policy=case.policy)
    assert fresh != certificate
    restored = module.NativeRuntimeV45(value, case.contract, case.authority, fresh, case.policy, tmp_path/'restored')
    successor = restored.restore(cap)
    assert value.descriptor(successor).supersedes == cap
    assert value.descriptor(successor).generation == 2
    assert value.descriptor(successor).dependencies[2:] == (dependency,)
    assert cap not in value.flash_live_ids() and successor in value.flash_live_ids()
    assert consequence not in value.flash_live_ids() and unrelated not in value.flash_live_ids()
    assert dependency in value.flash_live_ids()
    assert set(value.mt.live_ids(value.log)) == value.flash_live_ids()
    script = '''import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine_v44 import Machine
from research.unified_consequence_runtime.native_runtime_v45 import NativeRuntimeV45
from research.unified_consequence_runtime import native_execution_v45 as worker
root,output=map(Path,sys.argv[1:3]);cap=sys.argv[3]
before,compiled_before=worker.attempt_snapshot(),worker.compilation_snapshot()
report={'status':'UNKNOWN_CHILD_EXECUTION'}
machine=None
try:
 machine=Machine(Path('/workspace/components'),root/'state',root/'evaluator',root/'config')
 source=machine.descriptor(cap).source
 runtime=NativeRuntimeV45(machine,*(machine.get(source[key]) for key in ('contract','suite_authority','certificate','policy')),output)
 receipt,consequence=runtime.execute(cap)
 report.update(status=receipt['status'],consequence=consequence,source=source,
  closure_agrees=set(machine.mt.live_ids(machine.log))==machine.flash_live_ids(),
  native_calls=sum(row.get('costs',{}).get('native_calls',0) for row in machine.costs))
finally:
 after,compiled_after=worker.attempt_snapshot(),worker.compilation_snapshot()
 envelope={'schema':'UDM_NATIVE_V45_CHILD_ATTEMPTS','status':report['status'],
  'native_attempts':{'before':before,'after':after,'delta':{key:after[key]-before[key] for key in after}},
  'compilation_attempts':{'before':compiled_before,'after':compiled_after,
   'delta':{key:compiled_after[key]-compiled_before[key] for key in compiled_after if type(compiled_after[key]) in (int,float)}},
  'native_run_outputs':[row['output'] for row in machine.costs if row['phase']=='generic_native_v2_independent_verification'] if machine else []}
 (output.parent/'CHILD_NATIVE_ATTEMPTS.json').write_text(json.dumps(envelope,sort_keys=True)+'\\n')
 report['attempts']=envelope
 print(json.dumps(report))
'''
    process = subprocess.run([sys.executable, '-B', '-c', script, str(state), str(tmp_path/'restart'), successor],
                             capture_output=True, text=True, timeout=180)
    (tmp_path/'RESTART_STDOUT.log').write_text(process.stdout)
    (tmp_path/'RESTART_STDERR.log').write_text(process.stderr)
    assert process.returncode == 0, process.stderr
    replay = json.loads(process.stdout)
    assert replay['status'] == 'PASS_NATIVE' and replay['closure_agrees']
    assert replay['native_calls'] == replay['attempts']['native_attempts']['delta']['native_calls'] == 1
    assert replay['attempts']['native_attempts']['delta']['collection_calls'] == 1
    assert replay['attempts']['compilation_attempts']['delta']['compilation_calls'] > 0
    assert json.loads((tmp_path/'CHILD_NATIVE_ATTEMPTS.json').read_text()) == replay['attempts']
    assert replay['source'] == value.descriptor(successor).source
    replay_receipt, = (tmp_path/'restart/native-runs').glob('*/receipt.json')
    record_evidence(tmp_path, tmp_path/'fresh-collection/admission-certificate.json',
                    Path(costs(value)[-1]['output'])/'receipt.json', replay_receipt)
    with pytest.raises(ValueError, match='UNKNOWN'):
        restored.projection_payload(successor)


def test_native45_rejects_unbound_metadata_before_constructing_source(tmp_path):
    module = runtime_module()
    value = machine(tmp_path)
    with pytest.raises(ValueError, match='environment selection witness'):
        module.NativeRuntimeV45(value, {}, {}, {}, {}, tmp_path/'uncreated', bootstrap_binding={
            'capability_id': 'unqualified', 'consequence_id': 'unqualified'})
    assert not (tmp_path/'uncreated').exists()


def test_persisted_namespace_cas_and_worker_compiler_staleness_refuse_before_native(project_factory, tmp_path, monkeypatch):
    module = runtime_module()
    case = project_factory(control='W01_closed_production_wildcard')
    worker = implementation()
    certificate = worker.collect(case.contract, case.authority, tmp_path/'collection', policy=case.policy)
    value = machine(tmp_path)
    runtime = module.NativeRuntimeV45(value, case.contract, case.authority, certificate, case.policy, tmp_path/'native')
    before = worker.attempt_snapshot()
    compiler_before = worker.declaration_attempt_snapshot()
    authority_object = value.state/'objects'/runtime.source_descriptor['suite_authority']
    raw = authority_object.read_bytes()
    try:
        authority_object.write_text('{"namespace_certificate":"corrupt"}')
        with pytest.raises(ValueError, match='persisted executable object changed'):
            runtime._scope()
    finally:
        authority_object.write_bytes(raw)
    with monkeypatch.context() as changed:
        changed.setattr(runtime, 'suite_authority', dict(runtime.suite_authority,
            namespace_certificate={'schema': 'forged'}))
        with pytest.raises(ValueError, match='external input or CAS binding'):
            runtime._scope()
    stale = tmp_path/'stale-controller-source.py'
    stale.write_text('# engineering stale-source negative\n')
    for dependency in (module, module.verifier, module.admission):
        with monkeypatch.context() as changed:
            changed.setattr(dependency, '__file__', str(stale))
            with pytest.raises(ValueError, match='SOURCE_CHANGED'):
                runtime._scope()
    assert worker.attempt_snapshot() == before
    assert worker.declaration_attempt_snapshot() == compiler_before
    assert not costs(value)
    assert not value.active_capabilities()
