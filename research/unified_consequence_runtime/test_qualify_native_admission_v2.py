"""Qualification gates on local evidence fixtures; no exposed task execution."""
import copy
import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


class AdmissionQualificationV2(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(
            'research.unified_consequence_runtime.qualify_native_admission_v2'),
            'versioned admission qualification entrypoint is required')
        self.qualification = importlib.import_module(
            'research.unified_consequence_runtime.qualify_native_admission_v2')

    @staticmethod
    def evidence():
        nodes = ['tests/test_native.py::test_old', 'tests/test_native.py::test_new[case]']
        certificate = {'collection': {'collected_test_nodes': nodes}}
        authority = {'required_test_nodes': ['tests/test_native.py::test_new']}
        receipt = {'status': 'FAIL_NATIVE',
            'junit': {'tests': 2, 'passed': 1, 'failures': 1, 'errors': 0, 'skipped': 0},
            'execution': {'collected_test_nodes': nodes, 'selected_test_nodes': nodes,
                'deselected_test_nodes': [], 'reports': [
                    {'nodeid': node, 'when': 'call', 'outcome': 'failed' if 'new' in node else 'passed',
                     'wasxfail': ''} for node in nodes]},
            'independent_reexecution': {'output': '/fixture/recheck', 'costs': {'native_calls': 1}}}
        return authority, certificate, receipt

    def test_first_gate_requires_independently_reexecuted_complete_protected_native_failure(self):
        authority, certificate, receipt = self.evidence()
        result = self.qualification.first_task_gate(authority, certificate, receipt)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['protected_failed_nodes'], ['tests/test_native.py::test_new[case]'])
        variants = [
            {**receipt, 'status': 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'},
            {**receipt, 'status': 'PASS_NATIVE'},
            {key: value for key, value in receipt.items() if key != 'independent_reexecution'},
            {**receipt, 'junit': {**receipt['junit'], 'skipped': 1}},
            {**receipt, 'execution': {**receipt['execution'], 'reports': receipt['execution']['reports'][:1]}},
            {**receipt, 'execution': {**receipt['execution'], 'deselected_test_nodes': ['hidden']}}]
        for wrong in variants:
            with self.subTest(wrong=wrong):
                self.assertEqual(self.qualification.first_task_gate(authority, certificate, wrong)['status'], 'FAIL')

    def test_unrelated_failure_cannot_satisfy_protected_native_failure_gate(self):
        authority, certificate, receipt = self.evidence()
        receipt['execution']['reports'][0]['outcome'] = 'failed'
        receipt['execution']['reports'][1]['outcome'] = 'passed'
        self.assertEqual(self.qualification.first_task_gate(authority, certificate, receipt)['status'], 'FAIL')

    def test_only_three_exact_previously_exposed_specs_are_licensed(self):
        protocol, policy, packages = self.qualification.inputs()
        self.assertEqual([row['repo'] for row in protocol['diagnostics']], [
            'more-itertools/more-itertools', 'python-attrs/attrs', 'python-attrs/cattrs'])
        self.assertEqual(len(policy['plugins']), 5)
        self.assertEqual(len(packages), 38)
        self.assertEqual(protocol['mode'], 'EXPOSED_DEVELOPMENT_DIAGNOSTICS_ADMISSION_ONLY')
        self.assertEqual(protocol['verdicts']['G2'], 'UNKNOWN')

    def test_state_snapshot_matches_existing_246_records_and_76_addresses(self):
        from .qualify_decisive_native import copy_state
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); copy_state(root)
            snapshot = self.qualification.state_snapshot(root / 'state')
            self.assertEqual(snapshot['records'], 246)
            self.assertEqual(len(snapshot['objects']), 76)
            self.assertEqual(snapshot['ledger_sha256'],
                'b3696b388d2f3d1df95d819d1026eb9f87f042e93e4300f0cd987073949de9ac')
            name = next(iter(snapshot['objects']))
            (root / 'state/objects' / name).write_bytes(b'forged')
            with self.assertRaisesRegex(ValueError, 'address'):
                self.qualification.state_snapshot(root / 'state')


if __name__ == '__main__':
    unittest.main()
