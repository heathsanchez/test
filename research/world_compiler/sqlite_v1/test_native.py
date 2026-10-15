"""Negative controls beyond the protected native SQLite qualification."""
import json
import sqlite3
import unittest

from engine import (
    DEV, world, passive, candidate_probes, observe, discover_probe,
    discover_intervention, compile_method, apply_capability,
    qualify_capability, future_schema, fully_informed_baseline
)


class NativeSQLiteControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe, _ = discover_probe(DEV)
        cls.selection = discover_intervention(DEV, cls.probe)
        cls.method = compile_method(cls.probe, cls.selection['program'])

    def test_native_nonempty_modes_and_nonmutation(self):
        a, b = world(DEV, False), world(DEV, True)
        try:
            before = passive(a)
            self.assertEqual(before, passive(b))
            self.assertFalse(observe(a, self.probe))
            self.assertTrue(observe(b, self.probe))
            self.assertEqual(before, passive(a))
            self.assertEqual(before, passive(b))
        finally:
            a.close()
            b.close()

    def test_unique_winning_intervention(self):
        self.assertEqual(self.selection['valid_programs'], ['PRAGMA foreign_keys=ON'])
        self.assertEqual(self.selection['actual_tested'], self.selection['candidate_count'])

    def test_no_foreign_key_is_unknown(self):
        db = sqlite3.connect(':memory:', isolation_level=None)
        try:
            db.execute('CREATE TABLE no_fk(id INTEGER PRIMARY KEY)')
            self.assertEqual(candidate_probes(db), [])
            self.assertEqual(apply_capability(db, self.method)['status'], 'UNKNOWN_INTERFACE_NOT_UNIQUE')
        finally:
            db.close()

    def test_no_transactional_migration(self):
        db = world(DEV, False)
        try:
            db.execute('BEGIN')
            result = apply_capability(db, self.method)
            self.assertEqual(result, {'status': 'UNKNOWN_ACTIVE_TRANSACTION', 'changes': 0})
            db.execute('ROLLBACK')
            self.assertEqual(apply_capability(db, self.method)['status'], 'VERIFIED_NATIVE_INTERVENTION')
        finally:
            db.close()

    def test_invalid_manifest_source_and_hash(self):
        altered = json.loads(json.dumps(self.method))
        altered['intervention'] = 'PRAGMA query_only=ON'
        with self.assertRaises(PermissionError):
            qualify_capability(altered)
        altered = json.loads(json.dumps(self.method))
        altered['runtime']['sqlite_version'] = '0.0.0'
        with self.assertRaises(PermissionError):
            qualify_capability(altered)

    def test_guard_never_changes_already_safe_mode(self):
        db = world(DEV, True)
        try:
            self.assertEqual(
                apply_capability(db, self.method),
                {'status': 'VERIFIED_ALREADY_SAFE', 'changes': 0}
            )
        finally:
            db.close()

    def test_text_parent_key_future(self):
        schema = future_schema('test-text-key', 1)
        db = world(schema, False)
        try:
            self.assertEqual(apply_capability(db, self.method)['status'], 'VERIFIED_NATIVE_INTERVENTION')
        finally:
            db.close()

    def test_real_baseline_executes(self):
        result = fully_informed_baseline('unit-test')
        self.assertEqual(
            (result['native_successes'], result['direct_observation_reads'],
             result['configuration_changes']), (24, 24, 12)
        )


if __name__ == '__main__':
    unittest.main()
