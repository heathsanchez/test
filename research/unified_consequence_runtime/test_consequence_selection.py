"""Separate finite routing integration; no prospective frontier or V54 worlds."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ConsequenceSelectionTests(unittest.TestCase):
    def setUp(self):
        name = 'research.unified_consequence_runtime.consequence_selection'
        self.assertIsNotNone(importlib.util.find_spec(name), 'native selection adapter missing')
        from research.unified_consequence_runtime import consequence_selection
        self.selection = consequence_selection

    def test_native_minimum_distinction_resolves_only_live_repairs(self):
        native = self.selection.native_selectors()
        core = native['core']
        old = core.EquivalenceRelation.from_observation((0, 1, 2), lambda _: 0)
        residual = core.PairResidual(0, 1, old, 'left', 'right')
        state = core.DevelopmentState((0, 1, 2), old)
        repairs = native['version_space'].coarsest_representation_repairs(state, residual, ())
        pairs = native['version_space'].discriminating_pairs(repairs)
        self.assertEqual(len(repairs), 2)
        self.assertEqual(pairs[0], (0, 2))
        remaining = native['version_space'].update_version_space_from_pair_answer(
            repairs, pairs[0], observed_same=False)
        self.assertEqual(len(remaining), 1)
        basis = native['minimal_basis']([[int(r.same(*p)) for p in pairs] for r in repairs],
                                         [list(p) for p in pairs])
        self.assertEqual(basis['size'], 1)
        self.assertEqual(basis['classes'], 2)

    def test_current_machine_selects_all_available_typed_routes_without_method_id(self):
        assets = Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))
        with tempfile.TemporaryDirectory(prefix='udm-selection-test-') as work:
            report = self.selection.qualify(
                Path(os.environ.get('UDM_BASE_STATE',
                    '/workspace/v54-worlds/base_udm/artifact/qualified-state')),
                assets, Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')),
                Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified')),
                Path(work)/'selection-state')
            self.assertEqual(report['status'], 'PASS_BOUNDED_ROUTING_INTEGRATION')
            self.assertTrue(all(report['gates'].values()))
            self.assertEqual(report['native_successes'], 6)
            self.assertEqual(report['baseline'], 'TIE_SAME_AVAILABLE_OPERATIONS')
            self.assertEqual(report['retained_source_state_before'], report['retained_source_state_after'])
            for row in report['outcomes']:
                result = row['selection']
                self.assertEqual(result['status'], 'VERIFIED_EXISTING_METHOD_ACTIVATION')
                self.assertEqual(result['observation_basis']['size'], 1)
                self.assertFalse(result['language_changed'])
                self.assertEqual(result['mda']['verdict'], 'verified')
                self.assertEqual(result['mda']['retained'], ())
                self.assertEqual(result['expressivity'], 'NOT_TESTED')

    def test_equivalent_active_generations_remain_ambiguous(self):
        from research.unified_consequence_runtime.developmental_machine import Machine
        assets = Path(os.environ.get('UDM_ASSETS', '/workspace/archaeology/depth5-original'))
        tasks = {t['task_id']: t for t in json.loads((assets/'full_no_eval.json').read_text())}
        with tempfile.TemporaryDirectory(prefix='udm-selection-ambiguous-') as work:
            state = Path(work)/'state'
            shutil.copytree(Path(os.environ.get('UDM_BASE_STATE',
                '/workspace/v54-worlds/base_udm/artifact/qualified-state')), state)
            machine = Machine(Path(os.environ.get('UDM_COMPONENTS', '/workspace/components')),
                              state,
                              Path(os.environ.get('UDM_EVALUATOR', '/workspace/repos/webarena-verified')),
                              assets/'config.json')
            grouping = next(cap for cap in machine.active_capabilities()
                            if machine.descriptor(cap).operation == 'grouping')
            # A synthetic duplicate of a retained warranted generation tests ambiguity;
            # it acquires no new domain capability and runs no acquisition headline.
            payload = next(node.payload.copy() for node in machine.log if node.id == grouping)
            payload['generation'] += 1
            machine.append('executable_capability', payload, (grouping,))
            machine.flush()
            result = machine.select_and_execute(tasks[62])
            self.assertEqual(result['status'], 'UNKNOWN_AMBIGUOUS_METHOD')
            self.assertIsNone(result['selected_capability'])
            self.assertFalse(result['language_changed'])
            self.assertEqual(result['grammar_exhausted'], 'UNKNOWN')

    def test_report_path_cannot_change_input_or_copied_state(self):
        with tempfile.TemporaryDirectory(prefix='udm-selection-path-') as work:
            root = Path(work)
            state = root/'retained'
            copied = root/'copied'
            state.mkdir()
            for output in (state/'report.json', copied/'report.json'):
                run = subprocess.run([sys.executable, '-m',
                    'research.unified_consequence_runtime.consequence_selection',
                    '--state', str(state), '--state-out', str(copied),
                    '--assets', str(root/'absent'), '--components', str(root/'absent'),
                    '--evaluator', str(root/'absent'), '--out', str(output)],
                    capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertIn('--out must be outside', run.stderr)
                self.assertFalse(output.exists())
                self.assertFalse(copied.exists())


if __name__ == '__main__':
    unittest.main()
