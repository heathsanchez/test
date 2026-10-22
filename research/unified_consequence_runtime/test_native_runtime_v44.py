"""Bootstrap dependency transport controls; no double supplies native evidence."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def implementation():
    assert Path(__file__).with_name('native_runtime_v44.py').is_file(), 'V44 native bootstrap transport is absent'
    return importlib.import_module('research.unified_consequence_runtime.native_runtime_v44')


def bare(module):
    runtime = object.__new__(module.NativeRuntimeV44)
    runtime.machine = object()
    runtime.contract = {'wiring_only': True}
    runtime.suite_authority = {}
    runtime.policy = {}
    runtime.certificate = {}
    runtime.materialization_binding = None
    runtime.materialization_capability = None
    runtime.bootstrap_binding = {'capability_id': 'bootstrap-cap', 'generation': 'generation',
        'consequence_id': 'exact-invocation', 'request_sha256': 'a'*64,
        'observation_sha256': 'b'*64, 'environment_selection_id': 'environment-selection'}
    return runtime


@pytest.mark.parametrize('operation', ('_scope', 'admit'))
def test_withdrawn_bootstrap_is_rejected_before_original_runtime_operation(operation, monkeypatch):
    module = implementation()
    runtime = bare(module)
    seen = []

    def withdrawn(machine, binding, contract, authority, policy):
        assert machine is runtime.machine and binding is runtime.bootstrap_binding
        assert contract is runtime.contract and authority is runtime.suite_authority and policy is runtime.policy
        seen.append('bootstrap')
        raise PermissionError('exact bootstrap invocation withdrawn')

    def original_forbidden(*args, **kwargs):
        raise AssertionError('withdrawn bootstrap reached original runtime')

    monkeypatch.setattr(module.environment, 'preflight_bootstrap', withdrawn)
    monkeypatch.setattr(module.previous.NativeRuntimeV43, operation, original_forbidden)
    with pytest.raises(PermissionError, match='bootstrap invocation withdrawn'):
        getattr(runtime, operation)(*({'replacements': []},) if operation == 'admit' else ())
    assert seen == ['bootstrap']


def test_original_materialization_and_bootstrap_premises_both_survive():
    module = implementation()
    runtime = bare(module)
    runtime.source, runtime.authority = 'source', 'authority'
    runtime.materialization_capability = 'materialization-cap'
    runtime.materialization_binding = {'consequence_id': 'materialization-invocation'}
    assert runtime._observation_premises() == (
        'source', 'authority', 'materialization-cap', 'materialization-invocation',
        'bootstrap-cap', 'exact-invocation', 'environment-selection')
    assert runtime._bootstrap_dependencies() == ('bootstrap-cap', 'exact-invocation', 'environment-selection')


def test_bootstrap_binding_is_persisted_as_exact_native_source_input():
    module = implementation()
    runtime = bare(module)
    assert runtime._inputs()['bootstrap_binding'] == runtime.bootstrap_binding
    runtime.bootstrap_binding = None
    assert 'bootstrap_binding' not in runtime._inputs()


def test_metadata_observation_without_selected_environment_cannot_create_native_source(monkeypatch, tmp_path):
    module = implementation()
    binding = bare(module).bootstrap_binding
    binding.pop('environment_selection_id')

    def forbidden(*args, **kwargs):
        raise AssertionError('unbound observation reached native source construction')

    monkeypatch.setattr(module.previous.NativeRuntimeV43, '__init__', forbidden)
    with pytest.raises(ValueError, match='exact environment selection witness'):
        module.NativeRuntimeV44(object(), {}, {}, {}, {}, tmp_path/'never-created', bootstrap_binding=binding)
    assert not (tmp_path/'never-created').exists()

