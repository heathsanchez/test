"""New helper transport guards frozen before the V44 helpers are installed."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import FunctionType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parent
RECORDS = ROOT/'archaeology/native-bootstrap-v44/prospective'


def helper(name):
    path = RECORDS/name
    assert path.is_file(), 'V44 prospective helper is not implemented: '+name
    spec = importlib.util.spec_from_file_location('_v44_'+path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_new_curator_preserves_fixed_original_metadata_scanner():
    current = helper('curate_frontier.py')
    assert current.RECORDS == RECORDS
    assert current.SCHEMA == 'UDM_NATIVE_AUTHORITY_V44_METADATA_PREQUERY_V1'
    assert current.UNIVERSE == ()
    assert current.SCREENING_BUDGET['maximum_cases'] == 9
    assert current.METADATA_SECONDS == 900
    assert current._base_query.__code__.co_name == 'query'
    assert 'PREQUERY.json' in current.query.__code__.co_consts


def test_original_wrapper_alias_bug_is_not_reintroduced():
    current = helper('curate_frontier.py')
    # Source reconstruction must retrieve the actual definition name. A cloned
    # FunctionType alias need not be the key populated by exec(def ...).
    source = Path(current.__file__).read_text()
    assert 'function.__code__.co_name' in source


def test_records_assembly_binds_new_authority_and_separate_bootstrap_costs():
    current = helper('prepare_records.py')
    assert current.q.MODULE.endswith('qualify_native_frontier_v44')
    assert '_aggregate_bootstrap_costs' in current.finalize.__code__.co_names
    assert current.main.__globals__['prepare'] is current.prepare
    assert current.main.__globals__['finalize'] is current.finalize


def test_new_curator_requires_gate_before_target_universe_access(tmp_path, monkeypatch):
    current = helper('curate_frontier.py')
    wrapper = tmp_path/'WRAPPER.json'
    wrapper.write_text('{}')
    calls = []

    def unqualified(value):
        calls.append('gate')
        raise ValueError('unqualified new bootstrap gate')

    monkeypatch.setattr(current.q, 'require_environment_gate', unqualified)
    with pytest.raises(ValueError, match='unqualified new bootstrap'):
        current.configure_universe(tmp_path/'TARGETS_MUST_NOT_BE_READ.json', wrapper,
                                   tmp_path/'old.zip', tmp_path/'interface.zip', tmp_path/'bootstrap.zip')
    assert calls == ['gate']


def test_prior_exposure_covers_all_97_previous_identifiers():
    current = helper('curate_frontier.py')
    prior = current._exposure_record()
    assert len(prior['repositories']) >= 97
    for name in ('agronholm/typeguard', 'dabeaz/ply', 'facelessuser/wcmatch', 'uiri/toml', 'chardet/chardet'):
        assert name in prior['repositories']


def test_projection_changes_only_three_authority_schema_literals():
    current = helper('training_history_projection_v44.py')
    assert set(current.SCHEMA_BINDINGS.values()) == {
        'UDM_NATIVE_CLI_AUTHORITY_V44', 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V44', 'UDM_CODING_AGENT_NATIVE_ARM_V44'}
    assert hashlib.sha256(current.ORIGINAL_SOURCE.read_bytes()).hexdigest() == current.ORIGINAL_SOURCE_SHA256
    assert current.project.__code__.co_code == current._original.project.__code__.co_code


def test_actual_agent_watcher_keeps_native_execution_and_information_guards():
    path = RECORDS/'watch_actual_agent.py'
    assert path.is_file(), 'V44 actual-agent transport is not implemented'
    text = path.read_text()
    ast.parse(text)
    assert 'qualify_native_frontier_v44' in text
    assert 'UDM_CODING_AGENT_NATIVE_ARM_V44' in text
    assert 'actual_agent_executed' in text
    assert 'model_turn and native_calls > 0' in text
    assert 'Do not read RESULT.json' in text
    assert 'Do not fetch or query target metadata/source.' in text
    assert "['codex','exec'" in text


def alias_operation(value):
    return ('original', value)


def test_actual_aliased_source_binding_executes_the_new_definition():
    current = helper('curate_frontier.py')
    alias = FunctionType(alias_operation.__code__, globals(), 'renamed_operation')
    current.renamed_operation = alias
    changed = current._source_binding(alias, (("'original'", "'versioned'"),))
    assert changed(7) == ('versioned', 7)
    assert alias(7) == ('original', 7)


class PreApiBoundary(Exception):
    pass


def query_transport(current, tmp_path, monkeypatch):
    research = tmp_path/'repo/research/unified_consequence_runtime'
    records = research/'new-records'
    records.mkdir(parents=True)
    prepared = {'source_free_transport_only': True}
    plan = records/'PREQUERY.json'
    plan.write_text(json.dumps(prepared))
    wrapper = {'environment_gate': {'artifact_sha256': current.sha256(b'fixed-archive')},
               'catalog': {}, 'interface_gate': {}, 'interface_archive_audit': {},
               'bootstrap_gate': {}, 'bootstrap_archive_audit': {}}
    gate = records/'GATE_WRAPPER.json'
    gate.write_text(json.dumps(wrapper))
    archive = tmp_path/'qualified.zip'
    archive.write_bytes(b'fixed-archive')
    monkeypatch.setattr(current, 'RECORDS', records)
    monkeypatch.setattr(current, 'plan', lambda actual: prepared)
    monkeypatch.setattr(current, 'committed', lambda root, path: {
        'path': str(path), 'source_commit': 'a'*40, 'sha256': current._LOADED_SHA256})
    monkeypatch.setattr(current, 'subprocess', SimpleNamespace(check_output=lambda *args, **kwargs: b''))
    return research, records, plan, gate, archive, wrapper


def test_six_field_gate_reaches_independent_validation_before_any_api(tmp_path, monkeypatch):
    current = helper('curate_frontier.py')
    research, records, plan, gate, archive, wrapper = query_transport(current, tmp_path, monkeypatch)
    seen = []

    def boundary(actual):
        assert actual == wrapper
        seen.append('six-field-gate')
        raise PreApiBoundary('stopped before target access')

    monkeypatch.setattr(current.q, 'require_environment_gate', boundary)
    with pytest.raises(PreApiBoundary, match='before target access'):
        current.query(research, plan, gate, archive, records)
    assert seen == ['six-field-gate']
    assert not (records/'PREQUERY_EXECUTION.json').exists()


def test_first_query_receipt_cannot_be_replaced(tmp_path, monkeypatch):
    current = helper('curate_frontier.py')
    research, records, plan, gate, archive, _ = query_transport(current, tmp_path, monkeypatch)
    receipt = records/'PREQUERY_EXECUTION.json'
    receipt.write_bytes(b'original-source-free-receipt')
    with pytest.raises(ValueError, match='prior query receipt retained'):
        current.query(research, plan, gate, archive, records)
    assert receipt.read_bytes() == b'original-source-free-receipt'

