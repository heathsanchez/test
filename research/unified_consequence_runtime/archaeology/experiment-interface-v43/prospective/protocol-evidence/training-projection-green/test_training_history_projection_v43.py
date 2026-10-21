"""Source-free fixtures for the comparator's narrow training-only projection."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CODE = HERE / 'training_history_projection_v43.py'
BINDING = 'a' * 64
TRAINING = 'fixture/training-source'
FUTURE = 'fixture/sealed-future'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'
        self.run.mkdir()
        self.objects = self.run / 'state' / 'objects'
        self.objects.mkdir(parents=True)
        self.ledger = []
        self.arm = {'schema': 'UDM_CODING_AGENT_NATIVE_ARM_V43', 'protocol_binding': BINDING,
                    'contract': {'repository': FUTURE}, 'native_residual': {'status': 'FAIL_NATIVE'},
                    'common_acquisition_costs': [], 'released_at_unix': 100.0}
        self.metadata = {'selected': [{'repo': TRAINING, 'role': 'TRAINING'},
                                      {'repo': FUTURE, 'role': 'PROTECTED_FUTURE_1'}]}
        self.metadata_path = self.root / 'FRESH_TASK_METADATA.json'
        self.metadata_path.write_text(canonical(self.metadata))
        # These are prohibited inputs, even though they are adjacent to lawful state.
        (self.run / 'RESULT.json').write_text('{invalid hidden future result')
        (self.run / 'future-one').mkdir()
        (self.run / 'future-one' / 'SECRET.json').write_text('{invalid hidden source outcome')

    def load(self):
        self.assertTrue(CODE.is_file(), 'training-only projection helper is not implemented')
        spec = importlib.util.spec_from_file_location('training_history_projection_fixture', CODE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def put(self, value):
        raw = canonical(value).encode()
        key = digest(raw)
        (self.objects / key).write_bytes(raw)
        return key

    def event(self, kind, payload, premises=()):
        row = {'kind': kind, 'payload': payload, 'premises': list(premises)}
        # Metatron hashes ensure_ascii=False, unlike the CAS encoding.
        row['id'] = digest(json.dumps(row, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode())
        self.ledger.append(row)
        return row['id']

    def profile(self, name='LAW', *, binding=BINDING, repo=TRAINING, status='PASS_NATIVE', calls=2):
        candidate = {'replacements': [{'file': 'original.py', 'before': 'a', 'after': 'b'}]}
        candidate_id = digest(canonical(candidate).encode())
        contract = {'repository': repo, 'protocol_binding': binding, 'commit': 'b' * 40}
        record = {'schema': 'UDM_NATIVE_PROFILE_RECORD_V2', 'receipt': {
            'status': status, 'execution': {'process_exit_code': 0 if status == 'PASS_NATIVE' else 1},
            'junit': {'tests': 2, 'passed': 2 if status == 'PASS_NATIVE' else 1,
                      'failures': 0 if status == 'PASS_NATIVE' else 1, 'errors': 0, 'skipped': 0},
            'costs': {'native_calls': calls}}, 'contract': contract, 'candidate': candidate,
            'producer': {'source': 's', 'authority': 'v', 'dependencies': []}}
        record_key = self.put(record)
        probe = self.event('native_frontier_v2_probe', {'record': record_key, 'label': 'training'}, ('s', 'v'))
        baseline = self.put({'schema': 'UDM_NATIVE_PROFILE_RECORD_V2', 'contract': contract,
                             'candidate': {'replacements': []}, 'receipt': {'status': 'FAIL_NATIVE'}})
        context = {'contract': contract, 'catalog': [{'id': candidate_id, 'candidate': candidate}],
                   'orders': {name: [candidate_id]}, 'baseline_record': baseline,
                   'runtime_source': 's', 'runtime_authority': 'v'}
        context_key = self.put(context)
        scope = {'protocol_binding': binding, 'contexts': {repo: context_key}, 'budget': 8,
                 'receipt_objects': [context_key, baseline, record_key]}
        episode = {'attempts': [record_key], 'winner': candidate_id if status == 'PASS_NATIVE' else None,
                   'status': 'PASS_BOUNDED_SEARCH' if status == 'PASS_NATIVE' else 'UNKNOWN_SEARCH',
                   'within_budget': True, 'budget': 8}
        report = {'candidate': name, 'future': repo, 'scope': scope, 'order': [candidate_id],
                  'attempts': [record_key], 'episode': episode}
        report_key = self.put(report)
        event = self.event('native_frontier_v2_profile', {'report': report_key}, (probe,))
        return {'report': report, 'record': record, 'record_key': record_key, 'context_key': context_key,
                'report_key': report_key, 'event': event}

    def publish(self):
        arm_path = self.run / 'AGENT_ARM.json'
        arm_path.write_text(canonical(self.arm))
        descriptor = {'path': str(arm_path), 'sha256': digest(arm_path.read_bytes())}
        parent_path = self.run / 'AGENT_PARENT_RECEIPT.json'
        parent = {'schema': 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V43', 'arm': descriptor,
                  'freeze': {'path': str(self.root / 'FREEZE.json'), 'sha256': BINDING},
                  'released_at_unix': self.arm['released_at_unix']}
        parent_path.write_text(canonical(parent))
        authority = {'schema': 'UDM_NATIVE_CLI_AUTHORITY_V43', 'operation': 'agent',
                     'parent': {'path': str(parent_path), 'sha256': digest(parent_path.read_bytes())},
                     'freeze': parent['freeze']}
        authority_path = self.run / 'AGENT_AUTHORITY.json'
        authority_path.write_text(canonical(authority))
        ledger_path = self.run / 'state' / 'metatron-ledger.jsonl'
        ledger_path.write_text(''.join(canonical(row) + '\n' for row in self.ledger))
        return arm_path, authority_path

    def project(self):
        module = self.load()
        arm, authority = self.publish()
        return module.project(arm, authority, digest(authority.read_bytes()), self.metadata_path,
                              digest(self.metadata_path.read_bytes()))

    def test_recovers_exact_profiles_episodes_context_and_receipts(self):
        row = self.profile()
        result = self.project()
        self.assertEqual(result['profiles'], {'LAW': {TRAINING: [0, 2]}})
        self.assertEqual(result['episodes'], {'LAW': row['report']['episode']})
        self.assertEqual(result['native_records'][row['record_key']], row['record'])
        self.assertEqual(result['contexts'][TRAINING]['sha256'], row['context_key'])
        self.assertEqual(result['scope'], row['report']['scope'])
        self.assertNotIn(FUTURE, canonical(result))
        self.assertEqual(result['native_execution_performed'], False)

    def test_does_not_dereference_other_binding_or_future_attempts(self):
        self.profile()
        for binding, repo in [('c' * 64, TRAINING), (BINDING, FUTURE)]:
            report = {'scope': {'protocol_binding': binding}, 'future': repo,
                      'attempts': ['d' * 64], 'candidate': 'SEALED_MUST_NOT_DEREFERENCE'}
            self.event('native_frontier_v2_profile', {'report': self.put(report)})
        result = self.project()
        self.assertEqual(set(result['profiles']), {'LAW'})
        self.assertNotIn('d' * 64, canonical(result))

    def test_no_profiles_is_allowed_only_for_training_arm(self):
        self.arm['contract']['repository'] = TRAINING
        result = self.project()
        self.assertEqual(result['status'], 'TRAINING_BASELINE_ONLY_NO_PROFILE_CARRIER')
        self.assertEqual(result['baseline'], self.arm['native_residual'])
        self.assertEqual(result['profiles'], {})

    def test_missing_profiles_on_future_arm_refuses(self):
        with self.assertRaisesRegex(ValueError, 'future arm.*training'):
            self.project()

    def test_tampered_authority_pin_refuses(self):
        module = self.load()
        arm, authority = self.publish()
        with self.assertRaisesRegex(ValueError, 'authority'):
            module.project(arm, authority, '0' * 64, self.metadata_path,
                           digest(self.metadata_path.read_bytes()))

    def test_tampered_cas_refuses(self):
        row = self.profile()
        (self.objects / row['record_key']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'content-addressed'):
            self.project()

    def test_profile_from_wrong_candidate_order_refuses(self):
        row = self.profile()
        replacement = dict(row['report'], order=['e' * 64])
        self.ledger[-1]['payload']['report'] = self.put(replacement)
        self.ledger[-1].pop('id')
        self.ledger[-1]['id'] = digest(json.dumps(self.ledger[-1], sort_keys=True,
            separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())
        with self.assertRaisesRegex(ValueError, 'order'):
            self.project()

    def test_duplicate_profile_refuses(self):
        self.profile()
        self.event('native_frontier_v2_profile', dict(self.ledger[-1]['payload']), self.ledger[-1]['premises'])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.project()

    def test_unknown_receipt_is_preserved_without_promotion(self):
        self.profile(status='UNKNOWN_SOURCE', calls=1)
        result = self.project()
        self.assertEqual(result['profiles'], {'LAW': {TRAINING: [1, 1]}})
        self.assertEqual(result['profile_statuses']['LAW'], ['UNKNOWN_SOURCE'])
        self.assertEqual(result['scientific_verification'], 'NOT_PERFORMED_BY_PROJECTION')

    def test_boolean_native_cost_is_refused(self):
        self.profile(calls=True)
        with self.assertRaisesRegex(ValueError, 'native_calls'):
            self.project()

    def test_metadata_pin_prevents_training_identity_substitution(self):
        self.profile()
        module = self.load()
        arm, authority = self.publish()
        with self.assertRaisesRegex(ValueError, 'metadata'):
            module.project(arm, authority, digest(authority.read_bytes()), self.metadata_path, 'f' * 64)


if __name__ == '__main__':
    unittest.main()
