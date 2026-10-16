"""Qualification contracts over local evidence only; no exposed task execution."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class EnvironmentQualificationV3(unittest.TestCase):
    def setUp(self):
        name = 'research.unified_consequence_runtime.qualify_environment_selection_v3'
        self.assertIsNotNone(importlib.util.find_spec(name), 'versioned qualification entrypoint required')
        self.q = importlib.import_module(name)

    @staticmethod
    def evidence():
        nodes = ['tests/test_original.py::test_old', 'tests/test_original.py::test_protected[case]']
        certificate = {'collection': {'collected_test_nodes': nodes, 'selected_test_nodes': nodes,
                                     'deselected_test_nodes': []}}
        authority = {'required_test_nodes': ['tests/test_original.py::test_protected']}
        reports = [{'nodeid': node, 'when': phase,
                    'outcome': 'failed' if index == 1 and phase == 'call' else 'passed', 'wasxfail': ''}
                   for index, node in enumerate(nodes) for phase in ('setup', 'call', 'teardown')]
        data = {'collected_test_nodes': nodes, 'selected_test_nodes': nodes,
                'deselected_test_nodes': [], 'reports': reports, 'collection_errors': [],
                'source_mutations': [], 'unexpected_imports': [], 'external_project_imports': [],
                'changed_test_code': [], 'plugin_violations': [], 'timeout': False, 'process_exit_code': 1}
        receipt = {'status': 'FAIL_NATIVE', 'execution': data,
                   'junit': dict(tests=2, passed=1, failures=1, errors=0, skipped=0),
                   'costs': {'native_calls': 1},
                   'independent_reexecution': {'output': '/fixture/independent', 'costs': {'native_calls': 1}}}
        return authority, certificate, receipt

    def test_complete_protected_actual_failure_and_second_execution_pass(self):
        result = self.q.task_gate(*self.evidence())
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['selected_nodes'], 2)
        self.assertEqual(result['protected_failed_nodes'], ['tests/test_original.py::test_protected[case]'])

    def test_each_original_node_requires_setup_call_and_teardown(self):
        for phase in ('setup', 'call', 'teardown'):
            authority, certificate, receipt = self.evidence()
            receipt['execution']['reports'] = [r for r in receipt['execution']['reports']
                                             if not (r['when'] == phase and 'old' in r['nodeid'])]
            with self.subTest(phase=phase):
                self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_independently_collected_selection_order_is_preserved(self):
        authority, certificate, receipt = copy.deepcopy(self.evidence())
        selected = list(reversed(certificate['collection']['selected_test_nodes']))
        certificate['collection']['selected_test_nodes'] = selected
        receipt['execution']['selected_test_nodes'] = selected
        receipt['execution']['reports'] = [row for node in selected
            for row in receipt['execution']['reports'] if row['nodeid'] == node]
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'PASS')

    def test_only_the_two_prior_development_specs_are_licensed(self):
        protocol, catalog = self.q.inputs()
        self.assertEqual([(row['repo'].lower(), row['pr']) for row in protocol['diagnostics']],
            [('grahamdumpleton/wrapt', 99), ('more-itertools/more-itertools', 1309)])
        self.assertTrue(all(row['role'] == 'DEVELOPMENT_DIAGNOSTICS_ONLY' for row in protocol['diagnostics']))
        self.assertEqual(len(catalog['profiles']), 2)
        self.assertTrue(all(protocol['verdicts'][f'G{i}'] == 'UNKNOWN' for i in range(2, 7)))

    def test_skip_xfail_deselection_count_gap_and_unrelated_failure_fail_closed(self):
        mutations = [
            lambda r: r['execution']['reports'][0].update(outcome='skipped'),
            lambda r: r['execution']['reports'][1].update(wasxfail='reason'),
            lambda r: r['execution']['deselected_test_nodes'].append('hidden'),
            lambda r: r['junit'].update(tests=3),
            lambda r: r['execution']['reports'][2].update(outcome='failed'),
            lambda r: r['execution']['reports'][4].update(outcome='passed'),
            lambda r: r['execution'].update(selected_test_nodes=list(reversed(r['execution']['selected_test_nodes']))),
        ]
        for index, mutate in enumerate(mutations):
            authority, certificate, receipt = copy.deepcopy(self.evidence()); mutate(receipt)
            with self.subTest(index=index):
                self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_source_import_plugin_code_and_missing_independent_execution_refuse(self):
        for field in ('collection_errors', 'source_mutations', 'unexpected_imports',
                      'external_project_imports', 'changed_test_code', 'plugin_violations'):
            authority, certificate, receipt = self.evidence()
            receipt['execution'][field] = ['changed']
            with self.subTest(field=field):
                self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')
        authority, certificate, receipt = self.evidence(); del receipt['independent_reexecution']
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_unrelated_actual_call_failure_cannot_replace_protected_failure(self):
        authority, certificate, receipt = self.evidence()
        receipt['execution']['reports'][1]['outcome'] = 'failed'
        receipt['execution']['reports'][4]['outcome'] = 'passed'
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_native_success_is_not_the_required_original_regression_failure(self):
        authority, certificate, receipt = self.evidence(); receipt['status'] = 'PASS_NATIVE'
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_unknown_native_status_cannot_qualify(self):
        authority, certificate, receipt = self.evidence(); receipt['status'] = 'UNKNOWN_NATIVE_ERROR'
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_duplicate_original_node_is_refused(self):
        authority, certificate, receipt = self.evidence()
        certificate['collection']['selected_test_nodes'].append(certificate['collection']['selected_test_nodes'][0])
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_incomplete_original_collection_is_refused(self):
        authority, certificate, receipt = copy.deepcopy(self.evidence())
        certificate['collection']['collected_test_nodes'] = certificate['collection']['collected_test_nodes'][:1]
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_original_certificate_deselection_is_refused(self):
        authority, certificate, receipt = self.evidence(); certificate['collection']['deselected_test_nodes'] = ['hidden']
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_native_timeout_is_refused(self):
        authority, certificate, receipt = self.evidence(); receipt['execution']['timeout'] = True
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_native_process_error_is_refused(self):
        authority, certificate, receipt = self.evidence(); receipt['execution']['process_exit_code'] = 2
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_junit_errors_are_refused(self):
        authority, certificate, receipt = self.evidence(); receipt['junit']['errors'] = 1
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_junit_skipped_tests_are_refused(self):
        authority, certificate, receipt = self.evidence(); receipt['junit']['skipped'] = 1
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_producer_without_one_native_call_is_refused(self):
        authority, certificate, receipt = self.evidence(); receipt['costs']['native_calls'] = 0
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_second_execution_without_one_native_call_is_refused(self):
        authority, certificate, receipt = self.evidence(); receipt['independent_reexecution']['costs']['native_calls'] = 0
        self.assertEqual(self.q.task_gate(authority, certificate, receipt)['status'], 'UNKNOWN')

    def test_admission_gate_requires_both_diagnostics_and_no_genuine_frontier_verdict(self):
        passed = {'status': 'PASS'}
        self.assertEqual(self.q.first_task_gate([passed, passed])['status'], 'PASS')
        for gates in ([], [passed], [passed, {'status': 'UNKNOWN'}], [passed, passed, passed]):
            self.assertEqual(self.q.first_task_gate(gates)['status'], 'UNKNOWN')

    def test_freeze_requires_clean_source_and_preserves_every_baseline_file(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode().strip()
            git('init', '-q'); git('config', 'user.name', 'Fixture'); git('config', 'user.email', 'fixture@example.invalid')
            (repo/'old.py').write_text('original\n'); git('add', '.'); git('commit', '-qm', 'baseline')
            base = git('rev-parse', 'HEAD')
            (repo/'new.py').write_text('new version\n'); git('add', '.'); git('commit', '-qm', 'new only')
            frozen = self.q.freeze_source(repo, base, ['old.py', 'new.py'])
            self.assertEqual(frozen['source_commit'], git('rev-parse', 'HEAD'))
            self.assertEqual(set(frozen['files']), {'old.py', 'new.py'})
            (repo/'new.py').write_text('dirty\n')
            with self.assertRaisesRegex(ValueError, 'clean|commit'):
                self.q.freeze_source(repo, base, ['old.py', 'new.py'])
            git('checkout', '--', 'new.py'); (repo/'old.py').write_text('changed\n')
            git('add', '.'); git('commit', '-qm', 'changed old file')
            with self.assertRaisesRegex(ValueError, 'baseline|prior'):
                self.q.freeze_source(repo, base, ['old.py', 'new.py'])

    def test_preflight_validation_time_is_in_complete_qualification_wall_time(self):
        protocol, catalog = self.q.inputs(); protocol = copy.deepcopy(protocol); protocol['diagnostics'] = []
        clock = [0.0]
        def inputs():
            clock[0] += 5; return protocol, catalog
        def checked(*_):
            clock[0] += 7; return {'source_commit': 'fixture', 'runtimes': {}}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); freeze = root/'FREEZE.json'; freeze.write_text('{}\n')
            args = SimpleNamespace(repo=root, freeze=freeze, out=root/'evidence', components=root)
            with patch.object(self.q, 'inputs', inputs), patch.object(self.q, 'check_freeze', checked), \
                    patch.object(self.q, 'preserve_authority', return_value={}), \
                    patch.object(self.q.time, 'monotonic', side_effect=lambda: clock[0]):
                result = self.q.qualify(args)
            self.assertEqual(result['total_wall_seconds'], 19)

    def test_malformed_native_report_retains_launch_attempt_costs_in_task_finally(self):
        protocol, catalog = self.q.inputs(); protocol = copy.deepcopy(protocol)
        protocol['diagnostics'] = protocol['diagnostics'][:1]
        counters = {'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0}
        authority, certificate, _ = self.evidence(); certificate['costs'] = {}
        def collect(*_, **__):
            counters['collection_calls'] += 1; counters['subprocess_attempts'] += 1
            return certificate
        def verify(*_, **__):
            counters['collection_calls'] += 1; counters['native_calls'] += 1; counters['subprocess_attempts'] += 2
            raise json.JSONDecodeError('malformed native report', '[', 1)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); freeze = root/'FREEZE.json'; freeze.write_text('{}\n')
            args = SimpleNamespace(repo=root, freeze=freeze, out=root/'evidence', components=root)
            with patch.object(self.q, 'inputs', return_value=(protocol, catalog)), \
                    patch.object(self.q, 'check_freeze', return_value={'source_commit': 'fixture', 'runtimes': {}}), \
                    patch.object(self.q, 'preserve_authority', return_value={}), \
                    patch.object(self.q.environment, 'provision', return_value={
                        'status': 'PREPARED', 'contract': {}, 'authority': authority, 'policy': {}}), \
                    patch.object(self.q.execution, 'attempt_snapshot', side_effect=lambda: dict(counters)), \
                    patch.object(self.q.execution, 'collect', collect), patch.object(self.q.execution, 'verify', verify):
                result = self.q.qualify(args)
            self.assertEqual(result['tasks'][0]['status'], 'UNKNOWN_DIAGNOSTIC')
            self.assertEqual(result['tasks'][0]['attempt_costs'], counters)
            self.assertEqual(result['attempt_costs'], counters)
            self.assertEqual(json.loads((root/'evidence/RESULT.json').read_text())['tasks'][0]['attempt_costs'], counters)

    def test_cli_preflight_failure_preserves_error_and_elapsed_without_target_calls(self):
        clock = [0.0]
        def refused():
            clock[0] += 5; raise ValueError('frozen input refused')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); out = root/'evidence'
            with patch.object(self.q, 'inputs', refused), \
                    patch.object(self.q.time, 'monotonic', side_effect=lambda: clock[0]), \
                    patch.object(self.q.environment, 'provision') as transport:
                with self.assertRaises(SystemExit) as stopped:
                    self.q.main(['--repo', str(root), '--out', str(out), '--components', str(root),
                                 '--freeze', str(root/'FREEZE.json')])
            self.assertEqual(stopped.exception.code, 1); transport.assert_not_called()
            error = json.loads((out/'ERROR.json').read_text())
            self.assertEqual(error['total_wall_seconds'], 5)
            self.assertIn('frozen input refused', error['error'])
            self.assertEqual(error['attempt_costs'], {'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0})


if __name__ == '__main__':
    unittest.main()
