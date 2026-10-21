"""Reviewer controls, separate from the original frozen acceptance suite.

Output and accounting checks were written after their implementation fixes and
are only post-fix regression controls.  Build-requirement checks were separately
written and executed before the corresponding production fix.  Exact run
records preserve that distinction.  None of these fixtures is prospective.
"""
from __future__ import annotations

import copy

import pytest

from .native_v43_test_support import (
    implementation, modern_environment, project_factory,
)


@pytest.mark.parametrize('location', ('root', 'working-tree', 'git-admin', 'package'))
def test_build_evidence_cannot_be_written_into_original_source_or_git_admin(
        project_factory, location):
    build = implementation('native_build_v43')
    case = project_factory('alpha')
    targets = {
        'root': case.repo,
        'working-tree': case.repo / 'new-evidence',
        'git-admin': case.repo / '.git' / 'new-evidence',
        'package': case.repo / 'src' / case.package / 'new-evidence',
    }
    output = targets[location]
    existed = output.exists()
    before = copy.deepcopy(build.attempt_snapshot())
    inventory = case.inventory()
    with pytest.raises(ValueError):
        build.prepare(case.contract, case.authority, case.policy, output)
    assert build.attempt_snapshot() == before, 'refused output must launch no build'
    assert output.exists() is existed, 'refusal must create no evidence directory'
    assert case.inventory() == inventory, 'immutable source and author tests remain exact'
    assert not (case.repo / case.generated_path).exists()


@pytest.mark.parametrize('value', (
    None, {}, {'output': '/tmp/not-an-invocation', 'costs': {}},
    {'output': '/tmp/not-an-invocation', 'costs': {}, 'build_verification': {}},
    {'output': '/tmp/not-an-invocation', 'costs': {},
     'build_verification': {'status': 'VERIFIED_GENERATED_BUILD',
                            'verification_attempts': 0, 'seconds': 0}},
))
def test_missing_or_malformed_new_build_accounting_is_not_accepted(value):
    worker = implementation('native_execution_v43')
    with pytest.raises(ValueError):
        worker._validate_build_accounting({'generated_build': {}}, value)


def test_tracked_only_receipt_cannot_smuggle_generated_build_accounting():
    worker = implementation('native_execution_v43')
    with pytest.raises(ValueError):
        worker._validate_build_accounting({'generated_build': None},
            {'output': '/tmp/not-an-invocation', 'costs': {},
             'build_verification': {'build_calls': 0}})


@pytest.mark.parametrize('requirement', (
    'hatch-vcs==999',
    'udm-missing-build-requirement-v43==1',
    'hatch-vcs @ file:///definitely-missing-udm-v43-build.whl',
))
def test_original_build_requirement_is_checked_before_native_build(
        project_factory, tmp_path, requirement):
    """Separate reviewer-discovered gap: frozen before its production fix.

    --no-build-isolation disables dependency resolution and does not establish
    that installed build dependencies satisfy the original source declaration.
    """
    build = implementation('native_build_v43')
    seed = project_factory('alpha')
    metadata = seed.files['pyproject.toml']
    if requirement.startswith('hatch-vcs'):
        metadata = metadata.replace(b'hatch-vcs==0.5.0', requirement.encode())
    else:
        metadata = metadata.replace(b'"hatch-vcs==0.5.0"]',
            b'"hatch-vcs==0.5.0", "' + requirement.encode() + b'"]')
    case = project_factory('alpha', extra_files={'pyproject.toml': metadata})
    before = copy.deepcopy(build.attempt_snapshot())
    output = tmp_path / 'incompatible-build'
    with pytest.raises(ValueError, match='UNKNOWN.*(BUILD|REQUIREMENT|DEPENDENCY|ENVIRONMENT)'):
        build.prepare(case.contract, case.authority, case.policy, output)
    assert build.attempt_snapshot() == before, 'incompatible build requirements grant no launch'
    assert not output.exists(), 'environment rejection precedes source materialization'
