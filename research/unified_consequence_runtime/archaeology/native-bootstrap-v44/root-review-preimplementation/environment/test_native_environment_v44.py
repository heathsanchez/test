"""Preimplementation controls for the bounded environment bootstrap seam."""
import importlib
import json
from pathlib import Path

import pytest

HERE = Path(__file__).parent
CATALOG = json.loads((HERE/'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json').read_text())


def operation():
    try:
        module = importlib.import_module('research.unified_consequence_runtime.native_environment_v44')
    except ModuleNotFoundError:
        module = None
    assert module is not None, 'versioned source-derived environment bootstrap is missing'
    return module


def project(dynamic='classifiers'):
    return {'pyproject.toml': ('[build-system]\nrequires=["hatchling"]\n'
        'build-backend="hatchling.build"\n[project]\nname="original_example"\n'
        'version="1.0"\nrequires-python=">=3.9"\ndynamic=["'+dynamic+'"]\n').encode()}


def test_dynamic_declared_metadata_becomes_a_typed_existing_operation_residual():
    files = project()
    before = dict(files)
    row = operation().diagnose(files, CATALOG)
    assert row['route'] == 'ACTIVATE_EXISTING_METADATA_OBSERVATION'
    assert row['operation'] == 'source.observe_native_metadata'
    assert row['original_selection']['reason'] == 'UNKNOWN_DYNAMIC_METADATA'
    assert row['native_authority'] == 'NOT_ESTABLISHED'
    assert files == before


def test_existing_compatible_environment_does_not_invent_a_metadata_operation():
    files = {'pyproject.toml': b'[project]\nname="original_example"\nversion="1.0"\nrequires-python=">=3.9"\n'}
    row = operation().diagnose(files, CATALOG)
    assert row['route'] == 'ACTIVATE_EXISTING_ENVIRONMENT'
    assert row['operation'] is None


def test_unresolved_setup_test_metadata_cannot_be_erased_by_wheel_observation():
    files = project()
    files['setup.py'] = b'from setuptools import setup\nsetup(tests_require=unknown())\n'
    assert operation().diagnose(files, CATALOG)['route'] == 'UNKNOWN'


def test_dynamic_unrelated_field_is_not_a_license_to_run_an_observer():
    files = project('description')
    row = operation().diagnose(files, CATALOG)
    assert row['route'] == 'ACTIVATE_EXISTING_ENVIRONMENT'
    assert row['operation'] is None


def test_no_compatible_profile_remains_an_environment_authority_residual():
    files = {'pyproject.toml': b'[project]\nrequires-python="<3.0"\n'}
    row = operation().diagnose(files, CATALOG)
    assert row['route'] == 'UNKNOWN'
    assert row['original_selection']['reason'] == 'UNKNOWN_NO_COMPATIBLE_PROFILE'


def test_backend_requirements_filter_never_grants_test_or_plugin_authority():
    module = operation()
    profile = CATALOG['profiles'][-1]
    row = module.build_profile_constraints(project(), profile)
    assert row['status'] == 'COMPATIBLE'
    assert row['native_authority'] == 'NOT_ESTABLISHED'
    missing = project()
    missing['pyproject.toml'] = missing['pyproject.toml'].replace(b'"hatchling"', b'"not-externally-pinned-package"')
    assert module.build_profile_constraints(missing, profile)['status'] != 'COMPATIBLE'


def test_skip_or_xfail_is_not_a_metadata_residual():
    module = operation()
    assert not module.can_repair_native_refusal('UNKNOWN_SKIPPED_OR_XFAIL')
    assert not module.can_repair_native_refusal('UNKNOWN_COLLECTION')
    assert not module.can_repair_native_refusal('FAIL_NATIVE')


def test_mixed_dynamic_optional_dependencies_remain_precise_unknown_before_build():
    files = project()
    files['pyproject.toml'] = files['pyproject.toml'].replace(
        b'dynamic=["classifiers"]', b'dynamic=["classifiers","optional-dependencies"]')
    row = operation().diagnose(files, CATALOG)
    assert row['route'] == 'UNKNOWN'
    assert row['operation'] is None


def test_metadata_binding_alone_cannot_be_grafted_into_native_execution_authority():
    binding = {'capability_id':'cap', 'generation':1, 'consequence_id':'invocation',
               'request_sha256':'0'*64, 'observation_sha256':'1'*64}
    with pytest.raises(ValueError, match='environment selection witness'):
        operation().preflight_bootstrap(None, binding, {}, {}, {})


def test_profile_costs_charge_all_actual_successful_and_failed_original_attempts():
    module = operation()
    before = {'build_calls':3, 'build_seconds':4.0, 'records':[{'old':True}]}
    after = {'build_calls':7, 'build_seconds':9.5,
             'records':[{'old':True}, {'status':'BUILD_COMMAND_PASS'}, {'status':'UNKNOWN_BUILD_EXECUTION'}]}
    row = module.profile_attempt_costs(before, after)
    assert row['build_calls'] == 4
    assert row['build_seconds'] == 5.5
    assert row['records'] == after['records'][1:]
    assert row['inclusive_not_additive'] is True
