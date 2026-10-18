"""Pre-query source-free acceptance for v4 curator and record wrappers."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import qualify_native_frontier_v4 as q

RECORDS = Path(__file__).parent/'archaeology/native-authority-v4'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FrontierV4PreparationTools(unittest.TestCase):
    def test_record_assembly_uses_v4_without_changing_original_helper(self):
        path = RECORDS/'prepare_records.py'
        self.assertTrue(path.is_file(), 'new versioned local-only record wrapper required')
        wrapper = load('_acceptance_v4_record_wrapper', path)
        self.assertIs(wrapper.q, q)
        for name in ('prepare', 'requests', 'finalize'):
            function = getattr(wrapper, name)
            self.assertIs(function.__code__, getattr(wrapper._original, name).__code__)
            self.assertIs(function.__globals__['q'], q)
            self.assertIsNot(wrapper._original.q, q)

    def test_curator_has_no_universe_before_a_qualified_v4_gate(self):
        path = RECORDS/'curate_frontier.py'
        self.assertTrue(path.is_file(), 'new gate-bound metadata curator wrapper required')
        wrapper = load('_acceptance_v4_curator_empty', path)
        self.assertEqual(wrapper.UNIVERSE, ())
        with self.assertRaisesRegex(ValueError, 'qualified|universe'):
            wrapper.plan(q.HERE)
        with tempfile.TemporaryDirectory() as folder:
            gate = Path(folder)/'gate.json'; gate.write_text('{}')
            with patch.object(q, 'require_environment_gate', side_effect=ValueError('unqualified fixture')):
                with self.assertRaisesRegex(ValueError, 'unqualified fixture'):
                    wrapper.configure_universe(Path(folder)/'unread-universe.json', gate,
                                               Path(folder)/'unread-archive.zip')

    def test_curator_excludes_all_previous_v3_universe_members(self):
        path = RECORDS/'curate_frontier.py'
        self.assertTrue(path.is_file(), 'new metadata curator wrapper required')
        wrapper = load('_acceptance_v4_curator_exclusions', path)
        excluded, inputs = wrapper.exclusions(q.HERE, wrapper.original(q.HERE))
        prior = json.loads((q.HERE/'archaeology/native-environment-v3/PREQUERY.json').read_text())
        self.assertTrue(set(prior['repository_universe_fixed_before_github_queries']) <= set(excluded))
        self.assertTrue(all(row.get('status') != 'MISSING' for row in inputs))

    def test_curator_query_imports_v4_gate_before_any_metadata_query(self):
        path = RECORDS/'curate_frontier.py'
        self.assertTrue(path.is_file(), 'new metadata curator wrapper required')
        wrapper = load('_acceptance_v4_curator_gate', path)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); plan = root/'PREQUERY.json'; plan.write_text('{}')
            archive = root/'artifact.zip'; archive.write_bytes(b'synthetic archive')
            gate = root/'gate.json'
            gate.write_text(json.dumps({'environment_gate': {
                'artifact_sha256': wrapper.sha256(archive.read_bytes())}, 'catalog': {}}))
            committed = {'path': 'fixture', 'sha256': wrapper._LOADED_SHA256, 'source_commit': 'a'*40}
            with patch.object(wrapper, 'plan', return_value={}), \
                    patch.object(wrapper, 'RECORDS', root), \
                    patch.object(wrapper, 'committed', return_value=committed), \
                    patch.object(wrapper.subprocess, 'check_output', return_value=b''), \
                    patch.object(q, 'require_environment_gate', side_effect=ValueError('v4 gate sentinel')):
                with self.assertRaisesRegex(ValueError, 'v4 gate sentinel'):
                    wrapper.query(root/'research/unified_consequence_runtime', plan, gate, archive, root)


if __name__ == '__main__':
    unittest.main()
