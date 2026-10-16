"""Adversarial admission checks on disposable local Git/pytest fixtures only."""
from __future__ import annotations

import copy
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from . import decisive_native_verify as frozen
from . import native_admission_v2 as admission
from . import native_execution_v2 as execution


SOURCE = "VALUE = 2\nVALUES = [1, 2]\n"
TESTS = '''import pytest
from sample import VALUE, VALUES

def test_old():
    assert True

@pytest.mark.parametrize("value", VALUES, ids=lambda value: str(value))
def test_new(value):
    assert value > 0
    assert VALUE == 2
'''


class NativeAdmissionV2AdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = frozen.environment_identity(sys.executable)
        cls.policy = {
            'schema': 'UDM_NATIVE_EXECUTION_POLICY_V2',
            'collection_seconds': 7,
            'execution_seconds': 7,
            'pytest_version': cls.environment['pytest_version'],
            'plugins': [],
        }

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='udm-admission-v2-adversarial-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'source'
        (self.repo / 'src/sample').mkdir(parents=True)
        (self.repo / 'tests').mkdir()
        (self.repo / 'src/sample/__init__.py').write_text(SOURCE)
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        (self.repo / 'pytest.ini').write_text('[pytest]\naddopts = --import-mode=importlib\n')
        self.git('init', '-q')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(TESTS)
        self.refresh()
        self.run_count = 0

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Admission Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def refresh(self):
        commit = self.commit()
        self.contract = {
            'schema': 'UDM_GENERIC_NATIVE_PYTEST_V2',
            'repository': 'local/admission-v2-adversarial',
            'repo_path': str(self.repo),
            'commit': commit,
            **frozen.source_identity(self.repo, commit),
            'interpreter': sys.executable,
            'environment_sha256': frozen.fingerprint(self.environment),
            'protocol_binding': 'e' * 64,
            'horizon_seconds': self.policy['execution_seconds'],
        }
        self.authority = admission.derive_suite_contract(
            self.repo, self.base, commit, 'e' * 64,
            repository=self.contract['repository'])

    def output(self, label):
        self.run_count += 1
        return self.root / f'{label}-{self.run_count}'

    def collect(self):
        return execution.collect(self.contract, self.authority, self.output('collection'),
                                 policy=self.policy)

    def verify(self, certificate, source=None):
        candidate = {'replacements': []}
        if source is not None:
            candidate['replacements'].append({
                'path': 'src/sample/__init__.py',
                'original_sha256': frozen.sha256(SOURCE.encode()),
                'replacement': source,
            })
        return execution.verify(
            self.contract, candidate, self.output('execution'), authority=self.authority,
            admission_certificate=certificate, policy=self.policy)

    def assert_unknown(self, receipt):
        self.assertTrue(receipt['status'].startswith('UNKNOWN_'), receipt['status'])
        self.assertNotIn(receipt['status'], ('PASS_NATIVE', 'FAIL_NATIVE'))

    def test_independent_collection_then_full_original_parameter_cases_pass(self):
        certificate = self.collect()
        execution.validate_certificate(self.contract, self.authority, certificate, policy=self.policy)
        receipt = self.verify(certificate)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')
        self.assertEqual(receipt['junit']['passed'], 3)

    def test_original_fixture_reorder_binds_collection_and_final_execution_orders(self):
        (self.repo / 'conftest.py').write_text(
            'def pytest_collection_modifyitems(items):\n'
            '    items.reverse()\n')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(TESTS)
        self.refresh()
        certificate = self.collect()
        collection = certificate['collection']
        self.assertEqual(collection['collected_test_nodes'], [
            'tests/test_native.py::test_old', 'tests/test_native.py::test_new[1]',
            'tests/test_native.py::test_new[2]'])
        self.assertEqual(collection['selected_test_nodes'],
                         list(reversed(collection['collected_test_nodes'])))
        self.assertEqual(set(collection['selected_test_nodes']),
                         set(collection['collected_test_nodes']))
        self.assertFalse(collection['deselected_test_nodes'])
        receipt = self.verify(certificate)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')
        self.assertEqual(receipt['junit']['passed'], 3)
        self.assertEqual([row['nodeid'] for row in receipt['execution']['reports']
                          if row['when'] == 'call'], collection['selected_test_nodes'])

    def test_candidate_cannot_change_original_fixture_order_or_discard_collected_nodes(self):
        (self.repo / 'conftest.py').write_text(
            'def pytest_collection_modifyitems(items):\n'
            '    from sample import VALUE\n'
            '    if VALUE == 2:\n'
            '        items.reverse()\n'
            '    elif VALUE == 1:\n'
            '        items[:] = items[1:] + items[:1]\n'
            '    else:\n'
            '        items.pop()\n')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(TESTS)
        self.refresh()
        certificate = self.collect()
        for value, change in [(1, 'order'), (0, 'discard')]:
            with self.subTest(change=change):
                receipt = self.verify(certificate, f'VALUE = {value}\nVALUES = [1, 2]\n')
                self.assertEqual(receipt['status'], 'UNKNOWN_EXACT_COLLECTION')

    def test_candidate_cannot_shrink_or_expand_cases_behind_same_static_prefix(self):
        certificate = self.collect()
        for values in ('[1]', '[1, 2, 3]'):
            with self.subTest(values=values):
                receipt = self.verify(certificate, f'VALUE = 2\nVALUES = {values}\n')
                self.assert_unknown(receipt)

    def test_actual_assertion_failure_remains_native_failure(self):
        receipt = self.verify(self.collect(), 'VALUE = 1\nVALUES = [1, 2]\n')
        self.assertEqual(receipt['status'], 'FAIL_NATIVE')
        self.assertEqual(receipt['junit']['failures'], 2)

    def test_candidate_module_skip_cannot_hide_original_assertions(self):
        receipt = self.verify(self.collect(), 'import pytest\n'
                              'pytest.skip("candidate suppression", allow_module_level=True)\n'
                              + SOURCE)
        self.assert_unknown(receipt)

    def test_skip_xfail_and_xpass_are_not_fully_executed_native_passes(self):
        sources = [
            TESTS.replace('def test_old():', '@pytest.mark.skip(reason="fixture")\ndef test_old():'),
            TESTS.replace('@pytest.mark.parametrize',
                          '@pytest.mark.xfail(reason="fixture")\n@pytest.mark.parametrize'),
            TESTS.replace('@pytest.mark.parametrize',
                          '@pytest.mark.xfail(reason="fixture")\n@pytest.mark.parametrize')
                 .replace('assert VALUE == 2', 'assert VALUE == 3'),
        ]
        for source in sources:
            (self.repo / 'tests/test_native.py').write_text(source)
            self.refresh()
            with self.subTest(source=source):
                self.assert_unknown(self.verify(self.collect()))

    def test_reasonless_xpass_is_not_a_native_warrant(self):
        for strict, marker in [(False, '@pytest.mark.xfail'),
                               (True, '@pytest.mark.xfail(strict=True)')]:
            (self.repo / 'tests/test_native.py').write_text(TESTS.replace(
                'def test_old():', marker + '\ndef test_old():'))
            self.refresh()
            with self.subTest(strict=strict):
                receipt = self.verify(self.collect())
                self.assertEqual(receipt['status'], 'UNKNOWN_SKIPPED_OR_XFAIL')

    def test_selection_exclusion_and_invalid_expression_fail_for_distinct_reasons(self):
        cases = [('-k "test_new and 1"', 'DESELECTION'),
                 ('-m included', 'DESELECTION'),
                 ('-k "("', 'COLLECTION_ERROR'),
                 ('-m "("', 'COLLECTION_ERROR')]
        for options, reason in cases:
            (self.repo / 'pytest.ini').write_text(
                '[pytest]\naddopts = --import-mode=importlib ' + options + '\n')
            (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
            self.base = self.commit()
            (self.repo / 'tests/test_native.py').write_text(TESTS.replace(
                '@pytest.mark.parametrize', '@pytest.mark.included\n@pytest.mark.parametrize'))
            self.refresh()
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, reason):
                self.collect()

    def test_candidate_source_or_author_test_rewrite_is_not_a_native_pass(self):
        certificate = self.collect()
        sources = [
            'from pathlib import Path\n'
            'Path(__file__).write_text("VALUE = 2\\nVALUES = [1, 2]\\n")\n' + SOURCE,
            'from pathlib import Path\n'
            'Path("tests/test_native.py").write_text("def test_old(): pass\\n")\n' + SOURCE,
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assert_unknown(self.verify(certificate, source))

    def test_preloaded_installed_project_name_cannot_replace_frozen_source(self):
        # pytest imports pluggy before the runner prepends the frozen src root.
        # A project with that same name must not inherit the installed module.
        (self.repo / 'src/sample').rename(self.repo / 'src/pluggy')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(
            'import pluggy\n'
            'def test_old(): assert True\n'
            'def test_new(): assert pluggy.__name__ == "pluggy"\n')
        self.refresh()
        try:
            certificate = self.collect()
        except ValueError:
            return  # Refusing admission is the required fail-closed result.
        if certificate.get('status', '').startswith('UNKNOWN_'):
            return
        self.assert_unknown(self.verify(certificate))

    def test_namespace_project_root_cannot_leak_to_installed_dependency(self):
        package = self.repo / 'src/pluggy'
        (self.repo / 'src/sample').rename(package)
        (package / '__init__.py').rename(package / 'implementation.py')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(
            'import pluggy\n'
            'def test_old(): assert True\n'
            'def test_new(): assert pluggy.__name__ == "pluggy"\n')
        self.refresh()
        try:
            certificate = self.collect()
        except ValueError:
            return
        self.assert_unknown(self.verify(certificate))

    def test_original_source_plugin_declaration_still_requires_external_license(self):
        (self.repo / 'conftest.py').write_text('pytest_plugins = ["pytester"]\n')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(TESTS)
        self.refresh()
        try:
            certificate = self.collect()
        except ValueError:
            return
        self.assert_unknown(self.verify(certificate))

    def test_original_plugin_with_exact_external_distribution_license_can_run(self):
        (self.repo / 'conftest.py').write_text('pytest_plugins = ["pytester"]\n')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(TESTS)
        self.refresh()
        self.policy = {**self.policy, 'plugins': [
            {'module': module, 'distribution': 'pytest',
             'version': self.environment['pytest_version']}
            for module in ('pytester', 'pytester_assertions')
        ]}
        receipt = self.verify(self.collect())
        self.assertEqual(receipt['status'], 'PASS_NATIVE')
        self.assertEqual(receipt['junit']['passed'], 3)

    def test_candidate_cannot_register_new_plugin_from_tracked_production_source(self):
        (self.repo / 'conftest.py').write_text(
            'def pytest_configure(config):\n'
            '    global MANAGER\n'
            '    MANAGER = config.pluginmanager\n')
        (self.repo / 'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base = self.commit()
        (self.repo / 'tests/test_native.py').write_text(TESTS)
        self.refresh()
        source = ('import conftest\n'
                  'class CandidatePlugin:\n'
                  '    def pytest_runtest_setup(self, item): pass\n'
                  'conftest.MANAGER.register(CandidatePlugin(), "candidate-plugin")\n'
                  + SOURCE)
        self.assert_unknown(self.verify(self.collect(), source))

    def test_collection_packet_stream_or_junit_tampering_is_rejected(self):
        certificate = self.collect()
        for name in ('stdout.log', 'stderr.log', 'native.xml'):
            forged = copy.deepcopy(certificate)
            forged['packet'][name] = base64.b64encode(b'forged retained evidence\n').decode()
            with self.subTest(file=name), self.assertRaises(ValueError):
                execution.validate_certificate(self.contract, self.authority, forged,
                                               policy=self.policy)

    def test_forged_collection_costs_and_injected_packet_files_are_rejected(self):
        certificate = self.collect()
        changes = [{'native_calls': 1}, {'collection_calls': 0}, {'horizon_seconds': 8},
                   {'seconds': -1}, {'total_seconds': -1}]
        for change in changes:
            forged = copy.deepcopy(certificate)
            forged['costs'].update(change)
            with self.subTest(costs=change), self.assertRaises(ValueError):
                execution.validate_certificate(self.contract, self.authority, forged,
                                               policy=self.policy)
        forged = copy.deepcopy(certificate)
        forged['packet']['self-asserted-authority.json'] = base64.b64encode(b'{}').decode()
        with self.assertRaises(ValueError):
            execution.validate_certificate(self.contract, self.authority, forged, policy=self.policy)

    def test_resealed_collection_manifest_is_checked_against_original_recollection(self):
        certificate = self.collect()
        forged = copy.deepcopy(certificate)
        # Keep both protected static prefixes but remove a parameter instance.
        missing = 'tests/test_native.py::test_new[2]'
        for key in ('collected_test_nodes', 'selected_test_nodes'):
            forged['collection'][key].remove(missing)
        forged['collection']['test_items'] = [
            row for row in forged['collection']['test_items'] if row['nodeid'] != missing]
        for name in ('report.json', 'checked-report.json'):
            report = json.loads(base64.b64decode(forged['packet'][name]))
            for key in ('collected_test_nodes', 'selected_test_nodes'):
                report[key].remove(missing)
            report['test_items'] = [row for row in report['test_items'] if row['nodeid'] != missing]
            forged['packet'][name] = base64.b64encode(frozen.canonical(report).encode()).decode()
        if 'packet_sha256' in forged:
            forged['packet_sha256'] = {
                name: frozen.sha256(base64.b64decode(value))
                for name, value in forged['packet'].items()
            }
        with self.assertRaisesRegex(ValueError, 'independent|collection|packet'):
            execution.validate_certificate(self.contract, self.authority, forged, policy=self.policy)

    def test_weaker_required_assertions_are_not_certificate_authority(self):
        certificate = self.collect()
        weaker = copy.deepcopy(self.authority)
        weaker['required_test_nodes'] = ['tests/test_native.py::test_old']
        with self.assertRaises(ValueError):
            execution.validate_certificate(self.contract, weaker, certificate, policy=self.policy)

    def test_certificate_cannot_replay_to_other_protocol_environment_source_or_horizon(self):
        certificate = self.collect()
        changes = [
            {'protocol_binding': 'f' * 64},
            {'environment_sha256': 'f' * 64},
            {'commit': self.base},
            {'tracked_tree_sha256': 'f' * 64},
            {'horizon_seconds': self.policy['execution_seconds'] + 1},
            {'repository': 'local/other-task'},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                execution.validate_certificate({**self.contract, **change}, self.authority,
                                               certificate, policy=self.policy)

    def test_certificate_cannot_replay_to_changed_execution_or_plugin_policy(self):
        certificate = self.collect()
        policies = [
            {**self.policy, 'collection_seconds': self.policy['collection_seconds'] + 1},
            {**self.policy, 'execution_seconds': self.policy['execution_seconds'] + 1},
            {**self.policy, 'plugins': [{'module': 'pytest', 'distribution': 'pytest',
                                      'version': self.environment['pytest_version']}]},
        ]
        for policy in policies:
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                execution.validate_certificate(self.contract, self.authority, certificate,
                                               policy=policy)

    def test_self_declared_extra_authority_and_missing_certificate_fields_are_rejected(self):
        certificate = self.collect()
        forged = copy.deepcopy(certificate)
        forged['required_test_nodes'] = ['tests/test_native.py::test_old']
        with self.assertRaises(ValueError):
            execution.validate_certificate(self.contract, self.authority, forged, policy=self.policy)
        for key in certificate:
            forged = copy.deepcopy(certificate)
            del forged[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                execution.validate_certificate(self.contract, self.authority, forged,
                                               policy=self.policy)

    def test_receipt_packet_log_mutation_and_omission_are_rejected(self):
        self.assertTrue(callable(getattr(execution, 'validate_receipt', None)),
                        'independent native receipt validator is required')
        certificate = self.collect()
        receipt = self.verify(certificate)
        candidate = {'replacements': []}
        execution.validate_receipt(self.contract, candidate, self.authority, certificate, receipt,
                                   policy=self.policy, independent=False)
        for name in ('stdout.log', 'stderr.log', 'report.json', 'checked-report.json',
                     'tracked-source-manifest.json', 'native.xml'):
            mutated = copy.deepcopy(receipt)
            mutated['packet'][name] = base64.b64encode(b'forged retained evidence\n').decode()
            omitted = copy.deepcopy(receipt)
            del omitted['packet'][name]
            for label, forged in [('mutated', mutated), ('omitted', omitted)]:
                with self.subTest(file=name, change=label), self.assertRaises(ValueError):
                    execution.validate_receipt(
                        self.contract, candidate, self.authority, certificate, forged,
                        policy=self.policy, independent=False)

    def test_fully_resealed_false_native_pass_requires_independent_candidate_execution(self):
        self.assertTrue(callable(getattr(execution, 'validate_receipt', None)),
                        'independent native receipt validator is required')
        certificate = self.collect()
        failing_source = 'VALUE = 1\nVALUES = [1, 2]\n'
        candidate = {'replacements': [{
            'path': 'src/sample/__init__.py',
            'original_sha256': frozen.sha256(SOURCE.encode()),
            'replacement': failing_source,
        }]}
        receipt = self.verify(certificate, failing_source)
        self.assertEqual(receipt['status'], 'FAIL_NATIVE')
        forged = copy.deepcopy(receipt)
        forged['status'] = 'PASS_NATIVE'
        forged['junit'] = {'tests': 3, 'passed': 3, 'failures': 0, 'errors': 0, 'skipped': 0}
        forged['execution']['exit_code'] = 0
        forged['execution']['process_exit_code'] = 0
        for report in forged['execution']['reports']:
            report['outcome'] = 'passed'
        for name in ('report.json', 'checked-report.json'):
            report = json.loads(base64.b64decode(forged['packet'][name]))
            report['exit_code'] = 0
            if 'process_exit_code' in report:
                report['process_exit_code'] = 0
            for phase in report['reports']:
                phase['outcome'] = 'passed'
            forged['packet'][name] = base64.b64encode(frozen.canonical(report).encode()).decode()
        xml = ET.fromstring(base64.b64decode(forged['packet']['native.xml']))
        for suite in xml.iter('testsuite'):
            suite.set('failures', '0')
            suite.set('errors', '0')
        for case in xml.iter('testcase'):
            for child in list(case):
                if child.tag in ('failure', 'error', 'skipped'):
                    case.remove(child)
        forged['packet']['native.xml'] = base64.b64encode(ET.tostring(xml)).decode()
        forged['packet']['stdout.log'] = base64.b64encode(b'3 passed in 0.01s\n').decode()
        forged['packet_sha256'] = {
            name: frozen.sha256(base64.b64decode(value))
            for name, value in forged['packet'].items()
        }
        structural = execution.validate_receipt(
            self.contract, candidate, self.authority, certificate, forged,
            policy=self.policy, independent=False)
        self.assertEqual(structural['status'], 'PASS_NATIVE')
        with self.assertRaisesRegex(ValueError, 'independent|execution|candidate'):
            execution.validate_receipt(
                self.contract, candidate, self.authority, certificate, forged,
                policy=self.policy, output_dir=self.output('receipt-recheck'), independent=True)

    def test_receipt_call_outcomes_must_agree_with_native_junit_counts(self):
        certificate = self.collect()
        receipt = self.verify(certificate)
        for outcome in ('failed', 'invalid-outcome'):
            forged = copy.deepcopy(receipt)
            for phase in forged['execution']['reports']:
                if phase['when'] == 'call':
                    phase['outcome'] = outcome
                    break
            for name in ('report.json', 'checked-report.json'):
                report = json.loads(base64.b64decode(forged['packet'][name]))
                report['reports'] = forged['execution']['reports']
                forged['packet'][name] = base64.b64encode(frozen.canonical(report).encode()).decode()
            forged['packet_sha256'] = {
                name: frozen.sha256(base64.b64decode(value))
                for name, value in forged['packet'].items()
            }
            with self.subTest(outcome=outcome), self.assertRaises(ValueError):
                execution.validate_receipt(
                    self.contract, {'replacements': []}, self.authority, certificate, forged,
                    policy=self.policy, output_dir=self.output('receipt-outcome'), independent=True)

    def test_equal_failure_counts_cannot_replay_different_native_case_outcomes(self):
        certificate = self.collect()
        failing_source = 'VALUE = 1\nVALUES = [1, 2]\n'
        candidate = {'replacements': [{
            'path': 'src/sample/__init__.py',
            'original_sha256': frozen.sha256(SOURCE.encode()),
            'replacement': failing_source,
        }]}
        receipt = self.verify(certificate, failing_source)
        self.assertEqual(receipt['junit']['failures'], 2)
        forged = copy.deepcopy(receipt)
        for phase in forged['execution']['reports']:
            if phase['when'] == 'call' and phase['nodeid'].endswith('::test_old'):
                phase['outcome'] = 'failed'
            elif phase['when'] == 'call' and phase['nodeid'].endswith('::test_new[1]'):
                phase['outcome'] = 'passed'
        for name in ('report.json', 'checked-report.json'):
            report = json.loads(base64.b64decode(forged['packet'][name]))
            report['reports'] = forged['execution']['reports']
            forged['packet'][name] = base64.b64encode(frozen.canonical(report).encode()).decode()
        xml = ET.fromstring(base64.b64decode(forged['packet']['native.xml']))
        failed_case = next(case for case in xml.iter('testcase') if case.get('name') == 'test_new[1]')
        previous_pass = next(case for case in xml.iter('testcase') if case.get('name') == 'test_old')
        failure = failed_case.find('failure')
        self.assertIsNotNone(failure)
        failed_case.remove(failure)
        previous_pass.append(failure)
        forged['packet']['native.xml'] = base64.b64encode(ET.tostring(xml)).decode()
        forged['packet_sha256'] = {
            name: frozen.sha256(base64.b64decode(value))
            for name, value in forged['packet'].items()
        }
        with self.assertRaisesRegex(ValueError, 'independent|outcome|execution'):
            execution.validate_receipt(
                self.contract, candidate, self.authority, certificate, forged,
                policy=self.policy, output_dir=self.output('receipt-cases'), independent=True)

    def test_resealed_wrong_import_source_is_not_authenticated_by_equal_pass_counts(self):
        certificate = self.collect()
        receipt = self.verify(certificate)
        forged = copy.deepcopy(receipt)
        imported = next(row for row in forged['execution']['import_manifest']
                        if row['path'] == 'src/sample/__init__.py')
        imported['sha256'] = 'f' * 64
        for name in ('report.json', 'checked-report.json'):
            report = json.loads(base64.b64decode(forged['packet'][name]))
            report['import_manifest'] = forged['execution']['import_manifest']
            forged['packet'][name] = base64.b64encode(frozen.canonical(report).encode()).decode()
        forged['packet_sha256'] = {
            name: frozen.sha256(base64.b64decode(value))
            for name, value in forged['packet'].items()
        }
        with self.assertRaisesRegex(ValueError, 'independent|import|source|execution'):
            execution.validate_receipt(
                self.contract, {'replacements': []}, self.authority, certificate, forged,
                policy=self.policy, output_dir=self.output('receipt-import'), independent=True)


if __name__ == '__main__':
    unittest.main()
