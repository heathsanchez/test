"""Independent sealed controls for original declaration to direct code binding."""
from __future__ import annotations

import ast
import base64
import copy
import json
from pathlib import Path
import subprocess

import pytest

from .native_v45_test_support import (
    LEGACY, MODERN, ROOT, collect_and_run, implementation, ordinary_case,
    modern_environment, project_factory, record_evidence, sha,
    inherited_adversarial_suite, reseal_reports,
)


def test_versioned_native_v45_interface_is_required():
    worker = implementation()
    assert worker.SCHEMA == 'UDM_GENERIC_NATIVE_PYTEST_V45'
    assert worker.CERTIFICATE_SCHEMA == 'UDM_NATIVE_ADMISSION_CERTIFICATE_V45'
    assert worker.POLICY_SCHEMA == 'UDM_NATIVE_EXECUTION_POLICY_V45'


@pytest.mark.parametrize('control', ['W01_closed_production_wildcard', 'W02_unimported_malformed_python_data'])
def test_frozen_wildcard_controls_execute_actual_assertion_and_replay(project_factory, tmp_path, control):
    case = project_factory(control=control)
    certificate, receipt = collect_and_run(case, tmp_path / 'evidence')
    assert certificate['collection']['selected_test_nodes'] == ['tests/test_native.py::test_contract']
    assert receipt['status'] == 'PASS_NATIVE'
    assert receipt['junit']['tests'] == receipt['junit']['passed'] == 1
    result = implementation().validate_receipt(case.contract, {'replacements': []}, case.authority,
        certificate, receipt, policy=case.policy, output_dir=tmp_path / 'replay')
    assert result['status'] == 'PASS_NATIVE'
    assert result['independent_reexecution']['costs']['native_calls'] == 1
    record_evidence(tmp_path / 'evidence', tmp_path / 'evidence/collection/admission-certificate.json',
        tmp_path / 'evidence/native/receipt.json', tmp_path / 'replay/receipt.json')
    assert (tmp_path / 'evidence/collection/original-declaration-compilation.json').is_file()
    costs = implementation().declaration_attempt_snapshot()
    assert costs['compilation_calls'] > 0 and costs['compilation_seconds'] > 0


def test_runtime_malformed_import_preserves_real_syntaxerror_as_native_failure(project_factory, tmp_path):
    case = project_factory(control='W04_runtime_imported_malformed_python')
    certificate, receipt = collect_and_run(case, tmp_path / 'malformed')
    assert receipt['status'] == 'FAIL_NATIVE'
    assert receipt['junit']['failures'] == 1 and receipt['junit']['passed'] == 0
    stdout = base64.b64decode(receipt['packet']['stdout.log'])
    assert b'SyntaxError' in stdout
    assert receipt['execution']['process_exit_code'] == 1
    result = implementation().validate_receipt(case.contract, {'replacements': []}, case.authority,
        certificate, receipt, policy=case.policy, output_dir=tmp_path / 'malformed-replay')
    assert result['status'] == 'FAIL_NATIVE'
    record_evidence(tmp_path / 'malformed', tmp_path / 'malformed/collection/admission-certificate.json',
        tmp_path / 'malformed/native/receipt.json', tmp_path / 'malformed-replay/receipt.json')


def test_collection_malformed_import_cannot_obtain_native_authority(project_factory, tmp_path):
    with pytest.raises(ValueError):
        case = project_factory(control='W03_collection_imported_malformed_python')
        implementation().collect(case.contract, case.authority, tmp_path / 'refused', policy=case.policy)


@pytest.mark.parametrize('control', ['B01_same_prefix_literal_rebound', 'B02_same_prefix_noop_decorator',
    'B03_forged_wrapped_noop', 'B04_deleted_local_test', 'B05_imported_same_prefix_alias',
    'B06_duplicate_local_definition', 'B07_missing_collection_test_false', 'B08_class_method_rebound'])
def test_frozen_missing_or_rebound_declarations_cannot_obtain_native_authority(project_factory, tmp_path, control):
    with pytest.raises(ValueError):
        case = project_factory(control=control)
        implementation().collect(case.contract, case.authority, tmp_path / 'refused', policy=case.policy)


def test_real_failed_assertion_and_production_fix_keep_original_declaration(project_factory, tmp_path):
    case = ordinary_case(project_factory, b'from subject import value\ndef test_contract():\n    assert value() == 1\n')
    certificate, failed = collect_and_run(case, tmp_path / 'failed')
    assert failed['status'] == 'FAIL_NATIVE' and failed['junit']['failures'] == 1
    candidate = case.candidate('subject.py', 'def value():\n    return 1\n')
    fixed = implementation().verify(case.contract, candidate, tmp_path / 'fixed', authority=case.authority,
        admission_certificate=certificate, policy=case.policy)
    assert fixed['status'] == 'PASS_NATIVE' and fixed['junit']['passed'] == 1
    record_evidence(tmp_path / 'fixed', tmp_path / 'failed/collection/admission-certificate.json',
        tmp_path / 'fixed/receipt.json')


def test_c3_winning_origin_and_each_parameterized_case_have_real_code_binding(project_factory, tmp_path):
    before = (b'import pytest\nclass A:\n    @pytest.mark.parametrize("value", [1, 2])\n'
              b'    def test_contract(self, value):\n        assert value > 0\n'
              b'class B(A):\n    pass\nclass C(A):\n    pass\nclass TestD(B, C):\n    pass\n')
    case = ordinary_case(project_factory, before.replace(b'value > 0', b'value in (1, 2)'), baseline=before)
    declarations = case.authority['namespace_certificate']['required_declarations']
    assert declarations['tests/test_native.py::TestD::test_contract']['origin'] == 'A::test_contract'
    certificate, receipt = collect_and_run(case, tmp_path / 'parameterized')
    assert certificate['collection']['selected_test_nodes'] == [
        'tests/test_native.py::TestD::test_contract[1]', 'tests/test_native.py::TestD::test_contract[2]']
    assert receipt['status'] == 'PASS_NATIVE' and receipt['junit']['passed'] == 2


@pytest.mark.parametrize('decorator', ['mark.skip(reason="control")', 'mark.xfail(reason="control", strict=True)'])
def test_skipped_or_xfailed_protected_assertions_never_promote(project_factory, tmp_path, decorator):
    text = ('import pytest\n@pytest.' + decorator + '\ndef test_contract():\n    assert False\n').encode()
    case = ordinary_case(project_factory, text)
    _, receipt = collect_and_run(case, tmp_path / 'skip')
    assert receipt['status'].startswith('UNKNOWN')


def test_missing_namespace_or_compilation_authority_fails_closed(project_factory, tmp_path):
    case = project_factory(control='W01_closed_production_wildcard')
    missing = copy.deepcopy(case.authority)
    missing.pop('namespace_certificate')
    with pytest.raises(ValueError):
        implementation().collect(case.contract, missing, tmp_path / 'missing', policy=case.policy)
    forged = copy.deepcopy(case.authority)
    declarations = forged['namespace_certificate']['required_declarations']
    declarations['tests/test_native.py::test_contract']['origin'] = 'wrong_function'
    with pytest.raises(ValueError):
        implementation().collect(case.contract, forged, tmp_path / 'wrong-origin', policy=case.policy)
    for mutation in ('exports', 'origin'):
        forged = copy.deepcopy(case.authority)
        witness = forged['namespace_certificate']['wildcard_imports'][0]
        if mutation == 'exports':
            witness['exports'].append('test_fabricated')
        else:
            witness['path'] = 'tests/test_native.py'
        with pytest.raises(ValueError):
            implementation().collect(case.contract, forged, tmp_path / ('wrong-export-' + mutation), policy=case.policy)
    forged = copy.deepcopy(case.authority)
    forged['namespace_certificate']['schema'] = 'UNKNOWN_CALLER_NAMESPACE_REVISION'
    with pytest.raises(ValueError):
        implementation().collect(case.contract, forged, tmp_path / 'unknown-schema', policy=case.policy)


@pytest.mark.parametrize('path', ['library/constants.py', 'library/__init__.py'])
def test_candidate_wildcard_source_change_cannot_reuse_namespace_authority(project_factory, tmp_path, path):
    case = project_factory(control='W01_closed_production_wildcard')
    certificate = implementation().collect(case.contract, case.authority, tmp_path / 'collection', policy=case.policy)
    candidate = case.candidate(path, 'ANSWER = 42\ndef test_smuggled():\n    pass\n')
    with pytest.raises(ValueError):
        implementation().verify(case.contract, candidate, tmp_path / 'changed', authority=case.authority,
            admission_certificate=certificate, policy=case.policy)


def test_resealed_observed_code_forgery_does_not_grant_original_declaration_authority(project_factory, tmp_path):
    case = project_factory(control='W01_closed_production_wildcard')
    certificate = implementation().collect(case.contract, case.authority, tmp_path / 'collection', policy=case.policy)
    forged = copy.deepcopy(certificate)
    for name in ('report.json', 'checked-report.json'):
        data = json.loads(base64.b64decode(forged['packet'][name]))
        data['test_items'][0]['code_sha256'] = '0' * 64
        raw = implementation().canonical(data).encode()
        forged['packet'][name] = base64.b64encode(raw).decode()
        forged['packet_sha256'][name] = sha(raw)
    forged['collection']['test_items'][0]['code_sha256'] = '0' * 64
    with pytest.raises(ValueError):
        implementation().validate_certificate(case.contract, case.authority, forged,
            policy=case.policy, output_dir=tmp_path / 'forgery-replay')


@pytest.mark.parametrize('control', ['W05_wildcard_public_function_test', 'W06_wildcard_public_test_class'])
def test_resealed_hidden_test_like_export_does_not_grant_wildcard_authority(project_factory, tmp_path, control):
    worker = implementation()
    honest = project_factory(control='W01_closed_production_wildcard')
    certificate = worker.collect(honest.contract, honest.authority, tmp_path / 'honest', policy=honest.policy)
    case = project_factory(control=control, derive_authority=False)
    authority = copy.deepcopy(honest.authority)
    authority.update(baseline_commit=case.base, source_commit=case.commit,
        baseline_source=worker.source.snapshot(case.repo, case.base)[0],
        source={key: case.contract[key] for key in ('git_tree', 'tracked_tree_sha256', 'file_count')})
    manifest = {row['path']: row for row in case.manifest}
    for witness in authority['namespace_certificate']['wildcard_imports']:
        witness['source_sha256'] = manifest[witness['path']]['sha256']
        for row in witness['route']:
            original = manifest[row['path']]
            row.update(source_sha256=original['sha256'], mode=original['mode'], git_blob=original['blob'])
    forged = copy.deepcopy(certificate)
    forged.update(contract_sha256=worker.fingerprint(case.contract), authority_sha256=worker.fingerprint(authority))
    for imported in forged['collection']['import_manifest']:
        imported['sha256'] = manifest[imported['path']]['sha256']
    for name in ('report.json', 'checked-report.json'):
        report = json.loads(base64.b64decode(forged['packet'][name]))
        for imported in report['import_manifest']:
            imported['sha256'] = manifest[imported['path']]['sha256']
        forged['packet'][name] = base64.b64encode(worker.canonical(report).encode()).decode()
    forged['packet']['tracked-source-manifest.json'] = base64.b64encode(worker.canonical(case.manifest).encode()).decode()
    forged['packet_sha256'] = {name: sha(base64.b64decode(raw)) for name, raw in forged['packet'].items()}
    with pytest.raises(ValueError, match='protected or dynamic production export'):
        worker.validate_certificate(case.contract, authority, forged,
            policy=case.policy, output_dir=tmp_path / 'hidden-export-replay')


@pytest.mark.parametrize('control', ['W01_closed_production_wildcard', 'W04_runtime_imported_malformed_python'])
def test_frozen_legacy_importlib_configuration_remains_unknown(project_factory, tmp_path, control):
    case = project_factory(control=control, interpreter=LEGACY)
    with pytest.raises(ValueError, match='UNKNOWN_COLLECTION_ERROR'):
        implementation().collect(case.contract, case.authority, tmp_path / 'legacy-refusal', policy=case.policy)
    report = json.loads((tmp_path / 'legacy-refusal/checked-report.json').read_bytes())
    assert report['costs']['collection_calls'] == 1 and report['costs']['native_calls'] == 0
    assert b"invalid choice: 'importlib'" in (tmp_path / 'legacy-refusal/stderr.log').read_bytes()
    assert case.files['pytest.ini'] == (ROOT / control / 'augmented/pytest.ini').read_bytes()


@pytest.mark.parametrize('control,status', [('W01_closed_production_wildcard', 'PASS_NATIVE'),
                                         ('W04_runtime_imported_malformed_python', 'FAIL_NATIVE')])
def test_separately_declared_legacy_compatible_configuration_binds_real_assertion_and_replay(
        project_factory, tmp_path, control, status):
    views = [{path.relative_to(ROOT / control / view).as_posix(): path.read_bytes()
              for path in (ROOT / control / view).rglob('*') if path.is_file()}
             for view in ('baseline', 'augmented')]
    for files in views:
        files['pytest.ini'] = b'[pytest]\n'
    frozen_input = {'fixture_id': 'separately-declared-legacy-compatible-' + control,
        'baseline': {path: base64.b64encode(raw).decode() for path, raw in sorted(views[0].items())},
        'augmented': {path: base64.b64encode(raw).decode() for path, raw in sorted(views[1].items())}}
    (tmp_path / 'LEGACY_COMPATIBLE_INPUT.json').write_text(json.dumps(frozen_input, sort_keys=True) + '\n')
    case = project_factory(before=views[0], after=views[1], interpreter=LEGACY)
    certificate, receipt = collect_and_run(case, tmp_path / 'legacy')
    assert certificate['environment']['pytest_version'] == '5.4.3'
    assert receipt['status'] == status and receipt['junit']['tests'] == 1
    assert receipt['junit']['passed' if status == 'PASS_NATIVE' else 'failures'] == 1
    replay = implementation().validate_receipt(case.contract, {'replacements': []}, case.authority,
        certificate, receipt, policy=case.policy, output_dir=tmp_path / 'legacy-replay')
    assert replay['status'] == status and 'independent_reexecution' in replay
    record_evidence(tmp_path / 'legacy', tmp_path / 'legacy/collection/admission-certificate.json',
        tmp_path / 'legacy/native/receipt.json', tmp_path / 'legacy-replay/receipt.json')


def test_expected_compiler_does_not_execute_original_source_and_outer_wrapper_cannot_impersonate_it(tmp_path):
    worker = implementation()
    raw = b'exec("raise RuntimeError(123)")\ndef test_contract():\n    assert 1 == 2\n'
    declaration = ast.parse(raw).body[1]
    authority = {'namespace_certificate': {'schema': 'UDM_NATIVE_TEST_NAMESPACE_CERTIFICATE_V45',
        'wildcard_imports': [], 'required_declarations': {'tests/test_native.py::test_contract': {
            'path': 'tests/test_native.py', 'origin': 'test_contract', 'source_sha256': sha(raw),
            'ast_sha256': sha(ast.dump(declaration, include_attributes=False).encode())}}}}
    result = worker._compile_original_declarations({'tests/test_native.py': raw}, authority, str(MODERN))
    assert result['status'] == 'COMPILED_ORIGINAL_DECLARATIONS_WITHOUT_EXECUTION'
    assert len(result['declarations']['tests/test_native.py::test_contract']['code_sha256']) == 2
    # This exact frozen B03 program executes only in a diagnostic subprocess.
    # The instrumented hash must expose the no-op's actual outer code.
    fixture = (ROOT / 'B03_forged_wrapped_noop/augmented/tests/test_native.py').read_bytes()
    module = ast.parse(worker._BOOTSTRAP)
    code_hash = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'code_hash')
    script = ('import hashlib,json,pathlib,struct,types\nworld=pathlib.Path.cwd()\n' + ast.unparse(code_hash)
              + '\n' + fixture.decode() + '\nassert code_hash(test_contract) != code_hash(test_contract.__wrapped__)\n')
    checked = subprocess.run([str(MODERN), '-I', '-B', '-c', script], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr


def test_forged_function_attribute_cannot_impersonate_a_bound_method():
    worker = implementation()
    module = ast.parse(worker._BOOTSTRAP)
    node = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'code_hash')
    fixture = (ROOT / 'B03_forged_wrapped_noop/augmented/tests/test_native.py').read_text()
    script = ('import hashlib,json,pathlib,struct,types\nworld=pathlib.Path.cwd()\n' + ast.unparse(node)
        + '\n' + fixture + '\ntest_contract.__func__ = test_contract.__wrapped__\n'
        'assert code_hash(test_contract) != code_hash(test_contract.__wrapped__), "forged __func__ hid outer wrapper"\n')
    result = subprocess.run([str(MODERN), '-I', '-B', '-c', script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('spoof_class', [False, True])
def test_callable_instance_cannot_supply_an_original_function_code_attribute(spoof_class):
    worker = implementation()
    module = ast.parse(worker._BOOTSTRAP)
    node = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'code_hash')
    script = ('import hashlib,json,pathlib,struct,types\nworld=pathlib.Path.cwd()\n' + ast.unparse(node)
        + '\ndef original():\n    assert 1 == 2\n'
        'class Pretender:\n    __code__ = original.__code__\n    def __call__(self):\n        pass\n'
        + ('    @property\n    def __class__(self):\n        return types.FunctionType\n' if spoof_class else '') +
        'imposter = Pretender()\nimposter()\n'
        'assert code_hash(imposter) is None, "callable instance forged original code"\n')
    result = subprocess.run([str(MODERN), '-I', '-B', '-c', script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_direct_callable_type_objects_are_bound_before_source_imports():
    worker = implementation()
    node = next(node for node in ast.parse(worker._BOOTSTRAP).body
                if isinstance(node, ast.FunctionDef) and node.name == 'code_hash')
    script = ('import hashlib,json,pathlib,struct,types\nworld=pathlib.Path.cwd()\n' + ast.unparse(node)
        + '\ndef original():\n    assert 1 == 2\nbefore = code_hash(original)\n'
        'types.FunctionType = type(None)\n'
        'assert code_hash(original) == before, "native function type was replaced after bootstrap"\n')
    result = subprocess.run([str(MODERN), '-I', '-B', '-c', script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_real_unittest_bound_method_with_class_closure_retains_native_authority(project_factory, tmp_path):
    before = (b'import unittest\nclass NativeCase(unittest.TestCase):\n'
              b'    def test_contract(self):\n        assert __class__.__name__ == "wrong"\n')
    case = ordinary_case(project_factory, before.replace(b'"wrong"', b'"NativeCase"'), baseline=before)
    certificate, receipt = collect_and_run(case, tmp_path / 'unittest')
    assert certificate['collection']['selected_test_nodes'] == ['tests/test_native.py::NativeCase::test_contract']
    assert receipt['status'] == 'PASS_NATIVE' and receipt['junit']['passed'] == 1


@pytest.mark.parametrize('change', ['reverse_order', 'missing_protected'])
def test_resealed_selected_order_cannot_replace_independent_original_order(project_factory, tmp_path, change):
    case = ordinary_case(project_factory, b'def test_contract():\n    assert 1 == 1\n'
        b'def test_other():\n    assert 2 == 2\n')
    worker = implementation()
    certificate = worker.collect(case.contract, case.authority, tmp_path / 'collection', policy=case.policy)

    def reverse_order(report):
        if change == 'reverse_order':
            report['selected_test_nodes'].reverse()
        else:
            missing = 'tests/test_native.py::test_contract'
            report['selected_test_nodes'].remove(missing)
            report['collected_test_nodes'].remove(missing)
            report['test_items'] = [row for row in report['test_items'] if row['nodeid'] != missing]
    forged = reseal_reports(certificate, reverse_order)
    with pytest.raises(ValueError, match='independent original collection|UNKNOWN_MISSING_PROTECTED_ASSERTION'):
        worker.validate_certificate(case.contract, case.authority, forged,
            policy=case.policy, output_dir=tmp_path / 'independent-order')


def test_same_module_name_unlicensed_plugin_registration_does_not_grant_authority(project_factory, tmp_path):
    hook = b'def pytest_configure(config):\n    global MANAGER\n    MANAGER = config.pluginmanager\n'
    case = ordinary_case(project_factory, b'from subject import value\ndef test_contract():\n    assert value() == 0\n',
        extra={'conftest.py': hook})
    certificate = implementation().collect(case.contract, case.authority, tmp_path / 'collection', policy=case.policy)
    candidate = case.candidate('subject.py', 'import conftest\n'
        'class Imposter:\n    __module__ = "_pytest.assertion"\n'
        '    def pytest_runtest_setup(self, item):\n        pass\n'
        'conftest.MANAGER.register(Imposter(), "same-module-imposter")\n'
        'def value():\n    return 0\n')
    receipt = implementation().verify(case.contract, candidate, tmp_path / 'imposter',
        authority=case.authority, admission_certificate=certificate, policy=case.policy)
    assert receipt['status'].startswith('UNKNOWN')
    assert receipt['execution']['plugin_manifest'] != certificate['collection']['plugin_manifest']


@pytest.mark.parametrize('change', ['missing_call', 'execution_order'])
def test_resealed_missing_call_or_changed_execution_order_cannot_promote(project_factory, tmp_path, change):
    case = ordinary_case(project_factory, b'def test_contract():\n    assert 1 == 1\n'
        b'def test_other():\n    assert 2 == 2\n')
    certificate, receipt = collect_and_run(case, tmp_path / 'honest')

    def alter(report):
        if change == 'missing_call':
            call = next(row for row in report['reports'] if row['when'] == 'call')
            report['reports'].remove(call)
        else:
            report['reports'].reverse()
    forged = reseal_reports(receipt, alter)
    with pytest.raises(ValueError, match='status|assertion outcome'):
        implementation().validate_receipt(case.contract, {'replacements': []}, case.authority,
            certificate, forged, policy=case.policy, independent=False)


@pytest.mark.parametrize('operation', ['replace_object', 'mutate_code'])
def test_actual_outer_code_replacement_after_collection_is_unknown(project_factory, tmp_path, operation):
    original_hook = (b'def pytest_runtest_setup(item):\n'
        b'    original = item.obj\n    def wrapper():\n        pass\n'
        b'    wrapper.__wrapped__ = original\n    wrapper.__func__ = original\n'
        + (b'    item.obj = wrapper\n' if operation == 'replace_object' else b'    original.__code__ = wrapper.__code__\n'))
    case = ordinary_case(project_factory, b'def test_contract():\n    assert 1 == 2\n',
        extra={'conftest.py': original_hook})
    _, receipt = collect_and_run(case, tmp_path / 'outer-change')
    assert receipt['status'] == 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    assert receipt['execution']['changed_test_code'] == ['tests/test_native.py::test_contract']
    assert receipt['junit']['passed'] == 1  # the no-op really ran; it grants no warrant


@pytest.mark.parametrize('path', ['tests/test_native.py', 'pytest.ini', 'conftest.py'])
def test_direct_candidate_test_or_configuration_replacements_are_refused(project_factory, tmp_path, path):
    case = ordinary_case(project_factory, b'def test_contract():\n    assert 1 == 1\n',
        extra={'conftest.py': b''})
    worker = implementation()
    certificate = worker.collect(case.contract, case.authority, tmp_path / 'collection', policy=case.policy)
    candidate = case.candidate(path, 'def test_contract():\n    pass\n')
    with pytest.raises(ValueError):
        worker.verify(case.contract, candidate, tmp_path / 'candidate', authority=case.authority,
            admission_certificate=certificate, policy=case.policy)


def test_failed_independent_compiler_is_charged_and_never_falls_back(project_factory, tmp_path):
    case = project_factory(control='W01_closed_production_wildcard')
    worker = implementation()
    before = worker.declaration_attempt_snapshot()
    with pytest.raises(ValueError, match='UNKNOWN_V45_ORIGINAL_DECLARATION_COMPILATION'):
        worker._compile_original_declarations(case.files, case.authority, str(tmp_path / 'missing-python'))
    after = worker.declaration_attempt_snapshot()
    assert after['compilation_calls'] == before['compilation_calls'] + 1
    assert after['records'][-1]['status'] == 'UNKNOWN'


def test_original_generated_build_verifier_and_complete_native_replay_remain_available(tmp_path, modern_environment):
    from .native_v43_test_support import make_project
    worker = implementation()
    case = make_project(tmp_path / 'declared-generated', 'namespace', modern_environment)
    policy = dict(case.policy, schema=worker.POLICY_SCHEMA)
    contract = dict(case.contract, schema=worker.SCHEMA, interpreter=str(MODERN))
    authority = implementation('native_admission_v45').derive_suite_contract(case.repo, case.base,
        case.augmented, contract['protocol_binding'], repository=contract['repository'])
    evidence = worker.build.prepare(contract, authority, policy, tmp_path / 'build')
    contract['generated_build'] = evidence
    certificate = worker.collect(contract, authority, tmp_path / 'generated-collection', policy=policy)
    receipt = worker.verify(contract, {'replacements': []}, tmp_path / 'generated-native',
        authority=authority, admission_certificate=certificate, policy=policy)
    assert receipt['status'] == 'PASS_NATIVE' and receipt['junit']['passed'] == 2
    replay = worker.validate_receipt(contract, {'replacements': []}, authority, certificate, receipt,
        policy=policy, output_dir=tmp_path / 'generated-replay')
    assert replay['status'] == 'PASS_NATIVE'
    record_evidence(tmp_path, tmp_path / 'generated-collection/admission-certificate.json',
        tmp_path / 'generated-native/receipt.json', tmp_path / 'generated-replay/receipt.json')


TestNativeV45InheritedAdversarial = inherited_adversarial_suite()

# Each recipe maps to concrete V45 tests. Original test method statements remain
# frozen; their private dependency bindings exercise this worker and authority.
SEALED_REPLAY_CONTROL_TESTS = {
    'R01': ['test_certificate_cannot_replay_to_other_protocol_environment_source_or_horizon'],
    'R02': ['test_weaker_required_assertions_are_not_certificate_authority'],
    'R03': ['test_resealed_hidden_test_like_export_does_not_grant_wildcard_authority'],
    'R04': ['test_missing_namespace_or_compilation_authority_fails_closed'],
    'R05': ['test_resealed_observed_code_forgery_does_not_grant_original_declaration_authority'],
    'R06': ['test_resealed_selected_order_cannot_replace_independent_original_order[missing_protected]'],
    'R07': ['test_resealed_collection_manifest_is_checked_against_original_recollection'],
    'R08': ['test_resealed_missing_call_or_changed_execution_order_cannot_promote[missing_call]'],
    'R09': ['test_skip_xfail_and_xpass_are_not_fully_executed_native_passes'],
    'R10': ['test_fully_resealed_false_native_pass_requires_independent_candidate_execution'],
    'R11': ['test_certificate_cannot_replay_to_other_protocol_environment_source_or_horizon'],
    'R12': ['test_same_module_name_unlicensed_plugin_registration_does_not_grant_authority'],
    'R13': ['test_resealed_selected_order_cannot_replace_independent_original_order'],
    'R14': ['test_resealed_missing_call_or_changed_execution_order_cannot_promote[execution_order]'],
    'R15': ['test_candidate_wildcard_source_change_cannot_reuse_namespace_authority'],
    'R16': ['test_missing_namespace_or_compilation_authority_fails_closed'],
    'R17': ['test_direct_candidate_test_or_configuration_replacements_are_refused'],
    'R18': ['test_actual_outer_code_replacement_after_collection_is_unknown'],
}
