"""Frozen, real-backend V43 build acceptance controls; infrastructure only."""
from __future__ import annotations

import copy
from pathlib import Path
import zipfile

import pytest

from . import decisive_native_verify as original
from . import native_admission_v42 as admission
from . import native_source_v42 as source
from .native_v43_test_support import (
    assert_no_native_success, charged_build_calls, forged_wheel, git, implementation,
    modern_environment, normalized_digest, original_backend_build, project, project_factory,
    replace_values, sha, wheel_artifact, wheel_members,
)


def test_required_native_build_v43_module_exists():
    assert Path(__file__).with_name('native_build_v43.py').is_file(), 'V43 build interface is not implemented'


def test_fixture_has_distinct_base_author_test_and_source_identity(project):
    before, base_files, _ = source.snapshot(project.repo, project.base)
    after, augmented_files, _ = project.inventory()
    assert project.base != project.augmented
    assert before != after
    assert set(base_files) == set(augmented_files)
    assert [name for name in base_files if base_files[name] != augmented_files[name]] == ['tests/test_native.py']
    assert git(project.repo, 'rev-parse', 'refs/tags/v1.0.0') == project.base
    assert project.authority['baseline_commit'] == project.base
    assert project.authority['source_commit'] == project.augmented
    assert project.authority['schema'] == admission.SCHEMA
    assert project.generated_path not in project.files


def test_two_fixture_original_sources_are_independent(project_factory):
    alpha, beta = project_factory('alpha'), project_factory('beta')
    assert alpha.base != beta.base
    assert alpha.contract['tracked_tree_sha256'] != beta.contract['tracked_tree_sha256']
    assert alpha.authority['baseline_source'] != beta.authority['baseline_source']
    assert alpha.contract['repository'] != beta.contract['repository']


def test_actual_hatch_vcs_generates_wheel_member_and_author_commit_changes_scm_version(project, tmp_path):
    first = original_backend_build(project, tmp_path / 'direct-one')
    second = original_backend_build(project, tmp_path / 'direct-two')
    augmented = original_backend_build(project, tmp_path / 'direct-augmented', commit_id=project.augmented)
    members = wheel_members(first)
    assert members == wheel_members(second), 'independent original-backend wheel content must agree'
    assert project.wheel_generated_path in members
    assert b'1.0.0' in members[project.wheel_generated_path]
    assert members[project.wheel_generated_path] != wheel_members(augmented)[project.wheel_generated_path]
    assert not (project.repo / project.generated_path).exists()


def test_declared_output_is_derived_from_original_backend_declaration(project):
    build = implementation('native_build_v43')
    assert build.declared_outputs(project.files) == (project.generated_path,)
    assert project.generated_path not in project.files


@pytest.mark.parametrize('target', (
    '../outside.py', '/tmp/outside.py', 'src/native_alpha_v43/../outside.py',
    'src/native_alpha_v43//_version.py', 'tests/test_generated.py',
    'src/native_alpha_v43/test_generated.py', 'src/native_alpha_v43/generated_test.py',
    'src/native_alpha_v43/conftest.py', 'src/native_alpha_v43/pytest.py',
    'src/native_alpha_v43/pyproject.toml', 'src/native_alpha_v43/__init__.py',
    'new_root/_version.py', 'src/native_alpha_v43/_version.pyc',
))
def test_declared_output_refuses_traversal_tests_config_roots_and_tracked_bytes(project_factory, target):
    build = implementation('native_build_v43')
    case = project_factory('alpha', declared=target)
    with pytest.raises(ValueError):
        build.declared_outputs(case.files)


def test_declared_generated_module_cannot_be_originally_licensed_as_pytest_plugin(project_factory):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    files = dict(case.files)
    files['pyproject.toml'] = files['pyproject.toml'].replace(
        b'addopts = "--import-mode=importlib"',
        ('addopts = "--import-mode=importlib -p ' + case.package + '._version"').encode())
    with pytest.raises(ValueError):
        build.declared_outputs(files)


def test_unsupported_original_backend_remains_precise_unknown(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    files = dict(case.files)
    files['pyproject.toml'] = files['pyproject.toml'].replace(b'hatchling.build', b'setuptools.build_meta')
    with pytest.raises(ValueError, match='UNKNOWN.*(BACKEND|DECLARATION|BUILD)'):
        build.declared_outputs(files)


def test_prepare_and_independent_verify_match_all_original_base_wheel_members(project, tmp_path):
    build = implementation('native_build_v43')
    before = project.inventory()
    evidence = build.prepare(project.contract, project.authority, project.policy, tmp_path / 'prepared')
    assert isinstance(evidence, dict)
    assert_no_native_success(evidence)
    wheel = wheel_artifact(evidence)
    direct = original_backend_build(project, tmp_path / 'original-backend')
    assert wheel_members(wheel) == wheel_members(direct)
    generated = build.read_generated(project.contract, project.authority, project.policy, evidence)
    assert generated == {project.generated_path: wheel_members(direct)[project.wheel_generated_path]}
    checked, receipt = build.verify(project.contract, project.authority, project.policy,
                                    evidence, tmp_path / 'independent')
    assert checked == generated
    assert isinstance(receipt, dict)
    assert charged_build_calls(receipt) >= 1
    assert_no_native_success(receipt)
    independently_built = list((tmp_path / 'independent').rglob('*.whl'))
    assert independently_built, 'retain actual independent build artifacts'
    assert all(wheel_members(item) == wheel_members(wheel) for item in independently_built)
    assert project.inventory() == before
    assert not (project.repo / project.generated_path).exists()


def test_build_reads_immutable_source_without_overwriting_dirty_source_or_author_tests(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    subject = case.repo / 'src' / case.package / 'subject.py'
    tests = case.repo / 'tests/test_native.py'
    subject.write_bytes(b'dirty host source must remain unchanged\n')
    tests.write_bytes(b'dirty host tests must remain unchanged\n')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    checked, _ = build.verify(case.contract, case.authority, case.policy, evidence, tmp_path / 'verified')
    assert set(checked) == {case.generated_path}
    assert subject.read_bytes() == b'dirty host source must remain unchanged\n'
    assert tests.read_bytes() == b'dirty host tests must remain unchanged\n'
    assert not (case.repo / case.generated_path).exists()


@pytest.mark.parametrize('field', ('commit', 'tracked_tree_sha256', 'environment_sha256'))
def test_build_evidence_cannot_replay_under_wrong_source_or_environment(project_factory, tmp_path, field):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    wrong = dict(case.contract, **{field: '0' * len(case.contract[field])})
    with pytest.raises(ValueError):
        build.read_generated(wrong, case.authority, case.policy, evidence)


@pytest.mark.parametrize('field', ('baseline_commit', 'source_commit', 'protocol_binding'))
def test_build_evidence_cannot_replay_under_wrong_base_author_test_or_protocol(project_factory, tmp_path, field):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    wrong = copy.deepcopy(case.authority)
    wrong[field] = '0' * len(wrong[field])
    with pytest.raises(ValueError):
        build.read_generated(case.contract, wrong, case.policy, evidence)


def test_build_evidence_cannot_replay_for_other_independent_fixture(project_factory, tmp_path):
    build = implementation('native_build_v43')
    alpha, beta = project_factory('alpha'), project_factory('beta')
    evidence = build.prepare(alpha.contract, alpha.authority, alpha.policy, tmp_path / 'prepared')
    with pytest.raises(ValueError):
        build.read_generated(beta.contract, beta.authority, beta.policy, evidence)


def test_changed_build_recipe_binding_is_refused(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')

    def alter(value):
        if isinstance(value, dict):
            return {key: ('0' * 64 if 'recipe' in key.lower() and 'sha256' in key.lower() else alter(child))
                    for key, child in value.items()}
        if isinstance(value, list):
            return [alter(child) for child in value]
        return value
    wrong = alter(evidence)
    assert wrong != evidence, 'evidence must bind the executable build recipe'
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, wrong)


@pytest.mark.parametrize('change', ('retarget', 'delete', 'add'))
def test_original_scm_tag_snapshot_binds_evidence_and_changed_tags_refuse_replay(
        project_factory, tmp_path, change):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    if change == 'retarget':
        git(case.repo, 'tag', '-f', 'v1.0.0', case.augmented)
    elif change == 'delete':
        git(case.repo, 'tag', '-d', 'v1.0.0')
    else:
        git(case.repo, 'tag', 'v2.0.0', case.base)
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, evidence)
    with pytest.raises(ValueError):
        build.verify(case.contract, case.authority, case.policy, evidence, tmp_path / 'independent')


def test_author_test_descendant_tag_cannot_change_base_build_version(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    git(case.repo, 'tag', 'v9.9.9', case.augmented)
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    direct = original_backend_build(case, tmp_path / 'direct')
    assert wheel_members(wheel_artifact(evidence)) == wheel_members(direct)
    assert b'1.0.0' in build.read_generated(
        case.contract, case.authority, case.policy, evidence)[case.generated_path]


def test_forged_generated_wheel_with_consistent_hashes_requires_independent_rebuild(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    raw = wheel_members(wheel_artifact(evidence))[case.wheel_generated_path]
    forged = forged_wheel(evidence, tmp_path / 'forged' / wheel_artifact(evidence).name,
                          {case.wheel_generated_path: raw + b'\nFORGED_ACCEPTANCE_SENTINEL = True\n'})
    with pytest.raises(ValueError, match='(?i)(independent|rebuild|authentic|build.*differ)'):
        build.verify(case.contract, case.authority, case.policy, forged, tmp_path / 'independent')


def test_forged_wheel_cannot_change_original_tracked_source(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    forged = forged_wheel(evidence, tmp_path / 'forged' / wheel_artifact(evidence).name,
                          {case.package + '/subject.py': b'def value():\n    return 999\n'})
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, forged)


@pytest.mark.parametrize('member', ('test_extra.py', 'conftest.py', 'pytest.py', 'pyproject.toml',
                                  'new_root/_version.py', '../escape.py'))
def test_extra_undeclared_test_config_plugin_root_or_traversal_wheel_member_is_refused(
        project_factory, tmp_path, member):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    target = member if '/' in member else case.package + '/' + member
    forged = forged_wheel(evidence, tmp_path / 'forged' / wheel_artifact(evidence).name,
                          {target: b'VALUE = 1\n'})
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, forged)


@pytest.mark.parametrize('code', (b'pytest_plugins = []\n', b'def pytest_configure(config):\n    pass\n'))
def test_declared_generated_module_may_not_introduce_pytest_plugin_authority(project_factory, tmp_path, code):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    forged = forged_wheel(evidence, tmp_path / 'forged' / wheel_artifact(evidence).name,
                          {case.wheel_generated_path: code})
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, forged)


@pytest.mark.parametrize('kind', ('duplicate', 'symlink'))
def test_generated_wheel_duplicate_and_symlink_members_are_refused(project_factory, tmp_path, kind):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    raw = wheel_members(wheel_artifact(evidence))[case.wheel_generated_path]
    forged = forged_wheel(evidence, tmp_path / 'forged' / wheel_artifact(evidence).name,
                          {case.wheel_generated_path: raw},
                          extra_members=[(case.wheel_generated_path, raw)] if kind == 'duplicate' else (),
                          symlinks=[case.wheel_generated_path] if kind == 'symlink' else ())
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, forged)


def test_ambiguous_flat_and_src_package_roots_are_refused(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha', extra_files={'native_alpha_v43/__init__.py': b''})
    with pytest.raises(ValueError):
        build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')


@pytest.mark.parametrize('kind', ('generated-leaf-alias', 'package-root-alias'))
def test_declared_generated_path_cannot_replace_source_alias_or_follow_source_parent_alias(
        project_factory, tmp_path, kind):
    build = implementation('native_build_v43')
    if kind == 'generated-leaf-alias':
        case = project_factory('alpha', aliases={'src/native_alpha_v43/_version.py': 'subject.py'})
    else:
        case = project_factory('alpha', aliases={'src/native_alpha_v43/redirect.py': 'subject.py'},
                               declared='src/native_alpha_v43/redirect.py/_version.py')
    with pytest.raises(ValueError):
        build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')


@pytest.mark.parametrize('operation', ('read_generated', 'verify'))
def test_missing_build_artifact_is_refused(project_factory, tmp_path, operation):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    wheel_artifact(evidence).unlink()
    with pytest.raises(ValueError):
        args = [case.contract, case.authority, case.policy, evidence]
        if operation == 'verify':
            args.append(tmp_path / 'independent')
        getattr(build, operation)(*args)


def test_redirected_wheel_artifact_is_refused_even_with_identical_bytes(project_factory, tmp_path):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    evidence = build.prepare(case.contract, case.authority, case.policy, tmp_path / 'prepared')
    wheel = wheel_artifact(evidence)
    saved = wheel.with_name('saved-' + wheel.name)
    wheel.rename(saved)
    wheel.symlink_to(saved.name)
    with pytest.raises(ValueError):
        build.read_generated(case.contract, case.authority, case.policy, evidence)
