"""Preimplementation source-free contracts for the V42 frontier binding.

No task metadata, source outcomes, constructor search or native runs are read.
"""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v42'
RESEARCH = Path(__file__).resolve().parent
CATALOG = 'research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'


def helper(filename):
    path = RESEARCH/'archaeology/native-authority-v42'/filename
    if not path.is_file():
        raise AssertionError('versioned V42 helper required: '+filename)
    spec = importlib.util.spec_from_file_location('_v42_'+path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class NativeFrontierV42BindingContracts(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE), 'versioned V42 frontier required')
        self.q = importlib.import_module(MODULE)

    def test_default_paths_keep_previous_results_separate(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(self.q, 'PROTOCOL', Path(folder)/'absent'):
            value = self.q.protocol()
        self.assertEqual(value['schema'], 'UDM_NATIVE_FRONTIER_PROTOCOL_V42')
        self.assertEqual(value['state'], 'PREPARED_NOT_FROZEN')
        self.assertIsNone(value['environment_gate'])
        self.assertEqual(self.q.RECORDS, RESEARCH/'archaeology/native-authority-v42')
        self.assertEqual(self.q._BASELINE, 'dc59c8fcee6efede520c531eba5e42e7b84a1a9f')
        self.assertEqual(self.q.CATALOG_PATH, CATALOG)

    def test_prepare_selects_new_runtime_and_private_worker_without_old_mutation(self):
        from . import native_execution_v42 as worker
        from . import native_environment_v42 as environment
        from . import native_execution_v3 as old_worker
        from . import qualify_native_frontier_v3 as old
        self.assertIs(self.q.worker, worker)
        self.assertIs(self.q.environment, environment)
        self.assertIs(old.worker, old_worker)
        self.assertIn('native_runtime_v42', self.q._prepare.__code__.co_names)
        self.assertIn('NativeRuntimeV42', self.q._prepare.__code__.co_names)
        self.assertNotIn('native_runtime_v3', self.q._prepare.__code__.co_names)
        self.assertIn('native_runtime_v3', old._prepare.__code__.co_names)
        self.assertIs(self.q._prepare.__globals__['worker'], worker)

    def test_original_search_bytecode_and_matched_budget_are_preserved(self):
        from . import qualify_native_frontier_v2 as old
        bound = self.q.isolated_binding('search')
        self.assertIs(bound.__code__, old.search.__code__)
        self.assertIsNot(bound.__globals__, vars(old))
        self.assertIs(bound.__globals__['worker'], self.q.worker)
        self.assertEqual(bound.__globals__['MODULE'], MODULE)
        self.assertIs(bound.__globals__['bounded_catalog'], self.q.bounded_catalog)
        self.assertEqual(tuple(self.q.DEFAULTS[k] for k in ('search_budget', 'candidate_cap_per_file',
            'acquisition_native_calls', 'training_seconds', 'requested_roles')), (8, 64, 512, 3600, 2))

    def test_catalog_has_original_generator_and_versioned_snapshot(self):
        from . import decisive_native as old
        from . import native_source_v42 as source
        self.assertIs(self.q.catalog.__code__, old.catalog.__code__)
        self.assertIsNot(self.q.catalog.__globals__, vars(old))
        self.assertIs(self.q.catalog.__globals__['verifier']._snapshot, source.snapshot)
        self.assertIs(self.q.catalog.__globals__['original_candidates'], old.original_candidates)

    def test_independent_checker_has_importable_new_identity(self):
        from .native_meta_decision import _checker_source
        result = _checker_source(self.q.reconstruct_profiles)
        self.assertEqual(result['module'], MODULE)
        self.assertEqual(result['name'], 'reconstruct_profiles')
        self.assertEqual(Path(result['path']), Path(self.q.__file__).resolve())

    def test_old_admission_gate_cannot_authorize_new_worker(self):
        gate = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': 'a'*40,
                'run_id': 1, 'artifact_id': 2, 'artifact_sha256': 'b'*64,
                'qualification_result_sha256': 'c'*64, 'result_path': 'fixture/result.json'}
        value = copy.deepcopy(self.q.DEFAULTS)
        value.update(environment_gate=gate, catalog={'path': CATALOG, 'sha256': 'd'*64})
        result = {'status': gate['status'], 'source_commit': gate['source_commit'],
            'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V41',
            'freeze': {'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V41'},
            'first_task_gate': {'status': 'PASS'},
            'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
        with patch.object(self.q, '_bound_json', return_value=result):
            with self.assertRaisesRegex(ValueError, 'qualification|admission-only'):
                self.q.require_environment_gate(value)

    def test_pass_and_fail_admission_are_equally_eligible_in_fixed_order(self):
        pool = [{'repo': 'fixture/'+name} for name in ('first', 'second', 'third')]
        reports = [{'repository': row['repo'], 'spec_sha256': self.q.worker.fingerprint(row),
            'status': status, 'eligible': True,
            'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
            for row, status in zip(pool, ('PASS_NATIVE', 'FAIL_NATIVE', 'PASS_NATIVE'))]
        selected = self.q.select_screened_roles(pool, reports)
        self.assertEqual([row['repo'] for row in selected], ['fixture/first', 'fixture/second'])

    def test_curator_retains_all_nine_v41_exposures_and_no_initial_universe(self):
        curator = helper('curate_frontier.py')
        self.assertEqual(curator.UNIVERSE, ())
        self.assertEqual(curator.q.MODULE, MODULE)
        self.assertEqual(curator.SCHEMA, 'UDM_NATIVE_AUTHORITY_V42_METADATA_PREQUERY_V1')
        previous = json.loads((RESEARCH/'archaeology/native-authority-v41/DECLARED_UNIVERSE.json').read_text())
        excluded, inputs = curator.exclusions(RESEARCH, curator.original(RESEARCH))
        self.assertTrue(set(previous['repositories']) <= set(excluded))
        self.assertIn('archaeology/native-authority-v41/DECLARED_UNIVERSE.json', {r['path'] for r in inputs})
        self.assertTrue(all(r.get('status') != 'MISSING' for r in inputs))
        with self.assertRaisesRegex(ValueError, 'qualified|universe'):
            curator.plan(RESEARCH)

    def test_gate_validation_precedes_universe_reading(self):
        curator = helper('curate_frontier.py')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); gate = root/'gate.json'; gate.write_text('{}')
            with patch.object(curator.q, 'require_environment_gate', side_effect=ValueError('pending V42 qualification')):
                with self.assertRaisesRegex(ValueError, 'pending V42 qualification'):
                    curator.configure_universe(root/'unread.json', gate, root/'unread.zip')

    def test_record_assembly_uses_only_new_records(self):
        assembler = helper('prepare_records.py')
        self.assertEqual(assembler.q.MODULE, MODULE)
        self.assertEqual(assembler.prepare.__globals__['q'].RECORDS, self.q.RECORDS)


if __name__ == '__main__':
    unittest.main()
