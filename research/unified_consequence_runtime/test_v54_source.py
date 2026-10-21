"""Integrity and boundary tests; these do not substitute for native V54 qualification."""
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from research.unified_consequence_runtime.v54_source import (
    OriginalV54, PinnedProgram, SOURCE_COMMIT, SOURCE_PATH, SOURCE_SHA256,
    WORLD_PINS,
)

SOURCE_REPO = Path(os.environ.get('V54_SOURCE','/workspace/repos/triskelion'))
WORLDS = {name: Path(os.environ.get('V54_WORLDS','/workspace/v54-worlds')) / name for name in WORLD_PINS}


class OriginalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = subprocess.run(
            ['git', '-C', str(SOURCE_REPO), 'show', f'{SOURCE_COMMIT}:{SOURCE_PATH}'],
            capture_output=True, check=True, timeout=20,
        ).stdout

    def test_pinned_bytes_and_exact_ast_segments(self):
        program = PinnedProgram(self.source)
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), SOURCE_SHA256)
        original = ast.parse(self.source)
        for name, item in program.segments.items():
            selected = [node for node in original.body
                        if item['start_line'] <= node.lineno <= item['end_line']]
            self.assertEqual(ast.dump(program.module(name)),
                             ast.dump(ast.Module(body=selected, type_ignores=[])))
            exact = b''.join(self.source.splitlines(keepends=True)[
                item['start_line'] - 1:item['end_line']])
            self.assertEqual(item['sha256'], hashlib.sha256(exact).hexdigest())
        self.assertNotIn('O1', program.bootstrap_names())
        self.assertNotIn('cold_survivors', program.bootstrap_names())

    def test_changed_source_cannot_be_loaded(self):
        with self.assertRaisesRegex(ValueError, 'source SHA256'):
            PinnedProgram(self.source.replace(b"'TOKEN_REWRITE'", b"'FAKE_REWRITE'", 1))

    def test_native_helpers_keep_original_source_locations(self):
        program = PinnedProgram(self.source)
        namespace = {}
        program.execute('imports', namespace)
        program.execute('substrate', namespace)
        self.assertEqual(namespace['sh'].__code__.co_firstlineno, 15)
        self.assertEqual(namespace['emission_survivors'].__code__.co_firstlineno, 73)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'example.py'
            path.write_text('if size < bound or enabled:\n    pass\n')
            site = namespace['sites'](path, '<')[0]
            namespace['mutate'](path, site, '<=')
            live_or = namespace['sites'](path, 'or')[0]
            self.assertEqual(live_or[1], 17)
            namespace['mutate'](path, live_or, 'and')
            self.assertEqual(path.read_text(), 'if size <= bound and enabled:\n    pass\n')


class AdapterBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / 'out'

    def test_wrong_world_pin_fails_before_any_native_test(self):
        wrong = dict(WORLDS, requests=SOURCE_REPO)
        with self.assertRaisesRegex(ValueError, 'requests.*pin'):
            OriginalV54(SOURCE_REPO, wrong, self.out)

    def test_missing_worlds_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'world paths'):
            OriginalV54(SOURCE_REPO, {'requests': WORLDS['requests']}, self.out)

    def make_adapter(self):
        if not all((path / '.git').exists() for path in WORLDS.values()):
            self.skipTest('pinned native worlds are not provisioned')
        return OriginalV54(SOURCE_REPO, WORLDS, self.out)

    def test_process_observation_distinguishes_failure_and_timeout(self):
        adapter = self.make_adapter()
        failed, _ = adapter.env['sh']('exit 7', WORLDS['requests'], 1)
        self.assertFalse(failed)
        self.assertEqual(adapter.native_calls[-1]['status'], 'native_failure')
        self.assertEqual(adapter.native_calls[-1]['returncode'], 7)
        timed, output = adapter.env['sh']('sleep 5', WORLDS['requests'], 0.05)
        self.assertFalse(timed)
        self.assertIn('TIMEOUT', output)
        self.assertEqual(adapter.native_calls[-1]['status'], 'timeout')
        self.assertIn('src/requests/utils.py', adapter.native_calls[-1]['candidate_source_sha256'])

    def test_wrong_scope_rejects_before_mutating_unit_fixture(self):
        adapter = self.make_adapter()
        # A unit fixture for the authorization guard, never a native scientific outcome.
        path = Path(self.temp.name) / 'fixture.py'
        path.write_text('if size < bound or enabled:\n    pass\n')
        operator = {'kind': 'TOKEN_REWRITE', 'src': '<', 'dst': '<='}
        adapter.env.update(O1=operator, rq_path=path, line_no=1, scope_word='if')
        adapter._target_prepared = True
        before = path.read_bytes()
        with self.assertRaisesRegex(PermissionError, 'task scope'):
            adapter.apply_operator(operator, dict(adapter.target_scope(), first_word='while'))
        path.write_text('while size < bound or enabled:\n    pass\n')
        with self.assertRaisesRegex(PermissionError, 'first-word scope'):
            adapter.apply_operator(operator)
        self.assertNotEqual(before, path.read_bytes())
        self.assertEqual(path.read_text(), 'while size < bound or enabled:\n    pass\n')
        self.assertEqual(adapter.native_calls, [])

    def test_import_performs_no_acquisition_and_scope_rejects_unlearned(self):
        if not all((path / '.git').exists() for path in WORLDS.values()):
            self.skipTest('pinned native worlds are not provisioned')
        adapter = OriginalV54(SOURCE_REPO, WORLDS, self.out)
        self.assertEqual(adapter.native_calls, [])
        self.assertNotIn('O1', adapter.env)
        self.assertNotIn('rq_path', adapter.env)
        with self.assertRaisesRegex(RuntimeError, 'prepare_target'):
            adapter.target_scope()
        with self.assertRaisesRegex(PermissionError, 'acquired'):
            adapter.apply_operator({'kind': 'TOKEN_REWRITE', 'src': '<', 'dst': '<='})
        with self.assertRaisesRegex(RuntimeError, 'acquire_o1'):
            adapter.prepare_target()
        self.assertEqual(adapter.native_calls, [])


if __name__ == '__main__':
    unittest.main()
