"""Preimplementation V44 transport controls; no native verdict is supplied.

These controls check original algorithm identity and stop at the bootstrap
liveness boundary. Native evidence must come from the separate qualification.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import inspect
from pathlib import Path
from types import CodeType

import pytest


HERE = Path(__file__).resolve().parent


def controller():
    path = HERE / 'qualify_native_frontier_v44.py'
    assert path.is_file(), 'V44 prospective transport is not implemented'
    return importlib.import_module('research.unified_consequence_runtime.qualify_native_frontier_v44')


def literals(code):
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from literals(value)
        elif isinstance(value, str):
            yield value


def test_versioned_controller_preserves_original_algorithm_and_native_authority():
    current = controller()
    previous = importlib.import_module('research.unified_consequence_runtime.qualify_native_frontier_v43')
    native = importlib.import_module('research.unified_consequence_runtime.native_execution_v43')
    environment = importlib.import_module('research.unified_consequence_runtime.native_environment_v44')
    machine = importlib.import_module('research.unified_consequence_runtime.developmental_machine_v44').Machine
    assert current.environment is environment
    assert current.worker is native
    assert current.Machine is machine
    assert current.AUTHORITY_SCHEMA == 'UDM_NATIVE_CLI_AUTHORITY_V44'
    assert current.AGENT_SCHEMA == 'UDM_CODING_AGENT_NATIVE_ARM_V44'
    assert current.DEFAULTS['schema'] == 'UDM_NATIVE_FRONTIER_PROTOCOL_V44'
    assert current.RECORDS != previous.RECORDS
    assert current.orders.__code__ is previous.orders.__code__
    assert current.select_screened_roles.__code__ is previous.select_screened_roles.__code__
    assert current.isolated_binding('search').__code__ is previous.isolated_binding('search').__code__
    assert current.isolated_binding('search').__globals__['worker'] is native
    for key in ('search_budget', 'candidate_cap_per_file', 'acquisition_native_calls',
                'training_seconds', 'requested_roles', 'training_unique_calls'):
        assert current.DEFAULTS[key] == previous.DEFAULTS[key]


def test_preserved_v43_controller_and_old_verifier_bytes():
    expected = {
        'qualify_native_frontier_v43.py': 'd25a02b0fdeba507073b54b8297b73b488638f154de39fc53ef03a1fff246358',
        'native_execution_v43.py': '7d449419909c94ce6186d984545ce218c15ee97dc407104bd4e903180c564827',
    }
    for name, digest in expected.items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest


def test_new_bootstrap_gate_is_required_after_preserved_gates(monkeypatch):
    current = controller()
    seen = []
    monkeypatch.setattr(current._previous_controller, 'require_environment_gate',
                        lambda value: seen.append('preserved-gates') or {'old': 'exact'})
    monkeypatch.setattr(current, '_guard', lambda: None)
    with pytest.raises(ValueError, match='bootstrap'):
        current.require_environment_gate({})
    assert seen == ['preserved-gates']


@pytest.mark.parametrize('field', ('status', 'source_commit', 'artifact_sha256', 'run_id', 'artifact_id'))
def test_bootstrap_gate_rejects_incomplete_or_forged_descriptor(field, monkeypatch):
    current = controller()
    monkeypatch.setattr(current._previous_controller, 'require_environment_gate', lambda value: {})
    monkeypatch.setattr(current, '_guard', lambda: None)
    gate = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': 'a'*40, 'run_id': 1,
            'artifact_id': 2, 'artifact_sha256': 'b'*64,
            'qualification_result_sha256': 'c'*64, 'result_path': '/not/read'}
    gate.pop(field)
    with pytest.raises(ValueError, match='bootstrap'):
        current.require_environment_gate({'bootstrap_gate': gate})


@pytest.mark.parametrize('cached', (False, True))
def test_withdrawn_bootstrap_preflight_precedes_cached_and_uncached_native_receipt(cached, monkeypatch):
    current = controller()
    record = {'wiring_only': True}
    cache = {current.worker.fingerprint(record): 'untrusted-cache-token'} if cached else {}
    token = object()
    seen = []

    def withdrawn(actual, machine):
        assert actual is record and machine is token
        seen.append('bootstrap')
        raise PermissionError('withdrawn bootstrap invocation')

    monkeypatch.setattr(current, '_preflight_record', withdrawn)
    with pytest.raises(PermissionError, match='withdrawn bootstrap'):
        current.checked_record(record, token, cache=cache)
    assert seen == ['bootstrap']


def test_original_equal_pass_fail_eligibility_and_order():
    current = controller()
    pool = [{'repo': 'fixture/source-a'}, {'repo': 'fixture/source-b'}, {'repo': 'fixture/source-c'}]

    def pick(statuses):
        rows = [{'repository': spec['repo'], 'spec_sha256': current.worker.fingerprint(spec),
                 'status': status, 'eligible': status in ('PASS_NATIVE', 'FAIL_NATIVE'),
                 'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
                for spec, status in zip(pool, statuses)]
        return current.select_screened_roles(pool, rows, requested=2)

    assert pick(('PASS_NATIVE', 'FAIL_NATIVE', 'PASS_NATIVE')) == pick(('FAIL_NATIVE', 'PASS_NATIVE', 'FAIL_NATIVE'))
    assert [row['repo'] for row in pick(('PASS_NATIVE', 'FAIL_NATIVE', 'UNKNOWN'))] == [pool[0]['repo'], pool[1]['repo']]


def test_bootstrap_costs_are_separate_from_unchanged_native_counters():
    current = controller()
    row = {'bootstrap_attempts': {'before': {'backend_calls': 1, 'backend_seconds': 1.0},
                                   'after': {'backend_calls': 3, 'backend_seconds': 2.5}},
           'total_wall_seconds': 4.0}
    costs = current._screening_bootstrap_costs(row)
    assert costs['backend_calls'] == 2
    assert costs['backend_seconds'] == 1.5
    assert costs['inclusive_parent_wall_seconds'] == 4.0
    assert 'native_calls' not in costs
    for key in ('backend_calls', 'backend_seconds', 'inclusive_parent_wall_seconds'):
        malformed = copy.deepcopy(costs)
        malformed[key] = True
        with pytest.raises(ValueError):
            current._validate_screening_bootstrap_costs(malformed)


def test_no_target_identity_or_winning_method_in_new_controller():
    current = controller()
    text = Path(current.__file__).read_text()
    for forbidden in ('typeguard', 'exceptiongroup', 'wcmatch', 'pycparser', 'frozenlist', 'werkzeug'):
        assert forbidden not in text
    assert 'bootstrap_binding' in text

