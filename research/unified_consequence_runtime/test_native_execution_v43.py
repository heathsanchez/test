"""Frozen native V43 generated-view acceptance controls; no scientific tasks."""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

import pytest

from . import decisive_native_verify as original
from . import native_execution_v42 as previous
from .native_v43_test_support import (
    CERTIFICATE_SCHEMA, CONTRACT_SCHEMA, POLICY_SCHEMA, charged_build_calls,
    forged_wheel, implementation, modern_environment, mutate_packet_import_hash,
    project, project_factory, sha, wheel_artifact, wheel_members,
)


def warm(project, output):
    build = implementation('native_build_v43')
    evidence = build.prepare(project.contract, project.authority, project.policy, output)
    return project.with_evidence(evidence), evidence


def test_required_native_execution_v43_module_exists():
    assert Path(__file__).with_name('native_execution_v43.py').is_file(), 'V43 native interface is not implemented'


def test_fixture_obstructs_actual_original_collection_without_generated_file(project, tmp_path):
    old_contract = dict(project.contract, schema=previous.SCHEMA)
    old_contract.pop('generated_build')
    old_policy = dict(project.policy, schema=previous.POLICY_SCHEMA)
    with pytest.raises(ValueError, match='UNKNOWN.*COLLECTION'):
        previous.collect(old_contract, project.authority, tmp_path / 'original-cold', policy=old_policy)


def test_tracked_only_fixture_has_actual_original_native_collection_and_pass(project_factory, tmp_path):
    case = project_factory('alpha', generated=False)
    old_contract = dict(case.contract, schema=previous.SCHEMA)
    old_contract.pop('generated_build')
    old_policy = dict(case.policy, schema=previous.POLICY_SCHEMA)
    certificate = previous.collect(old_contract, case.authority, tmp_path / 'original-collection', policy=old_policy)
    receipt = previous.verify(old_contract, {'replacements': []}, tmp_path / 'original-native',
                              authority=case.authority, admission_certificate=certificate, policy=old_policy)
    assert certificate['collection']['collected_test_nodes'] == case.nodes
    assert receipt['status'] == 'PASS_NATIVE'
    assert receipt['junit']['passed'] == 2


def test_explicit_versioned_generated_contract_and_policy_schemas(project_factory):
    worker = implementation('native_execution_v43')
    assert worker.SCHEMA == CONTRACT_SCHEMA
    assert worker.POLICY_SCHEMA == POLICY_SCHEMA
    assert worker.CERTIFICATE_SCHEMA == CERTIFICATE_SCHEMA
    assert previous.SCHEMA == 'UDM_GENERIC_NATIVE_PYTEST_V42'
    assert previous.CERTIFICATE_SCHEMA == 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42'


def test_cold_tracked_only_native_collection_remains_unknown_without_build_evidence(project, tmp_path):
    worker = implementation('native_execution_v43')
    assert project.contract['generated_build'] is None
    with pytest.raises(ValueError, match='UNKNOWN.*COLLECTION'):
        worker.collect(project.contract, project.authority, tmp_path / 'cold', policy=project.policy)


def test_warm_native_complete_collection_pass_import_hash_and_independent_receipt(project, tmp_path):
    worker = implementation('native_execution_v43')
    contract, evidence = warm(project, tmp_path / 'build')
    source_before = project.inventory()
    certificate = worker.collect(contract, project.authority, tmp_path / 'collection', policy=project.policy)
    assert certificate['schema'] == CERTIFICATE_SCHEMA
    assert certificate['contract_sha256'] == original.fingerprint(contract)
    assert certificate['collection']['collected_test_nodes'] == project.nodes
    assert certificate['collection']['selected_test_nodes'] == project.nodes
    assert certificate['collection']['deselected_test_nodes'] == []
    candidate = {'replacements': []}
    receipt = worker.verify(contract, candidate, tmp_path / 'native', authority=project.authority,
                            admission_certificate=certificate, policy=project.policy)
    assert receipt['schema'] == CONTRACT_SCHEMA
    assert receipt['status'] == 'PASS_NATIVE'
    assert receipt['junit']['tests'] == 2
    assert receipt['junit']['passed'] == 2
    assert receipt['junit']['failures'] == receipt['junit']['errors'] == receipt['junit']['skipped'] == 0
    assert receipt['source'] == {key: project.contract[key]
                                 for key in ('git_tree', 'tracked_tree_sha256', 'file_count')}
    generated = implementation('native_build_v43').read_generated(
        project.contract, project.authority, project.policy, evidence)
    imports = receipt['execution']['import_manifest']
    assert {'path': project.generated_path, 'sha256': sha(generated[project.generated_path])}.items() <= next(
        row.items() for row in imports if row['path'] == project.generated_path)
    assert not receipt['execution']['unexpected_imports']
    manifest = json.loads(base64.b64decode(receipt['packet']['tracked-source-manifest.json']))
    assert manifest == project.manifest
    assert project.generated_path not in {row['path'] for row in manifest}
    assert charged_build_calls(receipt) >= 1
    checked = worker.validate_receipt(contract, candidate, project.authority, certificate, receipt,
                                     policy=project.policy, output_dir=tmp_path / 'independent-replay')
    assert checked['status'] == 'PASS_NATIVE'
    assert 'independent_reexecution' in checked
    assert project.inventory() == source_before
    assert not (project.repo / project.generated_path).exists()


def test_protected_assertion_failure_is_fail_native_with_generated_build_and_fix_still_passes(
        project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha', expected=1)
    contract, _ = warm(case, tmp_path / 'build')
    certificate = worker.collect(contract, case.authority, tmp_path / 'collection', policy=case.policy)
    failed = worker.verify(contract, {'replacements': []}, tmp_path / 'failure', authority=case.authority,
                           admission_certificate=certificate, policy=case.policy)
    assert failed['status'] == 'FAIL_NATIVE'
    assert failed['junit']['failures'] == 1
    assert failed['junit']['passed'] == 1
    passed = worker.verify(contract, case.candidate(), tmp_path / 'fixed', authority=case.authority,
                           admission_certificate=certificate, policy=case.policy)
    assert passed['status'] == 'PASS_NATIVE'
    assert passed['junit']['passed'] == 2
    assert certificate['collection']['collected_test_nodes'] == case.nodes


def test_explicit_none_preserves_actual_original_tracked_only_operation(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha', generated=False)
    certificate = worker.collect(case.contract, case.authority, tmp_path / 'collection', policy=case.policy)
    receipt = worker.verify(case.contract, {'replacements': []}, tmp_path / 'native', authority=case.authority,
                            admission_certificate=certificate, policy=case.policy)
    assert receipt['status'] == 'PASS_NATIVE'
    assert receipt['junit']['passed'] == 2
    assert not any(row['path'] == case.generated_path for row in receipt['execution']['import_manifest'])


def test_generated_field_must_be_explicit_and_raw_generated_bytes_are_not_authority(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha', generated=False)
    missing = dict(case.contract)
    missing.pop('generated_build')
    with pytest.raises(ValueError):
        worker.collect(missing, case.authority, tmp_path / 'missing-field', policy=case.policy)
    raw = dict(case.contract, generated_build={case.generated_path: b'__version__ = "1.0.0"\n'})
    with pytest.raises(ValueError):
        worker.collect(raw, case.authority, tmp_path / 'raw-generated', policy=case.policy)


def test_actual_v42_certificate_cannot_be_reused_under_v43_contract(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha', generated=False)
    old_contract = dict(case.contract, schema=previous.SCHEMA)
    old_contract.pop('generated_build')
    old_policy = dict(case.policy, schema=previous.POLICY_SCHEMA)
    old_certificate = previous.collect(old_contract, case.authority, tmp_path / 'old-collection', policy=old_policy)
    assert old_certificate['schema'] == previous.CERTIFICATE_SCHEMA
    with pytest.raises(ValueError):
        worker.validate_certificate(case.contract, case.authority, old_certificate,
                                    policy=case.policy, output_dir=tmp_path / 'reject-old')


def test_build_bound_certificate_cannot_replay_on_another_native_task(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    alpha, beta = project_factory('alpha'), project_factory('beta')
    contract, _ = warm(alpha, tmp_path / 'alpha-build')
    other, _ = warm(beta, tmp_path / 'beta-build')
    certificate = worker.collect(contract, alpha.authority, tmp_path / 'collection', policy=alpha.policy)
    with pytest.raises(ValueError):
        worker.validate_certificate(other, beta.authority, certificate,
                                    policy=beta.policy, output_dir=tmp_path / 'replay')


def test_certificate_binds_presence_and_exact_generated_evidence(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha', generated=False)
    cold = worker.collect(case.contract, case.authority, tmp_path / 'cold', policy=case.policy)
    generated_contract, _ = warm(case, tmp_path / 'build')
    with pytest.raises(ValueError):
        worker.validate_certificate(generated_contract, case.authority, cold,
                                    policy=case.policy, output_dir=tmp_path / 'changed-evidence')


def test_missing_wheel_blocks_new_collection_certificate_replay_and_execution(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha')
    contract, evidence = warm(case, tmp_path / 'build')
    certificate = worker.collect(contract, case.authority, tmp_path / 'collection', policy=case.policy)
    wheel_artifact(evidence).unlink()
    with pytest.raises(ValueError):
        worker.collect(contract, case.authority, tmp_path / 'missing-collection', policy=case.policy)
    with pytest.raises(ValueError):
        worker.validate_certificate(contract, case.authority, certificate,
                                    policy=case.policy, output_dir=tmp_path / 'missing-replay')
    with pytest.raises(ValueError):
        worker.verify(contract, {'replacements': []}, tmp_path / 'missing-native', authority=case.authority,
                      admission_certificate=certificate, policy=case.policy)


def test_consistently_rehashed_forged_generated_artifact_never_admits_native_collection(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha')
    _, evidence = warm(case, tmp_path / 'build')
    forged = forged_wheel(evidence, tmp_path / 'forged' / wheel_artifact(evidence).name,
                          {case.wheel_generated_path: b'__version__ = "1.0.0"\nFORGED = True\n'})
    with pytest.raises(ValueError):
        worker.collect(case.with_evidence(forged), case.authority, tmp_path / 'forged-collection', policy=case.policy)


def test_generated_import_hash_cannot_be_forged_with_consistent_native_packet_hashes(project_factory, tmp_path):
    worker = implementation('native_execution_v43')
    case = project_factory('alpha')
    contract, _ = warm(case, tmp_path / 'build')
    certificate = worker.collect(contract, case.authority, tmp_path / 'collection', policy=case.policy)
    receipt = worker.verify(contract, {'replacements': []}, tmp_path / 'native', authority=case.authority,
                            admission_certificate=certificate, policy=case.policy)
    forged = mutate_packet_import_hash(receipt, case.generated_path)
    with pytest.raises(ValueError):
        worker.validate_receipt(contract, {'replacements': []}, case.authority, certificate, forged,
                                policy=case.policy, output_dir=tmp_path / 'replay', independent=False)


@pytest.mark.parametrize('mutation', ('bytes', 'symlink'))
def test_post_execution_generated_bytes_and_topology_are_authenticated(project_factory, tmp_path, mutation):
    worker = implementation('native_execution_v43')
    if mutation == 'bytes':
        action = '    generated.write_bytes(b"MUTATED = True\\n")\n'
    else:
        action = ('    saved = generated.with_name("saved-generated.py")\n'
                  '    generated.rename(saved)\n    generated.symlink_to(saved.name)\n')
    tail = ('    from pathlib import Path\n    import native_alpha_v43._version as version\n'
            '    generated = Path(version.__file__)\n' + action)
    case = project_factory('alpha', test_tail=tail)
    contract, _ = warm(case, tmp_path / 'build')
    certificate = worker.collect(contract, case.authority, tmp_path / 'collection', policy=case.policy)
    receipt = worker.verify(contract, {'replacements': []}, tmp_path / 'native', authority=case.authority,
                            admission_certificate=certificate, policy=case.policy)
    assert receipt['status'] == 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    assert not (case.repo / case.generated_path).exists()
