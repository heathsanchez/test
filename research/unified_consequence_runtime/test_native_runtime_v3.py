"""Bounded portable-native execution over real Machine state; no G3 claim."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from . import decisive_native_verify as original
from . import native_admission_v2 as admission
from . import native_execution_v2 as old_worker
from . import native_execution_v3 as worker
from . import native_runtime_v2 as frozen
from .developmental_machine import Machine

try:
    from . import native_runtime_v3 as runtime_module
except ImportError:
    runtime_module = None


class NativeRuntimeV3BindingContracts(unittest.TestCase):
    def test_portable_runtime_is_available(self):
        self.assertIsNotNone(runtime_module, 'portable worker requires a versioned runtime binding')

    @unittest.skipIf(runtime_module is None, 'runtime binding missing')
    def test_reused_algorithms_have_isolated_globals_and_keep_v2_unchanged(self):
        runtime = runtime_module.NativeRuntimeV3
        self.assertTrue(issubclass(runtime, frozen.NativeRuntimeV2))
        for name, function in vars(frozen.NativeRuntimeV2).items():
            if not isinstance(function, types.FunctionType) or name in ('_scope', '_expected_scope', '_verify'):
                continue
            with self.subTest(method=name):
                bound = vars(runtime)[name]
                self.assertIs(bound.__code__, function.__code__)
                self.assertIs(bound.__closure__, function.__closure__)
                self.assertIsNot(bound.__globals__, vars(frozen))
                self.assertIs(bound.__globals__['verifier'], worker)
                self.assertIs(bound.__globals__['AUTHORITY'], runtime_module.AUTHORITY)
                self.assertIsNot(bound.__globals__['AUTHORITY'], frozen.AUTHORITY)
                self.assertEqual(bound.__globals__['__file__'], runtime_module.__file__)
        self.assertIs(runtime_module._runtime_scope.__code__, frozen.NativeRuntimeV2._scope.__code__)
        self.assertIs(runtime_module._runtime_expected_scope.__code__, frozen.NativeRuntimeV2._expected_scope.__code__)
        self.assertIs(frozen.verifier, old_worker)
        self.assertEqual(frozen.NativeRuntimeV2.__init__.__globals__['__file__'], frozen.__file__)

    @unittest.skipIf(runtime_module is None, 'runtime binding missing')
    def test_runtime_and_worker_sources_are_checked_before_machine_access(self):
        script = '''import pathlib,sys,tempfile
from research.unified_consequence_runtime import native_runtime_v3 as r
with tempfile.TemporaryDirectory() as folder:
    path=pathlib.Path(folder)/'changed.py';path.write_text('changed source')
    if sys.argv[1]=='new':r.__file__=str(path)
    elif sys.argv[1]=='old':r.frozen.__file__=str(path)
    else:r.verifier.__file__=str(path)
    try:r.NativeRuntimeV3._scope(object.__new__(r.NativeRuntimeV3))
    except ValueError as error:assert 'SOURCE' in str(error),str(error)
    else:raise AssertionError('changed source accepted')
'''
        for target in ('new', 'old', 'worker'):
            with self.subTest(target=target):
                result = subprocess.run([sys.executable, '-B', '-c', script, target],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipIf(runtime_module is None, 'runtime binding missing')
class NativeRuntimeV3Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_folder = tempfile.TemporaryDirectory(prefix='udm-v3-runtime-source-')
        cls.addClassCleanup(cls.source_folder.cleanup)
        cls.repo = Path(cls.source_folder.name)/'source'
        cls.repo.mkdir()

        def git(*args):
            return subprocess.check_output(['git', '-C', str(cls.repo), *args], stderr=subprocess.PIPE).decode().strip()

        git('init', '-q')
        (cls.repo/'subject.py').write_text('def value():\n return 0\n')
        (cls.repo/'test_subject.py').write_text('def test_old(): assert True\n')
        git('add', '.')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base')
        base = git('rev-parse', 'HEAD')
        (cls.repo/'test_subject.py').write_text('from subject import value\ndef test_old(): assert True\ndef test_new(): assert value()==1\n')
        git('add', '.')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'independent assertion')
        commit = git('rev-parse', 'HEAD')
        environment = worker.environment_identity(sys.executable)
        cls.contract = {'schema': worker.SCHEMA, 'repository': 'fixture/runtime-v3', 'repo_path': str(cls.repo),
            'commit': commit, **original.source_identity(cls.repo, commit), 'interpreter': sys.executable,
            'environment_sha256': worker.fingerprint(environment), 'protocol_binding': 'f'*64, 'horizon_seconds': 7}
        cls.authority = admission.derive_suite_contract(cls.repo, base, commit, 'f'*64, repository=cls.contract['repository'])
        cls.policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 7, 'execution_seconds': 7,
                      'pytest_version': environment['pytest_version'], 'plugins': []}
        cls.certificate = worker.collect(cls.contract, cls.authority, Path(cls.source_folder.name)/'collection', policy=cls.policy)
        cls.candidate = {'replacements': [{'path': 'subject.py',
            'original_sha256': original.sha256((cls.repo/'subject.py').read_bytes()),
            'replacement': 'def value():\n return 1\n'}]}

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='udm-v3-runtime-state-')
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.components = Path(os.environ.get('UDM_COMPONENTS', '/workspace/components'))
        self.machine = self.reload_machine()
        self.runtime = self.new_runtime(self.machine)

    def reload_machine(self):
        return Machine(self.components, self.root/'state', self.root/'evaluator', self.root/'config')

    def new_runtime(self, machine):
        return runtime_module.NativeRuntimeV3(machine, self.contract, self.authority,
            self.certificate, self.policy, self.root/'native-output')

    def native_costs(self):
        return [row for row in self.machine.costs if row['phase'] == 'generic_native_v2_independent_verification']

    def test_two_actual_checks_admit_execute_persist_and_restart_in_separate_process(self):
        capability = self.runtime.admit(self.candidate)
        costs = self.native_costs()
        self.assertEqual(len(costs), 2)
        self.assertEqual([row['costs']['native_calls'] for row in costs], [1, 1])
        self.assertTrue(all(Path(row['output'], 'receipt.json').is_file() for row in costs))
        for row in costs:
            self.assertEqual(row['controller_attempts'],
                             {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2})
            self.assertTrue(row['accounting_complete'])
            self.assertEqual(row['costs'], json.loads(Path(row['output'], 'receipt.json').read_text())['costs'])
        descriptor = self.machine.descriptor(capability)
        self.assertEqual(descriptor.operation, 'native.pytest_suite')
        self.assertEqual(descriptor.scope['native_runtime_version'], 3)
        self.assertEqual(descriptor.scope['authority_ceiling'], frozen.AUTHORITY)
        self.assertEqual(descriptor.source['adapter_sha256'], original.sha256(Path(runtime_module.__file__).read_bytes()))
        self.assertEqual(descriptor.source['verifier_sha256'], worker._runner_hash())
        for key, expected in (('contract', self.contract), ('suite_authority', self.authority),
                              ('certificate', self.certificate), ('policy', self.policy)):
            self.assertEqual(self.machine.get(descriptor.source[key]), expected)
        receipt, consequence = self.runtime.execute(capability)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')
        self.assertEqual(len(self.native_costs()), 3)
        self.assertEqual(next(node for node in self.machine.log if node.id == consequence).premises, (capability,))
        cold = self.reload_machine()
        loaded = self.new_runtime(cold)
        self.assertEqual(loaded.source, self.runtime.source)
        self.assertEqual(loaded.execute(capability)[0]['status'], 'PASS_NATIVE')
        script = '''import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine import Machine
from research.unified_consequence_runtime.native_runtime_v3 import NativeRuntimeV3
components,state,output=map(Path,sys.argv[1:4]);capability=sys.argv[4]
machine=Machine(components,state,state.parent/'evaluator',state.parent/'config')
source=machine.descriptor(capability).source
runtime=NativeRuntimeV3(machine,*(machine.get(source[key]) for key in
    ('contract','suite_authority','certificate','policy')),output)
receipt,consequence=runtime.execute(capability)
print(json.dumps({'status':receipt['status'],'source':source,'consequence':consequence,
    'closure_agrees':set(machine.mt.live_ids(machine.log))==machine.flash_live_ids(),
    'native_calls':sum(row.get('costs',{}).get('native_calls',0) for row in machine.costs)}))
'''
        process = subprocess.run([sys.executable, '-B', '-c', script, str(self.components), str(cold.state),
            str(self.root/'separate-process-output'), capability], check=True, capture_output=True, text=True)
        restarted = json.loads(process.stdout)
        self.assertEqual(restarted['status'], 'PASS_NATIVE')
        self.assertTrue(restarted['closure_agrees'])
        self.assertEqual(restarted['source'], descriptor.source)
        self.assertEqual(restarted['native_calls'], 1)
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            loaded.projection_payload(capability)

    def test_withdrawing_source_stops_before_native_and_preserves_unrelated_record(self):
        self.check_withdrawal('source')

    def test_withdrawing_authority_stops_before_native_and_preserves_unrelated_record(self):
        self.check_withdrawal('authority')

    def test_withdrawing_policy_dependency_stops_before_native_and_preserves_unrelated_record(self):
        self.check_withdrawal('policy')

    def check_withdrawal(self, target):
        policy = self.machine.append('fixture_policy_dependency', {'policy': self.machine.put(self.policy)})
        self.machine.flush()
        capability = self.runtime.admit(self.candidate, dependencies=(policy,))
        unrelated = self.machine.append('fixture_unrelated', {'fixture_only': True})
        self.machine.flush()
        self.machine.append('revoke', {'target': policy if target == 'policy' else getattr(self.runtime, target),
                                      'reason': 'bounded fixture support withdrawal'})
        self.machine.flush()
        self.assertNotIn(capability, self.machine.flash_live_ids())
        self.assertIn(unrelated, self.machine.flash_live_ids())
        with self.assertRaises(PermissionError):
            self.runtime.execute(capability)
        self.assertEqual(len(self.native_costs()), 2)
        self.assertFalse(any(node.kind == 'verified_consequence' for node in self.machine.log))
        self.assertEqual(set(self.machine.mt.live_ids(self.machine.log)), self.machine.flash_live_ids())

    def test_changed_policy_is_refused_before_a_third_native_call(self):
        capability = self.runtime.admit(self.candidate)
        self.runtime.policy['execution_seconds'] = 8
        with self.assertRaisesRegex(ValueError, 'external input'):
            self.runtime.execute(capability)
        self.assertEqual(len(self.native_costs()), 2)

    def test_failed_native_result_retains_observation_without_executable(self):
        with self.assertRaisesRegex(ValueError, 'FAIL_NATIVE'):
            self.runtime.admit({'replacements': []})
        observations = [node for node in self.machine.log if node.kind == 'generic_native_observation']
        self.assertEqual(len(observations), 1)
        self.assertEqual(self.machine.get(observations[0].payload['receipt'])['status'], 'FAIL_NATIVE')
        self.assertFalse(self.machine.active_capabilities())

    def test_malformed_native_report_still_charges_actual_controller_attempts(self):
        candidate = json.loads(json.dumps(self.candidate))
        candidate['replacements'][0]['replacement'] = '''import atexit,pathlib,sys
if len(sys.argv)>3 and sys.argv[2]=='run':
 atexit.register(pathlib.Path(sys.argv[3]).write_text,'{')
def value():
 return 1
'''
        with self.assertRaises(json.JSONDecodeError):
            self.runtime.admit(candidate)
        costs = self.native_costs()
        self.assertEqual(len(costs), 1)
        row = costs[0]
        output = Path(row['output'])
        self.assertEqual((output/'execution/report.json').read_text(), '{')
        self.assertIn('2 passed', (output/'execution/stdout.log').read_text())
        self.assertFalse((output/'receipt.json').exists())
        self.assertEqual(row['costs'].get('native_calls'), 1)
        self.assertEqual(row['costs'].get('collection_calls'), 1)
        self.assertEqual(row['controller_attempts'],
                         {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2})
        self.assertTrue(row['accounting_complete'])
        self.assertFalse(self.machine.active_capabilities())

    def test_missing_attempt_observation_refuses_a_real_native_pass(self):
        before = worker.attempt_snapshot()
        with patch.object(worker, 'attempt_snapshot', side_effect=[before, {}]):
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING'):
                self.runtime._verify(self.candidate)
        row = self.native_costs()[0]
        self.assertFalse(row['accounting_complete'])
        self.assertEqual(row['status'], 'UNKNOWN_NATIVE_ATTEMPT_ACCOUNTING')
        self.assertEqual(row['costs']['native_calls'], 1)
        self.assertFalse(self.machine.active_capabilities())

    def test_malformed_retained_receipt_cannot_erase_real_native_attempts(self):
        verify = worker.verify
        for retained in (None, {'native_calls': 'invalid', 'collection_calls': -1}):
            with self.subTest(retained=retained):
                def interrupted(*args, **kwargs):
                    verify(*args, **kwargs)
                    (Path(args[2])/'receipt.json').write_text(json.dumps({'costs': retained}))
                    raise ValueError('fixture post-launch interruption')

                with patch.object(worker, 'verify', side_effect=interrupted):
                    with self.assertRaisesRegex(ValueError, 'fixture post-launch interruption'):
                        self.runtime._verify(self.candidate)
                row = self.native_costs()[-1]
                self.assertEqual(row['costs']['native_calls'], 1)
                self.assertEqual(row['costs']['collection_calls'], 1)
                self.assertTrue(row['accounting_complete'])
        self.assertFalse(self.machine.active_capabilities())


if __name__ == '__main__':
    unittest.main()
