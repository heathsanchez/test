"""Prospective V43 wiring controls; doubles never return a native verdict.

Real native assertions, generated provenance and causal restart are qualified by
the existing V43 integration controls. These tests inspect code bindings or stop
execution at an explicit wiring boundary. No prospective source is accessed.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
from pathlib import Path

import pytest

from . import qualify_native_frontier_v42 as previous
from .developmental_machine import canonical
from .native_runtime_v2 import AUTHORITY
from .native_v43_test_support import implementation


AUTHORITY_SCHEMA = 'UDM_NATIVE_CLI_AUTHORITY_V43'


def controller():
    return implementation('qualify_native_frontier_v43')


def components():
    return Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')).resolve()


def fail_if_native(*args, **kwargs):
    raise AssertionError('a wiring control reached a native producer')


def test_versioned_environment_and_controller_modules_exist():
    missing = [name for name in ('native_environment_v43.py', 'qualify_native_frontier_v43.py')
               if not Path(__file__).with_name(name).is_file()]
    assert not missing, 'V43 prospective binding is not implemented: ' + ', '.join(missing)


def test_bindings_preserve_original_search_orders_eligibility_and_select_v43_core():
    current = controller()
    environment = implementation('native_environment_v43')
    machine_type = implementation('developmental_machine_v43').Machine
    assert inspect.signature(environment.provision).parameters['machine'].default is inspect.Parameter.empty
    assert inspect.signature(current.admission_only_screen).parameters['components'].default is inspect.Parameter.empty
    assert current.AUTHORITY_SCHEMA == AUTHORITY_SCHEMA
    assert current.DEFAULTS['schema'] == 'UDM_NATIVE_FRONTIER_PROTOCOL_V43'
    for key in ('search_budget', 'candidate_cap_per_file', 'acquisition_native_calls',
                'training_seconds', 'requested_roles'):
        assert current.DEFAULTS[key] == previous.DEFAULTS[key]
    assert previous.DEFAULTS['schema'] == 'UDM_NATIVE_FRONTIER_PROTOCOL_V42'
    assert current.PROTOCOL.parent != previous.PROTOCOL.parent
    assert current.Machine is machine_type
    assert current.physical_removal_counterfactual.__globals__['Machine'] is machine_type
    assert current.orders.__code__ is previous.orders.__code__
    assert current.catalog.__code__.co_code == previous.catalog.__code__.co_code
    assert current.select_screened_roles.__code__ is previous.select_screened_roles.__code__
    assert current.isolated_binding('search').__code__ is previous.isolated_binding('search').__code__
    assert current.isolated_binding('search').__globals__['worker'] is current.worker
    code = current._prepare.__code__
    assert code.co_names.count('native_runtime_v43') == 1
    assert code.co_names.count('NativeRuntimeV43') == 1
    keyword_sets = [set(item) for item in code.co_consts
                    if isinstance(item, tuple) and all(isinstance(value, str) for value in item)]
    assert any('machine' in keys for keys in keyword_sets)
    assert any('materialization_capability' in keys for keys in keyword_sets)
    assert current._execute_agent_candidate.__code__.co_names.count('_preflight_agent') == 1


def test_real_machine_records_external_obligation_before_environment_provision(tmp_path, monkeypatch):
    current = controller()
    real_type = implementation('developmental_machine_v43').Machine
    events = []
    created = []

    def create(*args, **kwargs):
        machine = real_type(*args, **kwargs)
        events.append('Machine')
        created.append(machine)
        return machine

    def provision_refusal(spec, root, binding, *, machine, **kwargs):
        assert events == ['Machine']
        assert machine is created[0]
        requested = [node for node in machine.log if node.kind == 'native_admission_request_v43']
        assert len(requested) == 1
        assert requested[0].payload['spec_sha256'] == current.worker.fingerprint(spec)
        assert requested[0].payload['authority_ceiling'] == AUTHORITY
        assert requested[0].id in machine.mt.live_ids(machine.log)
        assert set(machine.mt.live_ids(machine.log)) == machine.flash_live_ids()
        events.append('environment.provision')
        raise ValueError('UNKNOWN_WIRING_STOP_BEFORE_ANY_SOURCE_OR_NATIVE_OPERATION')

    monkeypatch.setattr(current, 'Machine', create)
    monkeypatch.setattr(current.environment, 'provision', provision_refusal)
    monkeypatch.setattr(current.worker, 'collect', fail_if_native)
    monkeypatch.setattr(current.worker, 'verify', fail_if_native)
    report = current.admission_only_screen({'repo': 'fixture/wiring-only'}, tmp_path / 'case', 'a' * 64,
                                           catalog={}, runtimes={}, components=components())
    assert events == ['Machine', 'environment.provision']
    assert report['eligible'] is False
    assert report['status'].startswith('UNKNOWN')
    assert (tmp_path / 'case/SCREENING_CASE.json').is_file()
    assert created[0].state.is_relative_to(tmp_path / 'case')


def test_screening_components_come_from_exact_committed_authority_not_environment(tmp_path, monkeypatch):
    current = controller()
    pins = Path(__file__).with_name('developmental_sources.json')
    ticket = {'schema': AUTHORITY_SCHEMA, 'operation': 'screen', 'repo': str(Path(__file__).resolve().parents[2]),
              'machine_components': {'path': str(components()),
                                     'pins_sha256': hashlib.sha256(pins.read_bytes()).hexdigest()}}
    path = tmp_path / 'SCREENING_AUTHORITY.json'
    path.write_text(canonical(ticket) + '\n')
    descriptor = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    reads = []

    def committed(repo, record, *args, **kwargs):
        assert repo == ticket['repo'] and record == descriptor
        reads.append(record)
        return json.loads(path.read_text())

    monkeypatch.setattr(current, '_committed_record', committed)
    monkeypatch.setenv('UDM_COMPONENTS', str(tmp_path / 'untrusted-components-override'))
    assert current._screening_components(ticket, descriptor) == Path(ticket['machine_components']['path'])
    assert reads
    bad = copy.deepcopy(ticket)
    bad['machine_components']['pins_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        current._screening_components(bad, descriptor)
    old = copy.deepcopy(ticket)
    old['schema'] = 'UDM_NATIVE_CLI_AUTHORITY_V3'
    with pytest.raises(ValueError):
        current._screening_components(old, descriptor)

    def uncommitted(*args, **kwargs):
        raise ValueError('authority is not committed')

    monkeypatch.setattr(current, '_committed_record', uncommitted)
    with pytest.raises(ValueError, match='committed'):
        current._screening_components(ticket, descriptor)


@pytest.mark.parametrize('cached', (False, True))
def test_profile_witness_preflight_precedes_uncached_and_cached_receipt_use(cached, monkeypatch):
    current = controller()
    # This is deliberately not a receipt. Refusal must occur before any original
    # native record/receipt validation or cache result could be consumed.
    record = {'wiring_only': True}
    cache = {current.worker.fingerprint(record): 'UNTRUSTED_CACHE_SENTINEL'} if cached else {}
    marker = object()
    seen = []

    def withdrawn(actual_record, machine):
        assert actual_record is record and machine is marker
        seen.append('materialization-witness')
        raise PermissionError('withdrawn materialization witness')

    monkeypatch.setattr(current, '_preflight_record', withdrawn)
    monkeypatch.setattr(current.worker, 'validate_receipt', fail_if_native)
    with pytest.raises(PermissionError, match='withdrawn materialization'):
        current.checked_record(record, marker, cache=cache)
    assert seen == ['materialization-witness']


def test_agent_candidate_witness_preflight_precedes_direct_worker_calls(tmp_path, monkeypatch):
    current = controller()
    candidate = {'replacements': []}
    arm = {'schema': current.AGENT_SCHEMA, 'candidate_budget': 8, 'total_acquisition_native_calls': 512,
           'total_acquisition_wall_seconds': 3600, 'protocol_binding': 'b' * 64,
           'contract': {'protocol_binding': 'b' * 64}, 'common_acquisition_costs': [],
           'common_acquisition_wall_seconds': 0, 'meter_path': str(tmp_path / 'ARM_METER.json'),
           'candidate_catalog': [{'id': current.worker.fingerprint(candidate), 'candidate': candidate}]}
    seen = []

    def withdrawn(actual_arm):
        assert actual_arm is arm
        seen.append('materialization-witness')
        raise PermissionError('withdrawn materialization witness')

    monkeypatch.setattr(current, '_preflight_agent', withdrawn)
    monkeypatch.setattr(current.worker, 'verify', fail_if_native)
    monkeypatch.setattr(current.worker, 'validate_receipt', fail_if_native)
    with pytest.raises(PermissionError, match='withdrawn materialization'):
        current._execute_agent_candidate(arm, candidate, tmp_path / 'native-never-launched')
    assert seen == ['materialization-witness']


def test_original_pass_and_fail_admission_have_identical_fixed_order_eligibility():
    current = controller()
    pool = [{'repo': 'fixture/source-one'}, {'repo': 'fixture/source-two'}, {'repo': 'fixture/source-three'}]

    def select(statuses):
        reports = [{'repository': spec['repo'], 'spec_sha256': current.worker.fingerprint(spec),
                    'status': status, 'eligible': status in ('PASS_NATIVE', 'FAIL_NATIVE'),
                    'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
                   for spec, status in zip(pool, statuses)]
        return current.select_screened_roles(pool, reports, requested=2)

    pass_then_fail = select(('PASS_NATIVE', 'FAIL_NATIVE', 'PASS_NATIVE'))
    fail_then_pass = select(('FAIL_NATIVE', 'PASS_NATIVE', 'FAIL_NATIVE'))
    assert pass_then_fail == fail_then_pass
    assert [row['repo'] for row in pass_then_fail] == ['fixture/source-one', 'fixture/source-two']
    assert [row['role'] for row in pass_then_fail] == ['TRAINING', 'PROTECTED_FUTURE_1']
