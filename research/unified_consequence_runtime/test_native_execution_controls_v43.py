"""Postimplementation V43 transport validation, not preimplementation controls.

The initial 2c23ade6 acceptance freeze remains unchanged.  These real-backend
local fixture controls retain the additional plugin/topology/accounting review
checks so that the qualification runner can reproduce them.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from . import native_build_v43 as build
from . import native_execution_v43 as worker
from .native_v43_test_support import make_project, modern_environment, project_factory


def _warm(case, output):
    evidence = build.prepare(case.contract, case.authority, case.policy, output)
    return case.with_evidence(evidence)


@pytest.fixture(scope='module')
def admitted(tmp_path_factory, modern_environment):
    root = tmp_path_factory.mktemp('postimplementation-native-v43')
    case = make_project(root/'honest', 'alpha', modern_environment)
    contract = _warm(case, root/'prepare')
    certificate = worker.collect(contract, case.authority, root/'collection', policy=case.policy)
    receipt = worker.verify(contract, {'replacements': []}, root/'native',
        authority=case.authority, admission_certificate=certificate, policy=case.policy)
    return case, contract, certificate, receipt, root


def _validate(admitted, receipt):
    case, contract, certificate, _, _ = admitted
    return worker.validate_receipt(contract, {'replacements': []}, case.authority,
        certificate, receipt, policy=case.policy, independent=False)


def _consistent_clone(receipt, output, mutation):
    clone = copy.deepcopy(receipt)
    (output/'generated-build-verification').mkdir(parents=True)
    clone['independent_collection']['output'] = str(output)
    record = clone['independent_collection']['build_verification']
    record['native_output'] = str(output)
    record['builder_attempts_after']['records'][-1] = str(output/'retained-build.json')
    mutation(record)
    (output/'generated-build-verification.json').write_text(worker.canonical(record)+'\n')
    (output/'generated-build-verification/verification.json').write_text(worker.canonical(record['receipt'])+'\n')
    (output/'retained-build.json').write_text(worker.canonical(record['receipt']['build'])+'\n')
    return clone


def test_honest_generated_native_receipt_retains_actual_build_accounting(admitted):
    receipt = admitted[3]
    assert receipt['status'] == 'PASS_NATIVE'
    assert _validate(admitted, receipt)['status'] == 'PASS_NATIVE'


def test_missing_generated_build_record_is_rejected(admitted):
    altered = copy.deepcopy(admitted[3])
    altered['independent_collection'].pop('build_verification')
    with pytest.raises(ValueError, match='UNKNOWN_V43_BUILD_ACCOUNTING'):
        _validate(admitted, altered)


def test_missing_retained_generated_build_sidecar_is_rejected(admitted):
    sidecar = Path(admitted[3]['independent_collection']['output'])/'generated-build-verification.json'
    saved = sidecar.with_suffix('.temporarily-held')
    sidecar.rename(saved)
    try:
        with pytest.raises(ValueError, match='UNKNOWN_V43_.*BUILD_ACCOUNTING'):
            _validate(admitted, admitted[3])
    finally:
        saved.rename(sidecar)


def test_unchanged_retained_accounting_clone_preserves_native_authority(admitted, tmp_path):
    clone = _consistent_clone(admitted[3], tmp_path/'unchanged', lambda record: None)
    assert _validate(admitted, clone)['status'] == 'PASS_NATIVE'


@pytest.mark.parametrize('forgery', ('zero-build-calls', 'recipe', 'counter'))
def test_consistently_modified_build_accounting_is_rejected(admitted, tmp_path, forgery):
    def mutation(record):
        if forgery == 'zero-build-calls':
            record['receipt']['costs']['build_calls'] = 0
            record['receipt']['build']['costs']['build_calls'] = 0
        elif forgery == 'recipe':
            record['receipt']['build']['recipe_sha256'] = '0'*64
        else:
            record['builder_attempts_after']['build_calls'] = 0
    altered = _consistent_clone(admitted[3], tmp_path/forgery, mutation)
    with pytest.raises(ValueError, match='UNKNOWN_V43_BUILD_'):
        _validate(admitted, altered)


@pytest.mark.parametrize('mutation', ('mode', 'parent-alias'))
def test_generated_mode_and_parent_alias_changes_refuse_native_warrant(project_factory, tmp_path, mutation):
    tail = '    from pathlib import Path\n    import native_alpha_v43._version as version\n'
    if mutation == 'mode':
        tail += '    Path(version.__file__).chmod(0o600)\n'
    else:
        tail += ('    parent = Path(version.__file__).parent\n'
                 '    saved = parent.with_name(parent.name + "_saved")\n'
                 '    parent.rename(saved)\n'
                 '    parent.symlink_to(saved.name, target_is_directory=True)\n')
    case = project_factory('alpha', test_tail=tail)
    contract = _warm(case, tmp_path/'prepare')
    certificate = worker.collect(contract, case.authority, tmp_path/'collection', policy=case.policy)
    receipt = worker.verify(contract, {'replacements': []}, tmp_path/'native',
        authority=case.authority, admission_certificate=certificate, policy=case.policy)
    assert receipt['status'] == 'UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    assert receipt['execution']['source_mutations']


def test_raw_generated_pytest_plugin_cannot_gain_native_authority(project_factory, tmp_path):
    plugin = (b'def pytest_configure(config):\n'
              b'    import native_alpha_v43._version as version\n'
              b'    config.pluginmanager.register(version, "generated-build-plugin")\n')
    case = project_factory('alpha', extra_files={'conftest.py': plugin})
    contract = _warm(case, tmp_path/'prepare')
    with pytest.raises(ValueError, match='UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'):
        worker.collect(contract, case.authority, tmp_path/'collection', policy=case.policy)
    checked = json.loads((tmp_path/'collection/checked-report.json').read_bytes())
    assert any(name.startswith('generated-pytest-plugin:') for name in checked['source_mutations'])


def test_independent_receipt_replay_exposes_fresh_actual_build_accounting(admitted, tmp_path):
    case, contract, certificate, receipt, _ = admitted
    checked = worker.validate_receipt(contract, {'replacements': []}, case.authority,
        certificate, receipt, policy=case.policy, output_dir=tmp_path/'replay', independent=True)
    actual = checked['independent_build_accounting']
    assert checked['status'] == 'PASS_NATIVE'
    assert actual['verification_attempts'] == 2
    assert actual['builder_attempts_after']['build_calls'] == actual['builder_attempts_before']['build_calls'] + 2
    assert all(record['receipt']['evidence_sha256'] == worker.fingerprint(contract['generated_build'])
               for record in actual['records'])
