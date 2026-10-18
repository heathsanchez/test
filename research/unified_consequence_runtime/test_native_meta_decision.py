"""Real Metatron/FLASH policy bookkeeping contracts; numeric receipts are fixtures.

These tests establish no new source-native scientific consequence.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research.unified_consequence_runtime.developmental_machine import Machine
try:
    from research.unified_consequence_runtime import native_meta_decision as meta
except ImportError:
    meta = None


def fixture_check(machine, candidates, futures, evidence_ids):
    """Fixture authority only: production qualification supplies a native checker."""
    nodes = {node.id: node for node in machine.log}
    rows = [machine.get(nodes[key].payload['receipt']) for key in evidence_ids]
    profiles = {candidate: {} for candidate in candidates}
    scope = rows[0]['scope']
    for row in rows:
        if 'packet' in row:
            packet = machine.get(row['packet'])
            raw = Path(packet['raw_path']).read_bytes()
            if meta.digest(raw) != packet['raw_sha256']:
                raise ValueError('fixture raw native packet digest mismatch')
        if row['scope'] != scope:
            raise ValueError('receipt scope disagreement')
        profiles[row['candidate']][row['future']] = row['metrics']
    return {'schema': meta.EVIDENCE_SCHEMA, 'profiles': profiles,
            'evidence_ids': list(evidence_ids), 'scope': scope}


class NativeMetaDecisionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(meta, 'native meta-decision implementation missing')
        self.folder = tempfile.TemporaryDirectory(prefix='udm-meta-policy-test-')
        self.addCleanup(self.folder.cleanup)
        self.state = Path(self.folder.name)/'state'
        self.components = Path(os.environ.get('UDM_COMPONENTS', '/workspace/components'))
        self.machine = Machine(self.components, self.state, Path(self.folder.name)/'eval', Path(self.folder.name)/'config')
        self.candidates, self.futures = ('RAW', 'WHEEL'), ('source-A', 'source-B')
        self.profiles = {'RAW': {'source-A': [1, 1], 'source-B': [1, 1]},
                         'WHEEL': {'source-A': [0, 1], 'source-B': [0, 1]}}
        self.scope = {'protocol_binding': 'a'*64, 'candidate_catalog_sha256': 'b'*64,
                      'source_binding': 'c'*64, 'budget': 1}
        self.ids = []
        for candidate in self.candidates:
            for future in self.futures:
                receipt = {'candidate': candidate, 'future': future,
                           'metrics': self.profiles[candidate][future], 'scope': self.scope,
                           'fixture_only': True}
                self.ids.append(self.machine.append('fixture_native_profile', {'receipt': self.machine.put(receipt)}))
        self.machine.flush()
        self.ids = tuple(self.ids)

    def choose(self, **overrides):
        values = {'candidates': self.candidates, 'futures': self.futures,
                  'profiles': self.profiles, 'evidence_ids': self.ids,
                  'independent_check': fixture_check}
        values.update(overrides)
        return meta.choose_meta_decision(self.machine, **values)

    def invoke(self, policy_id, machine=None, **overrides):
        args = {'protocol_binding': self.scope['protocol_binding'],
                'candidate_catalog_sha256': self.scope['candidate_catalog_sha256']}
        args.update(overrides)
        return meta.invoke_meta_policy(machine or self.machine, policy_id, **args)

    def test_unique_verified_consequence_compiles_policy_via_original_mda(self):
        result = self.choose()
        self.assertEqual(result['status'], 'WARRANTED_BOUNDED_POLICY_SELECTION')
        self.assertEqual(self.invoke(result['policy_id']), 'WHEEL')
        self.assertEqual(result['mda']['verdict'], 'verified')
        self.assertFalse(result['grammar_extension_licensed'])
        self.assertEqual(result['candidates'], list(self.candidates))
        self.assertEqual(set(self.machine.mt.live_ids(self.machine.log)), self.machine.flash_live_ids())

    def test_existing_same_scope_policy_is_activated_without_duplicate_admission(self):
        first = self.choose()
        second = self.choose()
        self.assertEqual(second['status'], 'WARRANTED_BOUNDED_POLICY_SELECTION')
        self.assertEqual(second['policy_id'], first['policy_id'])
        self.assertEqual(second['transition'], 'ACTIVATION')
        self.assertEqual(sum(node.kind == meta.POLICY_KIND for node in self.machine.log), 1)

    def test_supplied_numbers_cannot_override_independently_reconstructed_receipts(self):
        forged = copy.deepcopy(self.profiles)
        forged['WHEEL']['source-A'] = [0, 0]
        result = self.choose(profiles=forged)
        self.assertEqual(result['status'], 'UNKNOWN_EVIDENCE')
        self.assertIsNone(result['policy_id'])
        self.assertEqual(self.machine.costs[-1]['phase'], 'native_meta_decision')
        self.assertGreaterEqual(self.machine.costs[-1]['seconds'], 0)

    def test_checker_must_be_top_level_importable_not_closure_or_lambda(self):
        def closure(*args):
            return fixture_check(*args)
        for checker in (closure, lambda *args: fixture_check(*args)):
            with self.subTest(checker=checker):
                self.assertEqual(self.choose(independent_check=checker)['status'], 'UNKNOWN_EVIDENCE')

    def test_offline_checker_replays_nested_packet_and_raw_digest_on_invocation(self):
        nodes = {node.id:node for node in self.machine.log}
        raw_path = Path(self.folder.name)/'native-raw.log'
        raw_path.write_bytes(b'fixture native evidence, not a scientific result')
        packet_id = self.machine.put({'raw_path':str(raw_path),'raw_sha256':meta.digest(raw_path.read_bytes())})
        ids = []
        for old in self.ids:
            row = self.machine.get(nodes[old].payload['receipt'])
            row['packet'] = packet_id
            row['scope']['receipt_objects'] = []  # Deliberately incomplete: checker must traverse.
            ids.append(self.machine.append('fixture_native_profile',{'receipt':self.machine.put(row)}))
        self.machine.flush()
        result = self.choose(evidence_ids=tuple(ids))
        self.assertEqual(self.invoke(result['policy_id']), 'WHEEL')
        packet_path = self.machine.state/'objects'/packet_id
        packet_bytes = packet_path.read_bytes()
        packet_path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.invoke(result['policy_id'])
        packet_path.write_bytes(packet_bytes)
        raw_path.write_bytes(b'changed raw native packet')
        with self.assertRaisesRegex(ValueError,'packet digest'):
            self.invoke(result['policy_id'])

    def test_boolean_checker_is_not_independent_profile_authority(self):
        result = self.choose(independent_check=lambda *args: True)
        self.assertEqual(result['status'], 'UNKNOWN_EVIDENCE')

    def test_equivalent_successful_candidates_preserve_unknown_choice(self):
        candidates = self.candidates + ('ALTERNATIVE',)
        profiles = copy.deepcopy(self.profiles)
        profiles['ALTERNATIVE'] = copy.deepcopy(profiles['WHEEL'])
        ids = list(self.ids)
        for future in self.futures:
            raw = {'candidate': 'ALTERNATIVE', 'future': future,
                   'metrics': profiles['ALTERNATIVE'][future], 'scope': self.scope}
            ids.append(self.machine.append('fixture_native_profile', {'receipt': self.machine.put(raw)}))
        self.machine.flush()
        result = self.choose(candidates=candidates, profiles=profiles, evidence_ids=tuple(ids))
        self.assertEqual(result['status'], 'UNKNOWN_CHOICE')
        self.assertIsNone(result['policy_id'])
        self.assertEqual(result['candidates'], list(candidates))

    def test_missing_receipt_or_replayed_scope_is_unknown(self):
        self.assertEqual(self.choose(evidence_ids=self.ids[:-1])['status'], 'UNKNOWN_EVIDENCE')
        self.assertEqual(self.choose(evidence_ids=self.ids+('f'*64,))['status'], 'UNKNOWN_EVIDENCE')

    def test_exact_ancestor_revocation_blocks_invocation_independent_survives(self):
        result = self.choose()
        independent = self.machine.append('fixture_unrelated', {'independent': True})
        self.machine.flush()
        self.machine.append('revoke', {'target': self.ids[0], 'reason': 'exact causal ancestor test'})
        self.machine.flush()
        with self.assertRaises(PermissionError):
            self.invoke(result['policy_id'])
        self.assertIn(independent, self.machine.mt.live_ids(self.machine.log))
        self.assertNotIn(result['policy_id'], self.machine.flash_live_ids())

    def test_wrong_protocol_and_missing_or_corrupted_program_are_refused(self):
        result = self.choose()
        with self.assertRaises(ValueError):
            self.invoke(result['policy_id'], protocol_binding='d'*64)
        node = next(node for node in self.machine.log if node.id == result['policy_id'])
        path = self.machine.state/'objects'/node.payload['program']
        raw = path.read_bytes()
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.invoke(result['policy_id'])
        path.write_text('{"forged":true}')
        with self.assertRaises(ValueError):
            self.invoke(result['policy_id'])
        path.write_bytes(raw)
        self.assertEqual(self.invoke(result['policy_id']), 'WHEEL')

    def test_profile_authority_ancestors_cannot_be_substituted_by_unrelated_support(self):
        from dataclasses import asdict
        from research.unified_consequence_runtime.consequence_selection import native_selectors
        result = self.choose()
        old = next(node for node in self.machine.log if node.id == result['policy_id'])
        unrelated = self.machine.append('fixture_unrelated', {'unrelated': 'cannot support native profiles'})
        program = self.machine.get(old.payload['program'])
        program['evidence_ids'] = [unrelated]
        program_id = self.machine.put(program)
        forged = copy.deepcopy(old.payload)
        forged['program'] = program_id
        mda = native_selectors()['mda']
        repair = mda.Repair('policy', 'native-existing-operation-policy', program_id, meta.DOMAIN, (unrelated,))
        record = forged['mda_record']
        record['repair'] = asdict(repair)
        record['id'] = mda.admission_id(repair, record['evidence']['verifier'])
        record['evidence']['claim'] = repair.id
        record['evidence']['certificate']['program'] = program_id
        record['attachment']['program'] = program_id
        forged['event']['record'] = record
        key = self.machine.append(meta.POLICY_KIND, forged, (unrelated,))
        self.machine.flush()
        with self.assertRaises(ValueError):
            self.invoke(key)

    def test_forged_retained_msi_lineage_and_observation_basis_are_refused(self):
        result = self.choose()
        old = next(node for node in self.machine.log if node.id == result['policy_id'])
        for field, value in (('msi_lineage', self.machine.put({})), ('observation_basis', {})):
            forged = copy.deepcopy(old.payload)
            forged[field] = value
            key = self.machine.append(meta.POLICY_KIND, forged, old.premises)
            self.machine.flush()
            with self.assertRaises(ValueError):
                self.invoke(key)

    def test_missing_raw_independent_receipt_refuses_retained_policy_invocation(self):
        result = self.choose()
        first = next(node for node in self.machine.log if node.id == self.ids[0])
        (self.machine.state/'objects'/first.payload['receipt']).unlink()
        with self.assertRaises(FileNotFoundError):
            self.invoke(result['policy_id'])

    def test_forged_mda_admission_cannot_inherit_a_valid_policy_program(self):
        result = self.choose()
        old = next(node for node in self.machine.log if node.id == result['policy_id'])
        forged = copy.deepcopy(old.payload)
        forged['mda_record']['evidence']['verdict'] = 'unknown'
        key = self.machine.append(meta.POLICY_KIND, forged, old.premises)
        self.machine.flush()
        with self.assertRaises(ValueError):
            self.invoke(key)

    def test_unrelated_withdrawal_preserves_policy_and_fresh_restoration_changes_lineage(self):
        old = self.choose()
        unrelated = self.machine.append('fixture_unrelated', {'id': 'separate'})
        self.machine.flush()
        self.machine.append('revoke', {'target': unrelated, 'reason': 'unrelated'})
        self.machine.flush()
        self.assertEqual(self.invoke(old['policy_id']), 'WHEEL')
        self.machine.append('revoke', {'target': self.ids[0], 'reason': 'ancestor'})
        self.machine.flush()
        nodes = {node.id: node for node in self.machine.log}
        fresh = []
        for original in self.ids:
            receipt = self.machine.get(nodes[original].payload['receipt'])
            receipt['fresh_generation'] = 2
            fresh.append(self.machine.append('fixture_native_profile', {'receipt': self.machine.put(receipt)}))
        self.machine.flush()
        restored = self.choose(evidence_ids=tuple(fresh))
        self.assertNotEqual(restored['policy_id'], old['policy_id'])
        self.assertEqual(self.invoke(restored['policy_id']), 'WHEEL')
        with self.assertRaises(PermissionError):
            self.invoke(old['policy_id'])

    def test_separate_process_reloads_actual_ledger_policy(self):
        result = self.choose()
        script = '''import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine import Machine
from research.unified_consequence_runtime.native_meta_decision import invoke_meta_policy
m=Machine(*map(Path,sys.argv[1:5]))
print(json.dumps(invoke_meta_policy(m,sys.argv[5],protocol_binding=sys.argv[6],candidate_catalog_sha256=sys.argv[7])))
'''
        raw = subprocess.check_output([sys.executable, '-B', '-c', script, str(self.components), str(self.state),
            str(self.machine.evaluator), str(self.machine.config), result['policy_id'],
            self.scope['protocol_binding'], self.scope['candidate_catalog_sha256']], text=True)
        self.assertEqual(json.loads(raw), 'WHEEL')


if __name__ == '__main__':
    unittest.main()
