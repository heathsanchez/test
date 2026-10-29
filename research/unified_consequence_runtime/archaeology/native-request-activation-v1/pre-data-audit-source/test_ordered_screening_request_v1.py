"""Source-free original-factory and external-budget controls; no native launch."""
import ast
import importlib.util
import json
import math
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def module():
    path = HERE/'ordered_screening_request_v1.py'
    assert path.is_file(), 'versioned request ordered transport missing'
    spec = importlib.util.spec_from_file_location('request_ordered_transport', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_reuses_exact_original_factory_with_only_native_command_module_change():
    value = module()
    original = value.original_factory().prepare_driver_source()
    current = value.prepare_driver_source()
    before = 'research.unified_consequence_runtime.qualify_native_frontier_v45'
    after = 'research.unified_consequence_runtime.qualify_native_frontier_request_v1'
    assert original.count(before) == 1
    assert current == original.replace(before, after)
    assert 'UDM_V45_SCREENING_OPERATOR_PROCESS_COSTS_V1' in current
    assert 'UDM_V45_SCREENING_ACTOR_ATTESTATION_V1' in current
    assert "os.environ['UDM_SCREENING_ACTOR_IDENTITY']" in current


@pytest.mark.parametrize('size,refuse', [(0, True), (1, False), (4, False), (9, False), (10, True)])
def test_preserves_complete_fixed_pool_bounds(size, refuse):
    tree = ast.parse(module().prepare_driver_source())
    conditions = [node.test for node in tree.body if isinstance(node, ast.If)
        and 'len(pool)' in ast.unparse(node.test) and 'len(requests)' in ast.unparse(node.test)]
    assert len(conditions) == 1
    assert eval(compile(ast.Expression(conditions[0]), '<original-pool-bound>', 'eval'),
                {'len': len, 'pool': [None]*size, 'requests': [None]*size}) is refuse


def test_original_prior_outer_bytes_and_charged_remaining_horizon_are_bound():
    value = module()
    prior = value.prior_outer_cost()
    assert prior['sha256'] == '6e0104a9c1cb91078a189b349694496038f9ae21003ec883e13decc4bd7b95d1'
    assert prior['observed_outer_wall_seconds'] == 25.756850842999484
    assert prior['charged_outer_wall_seconds'] == 25.756850843
    assert value.remaining_seconds(0.0) == 7174.243149157
    assert math.isclose(value.remaining_seconds(10.5), 7163.743149157, abs_tol=1e-10)


@pytest.mark.parametrize('elapsed', [True, -1.0, float('nan'), float('inf'), '0'])
def test_invalid_outer_elapsed_is_not_a_valid_budget(elapsed):
    with pytest.raises(ValueError):
        module().remaining_seconds(elapsed)


def test_exhausted_prior_plus_outer_budget_refuses_further_child_time():
    value = module()
    assert value.remaining_seconds(7174.243149157) == 0.0
    assert value.remaining_seconds(7200.0) == 0.0


@pytest.mark.parametrize('changes', [
    {'returncode': 1}, {'timed_out': True}, {'process_completed': False},
    {'new_outer_wall_seconds': 7174.243149158}, {'returncode': None},
    {'returncode': False}, {'process_completed': 1},
])
def test_no_budget_qualification_for_failure_timeout_incomplete_or_overrun(changes):
    value = module()
    inputs = {'new_outer_wall_seconds': 10.0, 'returncode': 0,
              'timed_out': False, 'process_completed': True}
    inputs.update(changes)
    result = value.budget_result(**inputs)
    assert result['qualified'] is False
    assert result['status'].startswith('UNKNOWN_')


def test_completed_interval_charges_prior_and_new_without_adding_nested_clocks():
    result = module().budget_result(new_outer_wall_seconds=10.0, returncode=0,
                                   timed_out=False, process_completed=True)
    assert result['qualified'] is True
    assert result['combined_outer_wall_seconds'] == 35.756850843
    assert result['nested_intervals_not_additive'] is True
    assert result['total_budget_seconds'] == 7200.0
    assert result['scope'] == 'OUTER_TRANSPORT_COMPLETION_AND_COST_ONLY'


def test_wrong_records_version_and_missing_actor_fail_before_original_execution():
    value = module()
    env = {'UDM_REPO': '/workspace/udm-v54',
           'UDM_RECORDS': '/workspace/udm-v54/research/unified_consequence_runtime/archaeology/native-request-activation-v1/prospective',
           'UDM_OPERATOR': '/workspace/qualification/never-executed-request-fixture',
           'UDM_CONTROLLER_PYTHON': '/fixture/python', 'UDM_RUNTIME_PATHS': '/fixture/runtimes.json',
           'UDM_SCREENING_SOURCE_COMMIT': 'a'*40, 'UDM_PREQUERY_COMMIT': 'b'*40,
           'UDM_SCREENING_AUTHORITY_SHA256': 'c'*64, 'UDM_SCREENING_ACTOR_IDENTITY': 'independent fixture actor'}
    assert value.validate_settings(env)['UDM_SCREENING_SOURCE_COMMIT'] == 'a'*40
    for key, replacement in [('UDM_RECORDS', '/wrong/prospective'),
                             ('UDM_SCREENING_ACTOR_IDENTITY', ''),
                             ('UDM_SCREENING_SOURCE_COMMIT', 'not-a-pin')]:
        changed = {**env, key: replacement}
        with pytest.raises(ValueError):
            value.validate_settings(changed)


@pytest.mark.parametrize('change', ['schema', 'actor', 'prequery', 'source', 'authority', 'independence'])
def test_incorrect_original_completion_metadata_cannot_claim_completed_transport(tmp_path, change):
    value = module()
    env = {'UDM_SCREENING_SOURCE_COMMIT': 'a'*40, 'UDM_PREQUERY_COMMIT': 'b'*40,
           'UDM_SCREENING_AUTHORITY_SHA256': 'c'*64, 'UDM_SCREENING_ACTOR_IDENTITY': 'independent fixture actor'}
    manifest = {'schema': 'UDM_V45_SCREENING_OPERATOR_PROCESS_COSTS_V1', 'completed': True,
                'retries_performed': False, 'no_retry_or_substitution': True,
                'source_commit': env['UDM_SCREENING_SOURCE_COMMIT'], 'authority_sha256': env['UDM_SCREENING_AUTHORITY_SHA256']}
    path = tmp_path/'ORDERED_PROCESS_COSTS.json'
    path.write_text(json.dumps(manifest))
    actor = {'schema': 'UDM_V45_SCREENING_ACTOR_ATTESTATION_V1', 'completed_fixed_pool': True,
             'source_unchanged': True, 'index_changes': [], 'actor_identity': env['UDM_SCREENING_ACTOR_IDENTITY'],
             'controller_manifest_sha256': value.sha(path),
             'source_commit': env['UDM_SCREENING_SOURCE_COMMIT'], 'prequery_commit': env['UDM_PREQUERY_COMMIT'],
             'authority_sha256': env['UDM_SCREENING_AUTHORITY_SHA256'], 'independent_screener': True,
             'search_or_policy_outcomes_accessed': False, 'learner_future_source_accessed': False,
             'native_test_reruns_or_case_retries_performed': False}
    actor_path = tmp_path/'SCREENING_ACTOR_ATTESTATION.json'
    actor_path.write_text(json.dumps(actor))
    assert value.completed_process_metadata(tmp_path, env)[0] is True
    if change == 'schema':
        actor['schema'] = 'untrusted'
    elif change == 'actor':
        actor['actor_identity'] = 'another actor'
    elif change == 'prequery':
        actor['prequery_commit'] = 'd'*40
    elif change == 'source':
        actor['source_commit'] = 'd'*40
    elif change == 'authority':
        actor['authority_sha256'] = 'd'*64
    else:
        actor['independent_screener'] = False
    actor_path.write_text(json.dumps(actor))
    assert value.completed_process_metadata(tmp_path, env)[0] is False


def test_live_child_is_stopped_on_any_parent_exit_without_launching_native_code(monkeypatch):
    value = module()
    calls = []
    class Child:
        pid = 1234567
        def poll(self): return None
        def wait(self): calls.append('wait'); return -9
    monkeypatch.setattr(value.os, 'killpg', lambda pid, sig: calls.append((pid, sig)))
    assert value.stop_child(Child()) == -9
    assert calls == [(1234567, value.signal.SIGKILL), 'wait']


def test_linux_kernel_birth_clock_includes_interpreter_startup_without_native_launch():
    value = module()
    # Fields after the last ')' begin at state(field3); field22 is index19.
    raw = '7 (name with ) parenthesis) S '+' '.join(['0']*18+['12345']+['0']*5)
    clock = value.process_clock(raw=raw, clock_ticks=100)
    assert clock['process_start_lower_bound_seconds'] == 123.45
    assert clock['process_start_ticks'] == 12345
    assert value.outer_elapsed(clock, now=124.0) == 0.55
