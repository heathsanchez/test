"""New helper transport guards frozen before the V44 helpers are installed."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path

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

