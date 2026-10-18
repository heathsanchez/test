"""Preimplementation behavioral contracts for the versioned V4.1 plumbing.

UDM_V41_FRONTIER_BASELINE=v4 runs the same assertions against existing V4;
the expected RED is a version/authority/path failure, never a missing import.
Only synthetic records and previously exposed metadata inventories are read.
"""
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings


MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v41'
BASE = '7edf1018342b50f73ca226de3e0d0b7acdb31647'
CATALOG = 'research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
BASELINE = os.environ.get('UDM_V41_FRONTIER_BASELINE') == 'v4'
ACTIVE_MODULE = MODULE if not BASELINE else MODULE.removesuffix('41')+'4'
RESEARCH = Path(__file__).resolve().parent
ACTIVE_RECORDS = RESEARCH/('archaeology/native-authority-v4' if BASELINE else 'archaeology/native-authority-v41')


def helper(name, filename):
    path = ACTIVE_RECORDS/filename
    if not path.is_file():
        raise AssertionError('new versioned V41 helper required: '+filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeFrontierV41BindingContracts(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(ACTIVE_MODULE), 'versioned V41 controller required')
        self.q = importlib.import_module(ACTIVE_MODULE)

    def gate_fixture(self, version='V41', catalog_path=CATALOG):
        gate = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': 'a'*40,
                'run_id': 1, 'artifact_id': 2, 'artifact_sha256': 'b'*64,
                'qualification_result_sha256': 'c'*64, 'result_path': 'fixture/result.json'}
        catalog = {'schema': 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3', 'profiles': []}
        value = copy.deepcopy(self.q.DEFAULTS)
        value.update(environment_gate=gate, catalog={'path': catalog_path, 'sha256': 'd'*64})
        result = {'status': gate['status'], 'source_commit': gate['source_commit'],
                  'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_'+version,
                  'freeze': {'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_'+version,
                             'files': {catalog_path: 'd'*64},
                             'catalog_sha256': self.q.worker.fingerprint(catalog)},
                  'first_task_gate': {'status': 'PASS'},
                  'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)}}
        return value, gate, result, catalog

    def test_default_frontier_is_versioned_and_stays_unprepared(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(self.q, 'PROTOCOL', Path(folder)/'absent.json'):
            value = self.q.protocol()
        self.assertEqual(value['schema'], 'UDM_NATIVE_FRONTIER_PROTOCOL_V41')
        self.assertEqual(value['state'], 'PREPARED_NOT_FROZEN')
        self.assertIsNone(value['environment_gate'])

    def test_new_paths_and_baseline_preserve_all_previous_v4_bytes(self):
        self.assertEqual(self.q.RECORDS, RESEARCH/'archaeology/native-authority-v41')
        self.assertEqual(self.q.PROTOCOL, self.q.RECORDS/'FRONTIER_PROTOCOL.json')
        self.assertEqual(self.q.METADATA, self.q.RECORDS/'FRESH_TASK_METADATA.json')
        self.assertEqual(self.q._BASELINE, BASE)

    def test_new_environment_is_bound_without_changing_native_worker(self):
        from . import native_execution_v3 as worker
        from . import native_environment_v4 as previous_environment
        from . import qualify_native_frontier_v4 as previous
        self.assertIs(self.q.worker, worker)
        self.assertIs(previous.environment, previous_environment)
        self.assertEqual(self.q.environment.__name__,
                         'research.unified_consequence_runtime.native_environment_v41')
        self.assertIsNot(self.q.environment, previous_environment)
        self.assertIs(self.q._prepare.__code__, previous._prepare.__code__)
        self.assertIs(self.q._prepare.__globals__['environment'], self.q.environment)

    def test_original_policy_search_uses_private_v41_dispatch(self):
        from . import qualify_native_frontier_v2 as original
        from . import native_execution_v3 as worker
        bound = self.q.isolated_binding('search')
        self.assertIs(bound.__code__, original.search.__code__)
        self.assertIsNot(bound.__globals__, vars(original))
        self.assertIs(bound.__globals__['worker'], worker)
        self.assertIs(bound.__globals__['native_probe'], self.q.native_probe)
        self.assertIs(bound.__globals__['reconstruct_profiles'], self.q.reconstruct_profiles)
        self.assertEqual(bound.__globals__['MODULE'], MODULE)

    def test_checker_is_a_real_importable_v41_function(self):
        from .native_meta_decision import _checker_source
        record = _checker_source(self.q.reconstruct_profiles)
        self.assertEqual(record['module'], MODULE)
        self.assertEqual(Path(record['path']), Path(self.q.__file__).resolve())

    def test_v4_result_cannot_qualify_the_new_dependency_metadata_policy(self):
        value, _, result, catalog = self.gate_fixture('V4')
        with patch.object(self.q, 'ENVIRONMENT_GATE_FILES', ()), \
                patch.object(self.q, '_bound_json', side_effect=[result, catalog]):
            with self.assertRaisesRegex(ValueError, r'V41|v41|v4\.1'):
                self.q.require_environment_gate(value)

    def test_v41_result_and_exact_new_catalog_can_satisfy_the_gate(self):
        value, gate, result, catalog = self.gate_fixture()
        with patch.object(self.q, 'ENVIRONMENT_GATE_FILES', ()), \
                patch.object(self.q, '_bound_json', side_effect=[result, catalog]):
            try:
                actual = self.q.require_environment_gate(value)
            except ValueError as error:
                self.fail('V41 gate/schema/catalog binding is missing: '+str(error))
        self.assertEqual(actual, gate)

    def test_old_catalog_path_is_not_an_authority_for_v41(self):
        old = 'research/unified_consequence_runtime/archaeology/native-environment-v3/ENVIRONMENT_CATALOG.json'
        value, _, result, catalog = self.gate_fixture(catalog_path=old)
        with patch.object(self.q, 'ENVIRONMENT_GATE_FILES', ()), \
                patch.object(self.q, '_bound_json', side_effect=[result, catalog]):
            with self.assertRaisesRegex(ValueError, r'V41 catalog|v41 catalog|v4\.1 catalog'):
                self.q.require_environment_gate(value)

    def test_gate_pins_new_selector_qualifier_catalog_and_workflow(self):
        required = {CATALOG, '.github/workflows/udm-prospective-native-selection-v41.yml',
                    *(('research/unified_consequence_runtime/'+name) for name in (
                        'native_environment_selection_v41.py', 'native_environment_v41.py',
                        'qualify_environment_selection_v41.py', 'qualify_native_frontier_v41.py',
                        'test_qualify_native_frontier_v41.py'))}
        self.assertTrue(required <= set(self.q.ENVIRONMENT_GATE_FILES),
                        'the independent V41 qualification must pin all new authority sources')

    def test_canonical_module_entrypoint_keeps_checker_identity(self):
        called = []
        def source_free_main():
            from .native_meta_decision import _checker_source
            called.append(_checker_source(self.q.reconstruct_profiles)['module'])
        with patch.object(self.q, 'main', source_free_main), warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            runpy.run_module(ACTIVE_MODULE, run_name='__main__')
        self.assertEqual(called, [MODULE])

    def test_screening_and_original_matched_budgets_do_not_change(self):
        defaults = self.q.DEFAULTS
        self.assertEqual((defaults['search_budget'], defaults['candidate_cap_per_file'],
                          defaults['acquisition_native_calls'], defaults['training_seconds'],
                          defaults['requested_roles']), (8, 64, 512, 3600, 2))
        pool = [{'repo': 'fixture/'+name} for name in ('one', 'two', 'three')]
        reports = [{'repository': spec['repo'], 'spec_sha256': self.q.worker.fingerprint(spec),
                    'status': status, 'eligible': True,
                    'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
                   for spec, status in zip(pool, ('PASS_NATIVE', 'FAIL_NATIVE', 'PASS_NATIVE'))]
        selected = self.q.select_screened_roles(pool, reports)
        self.assertEqual([row['repo'] for row in selected], ['fixture/one', 'fixture/two'])
        self.assertEqual(len(reports), 3)
        with self.assertRaisesRegex(ValueError, 'shortfall'):
            self.q.select_screened_roles([], [])

    def test_no_source_reading_cli_can_self_authorize(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); request = root/'request.json'; request.write_text('{}')
            for flag, target in (('--catalog-spec', 'catalog'), ('--screen-spec', 'admission_only_screen'),
                                 ('--agent-spec', 'execute_agent_candidate')):
                with self.subTest(flag=flag), \
                        patch.object(sys, 'argv', [MODULE, flag, str(request), '--out', str(root/'out')]), \
                        patch.object(self.q, target) as operation:
                    with self.assertRaisesRegex(ValueError, 'external authority'):
                        self.q.main()
                    operation.assert_not_called()


class NativeFrontierV41PreparationContracts(unittest.TestCase):
    def test_curator_import_has_no_universe_and_uses_v41_authority(self):
        curator = helper('_v41_empty_curator', 'curate_frontier.py')
        self.assertEqual(curator.UNIVERSE, ())
        self.assertEqual(curator.q.MODULE, MODULE)
        self.assertEqual(curator.SCHEMA, 'UDM_NATIVE_AUTHORITY_V41_METADATA_PREQUERY_V1')
        with self.assertRaisesRegex(ValueError, 'qualified|universe'):
            curator.plan(RESEARCH)

    def test_v41_gate_precedes_any_universe_file_read(self):
        curator = helper('_v41_gate_curator', 'curate_frontier.py')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); gate = root/'gate.json'; gate.write_text('{}')
            with patch.object(curator.q, 'require_environment_gate', side_effect=ValueError('pending V41 gate')):
                with self.assertRaisesRegex(ValueError, 'pending V41 gate'):
                    curator.configure_universe(root/'unread.json', gate, root/'unread.zip')

    def test_every_prior_v4_universe_member_is_excluded(self):
        curator = helper('_v41_history_curator', 'curate_frontier.py')
        prior = json.loads((RESEARCH/'archaeology/native-authority-v4/DECLARED_UNIVERSE.json').read_text())
        excluded, inputs = curator.exclusions(RESEARCH, curator.original(RESEARCH))
        self.assertTrue(set(prior['repositories']) <= set(excluded),
                        'all nine previously queried V4 repositories are historical exposures')
        self.assertTrue(all(row.get('status') != 'MISSING' for row in inputs))
        prior_path = 'archaeology/native-authority-v4/DECLARED_UNIVERSE.json'
        self.assertIn(prior_path, {row['path'] for row in inputs})

    def test_local_record_assembler_is_bound_to_new_records(self):
        assembler = helper('_v41_record_assembler', 'prepare_records.py')
        self.assertEqual(assembler.q.MODULE, MODULE)
        self.assertEqual(assembler.prepare.__globals__['q'].RECORDS,
                         RESEARCH/'archaeology/native-authority-v41')

    def test_curator_cannot_retarget_an_existing_query_lineage(self):
        curator = helper('_v41_once_curator', 'curate_frontier.py')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(curator, 'RECORDS', root):
                with self.assertRaisesRegex(ValueError, 'canonical.*(query|prequery)'):
                    curator.query(root/'research/runtime', root/'PREQUERY.json', root/'gate.json',
                                  root/'artifact.zip', root/'replacement')
                (root/'PREQUERY_EXECUTION.json').write_text('{}')
                with self.assertRaisesRegex(ValueError, 'prior.*query|query.*retained'):
                    curator.query(root/'research/runtime', root/'PREQUERY.json', root/'gate.json',
                                  root/'artifact.zip', root)

    def test_workflow_is_new_source_pinned_and_does_not_claim_an_actual_agent(self):
        version = 'v4' if BASELINE else 'v41'
        path = RESEARCH.parents[1]/('.github/workflows/udm-prospective-native-selection-'+version+'.yml')
        self.assertTrue(path.is_file(), 'new source-pinned V41 reproduction workflow required')
        raw = path.read_text()
        self.assertTrue('research/udm-native-authority-v4-includes-20261016' in raw,
                        'V41 workflow must use the new declared research branch')
        self.assertIn('[qualify-native-v41]', raw)
        self.assertIn('qualify_native_frontier_v41', raw)
        self.assertRegex(raw, r'(?m)^      GIT_OPTIONAL_LOCKS: [\'"]0[\'"]$')
        self.assertIn("'actual_coding_agent_in_CI': False", raw)
        self.assertIn('archaeology/native-environment-v3/bootstrap/prepare_runtimes.py', raw)


if __name__ == '__main__':
    unittest.main()
