"""Qualification bookkeeping and resume-boundary checks, without native verdict stubs."""
import json
from pathlib import Path
import tempfile
import unittest

from research.unified_consequence_runtime.qualify_v54_machine import Journal, resume_session


class QualificationInfrastructureTests(unittest.TestCase):
    def test_journal_keeps_failed_stage_and_prior_completed_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = Journal(root)
            with journal.stage('completed'):
                journal.update('retained_evidence', {'source': 'actual-receipts-required'})
            with self.assertRaisesRegex(ValueError, 'controlled infrastructure failure'):
                with journal.stage('failed'):
                    raise ValueError('controlled infrastructure failure')
            checkpoint = json.loads((root / 'RESULT.json').read_text())
            rows = [json.loads(row) for row in (root / 'qualification-events.jsonl').read_text().splitlines()]
            self.assertEqual(checkpoint['stages']['completed']['status'], 'PASS')
            self.assertEqual(checkpoint['stages']['failed']['status'], 'FAILED')
            self.assertEqual(rows[0]['kind'], 'started')
            self.assertEqual(rows[-1]['kind'], 'stage_failed')
            with self.assertRaisesRegex(ValueError, 'journal already exists'):
                Journal(root)

    def test_resume_rejects_unbound_or_supplied_operator_before_running_worlds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / 'candidate.json'
            candidate.write_text(json.dumps({'operator': {'kind': 'TOKEN_REWRITE', 'src': 'x', 'dst': 'y'}}))
            with self.assertRaisesRegex(ValueError, 'provenance differs'):
                resume_session(root, root, root / 'native', candidate)
            self.assertFalse((root / 'native').exists())


if __name__ == '__main__':
    unittest.main()
