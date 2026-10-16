"""Pre-exposure authority contracts; fixtures are not scientific outcomes."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    from . import qualify_native_frontier_v2 as experiment
except ImportError:
    experiment = None


class NativeFrontierV2ProtocolContracts(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(experiment, 'versioned prospective controller is missing')

    def test_protocol_requires_independently_qualified_first_gate(self):
        protocol = experiment.protocol()
        self.assertEqual(protocol['search_budget'], 8)
        self.assertEqual(protocol['training_seconds'], 1200)
        self.assertEqual(protocol['metadata_sha256'], experiment.digest(experiment.METADATA.read_bytes()))
        with self.assertRaisesRegex(ValueError, 'admission qualification'):
            experiment.require_admission_gate(dict(protocol, admission_gate=None))
        forged = dict(protocol, admission_gate={'status': 'ADMISSION_ONLY_QUALIFIED'})
        with self.assertRaises(ValueError):
            experiment.require_admission_gate(forged)

    def test_qualified_admission_receipt_cannot_license_changed_or_missing_core(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder); here = repo/'research/unified_consequence_runtime'; here.mkdir(parents=True)
            names = ['research/unified_consequence_runtime/'+name+'.py' for name in (
                'native_admission_v2', 'native_environment_v2', 'native_execution_v2',
                'native_runtime_v2', 'qualify_native_admission_v2')]
            names.append('.github/workflows/udm-native-admission-v2.yml')
            files = {}
            for name in names:
                path = repo/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('independently qualified '+name+'\n')
                files[name] = experiment.digest(path.read_bytes())
            result_path = repo/'qualified-result.json'
            result = {'source_commit': 'a'*40, 'status': 'ADMISSION_ONLY_QUALIFIED',
                      'first_task_gate': {'status': 'PASS'},
                      'verdicts': {key: 'UNKNOWN' for key in ('G2', 'G3', 'G4')},
                      'freeze': {'files': files}}
            result_path.write_text(json.dumps(result))
            gate = {'status': result['status'], 'source_commit': result['source_commit'],
                    'run_id': 1, 'artifact_id': 2, 'artifact_sha256': 'b'*64,
                    'qualification_result_sha256': experiment.digest(result_path.read_bytes()),
                    'result_path': 'qualified-result.json'}
            with patch.object(experiment, 'HERE', here):
                self.assertEqual(experiment.require_admission_gate({'admission_gate': gate}), gate)
                worker = repo/names[2]; original = worker.read_bytes(); worker.write_bytes(b'changed 2.1 worker\n')
                with self.assertRaisesRegex(ValueError, 'qualified admission source'):
                    experiment.require_admission_gate({'admission_gate': gate})
                worker.write_bytes(original)
                for name in names:
                    saved = files.pop(name); result_path.write_text(json.dumps(result))
                    gate['qualification_result_sha256'] = experiment.digest(result_path.read_bytes())
                    with self.assertRaisesRegex(ValueError, 'qualified admission source'):
                        experiment.require_admission_gate({'admission_gate': gate})
                    files[name] = saved

    def test_agent_arm_uses_same_per_search_and_total_acquisition_budgets(self):
        context = {'setup': {'contract': {'fixture': 'contract'}, 'authority': {'fixture': 'authority'},
                            'policy': {'fixture': 'policy'}},
                   'certificate': {'fixture': 'certificate'}, 'baseline': {'receipt': {'fixture': 'residual'}},
                   'catalog': [{'fixture': 'original candidate'}], 'orders': {'ORIGINAL': ['fixture']}}
        with tempfile.TemporaryDirectory() as folder:
            arm = experiment.agent_arm(context, Path(folder)/'ARM.json', 'c'*64, 8)
        self.assertEqual(arm['candidate_budget'], 8)
        self.assertEqual(arm['total_acquisition_native_calls'], 128)
        self.assertEqual(arm['total_acquisition_wall_seconds'], 1200)
        self.assertTrue(arm['native_budget_includes_independent_verification'])
        self.assertEqual(arm['orders'], context['orders'])
        self.assertEqual(arm['candidate_catalog'], context['catalog'])
        self.assertIn('each declared', arm['candidate_budget_semantics'])

    def test_baseline_and_early_ledger_probe_refuse_before_and_preserve_after_budget_overrun(self):
        probe = {'record': 'actual-retained-CAS', 'evidence': 'actual-event',
                 'receipt': {'status': 'PASS_NATIVE', 'costs': {'native_calls': 1}}}
        with patch.object(experiment, 'acquisition_budget', side_effect=ValueError('exhausted')), \
                patch.object(experiment, 'native_probe') as execute:
            with self.assertRaisesRegex(ValueError, 'exhausted'):
                experiment.budgeted_native_probe(None, None, {}, 'baseline', {})
            execute.assert_not_called()
        with patch.object(experiment, 'acquisition_budget', side_effect=[None, ValueError('wall exhausted')]), \
                patch.object(experiment, 'native_probe', return_value=probe) as execute:
            result = experiment.budgeted_native_probe(None, None, {}, 'ledger', {})
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(result['budget_eligibility'], 'UNKNOWN_OVER_BUDGET')
        self.assertEqual(result['status'], 'UNKNOWN_ACQUISITION_BUDGET')
        self.assertEqual(result['record'], 'actual-retained-CAS')
        self.assertEqual(result['receipt']['status'], 'PASS_NATIVE')
        self.assertEqual(result['receipt']['costs']['native_calls'], 1)

    def test_genuine_v2_receipt_success_uses_actual_process_exit(self):
        receipt = {'status': 'PASS_NATIVE', 'execution': {'process_exit_code': 0},
                   'junit': dict(tests=3, passed=3, failures=0, errors=0, skipped=0)}
        self.assertTrue(experiment.passed(receipt))
        self.assertFalse(experiment.passed(dict(receipt, execution={'process_exit_code': 1})))
        self.assertFalse(experiment.passed(dict(receipt, status='FAIL_NATIVE')))
        self.assertFalse(experiment.passed(dict(receipt, status='UNKNOWN_SKIPPED_OR_XFAIL')))
        self.assertFalse(experiment.passed(dict(receipt, junit=dict(receipt['junit'], skipped=1))))
        self.assertFalse(experiment.passed(dict(receipt, junit=dict(tests=0, passed=0, failures=0, errors=0, skipped=0))))
        self.assertFalse(experiment.passed(dict(receipt, execution={})))

    def test_v2_proposal_and_reconstruction_share_exact_failure_trace_bytes(self):
        receipt = {'schema': 'UDM_GENERIC_NATIVE_PYTEST_V2', 'packet': {
            'stdout.log': base64.b64encode(b'pkg/source.py:42: AssertionError').decode(),
            'stderr.log': base64.b64encode(b'pkg/source.py:43: native frame').decode(),
            'native.xml': base64.b64encode(b'<failure>pkg/source.py:44</failure>').decode(),
            'checked-report.json': base64.b64encode(b'pkg/source.py:999').decode()}}
        observation = experiment.native_observation(receipt)
        from .decisive_native import trace_lines
        self.assertEqual(trace_lines(observation, ['pkg/source.py']), {'pkg/source.py': (42, 43, 44)})
        self.assertNotIn('evidence_dir', observation)
        self.assertEqual(experiment.native_observation(receipt), observation)

    def test_incomplete_or_unknown_native_prefix_is_never_closed_failure(self):
        values = {'r': {'candidate': {'replacements': []}, 'receipt': {'status': 'UNKNOWN_NATIVE_ERROR'}}}
        machine = type('Fixture', (), {'get': lambda _, key: values[key]})()
        order = [experiment.worker.fingerprint(values['r']['candidate'])]
        with patch.object(experiment, 'checked_record', return_value=values['r']['receipt']):
            self.assertFalse(experiment.closed_failure(machine, {'winner': None, 'attempts': ['r'], 'within_budget': True}, order, 8))
            values['r']['receipt']['status'] = 'FAIL_NATIVE'
            self.assertTrue(experiment.closed_failure(machine, {'winner': None, 'attempts': ['r'], 'within_budget': True}, order, 8))
            self.assertFalse(experiment.closed_failure(machine, {'winner': None, 'attempts': [], 'within_budget': True}, order, 8))
            self.assertFalse(experiment.closed_failure(machine, {'winner': 'x', 'attempts': ['r'], 'within_budget': True}, order, 8))

    def test_unknown_native_search_stops_without_promotion_or_hidden_calls(self):
        candidate = {'replacements': []}; ident = experiment.worker.fingerprint(candidate)
        rows = [{'id': ident, 'candidate': candidate}]
        observed = {'record': 'retained', 'evidence': 'event',
                    'receipt': {'status': 'UNKNOWN_NATIVE_ERROR', 'costs': {'native_calls': 1}}}
        with patch.object(experiment, 'native_probe', return_value=observed) as probe:
            result = experiment.search(None, None, rows, [ident], 8, {}, 'fixture', seconds=1200)
        self.assertEqual(probe.call_count, 1)
        self.assertEqual(result['status'], 'UNKNOWN_NATIVE_OBLIGATION')
        self.assertIsNone(result['winner'])
        self.assertEqual(result['attempts'], ['retained'])
        self.assertEqual(result['complete_old_language_obstruction'], 'NOT_ESTABLISHED')

    def test_post_call_wall_overrun_retains_attempt_without_winner(self):
        candidate = {'replacements': []}; ident = experiment.worker.fingerprint(candidate)
        observed = {'record': 'retained', 'evidence': 'event', 'receipt': {
            'status': 'PASS_NATIVE', 'execution': {'process_exit_code': 0},
            'junit': dict(tests=1, passed=1, failures=0, errors=0, skipped=0),
            'costs': {'native_calls': 1}}}
        with patch.object(experiment, 'native_probe', return_value=observed), \
                patch.object(experiment.time, 'monotonic', side_effect=[0.0, 0.0, 2.0]):
            result = experiment.search(None, None, [{'id': ident, 'candidate': candidate}], [ident],
                                       8, {}, 'fixture', seconds=1)
        self.assertEqual(result['attempts'], ['retained'])
        self.assertEqual(result['status'], 'UNKNOWN_SEARCH_BUDGET')
        self.assertIsNone(result['winner'])
        self.assertFalse(result['within_budget'])

    def test_future_gate_refuses_missing_cold_success_or_incomplete_warm(self):
        with patch.object(experiment, 'closed_failure', return_value=True), \
                patch.object(experiment, 'checked_record', return_value={'status': 'PASS_NATIVE'}):
            machine = type('Fixture', (), {'get': lambda _, key: {'fixture': key}})()
            good = {'cold': {'winner': None, 'attempts': ['cold'], 'within_budget': True},
                    'warm': {'winner': 'operator', 'attempts': ['warm'], 'within_budget': True}}
            self.assertTrue(experiment.future_selection_warrant(machine, good, ['operator'], 8))
            self.assertFalse(experiment.future_selection_warrant(machine, None, ['operator'], 8))
            self.assertFalse(experiment.future_selection_warrant(machine, dict(good,
                warm=dict(good['warm'], winner=None)), ['operator'], 8))
            self.assertFalse(experiment.future_selection_warrant(machine, dict(good,
                warm=dict(good['warm'], within_budget=False)), ['operator'], 8))
        with patch.object(experiment, 'closed_failure', return_value=False):
            self.assertFalse(experiment.future_selection_warrant(None, good, ['operator'], 8))

    def test_profile_receipt_requires_exact_producer_and_actual_independent_reexecution(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as folder:
            raw = {'schema': 'UDM_NATIVE_PROFILE_RECORD_V2', 'contract': {'fixture': 'contract'},
                   'candidate': {'replacements': []}, 'authority': {'fixture': 'suite'},
                   'certificate': {'fixture': 'certificate'}, 'policy': {'fixture': 'policy'},
                   'receipt': {'status': 'PASS_NATIVE'},
                   'producer': {'source': 'source', 'authority': 'authority', 'dependencies': []}}
            objects = {'contract': raw['contract'], 'suite': raw['authority'],
                       'certificate': raw['certificate'], 'policy': raw['policy']}
            descriptor = {'contract': 'contract', 'suite_authority': 'suite',
                          'certificate': 'certificate', 'policy': 'policy'}
            nodes = [SimpleNamespace(id='authority', kind='execution_authority_ceiling',
                         payload=experiment.AUTHORITY, premises=()),
                     SimpleNamespace(id='source', kind='generic_native_source',
                         payload={'source': descriptor}, premises=('authority',)),
                     SimpleNamespace(id='event', kind='native_frontier_v2_probe',
                         payload={'record': experiment.worker.fingerprint(raw)}, premises=('source', 'authority'))]
            live = {node.id for node in nodes}
            machine = SimpleNamespace(log=nodes, mt=SimpleNamespace(live_ids=lambda _: live),
                flash_live_ids=lambda: live, get=lambda key: objects[key], state=Path(folder)/'state', costs=[])
            with patch.object(experiment.worker, 'validate_receipt', return_value=raw['receipt']) as check:
                experiment.checked_record(raw, machine)
                self.assertIs(check.call_args.kwargs['independent'], True)
                nodes[-1].premises = ('source',)
                with self.assertRaisesRegex(ValueError, 'producer'):
                    experiment.checked_record(raw, machine)
                self.assertEqual(check.call_count, 1)
            nodes[-1].premises = ('source', 'authority')
            with patch.object(experiment.worker, 'validate_receipt', side_effect=ValueError('independent native rejection')):
                with self.assertRaisesRegex(ValueError, 'independent native rejection'):
                    experiment.checked_record(raw, machine)

    def test_same_budget_charges_separate_baseline_execution(self):
        candidate = {'replacements': []}; ident = experiment.worker.fingerprint(candidate)
        rows = [{'id': ident, 'candidate': candidate}]
        observed = {'record': 'retained', 'evidence': 'event',
                    'receipt': {'status': 'FAIL_NATIVE', 'costs': {'native_calls': 1}}}
        with patch.object(experiment, 'native_probe', return_value=observed) as probe:
            first = experiment.search(None, None, rows, [ident], 8, {}, 'original', seconds=1200)
            ledger = experiment.search(None, None, rows, [ident], 8, {}, 'ledger', seconds=1200)
        self.assertEqual(probe.call_count, 2)
        self.assertEqual(first['budget'], ledger['budget'])
        self.assertEqual(first['status'], 'UNKNOWN_SEARCH')

    def test_qualification_training_ledger_uses_inclusive_scope_and_deadline(self):
        from types import SimpleNamespace
        candidate = {'replacements': []}; ident = experiment.worker.fingerprint(candidate)
        receipt = {'status': 'FAIL_NATIVE', 'packet': {}, 'costs': {'native_calls': 1}}
        probe = {'record': 'candidate-record', 'evidence': 'candidate-event', 'receipt': receipt}
        rows = [{'id': ident, 'candidate': candidate}]
        real_search = experiment.search
        observed = {}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); output = root/'output'; metadata = root/'metadata.json'
            metadata.write_text(json.dumps({'selected': [
                {'repo': 'fixture/'+name, 'pr': 1, 'role': 'TRAINING', 'files': [
                    {'filename': 'subject.py'}, {'filename': 'tests/test_subject.py'}]}
                for name in ('training', 'future-one', 'future-two')]}))
            policy = root/'policy.json'; policy.write_text('{}')
            packages = root/'packages.json'; packages.write_text('[]')
            freeze = root/'freeze.json'; freeze.write_text('{}')
            limits = {'policy': {'path': str(policy)}, 'packages': {'path': str(packages)},
                'search_budget': 8, 'candidate_cap_per_file': 64, 'catalog_seconds': 45,
                'per_search_seconds': 1200, 'training_seconds': 1200,
                'training_unique_calls': 128, 'acquisition_native_calls': 128}
            objects = {'candidate-record': {'receipt': receipt}}
            machine = SimpleNamespace(state=output/'state', costs=[], log=[], flush=lambda: None)
            def put(value):
                key = experiment.worker.fingerprint(value); objects[key] = value; return key
            machine.put = put; machine.get = lambda key: objects[key]
            machine.append = lambda *args: 'fixture-event'
            def copy_state(destination):
                (destination/'state').mkdir(parents=True)
                (destination/'state/metatron-ledger.jsonl').write_bytes(b'')
            def search(*args, **kwargs):
                if args[6] == 'training-informed-ledger':
                    observed.update(kwargs)
                    machine.costs.append({'phase': 'generic_native_v2_independent_verification',
                                          'costs': {'native_calls': 128}})
                    return real_search(*args, **kwargs)
                args[5][ident] = probe
                return {'status': 'UNKNOWN_SEARCH', 'winner': None, 'attempts': [probe['record']],
                        'within_budget': True, 'budget': 8}
            setup = {'status': 'PREPARED', 'contract': {'repo_path': str(root/'fixture-source'),
                     'commit': 'a'*40}, 'authority': {}, 'policy': {}, 'source_boundaries': {}}
            baseline = {**probe, 'budget_eligibility': 'ELIGIBLE'}
            args = SimpleNamespace(repo=str(root), out=str(output), freeze=str(freeze),
                                   components=str(root/'components'), source_repos=str(root/'operators'))
            with patch.object(experiment, 'protocol', return_value=limits), \
                    patch.object(experiment, 'METADATA', metadata), \
                    patch.object(experiment, 'check_freeze', return_value={'source_commit': 'a'*40}), \
                    patch.object(experiment, 'copy_state', side_effect=copy_state), \
                    patch.object(experiment, 'Machine', return_value=machine), \
                    patch.object(experiment, 'provision', return_value=setup), \
                    patch.object(experiment.worker, 'collect', return_value={}), \
                    patch.object(experiment.worker, 'validate_certificate', return_value={}), \
                    patch.object(experiment, 'NativeRuntimeV2', return_value=SimpleNamespace(source='source', authority='authority')), \
                    patch.object(experiment, 'budgeted_native_probe', return_value=baseline), \
                    patch.object(experiment, 'bounded_catalog', return_value=rows), \
                    patch.object(experiment, 'orders', return_value={'COLD_V104_ORDER': [ident]}), \
                    patch.object(experiment, 'search', side_effect=search), \
                    patch.object(experiment, 'native_probe', return_value=probe) as execute, \
                    patch.object(experiment, 'choose_meta_decision', return_value={'status': 'UNKNOWN_CHOICE'}):
                result = experiment.qualify(args)
            self.assertIn('scope', observed)
            self.assertEqual(observed['deadline'], observed['scope']['acquisition_started_monotonic']+1200)
            self.assertEqual(result['conditions']['fully_informed_executable_ledger']['status'], 'UNKNOWN_SEARCH_BUDGET')
            execute.assert_not_called()

    def test_partial_independent_reexecution_costs_survive_missing_receipt(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            record = {'schema': 'UDM_NATIVE_PROFILE_RECORD_V2', 'contract': {}, 'candidate': {},
                'authority': {}, 'certificate': {}, 'policy': {}, 'receipt': {'status': 'FAIL_NATIVE'},
                'producer': {'source': 'source', 'authority': 'authority', 'dependencies': []}}
            descriptor = {key: key for key in ('contract', 'suite_authority', 'certificate', 'policy')}
            nodes = [SimpleNamespace(id='authority', kind='execution_authority_ceiling',
                        payload=experiment.AUTHORITY, premises=()),
                     SimpleNamespace(id='source', kind='generic_native_source',
                        payload={'source': descriptor}, premises=('authority',)),
                     SimpleNamespace(id='event', kind='native_frontier_v2_probe',
                        payload={'record': experiment.worker.fingerprint(record)}, premises=('source', 'authority'))]
            live = {node.id for node in nodes}
            machine = SimpleNamespace(log=nodes, mt=SimpleNamespace(live_ids=lambda _: live),
                flash_live_ids=lambda: live, get=lambda _: {}, state=Path(folder)/'state', costs=[])
            def partial(*args, **kwargs):
                output = kwargs['output_dir']/'execution'; output.mkdir(parents=True)
                (output/'checked-report.json').write_text(json.dumps({'costs': {
                    'native_calls': 1, 'collection_calls': 0, 'seconds': 0.01, 'horizon_seconds': 7}}))
                raise ValueError('retained partial native execution')
            with patch.object(experiment.worker, 'validate_receipt', side_effect=partial):
                with self.assertRaisesRegex(ValueError, 'partial native execution'):
                    experiment.checked_record(record, machine)
            self.assertEqual(len(machine.costs), 1)
            self.assertEqual(machine.costs[0]['costs']['native_calls'], 1)

    def test_partial_probe_costs_are_counted_once_without_final_receipt(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder); (output/'execution').mkdir()
            (output/'execution/checked-report.json').write_text(json.dumps({'costs': {
                'native_calls': 1, 'collection_calls': 0, 'seconds': 0.01, 'horizon_seconds': 7}}))
            machine = SimpleNamespace(costs=[], put=lambda _: 'record',
                                      append=lambda *args: 'event', flush=lambda: None)
            def partial(_):
                machine.costs.append({'phase': 'generic_native_v2_independent_verification',
                                      'output': str(output), 'costs': {}})
                raise ValueError('retained partial native execution')
            runtime = SimpleNamespace(_live=lambda *args: None, _verify=partial,
                source='source', authority='authority', contract={}, suite_authority={}, certificate={}, policy={})
            result = experiment.native_probe(machine, runtime, {}, 'fixture')
            self.assertEqual(result['receipt']['costs']['native_calls'], 1)
            self.assertEqual(sum(row.get('costs', {}).get('native_calls', 0) for row in machine.costs
                if row['phase'] == 'generic_native_v2_independent_verification'), 1)

    def test_final_save_recovers_partial_execution_cost_without_overwriting_counted_cost(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); output = root/'output'; metadata = root/'metadata.json'
            metadata.write_text(json.dumps({'selected': [
                {'repo': 'fixture/'+name, 'pr': 1, 'role': 'TRAINING', 'files': []}
                for name in ('training', 'future-one', 'future-two')]}))
            policy = root/'policy.json'; policy.write_text('{}')
            packages = root/'packages.json'; packages.write_text('[]')
            freeze = root/'freeze.json'; freeze.write_text('{}')
            limits = {'policy': {'path': str(policy)}, 'packages': {'path': str(packages)},
                      'training_seconds': 1200, 'acquisition_native_calls': 128}
            machine = SimpleNamespace(state=output/'state', costs=[], log=[])
            def copy_state(destination):
                (destination/'state').mkdir(parents=True)
                (destination/'state/metatron-ledger.jsonl').write_bytes(b'')
            def interrupted(*args):
                for name, reported, retained in (('partial', 1, {}), ('counted', 9, {'native_calls': 7})):
                    run = output/name; (run/'execution').mkdir(parents=True)
                    (run/'execution/checked-report.json').write_text(json.dumps({'costs': {'native_calls': reported}}))
                    machine.costs.append({'phase': 'generic_native_v2_independent_verification',
                                          'output': str(run), 'costs': retained})
                raise ValueError('interrupted direct native run')
            args = SimpleNamespace(repo=str(root), out=str(output), freeze=str(freeze),
                                   components=str(root/'components'))
            with patch.object(experiment, 'protocol', return_value=limits), \
                    patch.object(experiment, 'METADATA', metadata), \
                    patch.object(experiment, 'check_freeze', return_value={'source_commit': 'a'*40}), \
                    patch.object(experiment, 'copy_state', side_effect=copy_state), \
                    patch.object(experiment, 'Machine', return_value=machine), \
                    patch.object(experiment, 'provision', return_value={'status': 'PREPARED', 'contract': {}, 'authority': {}}), \
                    patch.object(experiment.worker, 'collect', return_value={}), \
                    patch.object(experiment.worker, 'validate_certificate', return_value={}), \
                    patch.object(experiment, 'NativeRuntimeV2'), \
                    patch.object(experiment, 'budgeted_native_probe', side_effect=interrupted):
                result = experiment.qualify(args)
            self.assertEqual(result['status'], 'UNKNOWN_NO_NATIVE_ACQUISITION_RESIDUAL')
            self.assertEqual([row['costs']['native_calls'] for row in result['machine_costs']], [1, 7])
            self.assertEqual(json.loads((output/'RESULT.json').read_text())['machine_costs'], machine.costs)


if __name__ == '__main__':
    unittest.main()
