"""Actual native fixtures over production Machine; no developmental claim."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import decisive_native_verify as original
from . import native_admission_v2 as admission
from . import native_execution_v2 as worker
from .developmental_machine import Machine
from .native_runtime_v2 import AUTHORITY, NativeRuntimeV2


class NativeRuntimeV2Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_folder = tempfile.TemporaryDirectory(prefix='udm-v2-runtime-fixture-source-')
        cls.addClassCleanup(cls.source_folder.cleanup)
        cls.repo = Path(cls.source_folder.name)/'source'
        cls.repo.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(cls.repo), *args], stderr=subprocess.PIPE).decode().strip()
        git('init', '-q')
        (cls.repo/'subject.py').write_text('def value():\n return 0\n')
        (cls.repo/'test_subject.py').write_text('from subject import value\ndef test_value(): assert value()==0\n')
        git('add', '.')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base')
        base = git('rev-parse', 'HEAD')
        (cls.repo/'test_subject.py').write_text('from subject import value\ndef test_value(): assert value()==1\n')
        git('add', '.')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'independent assertion')
        commit = git('rev-parse', 'HEAD')
        environment = original.environment_identity(sys.executable)
        cls.contract = {'schema': worker.SCHEMA, 'repository': 'fixture/source', 'repo_path': str(cls.repo),
            'commit': commit, **original.source_identity(cls.repo, commit), 'interpreter': sys.executable,
            'environment_sha256': original.fingerprint(environment), 'protocol_binding': 'f'*64, 'horizon_seconds': 7}
        cls.authority = admission.derive_suite_contract(cls.repo, base, commit, 'f'*64, repository='fixture/source')
        cls.policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 7, 'execution_seconds': 7,
                      'pytest_version': environment['pytest_version'], 'plugins': []}
        cls.certificate = worker.collect(cls.contract, cls.authority, Path(cls.source_folder.name)/'collection', policy=cls.policy)
        cls.candidate = {'replacements': [{'path': 'subject.py',
            'original_sha256': original.sha256((cls.repo/'subject.py').read_bytes()),
            'replacement': 'def value():\n return 1\n'}]}

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='udm-v2-runtime-fixture-state-')
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.components = Path(os.environ.get('UDM_COMPONENTS', '/workspace/components'))
        self.machine = self.reload_machine()
        self.runtime = self.new_runtime(self.machine)

    def reload_machine(self):
        return Machine(self.components, self.root/'state', self.root/'evaluator', self.root/'config')

    def new_runtime(self, machine, certificate=None):
        return NativeRuntimeV2(machine, self.contract, self.authority,
                               certificate or self.certificate, self.policy, self.root/'native-output')

    def test_two_actual_native_checks_admit_then_execute_and_cold_reload(self):
        capability = self.runtime.admit(self.candidate)
        costs = [row for row in self.machine.costs if row['phase'] == 'generic_native_v2_independent_verification']
        self.assertEqual(len(costs), 2)
        self.assertEqual(sum(row['costs']['native_calls'] for row in costs), 2)
        self.assertTrue(all(Path(row['output'], 'receipt.json').is_file() for row in costs))
        descriptor = self.machine.descriptor(capability)
        self.assertEqual(descriptor.operation, 'native.pytest_suite')
        self.assertEqual(descriptor.scope['authority_ceiling'], AUTHORITY)
        for key, expected in (('contract', self.contract), ('suite_authority', self.authority),
                              ('certificate', self.certificate), ('policy', self.policy)):
            self.assertEqual(self.machine.get(descriptor.source[key]), expected)
        receipt, consequence = self.runtime.execute(capability)
        self.assertEqual(receipt['status'], 'PASS_NATIVE')
        self.assertEqual(next(node for node in self.machine.log if node.id == consequence).premises, (capability,))
        cold = self.reload_machine()
        loaded = self.new_runtime(cold)
        self.assertEqual(loaded.source, self.runtime.source)
        self.assertEqual(loaded.execute(capability)[0]['status'], 'PASS_NATIVE')
        self.assertEqual(set(cold.mt.live_ids(cold.log)), cold.flash_live_ids())
        script = '''
import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine import Machine
from research.unified_consequence_runtime.native_runtime_v2 import NativeRuntimeV2
components,state,output,capability=map(Path,sys.argv[1:])
machine=Machine(components,state,state.parent/'evaluator',state.parent/'config')
capability=str(capability);source=machine.descriptor(capability).source
runtime=NativeRuntimeV2(machine,*(machine.get(source[key]) for key in
    ('contract','suite_authority','certificate','policy')),output)
receipt,consequence=runtime.execute(capability)
print(json.dumps({'status':receipt['status'],'source':source,'consequence':consequence,
    'closure_agrees':set(machine.mt.live_ids(machine.log))==machine.flash_live_ids(),
    'native_calls':sum(row.get('costs',{}).get('native_calls',0) for row in machine.costs)}))
'''
        process = subprocess.run([sys.executable, '-c', script, str(self.components), str(cold.state),
                                  str(self.root/'separate-process-output'), capability],
                                 check=True, capture_output=True, text=True)
        restarted = json.loads(process.stdout)
        self.assertEqual(restarted['status'], 'PASS_NATIVE')
        self.assertTrue(restarted['closure_agrees'])
        self.assertEqual(restarted['source'], descriptor.source)
        self.assertEqual(restarted['native_calls'], 1)
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            loaded.projection_payload(capability)

    def test_real_flash_dependency_closure_and_fresh_source_qualified_restoration(self):
        ancestor = self.runtime.admit(self.candidate)
        child_candidate = copy.deepcopy(self.candidate)
        child_candidate['replacements'][0]['replacement'] = 'def value():\n return int(1)\n'
        child = self.runtime.admit(child_candidate, dependencies=(ancestor,))
        unrelated = self.machine.append('fixture_unrelated', {'fixture_only': True})
        self.machine.flush()
        with self.assertRaisesRegex(ValueError, 'fresh certificate'):
            self.runtime.restore(ancestor)
        self.runtime.withdraw(ancestor, 'fixture exact ancestor withdrawal')
        for target in (ancestor, child):
            self.assertNotIn(target, self.machine.flash_live_ids())
            with self.assertRaises(PermissionError):
                self.runtime.execute(target)
        self.assertIn(unrelated, self.machine.flash_live_ids())
        with self.assertRaisesRegex(ValueError, 'fresh certificate'):
            self.runtime.restore(ancestor)
        cost_edit = copy.deepcopy(self.certificate)
        cost_edit['costs']['total_seconds'] += 1
        with self.assertRaisesRegex(ValueError, 'fresh certificate'):
            self.new_runtime(self.machine, cost_edit).restore(ancestor)
        with self.assertRaisesRegex(ValueError, 'explicit source-qualified'):
            self.runtime.admit(self.candidate)
        fresh = worker.collect(self.contract, self.authority, self.root/'fresh-collection', policy=self.policy)
        restored_runtime = self.new_runtime(self.machine, fresh)
        restored = restored_runtime.restore(ancestor)
        self.assertEqual(self.machine.descriptor(restored).supersedes, ancestor)
        self.assertEqual(self.machine.descriptor(restored).program, self.machine.descriptor(ancestor).program)
        self.assertEqual(self.machine.descriptor(restored).generation, 3)
        with self.assertRaisesRegex(ValueError, 'fresh certificate'):
            restored_runtime.restore(ancestor)
        self.assertEqual(restored_runtime.execute(restored)[0]['status'], 'PASS_NATIVE')
        self.assertNotIn(child, self.machine.flash_live_ids())
        self.assertEqual(set(self.machine.mt.live_ids(self.machine.log)), self.machine.flash_live_ids())
        restored_runtime.withdraw(restored, 'fixture restored ancestor withdrawal')
        with self.assertRaisesRegex(ValueError, 'fresh certificate'):
            self.runtime.restore(restored)

    def test_actual_failure_retains_observation_without_executable(self):
        with self.assertRaisesRegex(ValueError, 'FAIL_NATIVE'):
            self.runtime.admit({'replacements': []})
        observations = [node for node in self.machine.log if node.kind == 'generic_native_observation']
        self.assertEqual(len(observations), 1)
        retained = self.machine.get(observations[0].payload['receipt'])
        self.assertEqual(retained['status'], 'FAIL_NATIVE')
        self.assertEqual(retained['junit']['failures'], 1)
        self.assertFalse(self.machine.active_capabilities())

    def test_external_binding_and_cas_tampering_block_before_native_execution(self):
        capability = self.runtime.admit(self.candidate)
        certificate_key = self.runtime.source_descriptor['certificate']
        path = self.machine.state/'objects'/certificate_key
        original_bytes = path.read_bytes()
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'persisted executable object changed'):
            self.runtime.execute(capability)
        path.write_bytes(original_bytes)
        self.runtime.policy['execution_seconds'] = 8
        with self.assertRaisesRegex(ValueError, 'external input'):
            self.runtime.execute(capability)
        costs = [row for row in self.machine.costs if row['phase'] == 'generic_native_v2_independent_verification']
        self.assertEqual(len(costs), 2)

    def test_wrong_dependency_or_candidate_cannot_replace_causal_program(self):
        capability = self.runtime.admit(self.candidate)
        with self.assertRaises(ValueError):
            self.runtime.admit(self.candidate, dependencies=(capability, capability))
        with self.assertRaises(PermissionError):
            self.runtime.admit(self.candidate, dependencies=('0'*64,))
        node = next(node for node in self.machine.log if node.id == capability)
        forged = node.payload
        forged['program'] = self.machine.put({'replacements': []})
        forged_id = self.machine.append('executable_capability', forged, node.premises)
        self.machine.flush()
        with self.assertRaises(ValueError):
            self.runtime.execute(forged_id)
        self.assertEqual(len([row for row in self.machine.costs
                              if row['phase'] == 'generic_native_v2_independent_verification']), 2)

    def test_refused_source_output_creates_no_directory_or_authority_records(self):
        forbidden = self.repo/'forbidden-native-output'
        count = len(self.machine.log)
        with self.assertRaisesRegex(ValueError, 'outside source'):
            NativeRuntimeV2(self.machine, self.contract, self.authority, self.certificate, self.policy, forbidden)
        self.assertFalse(forbidden.exists())
        self.assertEqual(len(self.machine.log), count)


if __name__ == '__main__':
    unittest.main()
