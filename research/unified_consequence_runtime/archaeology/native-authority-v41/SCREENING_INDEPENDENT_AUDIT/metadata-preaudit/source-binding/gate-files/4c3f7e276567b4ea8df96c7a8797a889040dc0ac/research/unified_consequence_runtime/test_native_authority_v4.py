"""Frozen V4 acceptance: metadata choice never substitutes for native authority.

Run ``UDM_AUTHORITY_V4_BASELINE=v3 python -m unittest ...MetadataAuthorityV4``
for the intentionally behavioral RED baseline.  Normal runs import V4 lazily.
All native judgments use disposable Git sources and the real pinned V3 worker.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from . import decisive_native_verify as original
from . import native_execution_v3 as execution
from . import test_native_environment_selection_v3 as metadata_helpers
from . import test_native_execution_v3 as native_helpers


METADATA = b'[project]\nrequires-python = ">=3.11"\n'
NATIVE_METADATA = b'[project]\nrequires-python = ">=3.6,<4"\n'
MALFORMED = b'def invalid(:\n    print "python two corpus"\n'
BASELINE_VARIABLE = 'UDM_AUTHORITY_V4_BASELINE'


def selector():
    baseline = os.environ.get(BASELINE_VARIABLE)
    if baseline not in (None, 'v3'):
        raise ValueError('only the explicit v3 RED baseline alias is accepted')
    version = 'v3' if baseline == 'v3' else 'v4'
    return importlib.import_module(__package__ + '.native_environment_selection_' + version)


def inventory_hash(files):
    rows = {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(files.items())}
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class MetadataAuthorityV4(unittest.TestCase):
    def select(self, files, *profiles):
        return selector().select_profile(files, metadata_helpers.catalog(*(profiles or (metadata_helpers.profile(),))))

    def test_malformed_nonmetadata_python_does_not_veto_generic_environment_choice(self):
        for path in ('tests/data/python2_payload.py', 'src/broken_module.py',
                     'examples/invalid_syntax.py', 'fixtures/encoding.py'):
            with self.subTest(path=path):
                files = {'pyproject.toml': METADATA, path: MALFORMED}
                result = self.select(files)
                self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', result)
                self.assertEqual(result['selected_profile']['id'], 'modern')
                self.assertEqual(result['constraints']['source_sha256'], inventory_hash(files))
                self.assertFalse(any(row['path'] == path for row in result['constraints']['evidence']))

    def test_nonutf8_nonmetadata_python_is_byte_inventory_without_parser_veto(self):
        files = {'pyproject.toml': METADATA, 'fixtures/raw_python.py': b'\xff\x00\x81'}
        result = self.select(files)
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', result)
        self.assertEqual(result['constraints']['source_sha256'], inventory_hash(files))

    def test_every_tracked_byte_affects_inventory_even_unparsed_and_binary_files(self):
        files = {'pyproject.toml': METADATA, 'fixtures/legacy.py': MALFORMED,
                 'assets/data.bin': bytes(range(256)), 'README.md': b'fixture\n'}
        constraints = selector().derive_constraints(files)
        self.assertEqual(constraints['status'], 'DERIVED_SOURCE_CONSTRAINTS', constraints)
        self.assertEqual(constraints['source_sha256'], inventory_hash(files))
        for path in files:
            changed = dict(files, **{path: files[path] + b'\n'})
            with self.subTest(path=path):
                result = selector().derive_constraints(changed)
                self.assertEqual(result['source_sha256'], inventory_hash(changed))
                self.assertNotEqual(result['source_sha256'], constraints['source_sha256'])

    def test_selection_cannot_replay_after_ignored_fixture_byte_change(self):
        files = {'pyproject.toml': METADATA, 'fixtures/legacy.py': MALFORMED}
        catalog = metadata_helpers.catalog(metadata_helpers.profile())
        selected = selector().select_profile(files, catalog)
        self.assertEqual(selected['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', selected)
        selector().validate_selection(files, catalog, selected)
        with self.assertRaisesRegex(ValueError, 'SELECTION_IDENTITY'):
            selector().validate_selection({**files, 'fixtures/legacy.py': MALFORMED + b'# changed\n'}, catalog, selected)

    def test_malformed_authoritative_setup_remains_precise_unknown(self):
        result = self.select({'pyproject.toml': METADATA, 'setup.py': MALFORMED})
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'UNKNOWN_SOURCE_PARSER')

    def test_dynamic_and_unsupported_metadata_have_precise_unknown_reasons(self):
        cases = [
            ({'setup.py': b'from setuptools import setup\nsetup(python_requires=load())\n'}, 'UNKNOWN_DYNAMIC_METADATA'),
            ({'pyproject.toml': b'[project]\ndynamic=["requires-python"]\n'}, 'UNKNOWN_DYNAMIC_METADATA'),
            ({'pyproject.toml': METADATA + b'dependencies=["pkg @ https://example.invalid/a.whl"]\n'}, 'UNKNOWN_REQUIREMENT_GRAMMAR'),
            ({'pyproject.toml': METADATA + b'[dependency-groups]\ntest=[{include-group="test"}]\n'}, 'UNKNOWN_DEPENDENCY_GROUP'),
            ({'README.md': b'no declarations\n', 'fixture.py': MALFORMED}, 'UNKNOWN_UNDECLARED_PYTHON_COMPATIBILITY'),
            ({'pyproject.toml': METADATA, 'tox.ini': b'[tox]\nenvlist=py\n'}, 'UNKNOWN_METADATA_GRAMMAR'),
        ]
        for files, reason in cases:
            with self.subTest(reason=reason, files=sorted(files)):
                result = self.select(files)
                self.assertEqual(result['status'], 'UNKNOWN', result)
                self.assertEqual(result['reason'], reason, result)

    def test_static_authoritative_dependencies_and_python_still_constrain_catalog(self):
        files = {'setup.py': b'raise RuntimeError("metadata must not execute")\nfrom setuptools import setup\nsetup(python_requires=">=3.11,<3.13", install_requires=["attrs>=25"], extras_require={"test":["pytest>=8"]})\n',
                 'fixtures/legacy.py': MALFORMED}
        result = self.select(files, metadata_helpers.profile('old', '3.10.19', packages=['attrs==25.4.0']),
                             metadata_helpers.profile('underpinned', '3.11.9', packages=['attrs==24.1.0']),
                             metadata_helpers.profile('valid', packages=['attrs==25.4.0']))
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', result)
        self.assertEqual(result['selected_profile']['id'], 'valid')
        self.assertEqual([row['status'] for row in result['candidates']], ['REJECTED', 'UNKNOWN', 'COMPATIBLE'])

    def test_parseable_nonmetadata_api_mentions_are_deferred_to_native_authority(self):
        files = {'pyproject.toml': b'[project]\nrequires-python=">=3.6"\n',
                 'compat.py': b'import inspect as ins\nfrom pytest import collect as old\nx=ins.getargspec\ny=old.Module\n',
                 'fixtures/legacy.py': MALFORMED}
        result = self.select(files, metadata_helpers.profile('old', '3.6.12', '5.4.3'), metadata_helpers.profile())
        self.assertEqual(result['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', result)
        self.assertEqual(result['selected_profile']['id'], 'modern')
        self.assertNotIn('<3.11', result['constraints']['python_specifiers'])
        self.assertNotIn('pytest<6', [row['requirement'] for row in result['constraints']['requirements']])
        self.assertFalse(any(row['path'] == 'compat.py' for row in result['constraints']['evidence']))

    def test_external_catalog_license_and_selection_are_not_self_asserted(self):
        files = {'pyproject.toml': METADATA}
        profile = metadata_helpers.profile()
        profile['plugins'] = [{'module': 'unlicensed', 'distribution': 'absent', 'version': '1.0'}]
        result = self.select(files, profile)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'UNKNOWN_CATALOG_AUTHORITY')
        catalog = metadata_helpers.catalog(metadata_helpers.profile())
        selected = selector().select_profile(files, catalog)
        forged = copy.deepcopy(selected)
        forged['selected_profile']['id'] = 'candidate-asserted-authority'
        with self.assertRaisesRegex(ValueError, 'SELECTION_IDENTITY'):
            selector().validate_selection(files, catalog, forged)


# Reuse existing real native fixture methods; no worker/oracle mocking or edits.
_NATIVE_REGRESSIONS = (
    'test_independent_collection_then_full_original_parameter_cases_pass',
    'test_candidate_cannot_change_original_fixture_order_or_discard_collected_nodes',
    'test_candidate_cannot_shrink_or_expand_cases_behind_same_static_prefix',
    'test_actual_assertion_failure_remains_native_failure',
    'test_candidate_module_skip_cannot_hide_original_assertions',
    'test_selection_exclusion_and_invalid_expression_fail_for_distinct_reasons',
    'test_preloaded_installed_project_name_cannot_replace_frozen_source',
    'test_candidate_cannot_register_new_plugin_from_tracked_production_source',
    'test_resealed_collection_manifest_is_checked_against_original_recollection',
    'test_weaker_required_assertions_are_not_certificate_authority',
    'test_certificate_cannot_replay_to_other_protocol_environment_source_or_horizon',
    'test_certificate_cannot_replay_to_changed_execution_or_plugin_policy',
    'test_self_declared_extra_authority_and_missing_certificate_fields_are_rejected',
    'test_resealed_wrong_import_source_is_not_authenticated_by_equal_pass_counts',
)
_qualified = native_helpers.NativePortableQualifiedAdversarialTests
_methods = {name: vars(_qualified)[name] for name in
            ('setUpClass', 'setUp', 'git', 'commit', 'refresh', 'output', 'collect', 'verify', 'assert_unknown', *_NATIVE_REGRESSIONS)}
NativeAuthorityPreservationV4 = type('NativeAuthorityPreservationV4', (unittest.TestCase,), _methods)


class MalformedPythonNativeAuthorityV4(unittest.TestCase):
    setUpClass = classmethod(native_helpers.SelectedInterpreterNativeContracts.setUpClass.__func__)
    setUp = native_helpers.SelectedInterpreterNativeContracts.setUp
    git = native_helpers.SelectedInterpreterNativeContracts.git
    commit = native_helpers.SelectedInterpreterNativeContracts.commit
    fixture = native_helpers.SelectedInterpreterNativeContracts.fixture
    output = native_helpers.SelectedInterpreterNativeContracts.output
    test_missing_protected_assertion_is_refused = native_helpers.SelectedInterpreterNativeContracts.test_missing_protected_assertion_is_refused_in_selected_environment

    def malformed_fixture(self, body):
        (self.repo / 'fixtures').mkdir()
        (self.repo / 'fixtures/python2_payload.py').write_bytes(MALFORMED)
        (self.repo / 'pyproject.toml').write_bytes(NATIVE_METADATA)
        self.base = self.commit()
        self.contract, self.authority = self.fixture('def test_old(): assert True\ndef test_new():\n' + body)
        return self.contract, self.authority

    def test_unimported_malformed_fixture_allows_real_native_pass(self):
        contract, authority = self.malformed_fixture(' assert True\n')
        files = original._snapshot(self.repo, contract['commit'])[1]
        runtime_version = '.'.join(str(value) for value in self.environment['runtime_identity']['version_info'][:3])
        profile = metadata_helpers.profile('selected-runtime', runtime_version,
                                           self.environment['pytest_version'])
        selected = selector().select_profile(files, metadata_helpers.catalog(profile))
        self.assertEqual(selected['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', selected)
        self.assertEqual(selected['selected_profile'], profile)
        self.assertEqual(selected['constraints']['source_sha256'], inventory_hash(files))
        (self.root / 'selection.json').write_text(original.canonical(selected) + '\n')
        certificate = execution.collect(contract, authority, self.output(), policy=self.policy)
        receipt = execution.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                   admission_certificate=certificate, policy=self.policy)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')
        self.assertEqual(receipt['junit']['passed'], 2)
        checked = execution.validate_receipt(
            contract, {'replacements': []}, authority, certificate, receipt,
            policy=self.policy, output_dir=self.output(), independent=True)
        self.assertEqual(checked['status'], 'PASS_NATIVE')
        self.assertIn('independent_reexecution', checked)
        (self.root / 'checked-independent-receipt.json').write_text(original.canonical(checked) + '\n')

    def test_same_malformed_fixture_required_by_static_runtime_import_is_native_failure(self):
        contract, authority = self.malformed_fixture(' import fixtures.python2_payload\n assert True\n')
        certificate = execution.collect(contract, authority, self.output(), policy=self.policy)
        receipt = execution.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                   admission_certificate=certificate, policy=self.policy)
        self.assertEqual(receipt['status'], 'FAIL_NATIVE', receipt)
        self.assertEqual(receipt['junit']['failures'], 1)
        self.assertIn(b'SyntaxError', base64.b64decode(receipt['packet']['native.xml']))

    def test_dynamic_import_of_same_malformed_fixture_is_native_failure(self):
        contract, authority = self.malformed_fixture(' import importlib\n importlib.import_module("fixtures.python2_payload")\n assert True\n')
        certificate = execution.collect(contract, authority, self.output(), policy=self.policy)
        receipt = execution.verify(contract, {'replacements': []}, self.output(), authority=authority,
                                   admission_certificate=certificate, policy=self.policy)
        self.assertEqual(receipt['status'], 'FAIL_NATIVE', receipt)
        self.assertEqual(receipt['junit']['failures'], 1)

    def test_collection_time_import_of_same_malformed_fixture_is_refused(self):
        (self.repo / 'fixtures').mkdir()
        (self.repo / 'fixtures/python2_payload.py').write_bytes(MALFORMED)
        self.base = self.commit()
        contract, authority = self.fixture('import fixtures.python2_payload\ndef test_old(): assert True\ndef test_new(): assert True\n')
        with self.assertRaisesRegex(ValueError, 'COLLECTION_ERROR'):
            execution.collect(contract, authority, self.output(), policy=self.policy)


class LicensedPluginReplacementAuthorityV4(unittest.TestCase):
    setUpClass = vars(_qualified)['setUpClass']
    setUp = vars(_qualified)['setUp']
    git = vars(_qualified)['git']
    commit = vars(_qualified)['commit']
    refresh = vars(_qualified)['refresh']
    output = vars(_qualified)['output']
    collect = vars(_qualified)['collect']
    verify = vars(_qualified)['verify']
    assert_unknown = vars(_qualified)['assert_unknown']

    def test_candidate_cannot_replace_licensed_plugin_under_the_same_name(self):
        (self.repo / 'conftest.py').write_text(
            'def pytest_configure(config):\n'
            ' global MANAGER\n'
            ' MANAGER = config.pluginmanager\n')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(native_helpers.qualified_tests.TESTS)
        self.refresh()
        self.policy = {**self.policy, 'plugins': [
            {'module': 'doctest', 'distribution': 'pytest',
             'version': self.environment['pytest_version']}]}
        certificate = self.collect()
        source = ('import conftest\n'
                  'class ReplacementPlugin:\n'
                  ' def pytest_runtest_setup(self, item): pass\n'
                  'manager = conftest.MANAGER\n'
                  'manager.unregister(manager.get_plugin("doctest"))\n'
                  'manager.register(ReplacementPlugin(), "doctest")\n'
                  + native_helpers.qualified_tests.SOURCE)
        self.assert_unknown(self.verify(certificate, source))


def _retain_native_evidence(case):
    """Optionally archive raw outputs, including outputs preceding expected refusal."""
    destination = os.environ.get('UDM_V4_NATIVE_EVIDENCE_ROOT')
    if not destination:
        return
    target = Path(destination).absolute() / case.id()
    shutil.copytree(case.root, target, ignore=shutil.ignore_patterns(
        '.git', '__pycache__', '.venv', 'venv'))
    for filename in ('test_native_authority_v4.py', 'test_native_execution_v3.py',
                     'test_native_admission_v2_adversarial.py'):
        shutil.copyfile(Path(__file__).with_name(filename), target / filename)
    for label, revision in (('baseline', case.base), ('head', 'HEAD')):
        archive = subprocess.check_output(['git', '-C', str(case.repo), 'archive',
                                           '--format=tar', revision])
        (target / (label + '-source.tar')).write_bytes(archive)
    context = {'test_id': case.id(), 'policy': case.policy,
               'environment_sha256': original.fingerprint(case.environment)}
    for field in ('contract', 'authority'):
        if hasattr(case, field):
            context[field] = getattr(case, field)
    (target / 'fixture-context.json').write_text(original.canonical(context) + '\n')


def _with_evidence_retention(set_up):
    def retained_set_up(case):
        set_up(case)
        # addCleanup is LIFO, so archiving precedes the fixture's existing cleanup.
        case.addCleanup(_retain_native_evidence, case)
    return retained_set_up


for _case_class in (NativeAuthorityPreservationV4, MalformedPythonNativeAuthorityV4,
                    LicensedPluginReplacementAuthorityV4):
    _case_class.setUp = _with_evidence_retention(_case_class.setUp)
del _case_class, _qualified, _methods


if __name__ == '__main__':
    unittest.main()
