"""Private original environment binding controls, without new target acquisition."""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import FunctionType

import pytest

from .native_v45_test_support import project_factory, modern_environment, implementation
from . import native_environment_v44 as original
from . import native_environment_v42 as typed
from . import native_environment_v3 as portable
from . import native_admission_v42 as old_admission
from . import developmental_machine_v44 as framework


def operation():
    return implementation('native_environment_v45')


def test_original_profile_package_and_selection_mechanics_are_privately_bound():
    module = operation()
    assert inspect.signature(module.provision) == inspect.signature(original.provision)
    assert module._original_provision.__code__ is typed._original_provision.__code__
    assert module.selection is original.selection
    assert module._original_provision.__globals__ is not typed._original_provision.__globals__
    v2 = module._original_provision.__globals__['previous']
    assert v2.provision.__code__ is typed._v2_proxy.provision.__code__
    assert v2.provision.__globals__['derive_suite_contract'] is module.admission.derive_suite_contract
    assert typed._v2_proxy.provision.__globals__['derive_suite_contract'] is old_admission.derive_suite_contract
    assert module.bound_provision.__code__ is portable.bound_provision.__code__
    assert module.installed_package_identity.__code__ is portable.installed_package_identity.__code__
    profile = json.loads((Path(__file__).parent/'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json').read_text())['profiles'][-1]
    policy = module.execution_policy(profile, collection_seconds=17, execution_seconds=29)
    assert policy == dict(original.execution_policy(profile, collection_seconds=17, execution_seconds=29),
                          schema='UDM_NATIVE_EXECUTION_POLICY_V45')
    files = {'pyproject.toml': b'[project]\nname="fixture"\nversion="1.0"\nrequires-python=">=3.9"\n'}
    catalog = json.loads((Path(__file__).parent/'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json').read_text())
    assert module.diagnose(files, catalog) == original.diagnose(files, catalog)


def test_exact_prepared45_interface_keeps_namespace_authority_and_original_machine(project_factory, tmp_path):
    module = operation()
    case = project_factory(control='W01_closed_production_wildcard')
    value = framework.Machine(Path('/workspace/components'), tmp_path/'state', tmp_path/'evaluator', tmp_path/'config')
    setup = {'status': 'PREPARED', 'contract': case.contract, 'authority': case.authority, 'policy': case.policy}
    result = module._attach_interface(value, setup, tmp_path/'materialization')
    assert result['schema'] == 'UDM_SOURCE_ENVIRONMENT_ADMISSION_V45'
    assert result['contract'] == case.contract
    assert result['policy'] == case.policy
    assert result['authority'] == case.authority
    assert result['authority']['namespace_certificate'] == case.authority['namespace_certificate']
    assert result['materialization_capability'] is None
    assert result['materialization_status'] == 'TRACKED_ONLY_OR_UNKNOWN_UNSUPPORTED_DECLARATION'
    assert setup == {'status': 'PREPARED', 'contract': case.contract, 'authority': case.authority, 'policy': case.policy}


def test_v45_interface_never_projects_new_namespace_authority_into_old_worker(project_factory, tmp_path):
    module = operation()
    case = project_factory(control='W01_closed_production_wildcard')
    value = framework.Machine(Path('/workspace/components'), tmp_path/'state', tmp_path/'evaluator', tmp_path/'config')
    setup = {'status': 'PREPARED', 'contract': dict(case.contract, schema='UDM_GENERIC_NATIVE_PYTEST_V43'),
             'authority': case.authority, 'policy': dict(case.policy, schema='UDM_NATIVE_EXECUTION_POLICY_V43')}
    with pytest.raises(ValueError, match='V45'):
        module._attach_interface(value, setup, tmp_path/'materialization')
    with pytest.raises(ValueError, match='environment selection witness'):
        module.preflight_bootstrap(value, {'capability_id': 'not-selected'}, case.contract, case.authority, case.policy)


def test_original_provisioner_tracked_contract_gains_explicit_v45_generated_field(project_factory):
    module = operation()
    case = project_factory(control='W01_closed_production_wildcard')
    original_fields = {key: value for key, value in case.contract.items() if key != 'generated_build'}
    provisioner = module.bound_provision(case.contract['interpreter'])
    files, manifest, environment, plugins = provisioner.__globals__['execution']._context(
        original_fields, case.authority, case.policy)
    assert dict(files) == dict(case.files)
    assert manifest == case.manifest
    assert environment['pytest_version'] == case.policy['pytest_version']
    assert plugins == []
    assert 'generated_build' not in original_fields


def test_original_metadata_and_materialization_algorithms_keep_private_v45_bindings():
    module = operation()
    from . import native_materialization_v43 as original_materialization
    assert module.preflight_bootstrap.__code__ is original.preflight_bootstrap.__code__
    assert module.bind_bootstrap_environment.__code__ is original.bind_bootstrap_environment.__code__
    assert module.preflight_bootstrap.__globals__['_LOADED_SHA256'] == module._LOADED_SHA256
    assert module.preflight_bootstrap.__globals__['previous'].execution is module.execution
    assert module.materialization.request.__code__ is original_materialization.request.__code__
    assert module.materialization.request.__globals__['admission'] is module.admission
    assert module.materialization.request.__globals__['build'] is module.execution.build
    for name, function in vars(original_materialization.MaterializationRuntime).items():
        if isinstance(function, FunctionType):
            bound = vars(module.MaterializationRuntime)[name]
            assert bound.__code__ is function.__code__
            assert bound.__globals__ is not vars(original_materialization)
            assert bound.__globals__['admission'] is module.admission
            assert bound.__globals__['build'] is module.execution.build


def test_original_declared_materialization_can_carry_v45_namespace_authority(modern_environment, tmp_path):
    module = operation()
    from . import native_v43_test_support as original_fixture
    from .native_v45_test_support import MODERN, record_evidence
    original_case = original_fixture.make_project(tmp_path/'original-declared', 'namespace45', modern_environment)
    contract = dict(original_case.contract, schema=module.execution.SCHEMA, interpreter=str(MODERN))
    policy = dict(original_case.policy, schema=module.execution.POLICY_SCHEMA)
    authority = module.admission.derive_suite_contract(original_case.repo, original_case.base,
        original_case.augmented, contract['protocol_binding'], repository=contract['repository'])
    value = framework.Machine(Path('/workspace/components'), tmp_path/'state', tmp_path/'evaluator', tmp_path/'config')
    setup = module._attach_interface(value, {'status': 'PREPARED', 'contract': contract,
        'authority': authority, 'policy': policy}, tmp_path/'materialization')
    assert setup['status'] == 'PREPARED'
    assert setup['materialization_status'] == 'AUTHENTICATED_BUILD_ONLY'
    assert setup['authority'] == authority
    assert setup['contract']['generated_build'] is not None
    binding = setup['materialization_binding']
    assert binding['capability_id'] == setup['materialization_capability']
    assert binding['consequence_id'] in value.flash_live_ids()
    certificate = module.execution.collect(setup['contract'], authority, tmp_path/'collection', policy=policy)
    receipt = module.execution.verify(setup['contract'], {'replacements': []}, tmp_path/'native',
        authority=authority, admission_certificate=certificate, policy=policy)
    assert receipt['status'] == 'PASS_NATIVE'
    from .native_runtime_v45 import NativeRuntimeV45
    runtime = NativeRuntimeV45(value, setup['contract'], authority, certificate, policy, tmp_path/'runtime',
        materialization_capability=setup['materialization_capability'])
    assert runtime.materialization_binding == binding
    assert runtime._observation_premises()[-2:] == (binding['capability_id'], binding['consequence_id'])
    before = module.execution.attempt_snapshot()
    value.append('revoke', {'target': binding['consequence_id'],
                           'reason': 'engineering exact materialization invocation withdrawal'})
    value.flush()
    with pytest.raises(PermissionError, match='withdrawn'):
        runtime._scope()
    assert module.execution.attempt_snapshot() == before
    assert set(value.mt.live_ids(value.log)) == value.flash_live_ids()
    record_evidence(tmp_path, tmp_path/'collection/admission-certificate.json', tmp_path/'native/receipt.json')
