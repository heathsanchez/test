"""Frozen real-Machine V43 causal controls; fixture admission is not G2.

All source repositories are disposable infrastructure created by the existing
Hatch VCS fixture. No receipt, ledger, FLASH validator or native PASS is faked.
Run with a retained --basetemp to preserve every source/build/native raw tree.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from .developmental_machine import Machine as OriginalMachine, canonical
from .native_runtime_v2 import AUTHORITY
from .native_v43_test_support import (
    assert_no_native_success, charged_build_calls, clean_environment,
    implementation, modern_environment, project_factory, wheel_artifact,
)


MODULES = ('native_materialization_v43', 'cross_frontier_v43',
           'developmental_machine_v43', 'native_runtime_v43')
REQUEST_SCHEMA = 'UDM_NATIVE_MATERIALIZATION_REQUEST_V43'


def stack(root):
    module = implementation('native_materialization_v43')
    machine_type = implementation('developmental_machine_v43').Machine
    components = Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')).resolve()
    machine = machine_type(components, root / 'state', root / 'evaluator', root / 'unused-config.json')
    assert isinstance(machine, OriginalMachine)
    assert Path(machine.mt.__file__).resolve() == components / 'metatron/runtime/metatron/nucleus.py'
    assert Path(machine.router.__file__).resolve() == components / 'flash/qckn_flash_live_router.py'
    return module, machine, module.MaterializationRuntime(machine, root / 'materialization')


def closure_agrees(machine):
    assert set(machine.mt.live_ids(machine.log)) == machine.flash_live_ids()


def node(machine, ident):
    return next(item for item in machine.log if item.id == ident)


def native_runtime(machine, case, certificate, output, *, evidence=None, instrument=None):
    runtime_type = implementation('native_runtime_v43').NativeRuntimeV43
    contract = case.with_evidence(evidence) if evidence is not None else case.contract
    return runtime_type(machine, contract, case.authority, certificate, case.policy, output,
                        materialization_capability=instrument)


@contextmanager
def no_effect_launches():
    """Refusal must precede producers; ordinary Git/source checks still run."""
    build = implementation('native_build_v43')
    worker = implementation('native_execution_v43')
    before = worker.attempt_snapshot()
    real_popen = subprocess.Popen

    def audited_popen(argv, *args, **kwargs):
        values = [str(value) for value in argv] if isinstance(argv, (list, tuple)) else [str(argv)]
        if (('pip' in values and 'wheel' in values) or
                any('trusted-runner.py' in value for value in values) or
                ('-m' in values and 'pytest' in values)):
            raise AssertionError('withdrawn or corrupt instrument reached a build/native launch: ' + repr(values))
        return real_popen(argv, *args, **kwargs)

    with patch.object(build, 'prepare', side_effect=AssertionError('build prepare reached before preflight')), \
            patch.object(build, 'verify', side_effect=AssertionError('independent build reached before preflight')), \
            patch.object(worker, 'collect', side_effect=AssertionError('native collection reached before preflight')), \
            patch.object(worker, 'verify', side_effect=AssertionError('native execution reached before preflight')), \
            patch.object(subprocess, 'Popen', side_effect=audited_popen):
        yield
    assert worker.attempt_snapshot() == before


def test_required_causal_v43_modules_exist():
    missing = [name for name in MODULES if not Path(__file__).with_name(name + '.py').is_file()]
    assert not missing, 'V43 retained causal interface is not implemented: ' + ', '.join(missing)


def test_request_is_strict_source_bound_json_and_not_a_caller_output_allowlist(project_factory, tmp_path):
    module, machine, runtime = stack(tmp_path)
    case = project_factory('alpha')
    request = module.request(case.contract, case.authority, case.policy)
    assert set(request) == {'schema', 'contract', 'authority', 'policy'}
    assert request['schema'] == REQUEST_SCHEMA
    assert request == json.loads(canonical(request))
    assert request['contract'] == case.contract
    assert request['authority'] == case.authority
    assert request['policy'] == case.policy
    request['contract']['repository'] = 'fixture/mutated-caller-copy'
    assert case.contract['repository'] != request['contract']['repository']

    valid = module.request(case.contract, case.authority, case.policy)
    unsupported = copy.deepcopy(valid)
    unsupported['generated_paths'] = [case.generated_path]
    wrong_source = copy.deepcopy(valid)
    wrong_source['contract']['tracked_tree_sha256'] = '0' * 64
    for rejected in (unsupported, wrong_source):
        with no_effect_launches():
            with pytest.raises((ValueError, PermissionError)):
                runtime.register('rejected-source', rejected)
    assert not machine.active_capabilities()
    closure_agrees(machine)


def test_real_backend_instrument_causal_withdraw_restore_tamper_and_process_restart(project_factory, tmp_path):
    module, machine, materializer = stack(tmp_path)
    build = implementation('native_build_v43')
    worker = implementation('native_execution_v43')
    alpha = project_factory('alpha')
    beta = project_factory('beta')
    unrelated_case = project_factory('unrelated', generated=False)
    requests = {name: module.request(case.contract, case.authority, case.policy)
                for name, case in (('source-alpha', alpha), ('source-beta', beta))}
    registrations = {name: materializer.register(name, request) for name, request in requests.items()}
    assert all(node(machine, ident).kind == 'native_frontier_registration'
               for ident in registrations.values())
    with no_effect_launches():
        for name in requests:
            route = machine.select_and_execute_frontier(name, materializer)
            assert route['status'] == 'UNKNOWN_SEARCH'
    assert not machine.active_capabilities()

    with patch.object(build, 'prepare', wraps=build.prepare) as prepared, \
            patch.object(build, 'verify', wraps=build.verify) as independently_checked:
        capability = materializer.admit(requests['source-alpha'])
        assert prepared.call_count >= 1
        assert independently_checked.call_count >= 1
    descriptor = machine.descriptor(capability)
    assert descriptor.operation == 'source.materialize_declared_backend'
    assert descriptor.scope['authority_ceiling'] == AUTHORITY
    generic_program_and_scope = canonical([machine.get(descriptor.program), descriptor.scope])
    for case in (alpha, beta):
        for forbidden in (case.contract['repository'], case.base, case.augmented, case.package, case.generated_path):
            assert forbidden not in generic_program_and_scope
    assert set(machine.frontiers['changed_frontiers']) == set(requests)
    assert all(machine.frontiers['frontiers'][name]['status'] == 'READY' for name in requests)
    assert all(machine.frontiers['frontiers'][name]['capability_id'] == capability for name in requests)
    verified = node(machine, descriptor.evidence[0])
    retained_receipt = machine.get(verified.payload['receipt'])
    assert_no_native_success(retained_receipt)
    assert charged_build_calls(retained_receipt) >= 1
    assert all(machine.log.index(node(machine, ident)) < machine.log.index(node(machine, capability))
               for ident in registrations.values())

    with patch.object(build, 'prepare', wraps=build.prepare) as prepared, \
            patch.object(build, 'verify', wraps=build.verify) as independently_checked:
        activated = machine.select_and_execute_frontier('source-beta', materializer)
        assert prepared.call_count >= 1
        assert independently_checked.call_count >= 1
    assert activated['status'] == 'READY'
    assert activated['capability_id'] == capability
    evidence = activated['materialization']
    assert_no_native_success(evidence)
    assert wheel_artifact(evidence).is_file()
    assert node(machine, activated['consequence']).premises == (capability,)
    generated = build.read_generated(beta.contract, beta.authority, beta.policy, evidence)
    assert set(generated) == {beta.generated_path}
    with pytest.raises(ValueError):
        build.read_generated(alpha.contract, alpha.authority, alpha.policy, evidence)

    contract = beta.with_evidence(evidence)
    certificate = worker.collect(contract, beta.authority, tmp_path / 'beta-collection', policy=beta.policy)
    dependent = native_runtime(machine, beta, certificate, tmp_path / 'dependent-native',
                               evidence=evidence, instrument=capability)
    native_capability = dependent.admit({'replacements': []})
    child = dependent.admit(beta.candidate(0), dependencies=(native_capability,))
    receipt, native_consequence = dependent.execute(child)
    assert receipt['status'] == 'PASS_NATIVE'
    assert receipt['junit']['passed'] == 2
    assert receipt['authority'] == 'EXTERNALLY_SUPPLIED_LOCAL_RESEARCH_ONLY'
    for ident in (native_capability, child):
        assert capability in machine.descriptor(ident).dependencies
        assert capability in node(machine, ident).premises
    assert node(machine, native_consequence).premises == (child,)
    with no_effect_launches():
        with pytest.raises((ValueError, PermissionError)):
            native_runtime(machine, beta, certificate, tmp_path / 'missing-materializer', evidence=evidence)
        with pytest.raises((ValueError, PermissionError)):
            native_runtime(machine, alpha, certificate, tmp_path / 'replayed-source',
                           evidence=evidence, instrument=capability)

    unrelated_certificate = worker.collect(unrelated_case.contract, unrelated_case.authority,
                                           tmp_path / 'unrelated-collection', policy=unrelated_case.policy)
    unrelated = native_runtime(machine, unrelated_case, unrelated_certificate, tmp_path / 'unrelated-native')
    unrelated_capability = unrelated.admit({'replacements': []})
    assert unrelated.execute(unrelated_capability)[0]['status'] == 'PASS_NATIVE'
    closure_agrees(machine)

    # Corruption controls alter only disposable retained state, never installed
    # implementation source or native assertions. Restore bytes between controls.
    for label, object_key, remove in (
            ('corrupted-cas', descriptor.observation, False),
            ('missing-program', descriptor.program, True),
            ('missing-evidence', verified.payload['receipt'], True)):
        path = machine.state / 'objects' / object_key
        original = path.read_bytes()
        if remove:
            path.unlink()
        else:
            path.write_text('{"forged":true}')
        try:
            with no_effect_launches():
                for operation in (
                        lambda: materializer.execute(capability, requests['source-beta']),
                        lambda: machine.select_and_execute_frontier('source-beta', materializer),
                        lambda: dependent.execute(child)):
                    with pytest.raises((ValueError, PermissionError, OSError)):
                        operation()
        finally:
            path.write_bytes(original)
        (tmp_path / (label + '-checked.json')).write_text(canonical({'status': 'REJECTED_BEFORE_LAUNCH'}))

    ancestor = descriptor.dependencies[0]
    withdrawal = machine.withdraw(capability, 'V43 exact materialization support withdrawal')
    assert node(machine, withdrawal).payload['target'] == ancestor
    assert set(machine.frontiers['changed_frontiers']) == set(requests)
    assert all(machine.frontiers['frontiers'][name]['status'] == 'UNKNOWN_SEARCH' for name in requests)
    assert all(ident in machine.mt.live_ids(machine.log) for ident in registrations.values())
    for ident in (ancestor, capability, activated['consequence'], native_capability, child, native_consequence):
        assert ident not in machine.mt.live_ids(machine.log)
        assert ident not in machine.flash_live_ids()
    assert unrelated_capability in machine.mt.live_ids(machine.log)
    assert unrelated.execute(unrelated_capability)[0]['status'] == 'PASS_NATIVE'
    closure_agrees(machine)
    with no_effect_launches():
        for operation in (
                lambda: materializer.execute(capability, requests['source-beta']),
                lambda: dependent.observe(), lambda: dependent._verify({'replacements': []}),
                lambda: dependent.admit({'replacements': []}), lambda: dependent.execute(child)):
            with pytest.raises(PermissionError):
                operation()
        assert machine.select_and_execute_frontier('source-beta', materializer)['status'] == 'UNKNOWN_SEARCH'

    restored = materializer.restore(capability, requests['source-alpha'])
    fresh_descriptor = machine.descriptor(restored)
    assert restored != capability
    assert fresh_descriptor.supersedes == capability
    assert fresh_descriptor.generation > descriptor.generation
    assert fresh_descriptor.program == descriptor.program
    assert fresh_descriptor.evidence != descriptor.evidence
    assert all(machine.frontiers['frontiers'][name]['capability_id'] == restored for name in requests)
    assert all(ident not in machine.flash_live_ids()
               for ident in (capability, native_capability, child, native_consequence))
    fresh_evidence, _ = materializer.execute(restored, requests['source-beta'])
    assert wheel_artifact(fresh_evidence) != wheel_artifact(evidence)
    fresh_certificate = worker.collect(beta.with_evidence(fresh_evidence), beta.authority,
                                       tmp_path / 'fresh-beta-collection', policy=beta.policy)
    fresh_runtime = native_runtime(machine, beta, fresh_certificate, tmp_path / 'fresh-dependent-native',
                                   evidence=fresh_evidence, instrument=restored)
    fresh_native = fresh_runtime.admit({'replacements': []})
    assert restored in machine.descriptor(fresh_native).dependencies
    assert fresh_native != native_capability
    with no_effect_launches():
        with pytest.raises(PermissionError):
            dependent.execute(child)
    closure_agrees(machine)

    # A fresh interpreter reconstructs both executable adapters from retained
    # source/CAS state, then performs a real new build and independent native run.
    restart_output = tmp_path / 'separate-process'
    restart_output.mkdir()
    script = r'''
import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine_v43 import Machine
from research.unified_consequence_runtime.native_materialization_v43 import MaterializationRuntime,request
from research.unified_consequence_runtime.native_runtime_v43 import NativeRuntimeV43
from research.unified_consequence_runtime import native_execution_v43 as worker
from research.unified_consequence_runtime.native_v43_test_support import charged_build_calls
components,state,output,instrument,capability=sys.argv[1:]
output=Path(output);machine=Machine(Path(components),Path(state),output/'evaluator',output/'unused-config.json')
source=machine.descriptor(capability).source
contract,authority,certificate,policy=(machine.get(source[key]) for key in ('contract','suite_authority','certificate','policy'))
base_contract=dict(contract,generated_build=None)
materializer=MaterializationRuntime(machine,output/'materialization')
materializer._validated(instrument)
evidence,source_consequence=materializer.execute(instrument,request(base_contract,authority,policy))
runtime=NativeRuntimeV43(machine,contract,authority,certificate,policy,output/'native',materialization_capability=instrument)
before=worker.attempt_snapshot();receipt,consequence=runtime.execute(capability);after=worker.attempt_snapshot()
delta={key:after[key]-before[key] for key in ('native_calls','collection_calls','subprocess_attempts')}
source_node=next(node for node in machine.log if node.id==source_consequence)
result={'status':receipt['status'],'junit':receipt['junit'],'native_attempts':delta,
 'build_calls':charged_build_calls(machine.get(source_node.payload['receipt'])),
 'source_consequence':source_consequence,'consequence':consequence,
 'instrument':instrument,'capability':capability,'source':source,
 'closure_agrees':set(machine.mt.live_ids(machine.log))==machine.flash_live_ids()}
(output/'RESTART_RESULT.json').write_text(json.dumps(result,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
'''
    process = subprocess.run([sys.executable, '-B', '-c', script, str(machine.components), str(machine.state),
                              str(restart_output), restored, fresh_native], cwd=Path(__file__).resolve().parents[2],
                             env=clean_environment(), capture_output=True, text=True, timeout=240)
    (restart_output / 'stdout.log').write_text(process.stdout)
    (restart_output / 'stderr.log').write_text(process.stderr)
    assert process.returncode == 0, process.stdout + process.stderr
    restarted = json.loads((restart_output / 'RESTART_RESULT.json').read_text())
    assert restarted['status'] == 'PASS_NATIVE'
    assert restarted['junit']['passed'] == 2
    assert restarted['native_attempts']['native_calls'] == 1
    assert restarted['native_attempts']['subprocess_attempts'] >= 1
    assert restarted['build_calls'] >= 1
    assert restarted['closure_agrees']
    assert restarted['source'] == machine.descriptor(fresh_native).source
    assert restarted['instrument'] == restored
    assert restarted['capability'] == fresh_native
