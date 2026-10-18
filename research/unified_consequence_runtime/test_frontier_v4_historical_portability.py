"""Separate pre-fix controls for the CI historical-repository input gap.

The original untracked history file is never removed or changed by these tests.
Only its absence is simulated; no fresh metadata or native calls are made.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from .test_frontier_v4_preparation_tools import load, RECORDS

OLD_PATH = 'archaeology/programme-closure/REPOSITORIES.json'
NEW_PATH = 'archaeology/native-authority-v4/HISTORICAL_REPOSITORIES.json'


class FrontierV4HistoricalPortability(unittest.TestCase):
    def setUp(self):
        self.curator = load('_v4_historical_portability', RECORDS/'curate_frontier.py')
        self.research = self.curator.q.HERE
        self.old = self.curator.original(self.research)
        prior = json.loads((self.research/'archaeology/native-environment-v3/PREQUERY.json').read_text())
        self.frozen = next(row for row in prior['historical_metadata_inputs'] if row['path'] == OLD_PATH)

    def test_missing_untracked_original_keeps_complete_frozen_history(self):
        original = self.research/OLD_PATH
        real_exists = Path.exists
        before = tuple(self.old.HISTORICAL_METADATA)
        with patch.object(Path, 'exists', lambda path: False if path == original else real_exists(path)):
            excluded, inputs = self.curator.exclusions(self.research, self.old)
        self.assertTrue(all(row.get('status') != 'MISSING' for row in inputs),
                        'CI must retain historical authority when the old untracked file is absent')
        retained = next(row for row in inputs if row['path'] == NEW_PATH)
        self.assertEqual(retained['sha256'], self.frozen['sha256'])
        self.assertEqual(retained['repositories'], self.frozen['repositories'])
        self.assertTrue({name.lower() for name in self.frozen['repositories']} <= set(excluded))
        self.assertEqual(tuple(self.old.HISTORICAL_METADATA), before)

    def test_changed_versioned_copy_cannot_silently_replace_frozen_history(self):
        target = self.research/NEW_PATH
        real_read = Path.read_bytes
        with patch.object(Path, 'read_bytes', lambda path: b'changed historical authority' if path == target
                          else real_read(path)):
            with self.assertRaisesRegex(ValueError, 'historical.*(authority|bytes|hash)|frozen.*histor'):
                self.curator.exclusions(self.research, self.old)

    def test_other_missing_history_inputs_remain_explicit(self):
        missing = self.research/'native_policy.json'
        real_exists = Path.exists
        with patch.object(Path, 'exists', lambda path: False if path == missing else real_exists(path)):
            _, inputs = self.curator.exclusions(self.research, self.old)
        row = next(row for row in inputs if row['path'] == 'native_policy.json')
        self.assertEqual(row['status'], 'MISSING')


if __name__ == '__main__':
    unittest.main()
