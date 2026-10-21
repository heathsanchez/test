"""Additional pre-fix wiring controls; no double supplies a native verdict."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from .native_v43_test_support import implementation


def controller():
    return implementation('qualify_native_frontier_v43')


def producer_forbidden(*args, **kwargs):
    raise AssertionError('stale setup reached a public worker producer before preflight')


def test_explicit_setup_preflight_exists_before_runtime_construction():
    assert callable(getattr(controller(), '_preflight_setup', None)), 'live setup witness preflight is absent'


@pytest.mark.parametrize('boundary', ('collect', 'validate_certificate'))
def test_prepare_checks_live_setup_before_each_collection_operation(boundary, tmp_path, monkeypatch):
    current = controller()
    setup = {'status': 'PREPARED', 'contract': {'wiring_only': True}, 'authority': {}, 'policy': {}}
    machine = SimpleNamespace(costs=[])
    seen = []
    wanted = 1 if boundary == 'collect' else 2

    def preflight(actual_machine, actual_setup):
        assert actual_machine is machine and actual_setup is setup
        seen.append('preflight')
        if len(seen) == wanted:
            raise PermissionError('withdrawn exact setup witness')

    monkeypatch.setattr(current, '_preflight_setup', preflight, raising=False)
    monkeypatch.setattr(current, 'acquisition_budget', lambda *args, **kwargs: None)
    monkeypatch.setattr(current, '_bound_json', lambda value: {})
    monkeypatch.setattr(current.environment, 'provision', lambda *args, **kwargs: setup)
    if boundary == 'validate_certificate':
        # An opaque collection token is a wiring dependency, never a native
        # receipt or oracle. The independent validation boundary must refuse.
        monkeypatch.setattr(current.worker, 'collect', lambda *args, **kwargs: {'wiring_token': True, 'costs': {}})
    else:
        monkeypatch.setattr(current.worker, 'collect', producer_forbidden)
    monkeypatch.setattr(current.worker, 'validate_certificate', producer_forbidden)
    value = {'catalog': {}, '_runtime_inventory': {}, 'collection_seconds': 20, 'execution_seconds': 20}
    with pytest.raises(PermissionError, match='withdrawn exact setup witness'):
        current._prepare(machine, {'repo': 'fixture/wiring-only'}, tmp_path / 'prepare', 'a' * 64, value, {})
    assert len(seen) == wanted


@pytest.mark.parametrize('boundary', ('collect', 'validate_certificate'))
def test_screen_checks_live_setup_before_each_collection_operation(boundary, tmp_path, monkeypatch):
    current = controller()
    components = Path('/workspace/components')
    setup = {'status': 'PREPARED', 'contract': {'wiring_only': True}, 'authority': {}, 'policy': {}}
    seen = []
    wanted = 1 if boundary == 'collect' else 2

    def preflight(machine, actual_setup):
        assert actual_setup is setup
        seen.append('preflight')
        if len(seen) == wanted:
            raise PermissionError('withdrawn exact setup witness')

    monkeypatch.setattr(current, '_preflight_setup', preflight, raising=False)
    monkeypatch.setattr(current.environment, 'provision', lambda *args, **kwargs: setup)
    if boundary == 'validate_certificate':
        monkeypatch.setattr(current.worker, 'collect', lambda *args, **kwargs: {'wiring_token': True, 'costs': {}})
    else:
        monkeypatch.setattr(current.worker, 'collect', producer_forbidden)
    monkeypatch.setattr(current.worker, 'validate_certificate', producer_forbidden)
    result = current.admission_only_screen({'repo': 'fixture/wiring-only'}, tmp_path / 'screen', 'a' * 64,
                                         catalog={}, runtimes={}, components=components)
    assert len(seen) == wanted
    assert result['eligible'] is False
    assert result['status'].startswith('UNKNOWN')
    assert 'withdrawn exact setup witness' in result['reason']


def test_agent_rechecks_witness_before_independent_receipt_reexecution(tmp_path, monkeypatch):
    current = controller()
    candidate = {'replacements': []}
    arm = {'schema': current.AGENT_SCHEMA, 'candidate_budget': 8, 'total_acquisition_native_calls': 512,
           'total_acquisition_wall_seconds': 3600, 'protocol_binding': 'b' * 64,
           'contract': {'protocol_binding': 'b' * 64}, 'authority': {}, 'policy': {}, 'certificate': {},
           'common_acquisition_costs': [], 'common_acquisition_wall_seconds': 0,
           'meter_path': str(tmp_path / 'ARM_METER.json'),
           'candidate_catalog': [{'id': current.worker.fingerprint(candidate), 'candidate': candidate}]}
    seen = []

    def preflight(actual_arm):
        assert actual_arm is arm
        seen.append('preflight')
        if len(seen) == 2:
            raise PermissionError('witness withdrawn after producer before independent replay')

    monkeypatch.setattr(current, '_preflight_agent', preflight)
    # This opaque token has no status, assertion count, source identity or native
    # success. It reaches only the next preflight, which must reject it first.
    monkeypatch.setattr(current.worker, 'verify', lambda *args, **kwargs: {'wiring_token': True, 'costs': {'native_calls': 0}})
    monkeypatch.setattr(current.worker, 'validate_receipt', producer_forbidden)
    with pytest.raises(PermissionError, match='withdrawn after producer'):
        current._execute_agent_candidate(arm, candidate, tmp_path / 'native')
    assert len(seen) == 2
