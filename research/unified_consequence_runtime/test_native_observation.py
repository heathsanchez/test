"""Contracts for source-native observation admission; native science is separate."""
from pathlib import Path
from dataclasses import asdict, replace
import copy
import importlib.util
import marshal
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from research.unified_consequence_runtime.developmental_machine import Machine


class NativeObservationContracts(unittest.TestCase):
    def setUp(self):
        from research.unified_consequence_runtime.native_observation import NativeObservationRuntime
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.machine = Machine(Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')),
            self.root/'state', Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified')),
            Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))/'config.json')
        self.worlds = self.root/'worlds'
        self.worlds.mkdir()
        self.runtime = NativeObservationRuntime(self.machine,
            Path(os.environ.get('UDM_NATIVE_SOURCE_REPO', '/workspace/repos/test')),
            self.worlds, self.root/'output')

    def test_external_authority_is_not_acquired(self):
        self.assertEqual(self.runtime.authority_ceiling['external_effects'], 'NONE')
        self.assertEqual(self.runtime.authority_ceiling['reference_monitor'], 'UNKNOWN_NONBYPASSABILITY')

    def test_wrong_family_is_rejected_before_native_work(self):
        with self.assertRaises(ValueError):
            self.runtime.observe('unfamiliar')
        self.assertFalse(list(self.worlds.iterdir()))

    def test_missing_worlds_cannot_supply_observations(self):
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.observe('A')

    def test_no_descriptor_is_accepted_as_an_executable_capability(self):
        with self.assertRaises((PermissionError, ValueError, StopIteration)):
            self.runtime.execute('missing-capability', 'B')

    def test_empty_or_replayed_observations_have_no_native_authority(self):
        from research.unified_consequence_runtime.native_observation import validate_rows
        for bad in ({}, {'family':'A', 'source_sha':'another-task', 'rows':[]}):
            with self.assertRaises(ValueError):
                validate_rows(self.runtime.native, bad, 'A', 'old')

    def test_source_missing_after_loading_blocks_routes(self):
        self.runtime.source_repo = self.root/'missing-source'
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.runtime._check_sources()

    def test_authority_withdrawal_blocks_before_native_effect(self):
        self.machine.append('revoke', {'target':self.runtime.authority, 'reason':'test ceiling cut'})
        self.machine.flush()
        with self.assertRaises(PermissionError):
            self.runtime.observe('A')

    def poison_valid_cache(self, path):
        cache = Path(importlib.util.cache_from_source(str(path)))
        cache.parent.mkdir(parents=True, exist_ok=True)
        stat = path.stat()
        code = compile("raise RuntimeError('forged cached source executed')", str(path), 'exec')
        cache.write_bytes(importlib.util.MAGIC_NUMBER + struct.pack('<III', 0, int(stat.st_mtime), stat.st_size)
            + marshal.dumps(code))

    def test_valid_forged_producer_bytecode_is_not_executed(self):
        from research.unified_consequence_runtime.native_observation import load_sources
        self.poison_valid_cache(self.runtime.native.path)
        loaded = load_sources(self.runtime.source_repo, self.runtime.output/'original-source')
        self.assertEqual(len(loaded.producer.cases('A')), 40)

    def test_valid_forged_solver_bytecode_is_not_executed(self):
        self.poison_valid_cache(self.runtime.native.producer.SOURCE_SOLVER)
        solver = self.runtime.native.producer.basis_solver()
        self.assertEqual(solver.learned_exact_rank(1, lambda _:True), 1)

    def test_ignored_untracked_import_can_not_bypass_source_authentication(self):
        from research.unified_consequence_runtime.native_observation import checked_world
        source = self.root/'ignored-import-world'
        source.mkdir()
        subprocess.run(['git', 'init', '--quiet', str(source)], check=True)
        (source/'.gitignore').write_text('*.so\n')
        (source/'source.py').write_text('VALUE = 1\n')
        subprocess.run(['git', '-C', str(source), 'add', '.gitignore', 'source.py'], check=True)
        subprocess.run(['git', '-C', str(source), '-c', 'user.name=UDM contract',
            '-c', 'user.email=udm-contract@example.invalid', 'commit', '--quiet', '-m', 'native source fixture'], check=True)
        sha = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        (source/'source.so').write_bytes(b'unqualified import-affecting object')
        with self.assertRaises(ValueError):
            checked_world(source, sha)


@unittest.skipUnless(os.environ.get('UDM_NATIVE_OBSERVATION_TESTS') == '1',
    'native adversarial contracts require prepared exact tomlkit worlds')
class NativeObservationAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from research.unified_consequence_runtime.native_observation import NativeObservationRuntime
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        cls.machine = Machine(Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')),
            cls.root/'state', Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified')),
            Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))/'config.json')
        cls.runtime = NativeObservationRuntime(cls.machine,
            Path(os.environ.get('UDM_NATIVE_SOURCE_REPO', '/workspace/repos/test')),
            Path(os.environ.get('UDM_NATIVE_OBSERVATION_WORLDS', '/workspace/native-observation-worlds')),
            cls.root/'output')
        cls.capability = cls.runtime.acquire()

    def forged_capability(self, **changes):
        old = self.machine.descriptor(self.capability)
        new = replace(old, **changes)
        original = next(n for n in self.machine.log if n.id == self.capability)
        result = self.machine.append('executable_capability', asdict(new), tuple(original.premises))
        self.machine.flush()
        return result

    def test_wrong_scope_does_not_enter_native_execution(self):
        cap = self.machine.descriptor(self.capability)
        wrong = self.forged_capability(scope={**cap.scope, 'families':['A','B','C']})
        before = len(list(self.runtime.output.glob('*.json')))
        with self.assertRaises(ValueError):
            self.runtime.execute(wrong, 'B')
        self.assertEqual(before, len(list(self.runtime.output.glob('*.json'))))

    def test_false_constructor_dependencies_rejected(self):
        wrong = self.forged_capability(dependencies=())
        with self.assertRaises(ValueError):
            self.runtime._validated(wrong)

    def test_altered_executable_policy_rejected(self):
        cap = self.machine.descriptor(self.capability)
        program = self.machine.get(cap.program)
        program['selected_channels'] = ['native']
        wrong = self.forged_capability(program=self.machine.put(program))
        with self.assertRaises(ValueError):
            self.runtime._validated(wrong)

    def test_replayed_task_and_forged_observation_channel_rejected(self):
        from research.unified_consequence_runtime.native_observation import validate_rows
        cap = self.machine.descriptor(self.capability)
        observations = self.machine.get(cap.observation)
        wrong = copy.deepcopy(observations['old'])
        wrong['family'] = 'B'
        with self.assertRaises(ValueError):
            validate_rows(self.runtime.native, wrong, 'A', 'old')
        wrong = copy.deepcopy(observations['old'])
        witness = next(r for r in wrong['rows'] if r['label']=='FAIL')
        witness['features']['coherence'] = True
        with self.assertRaises(ValueError):
            validate_rows(self.runtime.native, wrong, 'A', 'old')

    def test_corrupted_persisted_program_rejected(self):
        cap = self.machine.descriptor(self.capability)
        file = self.machine.state/'objects'/cap.program
        original = file.read_bytes()
        try:
            file.write_bytes(original+b'x')
            with self.assertRaises(ValueError):
                self.runtime._validated(self.capability)
        finally:
            file.write_bytes(original)

    def test_forged_native_receipt_rejected(self):
        cap = self.machine.descriptor(self.capability)
        support = cap.dependencies[0]
        old = next(n for n in self.machine.log if n.id == cap.evidence[0])
        receipt = self.machine.get(old.payload['receipt'])
        receipt['native_reexecuted'] = False
        evidence = self.machine.append('native_observation_verification',
            {'receipt':self.machine.put(receipt), 'program':cap.program}, (support,))
        wrong = self.machine.append('executable_capability', asdict(replace(cap,evidence=(evidence,))), (support,evidence))
        self.machine.flush()
        with self.assertRaises(ValueError):
            self.runtime._validated(wrong)

    def test_wrong_frontier_profile_and_live_restore_rejected(self):
        with self.assertRaises(ValueError):
            self.runtime.projection_payload(self.capability, ['A'])
        with self.assertRaises(ValueError):
            self.runtime.restore(self.capability)

    def test_original_method_executes_native_future(self):
        result, _ = self.runtime.execute(self.capability, 'B')
        self.assertEqual((result['native_repaired'],result['detected_repaired'],result['false_warrants']), (8,8,0))

    def test_reuse_available_method_precedes_construction(self):
        with patch.object(self.runtime.native.producer, 'acquire',
                side_effect=AssertionError('existing qualified operation must precede construction')):
            selected = self.runtime.acquire()
        self.assertEqual(selected, self.capability)
        self.assertEqual(sum(n.kind == 'executable_capability' and n.id == self.capability
            for n in self.machine.log), 1)

    def test_z_ambiguous_live_methods_preserve_both_candidates(self):
        from research.unified_consequence_runtime.native_observation import NativeObservationRuntime
        root = self.root/'ambiguous'
        shutil.copytree(self.machine.state, root/'state')
        machine = Machine(self.machine.components, root/'state', self.machine.evaluator, self.machine.config)
        runtime = NativeObservationRuntime(machine, self.runtime.source_repo, self.runtime.worlds, root/'output')
        runtime.withdraw(self.capability)
        first = runtime.restore(self.capability)
        second = runtime.restore(self.capability)
        before = tuple(machine.active_capabilities())
        with patch.object(runtime.native.producer, 'acquire',
                side_effect=AssertionError('ambiguous available methods must not trigger construction')):
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_CHOICE'):
                runtime.acquire()
        self.assertEqual(before, tuple(machine.active_capabilities()))
        self.assertIn(first, before)
        self.assertIn(second, before)


if __name__ == '__main__':
    unittest.main()
