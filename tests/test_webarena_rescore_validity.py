"""Scorer contract tests; fake evaluator responses are test inputs, not benchmarks."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'webarena_rescore_retained.py'


def load_scorer():
    # Load the real scorer without requiring a live benchmark installation.
    package = types.ModuleType('webarena_verified')
    package.__path__ = []
    api = types.ModuleType('webarena_verified.api')
    configs = types.ModuleType('webarena_verified.types.config')
    tracing = types.ModuleType('webarena_verified.types.tracing')
    api.WebArenaVerified = object
    configs.WebArenaVerifiedConfig = object
    tracing.NetworkTrace = object
    with patch.dict(sys.modules, {
        'webarena_verified': package,
        'webarena_verified.api': api,
        'webarena_verified.types.config': configs,
        'webarena_verified.types.tracing': tracing,
    }):
        spec = importlib.util.spec_from_file_location('_scorer_under_test', SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class FakeTrace:
    @classmethod
    def model_construct(cls, **kwargs):
        return types.SimpleNamespace(evaluation_events=())

    @classmethod
    def from_har(cls, path):
        json.loads(Path(path).read_text())
        return types.SimpleNamespace(evaluation_events=({'observed': True},))


class ScorerValidityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'input'
        self.output = Path(self.temp.name) / 'output'
        self.root.mkdir()
        self.tasks = [{'task_id': n, 'sites': ['reddit']} for n in range(258)]
        self.manifest = {}
        for n in range(258):
            slot = f'{n:032x}'
            self.manifest[str(n)] = {
                'opaque_slot': slot, 'agent_exit_code': 0,
                'execution_class': 'agent_executed',
            }
            folder = self.root / 'output' / slot
            folder.mkdir(parents=True)
            (folder / 'agent_response.json').write_text(json.dumps({
                'task_type': 'RETRIEVE', 'status': 'SUCCESS',
                'retrieved_data': [n], 'error_details': None,
            }))
        (self.root / 'config.json').write_text('{}')
        self.save_inputs()
        self.module = load_scorer()

    def save_inputs(self):
        (self.root / 'hard.json').write_text(json.dumps(self.tasks))
        (self.root / 'execution_manifest.json').write_text(json.dumps(self.manifest))

    def evaluate(self, errors=(), successes=(), protected=(), bad_scores=None):
        errors, successes, protected = set(errors), set(successes), set(protected)
        bad_scores = bad_scores or {}

        class Authority:
            def __init__(self, **kwargs):
                pass

            def get_task(self, ident):
                criteria = [types.SimpleNamespace(evaluator='NetworkEventEvaluator')] if ident in protected else []
                return types.SimpleNamespace(eval=criteria)

            def evaluate_task(self, *, task_id, agent_response, network_trace):
                if task_id in errors:
                    raise AttributeError('simulated scorer schema mismatch')
                value = bad_scores.get(task_id, 1.0 if task_id in successes else 0.0)
                status = 'success' if value == 1.0 else 'failure'
                return types.SimpleNamespace(score=value, status=types.SimpleNamespace(value=status))

        config = types.SimpleNamespace(from_file=lambda path: {})
        with patch.object(self.module, 'WebArenaVerified', Authority), \
             patch.object(self.module, 'WebArenaVerifiedConfig', config), \
             patch.object(self.module, 'NetworkTrace', FakeTrace), \
             contextlib.redirect_stdout(io.StringIO()):
            return self.module.score(self.root, self.output)

    def test_evaluator_exception_cannot_produce_warranted_metric(self):
        report = self.evaluate(errors={0})
        self.assertEqual(report['epistemic_state'], 'UNKNOWN')
        self.assertFalse(report['metric_valid'])
        self.assertIsNone(report['score_fraction'])
        self.assertEqual(report['official_evaluation_error_count'], 1)
        self.assertIsNone(report['results']['0']['score'])

    def test_all_evaluator_errors_are_not_a_valid_zero_score(self):
        report = self.evaluate(errors=range(258))
        self.assertEqual(report['epistemic_state'], 'UNKNOWN')
        self.assertIsNone(report['score_fraction'])
        self.assertEqual(report['unknown_count'], 258)
        self.assertEqual(report['known_unsuccessful_count'], 0)

    def test_partial_results_preserve_a_lower_bound_not_a_complete_score(self):
        report = self.evaluate(errors={1}, successes={0})
        self.assertEqual(report['official_success_count'], 1)
        self.assertAlmostEqual(report['success_fraction_lower_bound'], 1 / 258)
        self.assertIsNone(report['score_fraction'])
        self.assertEqual(report['known_unsuccessful_count'], 256)

    def test_genuine_zero_score_is_still_valid(self):
        report = self.evaluate()
        self.assertTrue(report['metric_valid'])
        self.assertEqual(report['score_fraction'], 0)
        self.assertEqual(report['known_unsuccessful_count'], 258)
        self.assertEqual(report['unknown_count'], 0)

    def test_valid_results_keep_the_existing_metric(self):
        report = self.evaluate(successes=range(51))
        self.assertTrue(report['metric_valid'])
        self.assertEqual(report['official_success_count'], 51)
        self.assertAlmostEqual(report['score_fraction'], 51 / 258)
        self.assertEqual(report['official_evaluation_error_count'], 0)

    def test_duplicate_task_ids_do_not_satisfy_total_count(self):
        self.tasks[-1]['task_id'] = 0
        self.save_inputs()
        with self.assertRaisesRegex(RuntimeError, 'unique|identity'):
            self.evaluate()

    def test_equal_cardinality_but_different_manifest_ids_is_rejected(self):
        self.manifest['999'] = self.manifest.pop('257')
        self.save_inputs()
        with self.assertRaisesRegex(RuntimeError, 'identity|manifest'):
            self.evaluate()

    def test_duplicate_opaque_slots_are_not_independent_evidence(self):
        self.manifest['1']['opaque_slot'] = self.manifest['0']['opaque_slot']
        self.save_inputs()
        with self.assertRaisesRegex(RuntimeError, 'opaque|slot'):
            self.evaluate()

    def test_completed_agent_cannot_have_missing_response(self):
        (self.root / 'output' / self.manifest['0']['opaque_slot'] / 'agent_response.json').unlink()
        report = self.evaluate()
        self.assertFalse(report['metric_valid'])
        self.assertEqual(report['evidence_error_count'], 1)

    def test_protected_completion_requires_its_recorded_trace(self):
        report = self.evaluate(successes={0}, protected={0})
        self.assertFalse(report['metric_valid'])
        self.assertEqual(report['official_success_count'], 0)
        self.assertEqual(report['evidence_error_count'], 1)

    def test_missing_trace_is_not_required_for_failed_execution(self):
        self.manifest['0']['execution_class'] = 'agent_execution_failure'
        self.manifest['0']['agent_exit_code'] = 1
        self.save_inputs()
        report = self.evaluate(protected={0})
        self.assertTrue(report['metric_valid'])
        self.assertEqual(report['agent_completed'], 257)

    def test_nan_score_invalidates_result(self):
        report = self.evaluate(bad_scores={0: float('nan')})
        self.assertFalse(report['metric_valid'])
        self.assertIsNone(report['results']['0']['score'])

    def test_out_of_range_score_invalidates_result(self):
        report = self.evaluate(bad_scores={0: 1.1})
        self.assertFalse(report['metric_valid'])

    def test_input_slot_cannot_escape_output_directory(self):
        self.manifest['0']['opaque_slot'] = '../../outside'
        self.save_inputs()
        with self.assertRaisesRegex(RuntimeError, 'opaque|slot'):
            self.evaluate()

    def test_cli_exits_nonzero_for_invalid_metric(self):
        with patch.object(sys, 'argv', ['scorer', '--input', str(self.root), '--output', str(self.output)]), \
             patch.object(self.module, 'score', return_value={'metric_valid': False}):
            with self.assertRaises(SystemExit) as error:
                self.module.main()
            self.assertNotEqual(error.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
