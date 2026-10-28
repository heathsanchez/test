"""Source-free V45 scientific-carrier controls; no task or native verdicts."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from types import CodeType, FunctionType, SimpleNamespace
import unittest

import pytest

HERE = Path(__file__).resolve().parent


def controller():
    assert (HERE/'qualify_native_frontier_v45.py').is_file(), 'V45 scientific carrier is missing'
    return importlib.import_module('research.unified_consequence_runtime.qualify_native_frontier_v45')


def helper(name):
    path = HERE/'archaeology/native-namespace-v45/prospective'/name
    assert path.is_file(), 'V45 prospective helper is missing: '+name
    spec = importlib.util.spec_from_file_location('_test_v45_'+path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_original_algorithms_and_budgets_use_only_v45_native_transport():
    current = controller()
    previous = importlib.import_module('research.unified_consequence_runtime.qualify_native_frontier_v44')
    native = importlib.import_module('research.unified_consequence_runtime.native_execution_v45')
    environment = importlib.import_module('research.unified_consequence_runtime.native_environment_v45')
    machine = importlib.import_module('research.unified_consequence_runtime.developmental_machine_v44').Machine
    assert current.worker is native and current.environment is environment and current.Machine is machine
    assert current.AUTHORITY_SCHEMA == 'UDM_NATIVE_CLI_AUTHORITY_V45'
    assert current.AGENT_SCHEMA == 'UDM_CODING_AGENT_NATIVE_ARM_V45'
    assert current.DEFAULTS['schema'] == 'UDM_NATIVE_FRONTIER_PROTOCOL_V45'
    for key in ('search_budget', 'candidate_cap_per_file', 'acquisition_native_calls',
                'training_seconds', 'requested_roles', 'training_unique_calls'):
        assert current.DEFAULTS[key] == previous.DEFAULTS[key]
    assert current.orders.__code__ is previous.orders.__code__
    assert current.select_screened_roles.__code__ is previous.select_screened_roles.__code__
    bound = current.isolated_binding('search')
    assert bound.__code__ is previous.isolated_binding('search').__code__
    assert bound.__globals__['worker'] is native
    assert bound.__globals__['native_probe'] is current.native_probe
    assert current._prepare.__code__.co_names.count('native_runtime_v45') == 1
    assert current._prepare.__code__.co_names.count('NativeRuntimeV45') == 1
    assert current.RECORDS == HERE/'archaeology/native-namespace-v45/prospective'


def test_namespace_gate_is_added_after_all_preserved_gates(monkeypatch):
    current = controller()
    seen = []
    monkeypatch.setattr(current, '_guard', lambda: None)
    monkeypatch.setattr(current._previous_controller, 'require_environment_gate',
                        lambda value: seen.append('all-v44-gates') or {'old': 'preserved'})
    for key in ('environment_gate', 'interface_gate', 'interface_archive_audit',
                'bootstrap_gate', 'bootstrap_archive_audit', 'namespace_gate', 'namespace_archive_audit'):
        assert key in current.DEFAULTS
    with pytest.raises(ValueError, match='namespace'):
        current.require_environment_gate({})
    assert seen == ['all-v44-gates']


def _json(path, value, root):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode()
    path.write_bytes(raw)
    return {'path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()}


@pytest.fixture
def gate_fixture(tmp_path, monkeypatch):
    """Synthetic parser inputs retained under explicit non-native filenames."""
    current = controller()
    qualifier = importlib.import_module('research.unified_consequence_runtime.qualify_native_namespace_v45')
    root = tmp_path/'source-free-gate'
    here = root/'research/unified_consequence_runtime'
    here.mkdir(parents=True)
    monkeypatch.setattr(current, 'HERE', here)
    monkeypatch.setattr(current, '_guard', lambda: None)
    monkeypatch.setattr(current._previous_controller, 'require_environment_gate', lambda value: {'old': 'preserved'})
    files = {}
    for name in qualifier.GATE_FILES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = ('source-free gate fixture: '+name+'\n').encode()
        path.write_bytes(raw)
        files[name] = hashlib.sha256(raw).hexdigest()
    raw_audit = {'schema': 'UDM_V45_RAW_NATIVE_PACKET_AUDIT', 'status': 'PASS_BOUNDED_RAW_NATIVE_PACKETS',
                 'native_passes': 1, 'native_failures': 1, 'independent_replays': 1,
                 'certificates': 1,
                 'receipts': [{'path': 'synthetic/pass', 'invocation_path': 'synthetic/pass/execution',
                               'schema': 'UDM_GENERIC_NATIVE_PYTEST_V45', 'role': 'receipt', 'status': 'PASS_NATIVE',
                               'junit': {'tests': 1, 'passed': 1, 'failures': 0, 'errors': 0, 'skipped': 0}},
                              {'path': 'synthetic/fail', 'invocation_path': 'synthetic/fail/execution',
                               'schema': 'UDM_GENERIC_NATIVE_PYTEST_V45', 'role': 'independent_reexecution', 'status': 'FAIL_NATIVE',
                               'junit': {'tests': 1, 'passed': 0, 'failures': 1, 'errors': 0, 'skipped': 0}}],
                 'manifest_paths': ['synthetic/NATIVE_EVIDENCE.json']}
    nodes = ['research/unified_consequence_runtime/'+name+'::synthetic_parser_control'
             for name in ('test_native_admission_v45.py', 'test_native_execution_v45.py',
                          'test_native_runtime_v45.py', 'test_qualify_native_frontier_v45.py')]
    result = {'schema': 'UDM_NATIVE_NAMESPACE_QUALIFICATION_V45',
              'status': 'QUALIFIED_BOUNDED_NATIVE_NAMESPACE_ADMISSION_ONLY', 'source_commit': 'a'*40,
              'freeze': {'schema': 'UDM_NATIVE_NAMESPACE_FREEZE_V45', 'source_commit': 'a'*40,
                         'catalog_sha256': 'b'*64, 'files': files},
              'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)},
              'contracts': {'junit': {'tests': 4, 'failures': 0, 'errors': 0, 'skipped': 0}, 'collection': nodes},
              'raw_native_audit': raw_audit,
              'scope': 'NATIVE_NAMESPACE_ADMISSION_INFRASTRUCTURE_ONLY',
              'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
              'index_audit': {'changes': []},
              'native_attempts': {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY',
                                  'delta': {'native_calls': 2, 'collection_calls': 2, 'subprocess_attempts': 4}},
              'compilation_attempts': {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY',
                                       'delta': {'compilation_calls': 2, 'compilation_seconds': 0.02}}}
    child_native = {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2}
    child_compile = {'compilation_calls': 1, 'compilation_seconds': 0.01}
    child = {'schema': 'UDM_NATIVE_V45_CHILD_ATTEMPTS', 'status': 'PASS_NATIVE',
             'native_attempts': {'before': {key: 0 for key in child_native},
                                 'after': child_native, 'delta': child_native},
             'compilation_attempts': {'before': {'compilation_calls': 0, 'compilation_seconds': 0, 'records': []},
                                      'after': {**child_compile, 'records': [{'compilation_calls': 1}]},
                                      'delta': child_compile},
             'native_run_outputs': ['synthetic/child/restart/native-run']}
    descriptor = _json(root/'fixture/child/CHILD_NATIVE_ATTEMPTS.PARSER_FIXTURE.json', child, root)
    result['child_attempts'] = [{**descriptor, 'summary': child,
        'stdout': _json(root/'fixture/child/RESTART_STDOUT.log',
                        {'status': 'PASS_NATIVE', 'native_calls': 1, 'attempts': child}, root),
        'stderr': _json(root/'fixture/child/RESTART_STDERR.log', {}, root),
        'native_outputs': [_json(root/'fixture/child/restart/native-run/receipt.PARSER_FIXTURE.json',
            {'schema': 'UDM_GENERIC_NATIVE_PYTEST_V45', 'status': 'PASS_NATIVE'}, root)]}]
    result['known_attempt_totals'] = {'native_calls': 3, 'collection_calls': 3, 'subprocess_attempts': 6,
        'compilation_calls': 3, 'compilation_seconds': 0.03, 'child_processes': 1,
        'wall_intervals_additive': False, 'boundary': 'Synthetic main plus separately retained child intervals.'}
    result_path = root/'fixture/RESULT.json'
    result_descriptor = _json(result_path, result, root)
    gate = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': 'a'*40, 'run_id': 1, 'artifact_id': 2,
            'artifact_sha256': 'c'*64, 'qualification_result_sha256': result_descriptor['sha256'],
            'result_path': result_descriptor['path']}
    audit = {'schema': 'UDM_V45_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT',
             'status': 'PASS_INDEPENDENT_NATIVE_NAMESPACE_ARCHIVE_AUDIT',
             'namespace_gate': gate, 'gate_files_sha256': files, 'all_native_packets_checked': True,
             'raw_native_audit': _json(root/'fixture/RAW_NATIVE_AUDIT.json', raw_audit, root)}
    wrapper = {'catalog': {'path': 'fixture/catalog.json', 'sha256': 'b'*64},
               'namespace_gate': gate, 'namespace_archive_audit': _json(root/'fixture/INDEPENDENT.json', audit, root)}

    def reseal():
        descriptor = _json(result_path, result, root)
        gate['qualification_result_sha256'] = descriptor['sha256']
        audit['namespace_gate'] = copy.deepcopy(gate)
        audit['raw_native_audit'] = _json(root/'fixture/RAW_NATIVE_AUDIT.json', result['raw_native_audit'], root)
        wrapper['namespace_archive_audit'] = _json(root/'fixture/INDEPENDENT.json', audit, root)

    return current, root, wrapper, result, audit, reseal


def test_namespace_parser_accepts_complete_source_free_bound_inputs(gate_fixture):
    current, _, wrapper, _, _, _ = gate_fixture
    checked = current.require_environment_gate(wrapper)
    assert checked['namespace'] == wrapper['namespace_gate']
    assert checked['independent_namespace_audit'] == wrapper['namespace_archive_audit']
    assert checked['old'] == 'preserved'


def test_source_free_gate_inputs_cannot_publish_native_evidence(gate_fixture):
    """Parser fixtures remain retained data, outside actual native discovery."""
    current, root, wrapper, result, _, _ = gate_fixture
    qualifier = importlib.import_module('research.unified_consequence_runtime.qualify_native_namespace_v45')
    for name in ('receipt.json', 'admission-certificate.json', 'CHILD_NATIVE_ATTEMPTS.json',
                 'V45_NATIVE_EVIDENCE.json', 'checked-report.json'):
        assert list(qualifier._retained_files(root, name)) == [], name
    assert qualifier.native_invocation_inventory(root)['invocations'] == []
    assert qualifier.child_attempts(root, required=False) == []
    child = result['child_attempts'][0]
    assert json.loads((root/child['path']).read_text()) == child['summary']
    receipt = child['native_outputs'][0]
    assert json.loads((root/receipt['path']).read_text()) == {
        'schema': 'UDM_GENERIC_NATIVE_PYTEST_V45', 'status': 'PASS_NATIVE'}
    assert current.require_environment_gate(wrapper)['namespace'] == wrapper['namespace_gate']


def test_namespace_gate_counts_unique_v45_invocations_and_retains_original_versions(gate_fixture):
    current, _, wrapper, result, _, reseal = gate_fixture
    receipts = result['raw_native_audit']['receipts']
    for version, status in (('V2', 'PASS_NATIVE'), ('V42', 'FAIL_NATIVE'), ('V43', 'PASS_NATIVE')):
        origin = receipts[0 if status == 'PASS_NATIVE' else 1]
        receipts.append({**copy.deepcopy(origin), 'schema': 'UDM_GENERIC_NATIVE_PYTEST_'+version,
                         'path': 'synthetic/'+version+'/receipt.json',
                         'invocation_path': 'synthetic/'+version+'/execution', 'role': 'retained_receipt'})
    receipts.append({'schema': 'UDM_GENERIC_NATIVE_PYTEST_V43', 'path': 'synthetic/unknown/receipt.json',
                     'invocation_path': 'synthetic/unknown/execution', 'role': 'retained_receipt',
                     'status': 'UNKNOWN_SKIPPED_OR_XFAIL',
                     'junit': {'tests': 1, 'passed': 0, 'failures': 0, 'errors': 0, 'skipped': 1}})
    reseal()
    assert current.require_environment_gate(wrapper)['namespace'] == wrapper['namespace_gate']
    assert len(result['raw_native_audit']['receipts']) == 6
    assert result['raw_native_audit']['native_passes'] == 1
    assert result['raw_native_audit']['native_failures'] == 1
    assert result['raw_native_audit']['independent_replays'] == 1


@pytest.mark.parametrize('mutation', ('legacy-only', 'duplicate-invocation', 'missing-invocation'))
def test_namespace_gate_cannot_replace_or_duplicate_v45_actual_invocations(gate_fixture, mutation):
    current, _, wrapper, result, _, reseal = gate_fixture
    raw = result['raw_native_audit']
    if mutation == 'legacy-only':
        for row in raw['receipts']:
            row['schema'] = 'UDM_GENERIC_NATIVE_PYTEST_V43'
    elif mutation == 'duplicate-invocation':
        raw['receipts'].append({**copy.deepcopy(raw['receipts'][0]), 'path': 'synthetic/alias/receipt.json'})
        raw['native_passes'] = 2
    else:
        raw['receipts'][0].pop('invocation_path')
    reseal()
    with pytest.raises(ValueError):
        current.require_environment_gate(wrapper)


@pytest.mark.parametrize('mutation', ('missing-child', 'missing-child-digest', 'zero-child-native',
                                    'boolean-child-compiler', 'wrong-known-total', 'additive-wall', 'unscoped-main'))
def test_namespace_gate_requires_separate_authenticated_child_costs(gate_fixture, mutation):
    current, _, wrapper, result, _, reseal = gate_fixture
    if mutation == 'missing-child':
        result.pop('child_attempts')
    elif mutation == 'missing-child-digest':
        result['child_attempts'][0].pop('sha256')
    elif mutation == 'zero-child-native':
        result['child_attempts'][0]['summary']['native_attempts']['delta']['native_calls'] = 0
    elif mutation == 'boolean-child-compiler':
        result['child_attempts'][0]['summary']['compilation_attempts']['delta']['compilation_calls'] = True
    elif mutation == 'wrong-known-total':
        result['known_attempt_totals']['native_calls'] = 2
    elif mutation == 'additive-wall':
        result['known_attempt_totals']['wall_intervals_additive'] = True
    else:
        result['native_attempts'].pop('scope')
    reseal()
    with pytest.raises(ValueError):
        current.require_environment_gate(wrapper)


@pytest.mark.parametrize('mutation', ('missing-audit', 'unchecked-packets', 'wrong-run', 'wrong-artifact',
                                    'wrong-source', 'missing-evidence', 'changed-evidence', 'resealed-foreign-evidence',
                                    'stale-source', 'missing-control', 'nonzero-errors', 'nonzero-skips',
                                    'zero-native-pass', 'zero-native-fail', 'zero-replay', 'promoted-g2',
                                    'zero-native-calls', 'boolean-compilation-calls', 'forged-pass-count',
                                    'forged-fail-junit', 'missing-replay-receipt'))
def test_namespace_gate_rejects_self_report_and_resealed_foreign_evidence(gate_fixture, mutation):
    current, root, wrapper, result, audit, reseal = gate_fixture
    if mutation == 'missing-audit':
        wrapper.pop('namespace_archive_audit')
    elif mutation == 'unchecked-packets':
        audit['all_native_packets_checked'] = False
    elif mutation in ('wrong-run', 'wrong-artifact', 'wrong-source'):
        audit['namespace_gate'] = {**wrapper['namespace_gate'],
            {'wrong-run': 'run_id', 'wrong-artifact': 'artifact_sha256', 'wrong-source': 'source_commit'}[mutation]:
            99 if mutation == 'wrong-run' else 'd'*(64 if mutation == 'wrong-artifact' else 40)}
    elif mutation == 'missing-evidence':
        audit.pop('raw_native_audit')
    elif mutation in ('changed-evidence', 'resealed-foreign-evidence'):
        path = root/audit['raw_native_audit']['path']
        foreign = {**result['raw_native_audit'], 'manifest_paths': ['foreign-task/NATIVE_EVIDENCE.json']}
        descriptor = _json(path, foreign, root)
        if mutation == 'resealed-foreign-evidence':
            audit['raw_native_audit'] = descriptor
    elif mutation == 'stale-source':
        (root/next(iter(result['freeze']['files']))).write_bytes(b'changed current source\n')
    else:
        if mutation == 'missing-control':
            result['contracts']['collection'] = result['contracts']['collection'][:-1]
        elif mutation in ('nonzero-errors', 'nonzero-skips'):
            result['contracts']['junit']['errors' if mutation == 'nonzero-errors' else 'skipped'] = 1
        elif mutation == 'zero-native-calls':
            result['native_attempts']['delta']['native_calls'] = 0
        elif mutation == 'boolean-compilation-calls':
            result['compilation_attempts']['delta']['compilation_calls'] = True
        elif mutation == 'forged-pass-count':
            result['raw_native_audit']['native_passes'] = 5
        elif mutation == 'forged-fail-junit':
            result['raw_native_audit']['receipts'][1]['junit']['failures'] = 0
        elif mutation == 'missing-replay-receipt':
            result['raw_native_audit']['receipts'][1]['role'] = 'receipt'
        elif mutation.startswith('zero-'):
            key = {'zero-native-pass': 'native_passes', 'zero-native-fail': 'native_failures', 'zero-replay': 'independent_replays'}[mutation]
            result['raw_native_audit'][key] = 0
        elif mutation == 'promoted-g2':
            result['verdicts']['G2'] = 'PASS'
        reseal()
    if mutation not in ('missing-audit', 'wrong-run', 'wrong-artifact', 'wrong-source'):
        wrapper['namespace_archive_audit'] = _json(root/'fixture/INDEPENDENT.json', audit, root)
    elif mutation != 'missing-audit':
        wrapper['namespace_archive_audit'] = _json(root/'fixture/INDEPENDENT.json', audit, root)
    with pytest.raises(ValueError):
        current.require_environment_gate(wrapper)


def test_equal_native_pass_fail_eligibility_keeps_original_pool_order():
    current = controller()
    pool = [{'repo': 'fixture/a'}, {'repo': 'fixture/b'}, {'repo': 'fixture/c'}]
    def selected(statuses):
        reports = [{'repository': spec['repo'], 'spec_sha256': current.worker.fingerprint(spec),
                    'status': status, 'eligible': status in ('PASS_NATIVE', 'FAIL_NATIVE'),
                    'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
                   for spec, status in zip(pool, statuses)]
        return current.select_screened_roles(pool, reports, requested=2)
    expected = [{'repo': 'fixture/a', 'role': 'TRAINING'},
                {'repo': 'fixture/b', 'role': 'PROTECTED_FUTURE_1'}]
    assert selected(['PASS_NATIVE', 'FAIL_NATIVE', 'UNKNOWN']) == expected
    assert selected(['FAIL_NATIVE', 'PASS_NATIVE', 'UNKNOWN']) == expected


def test_curator_import_has_no_universe_and_preserves_full_latest_exposure_union():
    curator = helper('curate_frontier.py')
    assert curator.UNIVERSE == () and curator._qualification_binding is None
    exposed = curator._exposure_record()
    assert exposed['repository_count'] == 106 and len(exposed['repositories']) == 106
    latest = 'archaeology/native-bootstrap-v44/prospective-result/PROSPECTIVE_EXPOSURE_ADDENDUM.json'
    assert latest in exposed['input_files_sha256']
    touched, _ = curator.exclusions(curator.q.HERE, curator.original(curator.q.HERE))
    assert set(exposed['repositories']) <= set(touched)
    previous = curator._carrier
    assert curator.filter_existing_production.__code__ is previous.filter_existing_production.__code__
    assert curator.metadata_api.__code__ is previous.metadata_api.__code__


def test_curator_requires_four_artifacts_before_reading_universe(tmp_path, monkeypatch):
    curator = helper('curate_frontier.py')
    seen = []
    def refused(wrapper):
        seen.append('qualified-chain')
        raise PermissionError('qualification not yet independently archived')
    monkeypatch.setattr(curator.q, 'require_environment_gate', refused)
    gate = tmp_path/'gate.json'; gate.write_text('{}\n')
    with pytest.raises(PermissionError, match='not yet independently archived'):
        curator.configure_universe(tmp_path/'must-not-be-read.json', gate,
                                   tmp_path/'environment.zip', tmp_path/'interface.zip',
                                   tmp_path/'bootstrap.zip', tmp_path/'namespace.zip')
    assert seen == ['qualified-chain'] and curator.UNIVERSE == ()


def test_actual_agent_requires_real_model_turn_and_new_native_meter_calls():
    watcher = helper('watch_actual_agent.py')
    before = {'attempts': [], 'arm_sha256': 'a'*64, 'started_at_unix': 1}
    after = {**before, 'attempts': [{'controller_attempts': {'native_calls': 1}}]}
    model = [{'type': 'turn.completed', 'usage': {'output_tokens': 2}}]
    assert watcher._execution_telemetry(model, before, after, True)['actual_agent_executed'] is True
    assert watcher._execution_telemetry(model, before, before, True)['actual_agent_executed'] is False
    assert watcher._execution_telemetry([], before, after, True)['actual_agent_executed'] is False
    assert watcher._execution_telemetry(model, before, after, False)['actual_agent_executed'] is False


def test_generated_preflight_enters_v45_live_materialization_boundary(tmp_path, monkeypatch):
    current = controller()
    def withdrawn(self, capability):
        assert capability == 'source-free-materialization'
        raise PermissionError('V45 live materialization boundary')
    monkeypatch.setattr(current.environment.MaterializationRuntime, '_validated', withdrawn)
    setup = {'status': 'PREPARED', 'contract': {'schema': current.worker.SCHEMA, 'generated_build': {}},
             'authority': {}, 'policy': {}, 'materialization_capability': 'source-free-materialization',
             'materialization_binding': {}}
    machine = SimpleNamespace(state=tmp_path/'state')
    with pytest.raises(PermissionError, match='V45 live materialization boundary'):
        current._preflight_setup(machine, setup)


@pytest.mark.parametrize('bad_archive', ('environment_gate', 'interface_gate', 'bootstrap_gate', 'namespace_gate'))
def test_each_qualification_archive_digest_precedes_universe_read(tmp_path, monkeypatch, bad_archive):
    curator = helper('curate_frontier.py')
    monkeypatch.setattr(curator.q, 'require_environment_gate', lambda wrapper: {'source-free': True})
    wrapper = {'catalog': {'path': 'synthetic/catalog.json', 'sha256': 'a'*64},
               **{key: {} for key in curator.q.GATE_KEYS}}
    archives = []
    for key in ('environment_gate', 'interface_gate', 'bootstrap_gate', 'namespace_gate'):
        path = tmp_path/(key+'.zip')
        raw = ('synthetic archived bytes '+key).encode()
        path.write_bytes(raw)
        archives.append(path)
        wrapper[key]['artifact_sha256'] = hashlib.sha256(raw).hexdigest()
        if key == bad_archive:
            path.write_bytes(b'changed archive bytes')
    gate = tmp_path/'GATES.json'; gate.write_text(json.dumps(wrapper))
    with pytest.raises(ValueError, match='artifact digest differs: '+bad_archive):
        curator.configure_universe(tmp_path/'never-read-universe.json', gate, *archives)
    assert curator.UNIVERSE == () and curator._qualification_binding is None


def test_record_assembly_preserves_every_gate_and_original_resource_limits(tmp_path, monkeypatch):
    records = helper('prepare_records.py')
    current = records.q
    destination, curated = tmp_path/'new-records', tmp_path/'curated'
    curated.mkdir()
    wrapper = {'catalog': {'path': 'synthetic/catalog.json', 'sha256': 'a'*64},
               **{key: {'synthetic': key} for key in current.GATE_KEYS}}
    gate = tmp_path/'GATES.json'; gate.write_text(json.dumps(wrapper))
    for name, value in [('PREQUERY_EXECUTION.json', {key: wrapper[key] for key in current.GATE_KEYS}),
                        ('FROZEN_POOL.json', {'pool': []}), ('METADATA_CURATION.json', {'synthetic': True})]:
        (curated/name).write_text(json.dumps(value))
    components = tmp_path/'components'; components.mkdir()
    synthetic_here = tmp_path/'research/unified_consequence_runtime'
    synthetic_here.mkdir(parents=True)
    (synthetic_here/'developmental_sources.json').write_bytes((HERE/'developmental_sources.json').read_bytes())
    monkeypatch.setattr(current, 'HERE', synthetic_here)
    monkeypatch.setattr(current, 'RECORDS', destination)
    monkeypatch.setattr(current, 'PROTOCOL', destination/'FRONTIER_PROTOCOL.json')
    monkeypatch.setattr(current, 'require_environment_gate', lambda value: {'synthetic-only': True})
    records.prepare(SimpleNamespace(environment_gate=gate, curation=curated,
                                    screen_root=tmp_path/'screen', components=components))
    protocol = json.loads(current.PROTOCOL.read_text())
    authority = json.loads((destination/'SCREENING_AUTHORITY.json').read_text())
    for key in current.GATE_KEYS:
        assert protocol[key] == authority[key] == wrapper[key]
    assert authority['schema'] == 'UDM_NATIVE_CLI_AUTHORITY_V45'
    assert authority['machine_components']['path'] == str(components)
    assert protocol['search_budget'] == 8 and protocol['acquisition_native_calls'] == 512
    assert protocol['training_seconds'] == 3600


@pytest.mark.parametrize('method', (
    'test_recovers_exact_profiles_episodes_context_and_receipts',
    'test_does_not_dereference_other_binding_or_future_attempts',
    'test_no_profiles_is_allowed_only_for_training_arm', 'test_missing_profiles_on_future_arm_refuses',
    'test_tampered_authority_pin_refuses', 'test_tampered_cas_refuses',
    'test_profile_from_wrong_candidate_order_refuses', 'test_duplicate_profile_refuses',
    'test_unknown_receipt_is_preserved_without_promotion', 'test_boolean_native_cost_is_refused',
    'test_metadata_pin_prevents_training_identity_substitution'))
def test_original_training_projection_assertions_with_v45_transport(method):
    source = HERE/'archaeology/experiment-interface-v43/prospective/test_training_history_projection_v43.py'
    spec = importlib.util.spec_from_file_location('_v45_original_projection_assertions', source)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    namespace = dict(vars(original), CODE=HERE/'archaeology/native-namespace-v45/prospective/training_history_projection_v45.py')
    def schema_transport(code):
        return code.replace(co_consts=tuple(schema_transport(value) if isinstance(value, CodeType)
            else value.replace('_V43', '_V45') if isinstance(value, str) and value.startswith('UDM_')
            else value for value in code.co_consts))
    methods = {}
    for name, function in vars(original.ProjectionTests).items():
        if isinstance(function, FunctionType):
            methods[name] = FunctionType(schema_transport(function.__code__), namespace, name,
                                         function.__defaults__, function.__closure__)
            methods[name].__kwdefaults__ = function.__kwdefaults__
    fixture = type('OriginalProjectionV45', (original.ProjectionTests,), methods)(method)
    result = unittest.TestResult()
    fixture.run(result)
    assert result.wasSuccessful(), result.errors+result.failures
