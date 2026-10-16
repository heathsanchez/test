"""Synthetic pre-exposure contracts; these establish no scientific outcome."""
import copy
import importlib
import importlib.util
import json
import inspect
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

MODULE = 'research.unified_consequence_runtime.qualify_native_frontier_v3'


class NativeFrontierV3Contracts(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE), 'new versioned controller required')
        self.q = importlib.import_module(MODULE)

    def test_prepared_defaults_cannot_freeze_without_exact_environment_gate(self):
        value = self.q.protocol()
        self.assertEqual(value['state'], 'PREPARED_NOT_FROZEN')
        self.assertIsNone(value['environment_gate'])
        self.assertEqual((value['search_budget'], value['candidate_cap_per_file']), (8, 64))
        self.assertEqual((value['acquisition_native_calls'], value['training_seconds']), (512, 3600))
        with self.assertRaisesRegex(ValueError, 'environment qualification'):
            self.q.require_environment_gate(value)

    def test_gate_names_resolve_to_actual_qualified_sources_and_bootstrap(self):
        self.assertTrue(hasattr(self.q, 'ENVIRONMENT_GATE_FILES'), 'actual gate source list required')
        root = Path(self.q.HERE).parents[1]
        for name in self.q.ENVIRONMENT_GATE_FILES:
            self.assertTrue((root/name).is_file(), name)
        self.assertIn('research/unified_consequence_runtime/qualify_environment_selection_v3.py',
                      self.q.ENVIRONMENT_GATE_FILES)
        self.assertIn('.github/workflows/udm-native-environment-selection-v3.yml', self.q.ENVIRONMENT_GATE_FILES)
        self.assertIn('runtime_paths', inspect.signature(self.q.write_freeze).parameters)

    def test_runner_runtime_inventory_is_fresh_identity_not_qualified_ci_paths(self):
        self.assertTrue(hasattr(self.q, 'freeze_runtime_inventory'), 'runner-local inventory creation required')
        catalog = {'schema': 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3', 'profiles': [
            {'id': 'fixture', 'python_version': '3.12.14', 'python_implementation': 'CPython',
             'pytest_version': '8.4.1', 'packages': ['pytest==8.4.1'], 'plugins': []}]}
        record = {'interpreter': '/new-runner/python', 'identity': {'fixture': 'runtime'}}
        with patch.object(self.q.environment, 'freeze_runtime', return_value=record) as freeze, \
             patch.object(self.q.environment, 'validate_runtime', return_value=record['identity']) as validate:
            inventory = self.q.freeze_runtime_inventory({'fixture': '/new-runner/python'}, catalog)
        freeze.assert_called_once_with('/new-runner/python')
        validate.assert_called_once_with(catalog['profiles'][0], record)
        self.assertEqual(inventory['runtimes'], {'fixture': record})
        self.assertEqual(inventory['catalog_sha256'], self.q.worker.fingerprint(catalog))
        with self.assertRaisesRegex(ValueError, 'complete runner-local'):
            self.q.freeze_runtime_inventory({}, catalog)

    def test_reused_algorithms_are_identical_bytecode_with_isolated_worker_globals(self):
        from . import qualify_native_frontier_v2 as old
        bound = self.q.isolated_binding('search')
        self.assertIs(bound.__code__, old.search.__code__)
        self.assertIsNot(bound.__globals__, old.search.__globals__)
        self.assertIs(bound.__globals__['worker'], self.q.worker)
        self.assertIsNot(old.worker, self.q.worker)

    def test_screening_accepts_pass_and_failure_equally_and_keeps_all_refusals(self):
        pool = [{'repo': 'fixture/'+name} for name in ('one', 'two', 'three', 'four')]
        reports = [{'spec_sha256': self.q.worker.fingerprint(row), 'repository': row['repo'],
                    'status': status, 'eligible': status in ('PASS_NATIVE', 'FAIL_NATIVE'),
                    'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'}
                   for row, status in zip(pool, ('UNKNOWN_COLLECTION_ERROR', 'PASS_NATIVE', 'FAIL_NATIVE', 'PASS_NATIVE'))]
        selected = self.q.select_screened_roles(pool, reports, requested=3)
        self.assertEqual([r['repo'] for r in selected], ['fixture/two', 'fixture/three', 'fixture/four'])
        self.assertEqual([r['role'] for r in selected], ['TRAINING', 'PROTECTED_FUTURE_1', 'PROTECTED_FUTURE_2'])
        self.assertEqual(len(reports), 4)
        altered = copy.deepcopy(reports); altered[1]['eligible'] = False
        with self.assertRaisesRegex(ValueError, 'eligibility'):
            self.q.select_screened_roles(pool, altered, requested=3)

    def test_screening_forbids_catalog_or_policy_outcome_fields(self):
        pool = [{'repo': 'fixture/one'}]
        report = {'spec_sha256': self.q.worker.fingerprint(pool[0]), 'repository': 'fixture/one',
                  'status': 'FAIL_NATIVE', 'eligible': True,
                  'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH', 'candidate_catalog': []}
        with self.assertRaisesRegex(ValueError, 'search information'):
            self.q.select_screened_roles(pool, [report], requested=1)

    def test_screening_envelope_seals_future_native_packets_and_failure_bit(self):
        self.assertTrue(hasattr(self.q, 'screening_envelope'), 'sealed screening envelope required')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'SCREENING_CASE.json'
            base = {'repository': 'fixture/future', 'spec_sha256': 'a'*64, 'eligible': True,
                    'screening_mode': 'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH',
                    'baseline': {'packet': {'stdout.log': 'protected future source trace'}},
                    'partial_native_reports': [], 'total_wall_seconds': 2.0}
            envelopes = []
            for status in ('PASS_NATIVE', 'FAIL_NATIVE'):
                report = dict(base, status=status); path.write_text(json.dumps(report))
                envelope = self.q.screening_envelope(report, path)
                self.assertNotIn('baseline', envelope)
                self.assertNotIn('protected future source trace', json.dumps(envelope))
                envelopes.append(envelope['status'])
            self.assertEqual(envelopes, ['ADMITTED_NATIVE', 'ADMITTED_NATIVE'])

    def test_screening_shortfall_never_selects_unlisted_replacement(self):
        with self.assertRaisesRegex(ValueError, 'shortfall'):
            self.q.select_screened_roles([], [], requested=3)

    def test_acquisition_budget_counts_both_producer_and_independent_calls(self):
        machine = SimpleNamespace(costs=[
            {'phase': 'generic_native_v2_independent_verification', 'costs': {'native_calls': 256}},
            {'phase': 'independent_native_v2_receipt_reexecution', 'costs': {'native_calls': 256}},
            {'phase': 'native_v2_probe_envelope', 'native_calls': 512, 'inclusive_not_additive': True}])
        with patch.object(self.q.time, 'monotonic', return_value=1):
            with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                self.q.acquisition_budget(machine, {'acquisition_started_monotonic': 0})
            self.q.acquisition_budget(machine, {'acquisition_started_monotonic': 0}, reserve=False)

    def test_incomplete_native_attempt_accounting_refuses_promotion_budget(self):
        machine = SimpleNamespace(costs=[{'phase': 'generic_native_v2_independent_verification',
            'costs': {'native_calls': 0}, 'accounting_complete': False}])
        with patch.object(self.q.time, 'monotonic', return_value=1):
            with self.assertRaisesRegex(ValueError, 'ATTEMPT_ACCOUNTING'):
                self.q.acquisition_budget(machine, {'acquisition_started_monotonic': 0}, reserve=False)

    def test_training_reserves_all_four_reconstruction_passes_and_future(self):
        machine = SimpleNamespace(costs=[{'phase': 'generic_native_v2_independent_verification',
                                         'costs': {'native_calls': 100}}])
        with patch.object(self.q.time, 'monotonic', return_value=1):
            with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                self.q.acquisition_budget(machine, {'acquisition_started_monotonic': 0, 'stage': 'TRAINING'})

    def fixture_episodes(self):
        candidates = [{'replacements': [{'replacement': str(i)}]} for i in range(8)]
        order = [self.q.worker.fingerprint(c) for c in candidates]
        records = {str(i): {'candidate': c, 'contract': {'task': 'future'},
                            'producer': {'dependencies': []}, 'receipt': {'status': 'FAIL_NATIVE'}}
                   for i, c in enumerate(candidates)}
        winner = 'warm'
        records[winner] = {'candidate': candidates[-1], 'contract': {'task': 'future'},
                           'producer': {'dependencies': ['policy']}, 'receipt': {'status': 'PASS_NATIVE',
                            'execution': {'process_exit_code': 0},
                            'junit': dict(tests=1, passed=1, failures=0, errors=0, skipped=0)}}
        cold = {'winner': None, 'attempts': [str(i) for i in range(8)], 'within_budget': True, 'budget': 8}
        warm = {'winner': order[-1], 'attempts': [winner], 'within_budget': True, 'budget': 8}
        machine = SimpleNamespace(get=lambda key: records[key])
        return machine, records, order, cold, warm

    def test_future_requires_exact_selected_order_candidate_contract_and_dependency(self):
        machine, records, order, cold, warm = self.fixture_episodes()
        def check(record, *args, **kwargs): return record['receipt']
        with patch.object(self.q, 'checked_record', side_effect=check):
            self.assertTrue(self.q.future_selection_warrant(machine, {'cold': cold, 'warm': warm}, order,
                [order[-1], *order[:-1]], 8, contract={'task': 'future'}, policy_id='policy'))
            records['warm']['producer']['dependencies'] = []
            self.assertFalse(self.q.future_selection_warrant(machine, {'cold': cold, 'warm': warm}, order,
                [order[-1], *order[:-1]], 8, contract={'task': 'future'}, policy_id='policy'))
            records['warm']['producer']['dependencies'] = ['policy']
            warm['winner'] = order[0]
            self.assertFalse(self.q.future_selection_warrant(machine, {'cold': cold, 'warm': warm}, order,
                [order[-1], *order[:-1]], 8, contract={'task': 'future'}, policy_id='policy'))

    def test_future_cold_must_complete_all_eight_native_failures(self):
        machine, records, order, cold, warm = self.fixture_episodes()
        with patch.object(self.q, 'checked_record', side_effect=lambda row, *a, **k: row['receipt']):
            cold['attempts'].pop()
            self.assertFalse(self.q.future_selection_warrant(machine, {'cold': cold, 'warm': warm}, order,
                [order[-1], *order[:-1]], 8, contract={'task': 'future'}, policy_id='policy'))

    def test_policy_route_falls_back_only_when_physical_program_is_absent(self):
        with tempfile.TemporaryDirectory() as folder:
            machine = SimpleNamespace(state=Path(folder)); (machine.state/'objects').mkdir()
            node = SimpleNamespace(payload={'program': 'a'*64})
            machine.log = [SimpleNamespace(id='policy', **vars(node))]
            orders = {'COLD_V104_ORDER': ['cold'], 'selected': ['warm']}
            with patch.object(self.q, 'invoke_meta_policy') as invoke:
                route = self.q.operation_order(machine, 'policy', orders, binding='b'*64, catalog_sha256='c'*64)
                self.assertEqual(route['order'], ['cold']); invoke.assert_not_called()
            (machine.state/'objects'/('a'*64)).write_text('{}')
            with patch.object(self.q, 'invoke_meta_policy', side_effect=ValueError('forged scope')):
                with self.assertRaisesRegex(ValueError, 'forged scope'):
                    self.q.operation_order(machine, 'policy', orders, binding='b'*64, catalog_sha256='c'*64)

    def test_agent_requires_original_candidate_membership_and_charges_all_calls(self):
        candidate = {'replacements': []}; ident = self.q.worker.fingerprint(candidate)
        arm = {'schema': self.q.AGENT_SCHEMA, 'status': 'READY_NOT_EXECUTED', 'protocol_binding': 'b'*64,
               'candidate_budget': 8, 'total_acquisition_native_calls': 512,
               'total_acquisition_wall_seconds': 3600, 'candidate_catalog': [{'id': ident, 'candidate': candidate}],
               'contract': {'protocol_binding': 'b'*64}, 'authority': {}, 'certificate': {}, 'policy': {}}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'original catalog'):
                self.q.execute_agent_candidate(arm, {'replacements': [{'replacement': 'extra'}]}, Path(folder)/'reject')
            with patch.object(self.q.worker, 'verify', return_value={'status': 'FAIL_NATIVE', 'costs': {'native_calls': 1}}), \
                 patch.object(self.q.worker, 'validate_receipt', return_value={'independent_reexecution': {'costs': {'native_calls': 1}}}):
                self.q.execute_agent_candidate(arm, candidate, Path(folder)/'run')
            meter = json.loads((Path(folder)/'ARM_METER.json').read_text())
            self.assertEqual(meter['native_calls'], 2)
            self.assertEqual(meter['proposals'], 1)

    def test_agent_independent_rejection_retains_producer_and_partial_check_cost(self):
        candidate = {'replacements': []}; ident = self.q.worker.fingerprint(candidate)
        arm = {'schema': self.q.AGENT_SCHEMA, 'protocol_binding': 'b'*64,
               'candidate_budget': 8, 'total_acquisition_native_calls': 512,
               'total_acquisition_wall_seconds': 3600, 'candidate_catalog': [{'id': ident, 'candidate': candidate}],
               'contract': {'protocol_binding': 'b'*64}, 'authority': {}, 'certificate': {}, 'policy': {}}
        with tempfile.TemporaryDirectory() as folder:
            def rejected(*args, **kwargs):
                out = kwargs['output_dir']/'execution'; out.mkdir(parents=True)
                (out/'checked-report.json').write_text(json.dumps({'costs': {'native_calls': 1}}))
                raise ValueError('independent native rejection')
            with patch.object(self.q.worker, 'verify', return_value={'status': 'PASS_NATIVE', 'costs': {'native_calls': 1}}), \
                 patch.object(self.q.worker, 'validate_receipt', side_effect=rejected):
                with self.assertRaisesRegex(ValueError, 'independent native rejection'):
                    self.q.execute_agent_candidate(arm, candidate, Path(folder)/'run')
            meter = json.loads((Path(folder)/'ARM_METER.json').read_text())
            self.assertEqual(meter['native_calls'], 2)

    def test_qualification_refuses_unqualified_gate_before_any_source_transport(self):
        args = SimpleNamespace(repo='/unused', freeze='/unused', out='/unused')
        self.assertTrue(hasattr(self.q, 'qualify'), 'prepared qualifier entrypoint required')
        with patch.object(self.q.environment, 'provision') as provision:
            with self.assertRaisesRegex(ValueError, 'environment qualification'):
                self.q.qualify(args)
            provision.assert_not_called()

    def test_agent_common_learning_wall_is_charged_before_fresh_execution(self):
        candidate = {'replacements': []}; ident = self.q.worker.fingerprint(candidate)
        arm = {'schema': self.q.AGENT_SCHEMA, 'protocol_binding': 'b'*64,
               'candidate_budget': 8, 'total_acquisition_native_calls': 512,
               'total_acquisition_wall_seconds': 3600, 'candidate_catalog': [{'id': ident, 'candidate': candidate}],
               'common_acquisition_wall_seconds': 3601,
               'contract': {'protocol_binding': 'b'*64}, 'authority': {}, 'certificate': {}, 'policy': {}}
        with tempfile.TemporaryDirectory() as folder, patch.object(self.q.worker, 'verify') as verify:
            with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                self.q.execute_agent_candidate(arm, candidate, Path(folder)/'run')
            verify.assert_not_called()

    def test_physical_removal_deletes_real_program_and_retains_restart_cost(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); state = root/'original-state'; (state/'objects').mkdir(parents=True)
            raw = b'original retained executable'; program = self.q.digest(raw)
            (state/'objects'/program).write_bytes(raw)
            node = SimpleNamespace(id='policy', payload={'program': program})
            machine = SimpleNamespace(state=state, costs=[{'phase': 'common'}])
            def clone_machine(components, clone_state, *args):
                return SimpleNamespace(state=clone_state, costs=[{'phase': 'actual-clone-reclosure'}], log=[node])
            def unavailable(clone, *args):
                self.assertFalse((clone.state/'objects'/program).exists())
                self.assertEqual((state/'objects'/program).read_bytes(), raw)
                return {'status': 'UNKNOWN_ENVIRONMENT', 'setup': {'status': 'UNKNOWN_ENVIRONMENT'}}
            with patch.object(self.q, 'Machine', side_effect=clone_machine), \
                 patch.object(self.q, '_prepare', side_effect=unavailable) as prepare:
                result = self.q.physical_removal_counterfactual(machine,
                    {'program': program, 'policy_id': 'policy', 'catalog_sha256': 'a'*64}, {}, {}, [],
                    {'COLD_V104_ORDER': ['original']}, SimpleNamespace(components=root/'components'),
                    root/'removal', 'b'*64, {}, {})
            self.assertTrue(result['policy_program_absent'])
            self.assertEqual(result['route']['order'], ['original'])
            prepare.assert_called_once()
            self.assertIn('actual-clone-reclosure', [row['phase'] for row in result['costs']])

    def test_agent_meter_excludes_overlapping_invocations(self):
        candidate = {'replacements': []}; ident = self.q.worker.fingerprint(candidate)
        arm = {'schema': self.q.AGENT_SCHEMA, 'protocol_binding': 'b'*64,
               'candidate_budget': 8, 'total_acquisition_native_calls': 512,
               'total_acquisition_wall_seconds': 3600, 'candidate_catalog': [{'id': ident, 'candidate': candidate}],
               'contract': {'protocol_binding': 'b'*64}, 'authority': {}, 'certificate': {}, 'policy': {}}
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder)/'ARM_METER.json.lock'; lock.write_text('another actual execution')
            with patch.object(self.q.worker, 'verify', side_effect=AssertionError('overlapping execution admitted')):
                with self.assertRaisesRegex(ValueError, 'already active'):
                    self.q.execute_agent_candidate(arm, candidate, Path(folder)/'run')
            self.assertEqual(lock.read_text(), 'another actual execution')

    def test_agent_malformed_raw_report_preserves_controller_launch_delta(self):
        candidate = {'replacements': []}; ident = self.q.worker.fingerprint(candidate)
        arm = {'schema': self.q.AGENT_SCHEMA, 'protocol_binding': 'b'*64,
               'candidate_budget': 8, 'total_acquisition_native_calls': 512,
               'total_acquisition_wall_seconds': 3600, 'candidate_catalog': [{'id': ident, 'candidate': candidate}],
               'contract': {'protocol_binding': 'b'*64}, 'authority': {}, 'certificate': {}, 'policy': {}}
        snapshots = [{'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0},
                     {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2}]
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(self.q.worker, 'attempt_snapshot', side_effect=snapshots), \
             patch.object(self.q.worker, 'verify', side_effect=ValueError('malformed original raw report')):
            with self.assertRaisesRegex(ValueError, 'malformed original raw report'):
                self.q.execute_agent_candidate(arm, candidate, Path(folder)/'run')
            meter = json.loads((Path(folder)/'ARM_METER.json').read_text())
            self.assertEqual(meter['native_calls'], 1)
            self.assertTrue(meter['attempts'][-1]['accounting_complete'])

    def test_screen_malformed_raw_report_preserves_controller_launch_delta(self):
        snapshots = [{'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0},
                     {'native_calls': 1, 'collection_calls': 2, 'subprocess_attempts': 3}]
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(self.q.worker, 'attempt_snapshot', side_effect=snapshots), \
             patch.object(self.q.environment, 'provision', return_value={
                 'status': 'PREPARED', 'contract': {}, 'authority': {}, 'policy': {}}), \
             patch.object(self.q.worker, 'collect', return_value={}), \
             patch.object(self.q.worker, 'validate_certificate', return_value={}), \
             patch.object(self.q.worker, 'verify', side_effect=ValueError('malformed original raw report')):
            report = self.q.admission_only_screen({'repo': 'fixture/future'}, Path(folder)/'screen',
                                                 'a'*64, catalog={}, runtimes={})
            self.assertFalse(report['eligible'])
            self.assertEqual(report.get('controller_attempts', {}).get('native_calls'), 1)

    def test_versioned_partial_probe_cost_is_retained_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'execution').mkdir()
            (root/'execution/checked-report.json').write_text(json.dumps({'costs': {'native_calls': 1}}))
            machine = SimpleNamespace(costs=[], put=lambda _: 'record', append=lambda *a: 'event', flush=lambda: None)
            def interrupted(candidate):
                machine.costs.append({'phase': 'generic_native_v3_independent_verification',
                                      'output': str(root), 'costs': {}})
                raise ValueError('actual interrupted native run')
            runtime = SimpleNamespace(_live=lambda *a: None, _verify=interrupted, source='s', authority='a',
                                      contract={}, suite_authority={}, certificate={}, policy={})
            retained = self.q.native_probe(machine, runtime, {}, 'interrupted')
            self.assertEqual(retained['receipt']['costs']['native_calls'], 1)
            self.assertEqual(self.q._native_calls(machine), 1)

    def test_profiles_without_in_budget_exact_episode_cannot_reconstruct(self):
        report = {'episode': {'within_budget': False}, 'attempts': []}
        node = SimpleNamespace(id='e', payload={'report': 'r'})
        machine = SimpleNamespace(log=[node], get=lambda _: report)
        with self.assertRaisesRegex(ValueError, 'episode'):
            self.q.reconstruct_profiles(machine, ('cold',), ('training',), ('e',))


if __name__ == '__main__':
    unittest.main()
