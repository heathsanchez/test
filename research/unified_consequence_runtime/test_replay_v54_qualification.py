"""Artifact-reuse qualification bookkeeping; native subprocess effects are intercepted."""
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

from research.unified_consequence_runtime.developmental_machine import Capability, Machine, digest


class QualifiedStateReplayTests(unittest.TestCase):
    def setUp(self):
        name = 'research.unified_consequence_runtime.replay_v54_qualification'
        self.assertIsNotNone(importlib.util.find_spec(name), 'artifact-reuse qualification helper missing')
        from research.unified_consequence_runtime import replay_v54_qualification
        self.helper = replay_v54_qualification
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.archive = root/'archive'
        self.qualified = self.archive/'qualification/v54'
        code = self.archive/'research/unified_consequence_runtime'
        code.mkdir(parents=True)
        for filename in ('v54_source.py', 'v54_verify.py', 'qualify_v54_machine.py'):
            shutil.copyfile(Path(__file__).with_name(filename), code/filename)
        self.args = SimpleNamespace(qualified_root=self.archive, out=root/'replay',
            source=Path(os.environ.get('V54_SOURCE', '/workspace/repos/triskelion')), worlds=root/'unused-worlds',
            components=Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')),
            evaluator=Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified')),
            config=Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))/'config.json',
            native_python=Path(sys.executable))
        machine = Machine(self.args.components, self.qualified/'state', self.args.evaluator, self.args.config)
        capabilities = []
        for operation in ('v54.token_rewrite', 'v54.token_rewrite', 'grouping', 'stars'):
            support = machine.append('fixture_support', {'index': len(capabilities)})
            cap = Capability(operation, {}, {}, machine.put({}), machine.put({}), 1,
                (support,), (), 'FIXTURE_ONLY_NO_NATIVE_AUTHORITY')
            capabilities.append(machine.append('executable_capability', asdict(cap), (support,)))
        ancestor = machine.append('fixture_old_support', {})
        old1 = machine.append('fixture_old_O1', {}, (ancestor,))
        old2 = machine.append('fixture_old_O2', {}, (old1,))
        machine.append('revoke', {'target': ancestor, 'reason': 'fixture old lineage withdrawn'})
        machine.flush()
        operators, protected = capabilities[:2], dict(zip(('grouping', 'stars'), capabilities[2:]))
        self.spec = {'operators': operators, 'protected_capabilities': protected,
            'withdrawn': [ancestor, old1, old2], 'historical_ids': sorted(machine.mt.ids(machine.log))}
        self.native = {'status': 'PASS', 'native': {'passed': True, 'source_sha256': 'fixture-native-source'},
            'independent_receipt': {'status': 'accepted', 'evaluated': True, 'gates': {'fixture': True}},
            'protected': {str(task): {'response_sha256': str(task)} for task in (62, 64, 65, 168, 169, 172)},
            'withdrawn_generations_inactive': True, 'history_retained': True, 'acquisition_rerun': False}
        names = ('restore_qualified_base original_O1_acquisition native_target_and_O1_admission '
            'protected_original_ED_before original_complete_cold_search UDM_O1_reuse_and_original_O2_construction '
            'fresh_equal_information_executable_ledger_baseline selective_exact_O1_ancestor_withdrawal '
            'independent_native_restoration_new_lineage separate_process_cold_restart_native_and_ED').split()
        self.result = {'schema': 'udm.v54.native-developmental-qualification.v1',
            'status': 'WARRANTED_BOUNDED_V54_TWO_GENERATION_EXTENSION',
            'stages': {name: {'status': 'PASS'} for name in names},
            'baseline': {'status': 'PASS', 'equal_information': True,
                'comparison': 'TIE_ON_NATIVE_CAPABILITY_AND_SEARCH_HORIZON'},
            'restoration': {'status': 'PASS', 'operators': operators,
                'independent_receipt': {'native_python': str(Path(sys.executable).absolute())}},
            'restart': self.native,
            'withdrawal': {'exact_ancestor': ancestor}, 'O1_capability': old1,
            'warm': {'O2_capability': old2}, 'base': {'protected_capabilities': protected},
            'retention': {'final_ledger_sha256': digest((machine.state/'metatron-ledger.jsonl').read_bytes())}}
        self.save()

    def save(self):
        for filename, value in (('RESULT.json', self.result), ('replay-spec.json', self.spec), ('cold-replay.json', self.native)):
            (self.qualified/filename).write_text(json.dumps(value))

    def run_replay(self, native=None):
        # Only the external native subprocess is intercepted. Copying, Metatron,
        # FLASH, history checks and the independent control withdrawal are real.
        with patch.object(self.helper, '_subprocess_mode', return_value=native or self.native):
            return self.helper.qualify(self.args)

    def test_reuses_history_on_copy_and_keeps_replay_claim_distinct(self):
        before = self.helper._state_digest(self.qualified/'state')
        report = self.run_replay()
        self.assertEqual(report['status'], 'REPLAY_VERIFIED_QUALIFIED_V54_STATE')
        self.assertFalse(report['acquisition_rerun'])
        self.assertFalse(report['fresh_discovery_claim'])
        self.assertEqual(report['input_state_before'], before)
        self.assertEqual(report['input_state_after'], before)
        copied = Machine(self.args.components, self.args.out/'state', self.args.evaluator, self.args.config)
        self.assertNotIn(report['independent_control']['parent'], copied.mt.live_ids(copied.log))
        self.assertNotIn(report['independent_control']['child'], copied.flash_live_ids())
        self.assertEqual(report['independent_control']['removed_count'], 2)
        self.assertTrue(set(self.spec['historical_ids']) <= set(copied.mt.ids(copied.log)))
        relocated = json.loads((self.args.out/'replay-spec.json').read_text())
        self.assertEqual(relocated['state'], str(self.args.out/'state'))
        self.assertEqual(relocated['assets'], str(self.args.config.parent))

    def test_rejects_unqualified_or_incomplete_original_evidence(self):
        for change in ('status', 'stage', 'missing_stage', 'baseline', 'restart'):
            with self.subTest(change=change):
                original = json.loads(json.dumps(self.result))
                self.args.out = self.args.out.parent/change
                if change == 'status': self.result['status'] = 'RUNNING'
                if change == 'stage': self.result['stages']['original_O1_acquisition']['status'] = 'FAILED'
                if change == 'missing_stage': self.result['stages'].pop('original_complete_cold_search')
                if change == 'baseline': self.result['baseline']['equal_information'] = False
                if change == 'restart': self.result['restart']['status'] = 'FAILED'
                self.save()
                with self.assertRaisesRegex(ValueError, 'qualified|stages|baseline|restart'):
                    self.run_replay()
                self.assertEqual(json.loads((self.args.out/'RESULT.json').read_text())['status'], 'FAILED_OR_UNKNOWN')
                self.result = original

    def test_rejects_changed_archived_source_before_copying_state(self):
        path = self.archive/'research/unified_consequence_runtime/v54_verify.py'
        path.write_text('changed source')
        with self.assertRaisesRegex(ValueError, 'source bytes'):
            self.run_replay()
        self.assertFalse((self.args.out/'state').exists())

    def test_rejects_interpreter_relocation_without_rewriting_receipts(self):
        self.args.native_python = Path('/different/venv/bin/python')
        with self.assertRaisesRegex(ValueError, 'interpreter path'):
            self.run_replay()
        self.assertFalse((self.args.out/'state').exists())

    def test_failed_separate_process_keeps_logs_and_input_bytes(self):
        before = self.helper._state_digest(self.qualified/'state')
        failure = subprocess.CompletedProcess([], 7, 'partial native output\n', 'native failure detail\n')
        original_run = subprocess.run
        def intercept_replay(command, *args, **kwargs):
            return failure if '--replay' in command else original_run(command, *args, **kwargs)
        with patch('research.unified_consequence_runtime.qualify_v54_machine.subprocess.run', side_effect=intercept_replay):
            with self.assertRaisesRegex(RuntimeError, 'process failed'):
                self.helper.qualify(self.args)
        self.assertEqual((self.args.out/'process-replay.log').read_text(), failure.stdout+failure.stderr)
        report = json.loads((self.args.out/'RESULT.json').read_text())
        self.assertEqual(report['status'], 'FAILED_OR_UNKNOWN')
        self.assertEqual(report['input_state_after'], before)
        self.assertEqual(self.helper._state_digest(self.qualified/'state'), before)

    def test_rejects_empty_withdrawal_or_changed_protected_bindings(self):
        for change in ('withdrawn', 'protected_capabilities'):
            with self.subTest(change=change):
                original = json.loads(json.dumps(self.spec))
                self.args.out = self.args.out.parent/change
                if change == 'withdrawn': self.spec['withdrawn'] = []
                else: self.spec['protected_capabilities']['grouping'] = self.spec['operators'][0]
                self.save()
                with self.assertRaisesRegex(ValueError, 'bindings'):
                    self.run_replay()
                self.spec = original

    def test_timed_out_native_process_keeps_partial_output(self):
        timeout = subprocess.TimeoutExpired('fixture replay', 1200, output=b'partial native output\n')
        with patch.object(self.helper, '_subprocess_mode', side_effect=timeout):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.helper.qualify(self.args)
        self.assertEqual((self.args.out/'process-replay.log').read_text(), 'partial native output\n')

    def test_native_worlds_must_be_outside_archived_evidence(self):
        self.args.worlds = self.archive/'native-worlds'
        with self.assertRaisesRegex(ValueError, 'native worlds.*archive'):
            self.run_replay()
        self.assertFalse(self.args.out.exists())

    def test_rejects_changed_native_response_or_missing_history(self):
        for change in ('native', 'response', 'history', 'independent_receipt'):
            with self.subTest(change=change):
                native = json.loads(json.dumps(self.native))
                self.args.out = self.args.out.parent/change
                if change == 'native': native['native']['passed'] = False
                if change == 'response': native['protected']['168']['response_sha256'] = 'changed'
                if change == 'history': native['history_retained'] = False
                if change == 'independent_receipt': native['independent_receipt']['status'] = 'rejected'
                with self.assertRaisesRegex(ValueError, 'replay|response|history|native'):
                    self.run_replay(native)
                self.assertEqual(json.loads((self.args.out/'RESULT.json').read_text())['status'], 'FAILED_OR_UNKNOWN')

    def test_output_must_be_fresh_and_outside_archived_state(self):
        for destination in (self.archive/'new-output', self.qualified/'state/new-output'):
            self.args.out = destination
            with self.assertRaisesRegex(ValueError, 'separate|outside'):
                self.run_replay()
            self.assertFalse(destination.exists())
        self.args.out = self.archive.parent/'existing'
        self.args.out.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_replay()

    def test_alias_packet_cannot_write_inside_original_qualification(self):
        alias = self.archive.parent/'alias'
        (alias/'qualification').mkdir(parents=True)
        (alias/'qualification/v54').symlink_to(self.qualified, target_is_directory=True)
        (alias/'research').symlink_to(self.archive/'research', target_is_directory=True)
        self.args.qualified_root = alias
        self.args.out = self.qualified/'new-output'
        with self.assertRaisesRegex(ValueError, 'separate|outside'):
            self.run_replay()
        self.assertFalse(self.args.out.exists())


if __name__ == '__main__':
    unittest.main()
