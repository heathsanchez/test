"""Revision 2: independently corrected original-verifier accounting only.

The sealed V1 file remains unchanged and its 13 PASS / 2 counter-expectation
RED result is retained. Original execution performs two native runs and four
collections, including independent certificate and receipt recollections.
No oracle, protected assertion, source fixture, skip/import rule or budget is
weakened. This engineering correction establishes no prospective result.

The main-entrypoint controls use an explicitly trusted qualification broker for
the external ticket/pool and an already prepared sealed source provider. They
retain the real Machine, request operation, execution meter, native collector,
independent source/namespace/certificate checker, pytest and native reexecution.
No new task or native oracle is supplied by a broker.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from types import FunctionType

import pytest

from . import native_environment_v43 as request_source
from . import native_environment_v44 as previous_environment
from . import native_environment_v45 as qualified_environment
from . import qualify_native_frontier_v45 as qualified_controller
from . import developmental_machine_v44 as framework
from . import native_execution_v45 as native
from .native_v45_test_support import (
    MODERN, ROOT as SEALED_FIXTURES, git, commit, make_project, modern_environment,
    project_factory, ordinary_case, implementation as recorded_worker, record_evidence,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ENVIRONMENT_MODULE = 'research.unified_consequence_runtime.native_environment_request_v1'
CONTROLLER_MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_request_v1'
PROFILE_CATALOG = HERE/'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
RUNTIME_PATHS = Path(os.environ.get('UDM_REQUEST_V1_RUNTIMES',
    '/workspace/qualification/native-namespace-v45-environment/RUNTIME_PATHS.json'))
COMPONENTS = Path(os.environ.get('UDM_COMPONENTS', '/workspace/components'))
PUBLIC_OPERATIONS = (
    'bind_bootstrap_environment', 'bootstrap_snapshot', 'build_profile_constraints',
    'can_repair_native_refusal', 'canonical', 'diagnose', 'execution_policy',
    'fingerprint', 'freeze_runtime', 'installed_package_identity',
    'metadata_environment_identity', 'package_requirements', 'preflight_bootstrap',
    'profile_attempt_costs', 'provision', 'record_admission_request', 'sha256',
    'validate_runtime',
)


def _module(name, original):
    # Before implementation, exercise the original failing call path rather
    # than earning a RED only by a missing import. Installation is also checked.
    path = HERE/(name.rsplit('.', 1)[-1]+'.py')
    return importlib.import_module(name) if path.is_file() else original


def environment():
    return _module(ENVIRONMENT_MODULE, qualified_environment)


def controller():
    return _module(CONTROLLER_MODULE, qualified_controller)


def _machine(root):
    return framework.Machine(COMPONENTS, root/'state', root/'evaluator', root/'config')


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n')
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def test_versioned_transport_is_additive_and_explicitly_installed():
    assert environment().__name__ == ENVIRONMENT_MODULE
    assert controller().__name__ == CONTROLLER_MODULE
    assert controller().environment is environment()
    assert controller().worker is native
    assert controller().RECORDS != qualified_controller.RECORDS


def test_all_eighteen_existing_operations_are_available_without_rebinding_the_seventeen():
    value = environment()
    missing = [name for name in PUBLIC_OPERATIONS if not callable(getattr(value, name, None))]
    assert missing == [], 'missing inherited executable operations: '+repr(missing)
    assert value.record_admission_request is request_source.record_admission_request
    assert previous_environment.record_admission_request is request_source.record_admission_request
    for name in PUBLIC_OPERATIONS:
        if name != 'record_admission_request':
            assert getattr(value, name) is getattr(qualified_environment, name), name
    assert not hasattr(qualified_environment, 'record_admission_request'), 'no global patch to qualified V45'


def test_real_request_is_idempotent_persistent_and_grants_no_execution_authority(tmp_path):
    value = environment()
    machine = _machine(tmp_path)
    spec = {'repo': 'qualification/request-v1', 'base_commit': 'a'*40, 'head_commit': 'b'*40}
    before = list(machine.active_capabilities())
    failure = None
    try:
        first = value.record_admission_request(machine, spec, 'c'*64)
        second = value.record_admission_request(machine, copy.deepcopy(spec), 'c'*64)
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    assert failure is None, 'actual request operation failed: '+str(failure)
    assert first == second
    records = [node for node in machine.log if node.kind == 'native_admission_request_v43']
    assert len(records) == 1 and records[0].id == first
    from .native_runtime_v45 import AUTHORITY
    assert records[0].payload['authority_ceiling'] == AUTHORITY
    assert AUTHORITY['external_effects'] == 'NONE'
    assert machine.get(records[0].payload['spec']) == spec
    assert list(machine.active_capabilities()) == before
    reloaded = _machine(tmp_path)
    assert value.record_admission_request(reloaded, spec, 'c'*64) == first
    assert len([node for node in reloaded.log if node.kind == 'native_admission_request_v43']) == 1
    with pytest.raises(ValueError, match='Machine'):
        value.record_admission_request(object(), spec, 'c'*64)


def test_existing_policy_stays_v45_and_preserves_explicit_native_bounds():
    profile = {'pytest_version': '8.4.1', 'plugins': []}
    assert environment().execution_policy(profile, collection_seconds=17, execution_seconds=29) == {
        'schema': 'UDM_NATIVE_EXECUTION_POLICY_V45', 'pytest_version': '8.4.1',
        'plugins': [], 'collection_seconds': 17, 'execution_seconds': 29}


def _run_main_control(q, monkeypatch, tmp_path, *, case=None, refusal=None, interrupted=None, alter=None):
    """Only the declared qualification broker/source provider is substituted."""
    output = tmp_path/'screening'
    control = tmp_path/'controller-authority'
    control.mkdir()
    git(control, 'init', '-q')
    spec = {'repo': 'qualification/request-v1'} if case is None else {
        'repo': case.contract['repository'], 'base_commit': case.base, 'head_commit': case.commit}
    ticket = {'schema': q.AUTHORITY_SCHEMA, 'operation': 'screen', 'repo': str(control),
        'output_root': str(output), 'machine_components': q._components_record(COMPONENTS),
        'qualification_only': True}
    ticket_path = control/'AUTHORITY.json'
    descriptor = _json(ticket_path, ticket)
    source_commit = commit(control)
    request = {'pool_index': 0, 'spec': spec, 'protocol_binding': descriptor['sha256']}
    request_path = tmp_path/'request.json'; _json(request_path, request)
    pool = {'pool': [spec], 'screening_budget': {
        'maximum_native_executions_per_case': 2, 'collection_seconds_per_call': 60,
        'execution_seconds_per_call': 600, 'maximum_cases': 9,
        'total_screening_wall_seconds': 7200}}
    catalog_descriptor = {'path': PROFILE_CATALOG.relative_to(REPO).as_posix(),
                          'sha256': hashlib.sha256(PROFILE_CATALOG.read_bytes()).hexdigest()}

    def ticket_broker(path, expected_hash, operation):
        if operation != 'screen' or Path(path) != ticket_path or expected_hash != descriptor['sha256']:
            raise ValueError('qualification ticket scope differs')
        assert q._external_json(descriptor) == ticket
        assert q._committed_record(control, descriptor) == ticket
        return ticket, descriptor, None

    def pool_broker(supplied, supplied_ticket, supplied_descriptor):
        if supplied != request or supplied_ticket != ticket or supplied_descriptor != descriptor:
            raise ValueError('qualification fixed pool/binding differs')
        return pool, {'source_commit': source_commit}, output

    def prepared_provider(supplied_spec, root, binding, **kwargs):
        if supplied_spec != spec or binding != descriptor['sha256']:
            raise ValueError('qualification source provider scope differs')
        if refusal is not None:
            return {'status': refusal, 'reason': 'declared qualification source refusal'}
        assert case is not None
        contract = dict(case.contract, protocol_binding=binding)
        authority = q.environment.admission.derive_suite_contract(case.repo, case.base, case.commit,
            binding, repository=case.contract['repository'])
        setup = q.environment._attach_interface(kwargs['machine'], {'status': 'PREPARED',
            'contract': contract, 'authority': authority, 'policy': case.policy}, Path(root)/'materialization')
        setup['bootstrap_binding'] = None
        if alter is not None:
            alter(setup)
        return setup

    monkeypatch.setattr(q, 'protocol', lambda: dict(q.DEFAULTS, catalog=catalog_descriptor))
    # Recording-only wrappers retain exact public native inputs before calling
    # the original qualified implementation. No verifier result is substituted.
    monkeypatch.setattr(q, 'worker', recorded_worker())
    monkeypatch.setattr(q, 'cli_authority', ticket_broker)
    monkeypatch.setattr(q, 'screening_request', pool_broker)
    monkeypatch.setattr(q.environment, 'provision', prepared_provider)
    if interrupted is not None:
        def fail_before_return(supplied_spec, destination, binding, **kwargs):
            if interrupted == 'after-real-collection':
                Path(destination).mkdir(parents=True, exist_ok=False)
                contract = dict(case.contract, protocol_binding=binding)
                authority = q.environment.admission.derive_suite_contract(case.repo, case.base, case.commit,
                    binding, repository=case.contract['repository'])
                q.worker.collect(contract, authority, Path(destination)/'partial-collection', policy=case.policy)
            raise ValueError('DECLARED_QUALIFICATION_INTERRUPTION_'+interrupted)
        monkeypatch.setattr(q, '_screen_original', fail_before_return)
    monkeypatch.setattr(sys, 'argv', [CONTROLLER_MODULE, '--screen-spec', str(request_path),
        '--authority', str(ticket_path), '--authority-sha256', descriptor['sha256'],
        '--runtimes', str(RUNTIME_PATHS), '--out', str(output/'case-000')])
    before = native.attempt_snapshot(); bootstrap_before = q.environment.bootstrap_snapshot()
    error = None
    try:
        result = q.main()
        assert result is None, 'the original main normal completion has no status exit override'
    except Exception as caught:
        error = type(caught).__name__+': '+str(caught)
    after = native.attempt_snapshot(); bootstrap_after = q.environment.bootstrap_snapshot()
    retained = {'schema': 'UDM_REQUEST_V1_QUALIFICATION_CONTROL',
        'scientific_result': 'NONE_ENGINEERING_ONLY', 'broker_scope':
        'Qualification-only externally held ticket and fixed-pool broker, preprepared original control-source provider. Real committed authority bytes, Machine, request operation, meter, native authority and independent oracle are unchanged.',
        'native_before': before, 'native_after': after,
        'bootstrap_before': bootstrap_before, 'bootstrap_after': bootstrap_after, 'error': error}
    _json(tmp_path/'CONTROL_ACCOUNTING.json', retained)
    assert error is None, 'actual main/execute-screening path failed: '+str(error)
    report = json.loads((output/'case-000/SCREENING_CASE.json').read_text())
    envelope = json.loads((output/'case-000/SCREENING_ENVELOPE.json').read_text())
    meter = json.loads((output/'SCREENING_METER.json').read_text())
    assert meter['pending'] is None and meter['accounting_complete'] is True
    assert len(meter['cases']) == 1 and not (output/'SCREENING_METER.lock').exists()
    delta = {key: after[key]-before[key] for key in after}
    assert report['controller_attempts'] == delta
    assert meter['native_calls'] == delta['native_calls']
    assert meter['collection_calls'] == delta['collection_calls']
    assert report['bootstrap_attempts']['before'] == bootstrap_before
    assert report['bootstrap_attempts']['after'] == bootstrap_after
    assert envelope['bootstrap_costs']['backend_calls'] == bootstrap_after['backend_calls']-bootstrap_before['backend_calls']
    return report, envelope, meter, delta


@pytest.mark.parametrize('outcome', ('PASS_NATIVE', 'FAIL_NATIVE'))
def test_actual_main_executes_complete_native_assertions_and_independent_replay(
        project_factory, tmp_path, monkeypatch, outcome):
    q = controller()
    case = (project_factory(control='W01_closed_production_wildcard') if outcome == 'PASS_NATIVE'
            else ordinary_case(project_factory, b'from subject import value\ndef test_contract():\n    assert value() == 1\n'))
    report, envelope, meter, delta = _run_main_control(q, monkeypatch, tmp_path, case=case)
    assert report['status'] == outcome and report['eligible'] is True
    assert envelope['status'] == 'ADMITTED_NATIVE' and envelope['eligible'] is True
    assert delta == {'native_calls': 2, 'collection_calls': 4, 'subprocess_attempts': 6}
    assert report['baseline']['junit']['tests'] == 1
    assert report['baseline']['junit']['failures'] == (outcome == 'FAIL_NATIVE')
    assert len(report['costs']) == 2 and all(row['native_calls'] == 1 for row in report['costs'])
    assert report['certificate']['schema'] == 'UDM_NATIVE_ADMISSION_CERTIFICATE_V45'
    assert (tmp_path/'screening/case-000/independent-baseline/receipt.json').is_file()
    assert report['machine_context']['schema'] == 'UDM_NATIVE_MACHINE_CONTEXT_V45'
    case_root = tmp_path/'screening/case-000'
    record_evidence(case_root, case_root/'collection/admission-certificate.json',
        case_root/'baseline/receipt.json', case_root/'independent-baseline/receipt.json')


def test_complete_source_refusal_closes_unknown_without_native_or_nonzero_exit(tmp_path, monkeypatch):
    report, envelope, _, delta = _run_main_control(controller(), monkeypatch, tmp_path,
        refusal='UNKNOWN_QUALIFICATION_SOURCE_REFUSAL')
    assert report['status'] == 'UNKNOWN_QUALIFICATION_SOURCE_REFUSAL'
    assert report['eligible'] is False and envelope['eligible'] is False
    assert envelope['status'] == 'UNKNOWN_ADMISSION_SCREENING'
    assert delta == {'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0}


@pytest.mark.parametrize('phase', ('before-setup', 'after-real-collection'))
def test_interrupted_pre_return_path_retains_real_costs_and_precise_unknown(
        project_factory, tmp_path, monkeypatch, phase):
    case = project_factory(control='W01_closed_production_wildcard')
    report, envelope, _, delta = _run_main_control(controller(), monkeypatch, tmp_path,
        case=case, interrupted=phase)
    assert report['status'] == 'UNKNOWN_INTERRUPTED_SCREENING'
    assert report['eligible'] is False and envelope['eligible'] is False
    assert report['reason'] == 'DECLARED_QUALIFICATION_INTERRUPTION_'+phase
    assert delta['native_calls'] == 0
    assert delta['collection_calls'] == (phase == 'after-real-collection')
    if phase == 'after-real-collection':
        assert (tmp_path/'screening/case-000/partial-collection/admission-certificate.json').is_file()


@pytest.mark.parametrize('mutation', ('old-policy-schema', 'forged-namespace'))
def test_native_authority_bypasses_still_refuse_before_native_launch(
        project_factory, tmp_path, monkeypatch, mutation):
    case = project_factory(control='W01_closed_production_wildcard')
    def alter(setup):
        if mutation == 'old-policy-schema':
            setup['policy'] = dict(setup['policy'], schema='UDM_NATIVE_EXECUTION_POLICY_V43')
        else:
            setup['authority'] = dict(setup['authority'], namespace_certificate={'schema': 'forged'})
    report, envelope, _, delta = _run_main_control(controller(), monkeypatch, tmp_path,
        case=case, alter=alter)
    assert report['eligible'] is False and envelope['eligible'] is False
    assert report['status'].startswith('UNKNOWN')
    assert delta['native_calls'] == 0


@pytest.mark.parametrize('mode', ('missing', 'wrong-hash', 'wrong-operation'))
def test_real_cli_authority_refuses_forgery_before_source_dispatch(tmp_path, monkeypatch, mode):
    q = controller()
    wrapper = json.loads((HERE/'archaeology/native-namespace-v45/prospective/GATE_WRAPPER.json').read_text())
    monkeypatch.setattr(q, 'protocol', lambda: dict(q.DEFAULTS, **wrapper))
    path = tmp_path/'request.json'; _json(path, {})
    authority = tmp_path/'authority.json'
    descriptor = _json(authority, {'schema': q.AUTHORITY_SCHEMA,
        'operation': 'agent' if mode == 'wrong-operation' else 'screen', 'repo': str(REPO)})
    arguments = [CONTROLLER_MODULE, '--screen-spec', str(path), '--out', str(tmp_path/'screen')]
    if mode != 'missing':
        arguments += ['--authority', str(authority), '--authority-sha256',
                      '0'*64 if mode == 'wrong-hash' else descriptor['sha256']]
    monkeypatch.setattr(sys, 'argv', arguments)
    before = native.attempt_snapshot()
    with pytest.raises(ValueError, match='authority'):
        q.main()
    assert native.attempt_snapshot() == before
    assert not (tmp_path/'screen').exists()


def test_new_source_pins_refuse_stale_adapter_before_any_native_call(tmp_path, monkeypatch):
    stale = tmp_path/'stale.py'; stale.write_text('# unrelated source\n')
    before = native.attempt_snapshot()
    for module in (environment(), controller()):
        with monkeypatch.context() as changed:
            changed.setattr(module, '__file__', str(stale))
            with pytest.raises(ValueError, match='SOURCE|source|changed'):
                module._guard()
    assert native.attempt_snapshot() == before
