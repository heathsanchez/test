"""Source-free acceptance contracts for the metadata-only v4 G2 binding.

Synthetic records only; no fresh target metadata, source or native execution.
"""
import copy
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v4'


class NativeFrontierV4BindingContracts(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
                             'new metadata-only v4 frontier binding required')
        self.q = importlib.import_module(MODULE)

    def test_unqualified_metadata_bridge_cannot_freeze_or_read_source(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(self.q, 'PROTOCOL', Path(folder)/'unprepared.json'):
            value = self.q.protocol()
        self.assertEqual(value['schema'], 'UDM_NATIVE_FRONTIER_PROTOCOL_V4')
        self.assertEqual(value['state'], 'PREPARED_NOT_FROZEN')
        self.assertIsNone(value['environment_gate'])
        self.assertEqual((value['search_budget'], value['candidate_cap_per_file'],
                          value['acquisition_native_calls'], value['training_seconds'],
                          value['requested_roles']), (8, 64, 512, 3600, 2))
        with patch.object(self.q.environment, 'provision') as source:
            with self.assertRaisesRegex(ValueError, 'qualification'):
                self.q.require_environment_gate(value)
            source.assert_not_called()

    def test_native_v3_execution_and_original_search_algorithms_remain_bound(self):
        from . import native_execution_v3 as worker
        from . import native_runtime_v3 as runtime
        from . import qualify_native_frontier_v2 as original
        from . import qualify_native_frontier_v3 as frozen
        self.assertIs(self.q.worker, worker)
        self.assertIs(self.q._prepare.__code__, frozen._prepare.__code__)
        self.assertIs(runtime.verifier, worker)
        bound = self.q.isolated_binding('search')
        self.assertIs(bound.__code__, original.search.__code__)
        self.assertIsNot(bound.__globals__, vars(original))
        self.assertIsNot(bound.__globals__, vars(frozen))
        self.assertIs(bound.__globals__['worker'], worker)
        self.assertIs(bound.__globals__['native_probe'], self.q.native_probe)
        self.assertIs(bound.__globals__['bounded_catalog'], self.q.bounded_catalog)
        self.assertIs(bound.__globals__['reconstruct_profiles'], self.q.reconstruct_profiles)
        self.assertEqual(bound.__globals__['MODULE'], MODULE)

    def test_qualified_environment_v4_is_used_without_mutating_v3_globals(self):
        from . import native_environment_v3 as environment
        from . import native_execution_v3 as worker
        from . import qualify_native_frontier_v3 as frozen
        old_prepare_globals = frozen._prepare.__globals__
        self.assertIs(frozen.environment, environment)
        self.assertIs(frozen.worker, worker)
        self.assertIsNot(self.q.environment, environment)
        self.assertEqual(self.q.environment.__name__,
                         'research.unified_consequence_runtime.native_environment_v4')
        self.assertIs(self.q._prepare.__globals__['environment'], self.q.environment)
        self.assertIs(old_prepare_globals['environment'], environment)
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(self.q, 'acquisition_budget'), \
                patch.object(self.q, '_bound_json', return_value={'fixture': 'catalog'}), \
                patch.object(self.q.environment, 'provision',
                             return_value={'status': 'UNKNOWN_METADATA_FIXTURE'}) as provision:
            outcome = self.q._prepare(SimpleNamespace(costs=[]), {'repo': 'fixture/only'},
                Path(folder)/'not-created', 'a'*64,
                {'catalog': {}, '_runtime_inventory': {},
                 'collection_seconds': 60, 'execution_seconds': 600}, {})
        self.assertEqual(outcome['status'], 'UNKNOWN_METADATA_FIXTURE')
        self.assertEqual(provision.call_args.kwargs['catalog'], {'fixture': 'catalog'})
        self.assertIs(old_prepare_globals['environment'], environment)

    def test_profile_checker_has_real_importable_v4_source_identity(self):
        from .native_meta_decision import _checker_source
        source = _checker_source(self.q.reconstruct_profiles)
        self.assertEqual(source['module'], MODULE)
        self.assertEqual(source['name'], 'reconstruct_profiles')
        self.assertEqual(Path(source['path']), Path(self.q.__file__).resolve())
        self.assertEqual(Path(inspect.getsourcefile(self.q.reconstruct_profiles)).resolve(),
                         Path(self.q.__file__).resolve())
        self.assertEqual(source['sha256'], self.q.digest(Path(self.q.__file__).read_bytes()))

    def test_v3_admission_result_does_not_qualify_v4_metadata_inference(self):
        value = copy.deepcopy(self.q.DEFAULTS)
        gate = {'status': 'ADMISSION_ONLY_QUALIFIED', 'source_commit': 'a'*40,
                'run_id': 1, 'artifact_id': 2, 'artifact_sha256': 'b'*64,
                'qualification_result_sha256': 'c'*64, 'result_path': 'fixture/result.json'}
        value.update(environment_gate=gate, catalog={})
        receipt = {'status': gate['status'], 'source_commit': gate['source_commit'],
            'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V3',
            'freeze': {'schema': 'UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V3'},
            'first_task_gate': {'status': 'PASS'},
            'verdicts': {'G2': 'UNKNOWN', 'G3': 'UNKNOWN', 'G4': 'UNKNOWN'}}
        with patch.object(self.q, '_bound_json', return_value=receipt), \
                patch.object(self.q.environment, 'provision') as source:
            with self.assertRaisesRegex(ValueError, 'admission-only|qualification'):
                self.q.require_environment_gate(value)
            source.assert_not_called()

    def test_screening_keeps_pass_and_fail_equal_in_fixed_source_order(self):
        pool = [{'repo': 'fixture/'+name} for name in ('first', 'second', 'third')]
        reports = [{'repository': spec['repo'], 'spec_sha256': self.q.worker.fingerprint(spec),
                    'status': status, 'eligible': status in ('PASS_NATIVE', 'FAIL_NATIVE'),
                    'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
                   for spec, status in zip(pool, ('PASS_NATIVE', 'FAIL_NATIVE', 'PASS_NATIVE'))]
        roles = self.q.select_screened_roles(pool, reports)
        self.assertEqual([row['repo'] for row in roles], ['fixture/first', 'fixture/second'])
        self.assertEqual([row['role'] for row in roles], ['TRAINING', 'PROTECTED_FUTURE_1'])
        self.assertEqual(len(reports), 3)
        reports[0]['eligible'] = False
        with self.assertRaisesRegex(ValueError, 'eligibility'):
            self.q.select_screened_roles(pool, reports)

    def test_v4_source_reading_cli_refuses_missing_external_authority(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); request = root/'request.json'; request.write_text('{}')
            for flag, target in (('--catalog-spec', 'catalog'),
                                 ('--screen-spec', 'admission_only_screen'),
                                 ('--agent-spec', 'execute_agent_candidate')):
                with self.subTest(flag=flag), \
                        patch.object(sys, 'argv', [MODULE, flag, str(request), '--out', str(root/'out')]), \
                        patch.object(self.q, target) as operation:
                    with self.assertRaisesRegex(ValueError, 'external authority'):
                        self.q.main()
                    operation.assert_not_called()

    def test_v4_freeze_rejects_an_omitted_committed_file_set(self):
        repo = self.q.HERE.parents[1]
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'freeze.json'
            path.write_text(json.dumps({'schema': 'UDM_NATIVE_FRONTIER_FREEZE_V4',
                'source_commit': head, 'baseline_commit': '95029db0d0b2122836bee7268299461bfbdb5a66',
                'all_baseline_files_preserved': True, 'files': {}}))
            with self.assertRaisesRegex(ValueError, 'omits exact committed source'):
                self.q.check_freeze(repo, path)


if __name__ == '__main__':
    unittest.main()
