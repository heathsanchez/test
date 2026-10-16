"""Pre-fix source-free controls for durable, single-frontier curation paths."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .test_frontier_v4_preparation_tools import load, RECORDS


class FrontierV4CurationLineage(unittest.TestCase):
    def setUp(self):
        self.curator = load('_curator_lineage_fixture', RECORDS/'curate_frontier.py')

    def test_a_fresh_output_directory_cannot_start_a_replacement_query_round(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); canonical = root/'records'; canonical.mkdir()
            (canonical/'PREQUERY.json').write_text('{}')
            with patch.object(self.curator, 'RECORDS', canonical, create=True), \
                    patch.object(self.curator.subprocess, 'check_output', return_value=b''):
                with self.assertRaisesRegex(ValueError, 'canonical.*(query|prequery)'):
                    self.curator.query(root/'research/runtime', canonical/'PREQUERY.json',
                                       root/'gate.json', root/'artifact.zip', root/'replacement')

    def test_a_new_process_cannot_replay_a_retained_query_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            records = Path(folder); (records/'PREQUERY_EXECUTION.json').write_text('{}')
            (records/'PREQUERY.json').write_text('{}')
            with patch.object(self.curator, 'RECORDS', records, create=True), \
                    patch.object(self.curator.subprocess, 'check_output', return_value=b''):
                with self.assertRaisesRegex(ValueError, 'prior.*query|query.*retained'):
                    self.curator.query(records/'research/runtime', records/'PREQUERY.json',
                                       records/'gate.json', records/'artifact.zip', records)

    def test_a_replacement_universe_filename_is_rejected_before_its_contents(self):
        q = self.curator.q
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); gate = root/'gate.json'; archive = root/'artifact.zip'
            archive.write_bytes(b'fixture archive')
            authority = {'artifact_sha256': self.curator.sha256(archive.read_bytes())}
            gate.write_text(json.dumps({'environment_gate': authority, 'catalog': {}}))
            universe = root/'replacement-universe.json'
            universe.write_text(json.dumps({'schema': 'UDM_NATIVE_AUTHORITY_V4_DECLARED_UNIVERSE_V1',
                'environment_gate': authority, 'repositories': ['fixture/fresh']}))
            with patch.object(self.curator, 'RECORDS', root, create=True), \
                    patch.object(q, 'require_environment_gate', return_value=authority):
                with self.assertRaisesRegex(ValueError, 'canonical declared universe'):
                    self.curator.configure_universe(universe, gate, archive)


if __name__ == '__main__':
    unittest.main()
