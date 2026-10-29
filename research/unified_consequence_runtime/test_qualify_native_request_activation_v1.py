"""Pure qualification-boundary controls; manufactured rows grant no evidence."""
from __future__ import annotations

import copy
import hashlib
import importlib
from pathlib import Path
from types import FunctionType

import pytest

HERE = Path(__file__).resolve().parent


def qualifier():
    path = HERE/'qualify_native_request_activation_v1.py'
    assert path.is_file(), 'request activation qualifier is not implemented'
    return importlib.import_module('research.unified_consequence_runtime.qualify_native_request_activation_v1')


def record():
    return {'scope': 'NATIVE_REQUEST_ACTIVATION_QUALIFICATION_ONLY',
            'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
            'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)},
            'index_audit': {'changes': []},
            'native_attempts': {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY',
                                'delta': {'native_calls': 2, 'collection_calls': 2, 'subprocess_attempts': 4}},
            'compilation_attempts': {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY',
                                     'delta': {'compilation_calls': 2, 'compilation_seconds': 0.01}},
            'raw_native_audit': {'native_passes': 1, 'native_failures': 1, 'independent_replays': 1},
            'child_attempts': [],
            'known_attempt_totals': {'native_calls': 2, 'collection_calls': 2, 'subprocess_attempts': 4,
                                     'compilation_calls': 2, 'compilation_seconds': 0.01,
                                     'child_processes': 0, 'wall_intervals_additive': False}}


def test_every_fixed_baseline_blob_and_mode_must_survive():
    current = qualifier()
    before = {'core.py': {'mode': '100644', 'oid': 'a'*40},
              'old-report.json': {'mode': '100644', 'oid': 'b'*40}}
    after = {**copy.deepcopy(before), 'new.py': {'mode': '100644', 'oid': 'c'*40}}
    assert current._preserve_baseline(before, after) == 2


@pytest.mark.parametrize('mutation', ('missing', 'bytes', 'mode'))
def test_fixed_baseline_refuses_any_old_change(mutation):
    current = qualifier()
    before = {'core.py': {'mode': '100644', 'oid': 'a'*40}}
    after = copy.deepcopy(before)
    if mutation == 'missing':
        after.pop('core.py')
    else:
        after['core.py']['mode' if mutation == 'mode' else 'oid'] = '100755' if mutation == 'mode' else 'b'*40
    with pytest.raises(ValueError, match='baseline|preserv'):
        current._preserve_baseline(before, after)


def test_preimplementation_freeze_is_a_separate_preserved_baseline():
    assert qualifier().PREIMPLEMENTATION_BASE == '866a107d111e4b64f753d57323ed2a89098cd046'


def test_source_check_refuses_frozen_test_loss_even_if_old_native_base_survives(monkeypatch):
    current = qualifier()
    core = {'mode': '100644', 'oid': 'a'*40}
    frozen = {'mode': '100644', 'oid': 'b'*40}
    trees = {current.BASE: {'core.py': core},
             '866a107d111e4b64f753d57323ed2a89098cd046': {'core.py': core, 'frozen-control.py': frozen}}
    monkeypatch.setattr(current.previous, '_source', lambda repo: {
        'source_tree': {'core.py': core}, 'files': {name: 'c'*64 for name in current.GATE_FILES}})
    monkeypatch.setattr(current.original, '_tree', lambda repo, ref: trees[ref])
    monkeypatch.setattr(current, 'existing_gate', lambda: {})
    with pytest.raises(ValueError, match='baseline|preserv'):
        current._source(Path('/unused-source-free-fixture'))


def test_no_native_child_is_invented_for_in_process_controls(tmp_path):
    current = qualifier()
    assert current.child_attempts(tmp_path) == []
    current._validate_claims(record())


@pytest.mark.parametrize('mutation', ('scope', 'prospective', 'agent', 'G2', 'index', 'main-scope', 'additive', 'wrong-total'))
def test_qualification_cannot_promote_science_or_unchecked_costs(mutation):
    current = qualifier()
    value = record()
    if mutation == 'scope':
        value['scope'] = 'DEVELOPMENTAL_SUCCESS'
    elif mutation == 'prospective':
        value['prospective_task_sources_accessed'] = True
    elif mutation == 'agent':
        value['coding_agent_executed'] = True
    elif mutation == 'G2':
        value['verdicts']['G2'] = 'WARRANTED_BOUNDED'
    elif mutation == 'index':
        value['index_audit']['changes'] = ['changed']
    elif mutation == 'main-scope':
        value['native_attempts']['scope'] = 'ALL_PROCESSES'
    elif mutation == 'additive':
        value['known_attempt_totals']['wall_intervals_additive'] = True
    else:
        value['known_attempt_totals']['native_calls'] = 3
    with pytest.raises(ValueError):
        current._validate_claims(value)


@pytest.mark.parametrize('field', ('native_passes', 'native_failures', 'independent_replays'))
@pytest.mark.parametrize('bad', (0, True))
def test_actual_pass_failure_and_independent_replay_all_required(field, bad):
    current = qualifier()
    value = record()
    value['raw_native_audit'][field] = bad
    with pytest.raises(ValueError, match='native|replay|witness'):
        current._validate_claims(value)


def test_only_new_caller_controls_are_scheduled():
    current = qualifier()
    assert current._control_tests() == [
        'research/unified_consequence_runtime/test_native_request_activation_v1_revision2.py',
        'research/unified_consequence_runtime/test_qualify_native_request_activation_v1.py']
    assert current.BASE == 'cfab3f080cd199f367528e6631bcb93f3ebbc510'
    assert current.QUALIFIED == 'QUALIFIED_BOUNDED_REQUEST_ACTIVATION_ONLY'


def test_raw_native_checker_is_the_original_qualified_function():
    current = qualifier()
    previous = importlib.import_module('research.unified_consequence_runtime.qualify_native_namespace_v45')
    assert current.audit_native_packets is previous.audit_native_packets
    assert current.native_invocation_inventory is previous.native_invocation_inventory


def test_actual_existing_four_gate_receipt_stays_required():
    current = qualifier()
    gate = current.existing_gate()
    assert gate['namespace']['source_commit'] == '8ecdf15598a2e67d39acd7a5a0e0f7c201000bb7'
    assert gate['namespace']['run_id'] == 40783387334
    assert gate['namespace']['artifact_id'] == 12858458718


def test_revision2_seal_preserves_original_red_and_charges_known_prior_work():
    accepted = qualifier().sealed_controls()
    assert accepted['control_revision'] == 2
    assert accepted['original_request_controls']['seal_sha256'] == 'ea1de5102aa0654d714890def4abbd07b63146d2b5525347c60a0fc5060ee3ef'
    assert accepted['retained_previous_result'] == {'tests': 15, 'passed': 13, 'failures': 2,
        'corrected_fields_only': ['expected_collection_calls', 'expected_subprocess_attempts']}
    assert accepted['known_prior_engineering_invocations'] == {
        'native_calls': 4, 'collection_calls': 9, 'subprocess_attempts': 13}


def test_existing_independent_checker_accepts_truthful_physical_source(monkeypatch):
    """CI regression for the real pre-data checker-source RED, not a new theorem."""
    current = importlib.import_module('research.unified_consequence_runtime.qualify_native_frontier_request_v1')
    old = importlib.import_module('research.unified_consequence_runtime.qualify_native_frontier_v45')
    verifier = importlib.import_module('research.unified_consequence_runtime.native_meta_decision')
    # The formerly rebound code has the new module identity but another source
    # file. The unchanged independent checker must continue to reject that.
    bad = FunctionType(old.reconstruct_profiles.__code__, vars(current),
                       'reconstruct_profiles', old.reconstruct_profiles.__defaults__)
    bad.__kwdefaults__ = old.reconstruct_profiles.__kwdefaults__
    with monkeypatch.context() as temporary:
        temporary.setattr(current, 'reconstruct_profiles', bad)
        with pytest.raises(ValueError, match='source|import'):
            verifier._checker_source(bad)
    checked = verifier._checker_source(current.reconstruct_profiles)
    source = Path(current.__file__).resolve()
    assert checked == {'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                       'module': current.MODULE, 'name': 'reconstruct_profiles'}
    assert current._qualified_reconstruct_profiles.__code__ is old.reconstruct_profiles.__code__
    assert current._qualified_reconstruct_profiles.__defaults__ == old.reconstruct_profiles.__defaults__
    # Controller functions deliberately have a new private caller namespace;
    # their algorithm code/defaults/closure remain the original objects.
    assert current._reconstruct_profiles.__code__ is old._reconstruct_profiles.__code__
    assert current._reconstruct_profiles.__defaults__ == old._reconstruct_profiles.__defaults__
    assert current._reconstruct_profiles.__kwdefaults__ == old._reconstruct_profiles.__kwdefaults__
    assert current._reconstruct_profiles.__closure__ is old._reconstruct_profiles.__closure__
