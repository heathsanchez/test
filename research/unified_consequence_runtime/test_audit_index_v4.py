"""Local index preservation utility tests; no task or native worker access."""
import base64
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


MODULE = 'research.unified_consequence_runtime.audit_index_v4'


class AuditIndexV4Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
                             'new index audit helper must exist')
        self.audit = importlib.import_module(MODULE)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'linked'
        self.repo.mkdir()
        self.common = self.root / 'common.git'
        self.gitdir = self.common / 'worktrees' / 'linked'
        self.other = self.common / 'worktrees' / 'other'
        self.gitdir.mkdir(parents=True)
        self.other.mkdir()
        (self.repo / '.git').write_text('gitdir: ' + str(self.gitdir) + '\n')
        (self.gitdir / 'commondir').write_text('../..\n')
        (self.gitdir / 'index').write_bytes(b'\x00before\xff')
        self.environ = {key: value for key, value in os.environ.items()
                        if key not in ('GIT_INDEX_FILE', 'GIT_DIR', 'GIT_WORK_TREE',
                                       'GIT_COMMON_DIR')}
        self.env_patch = patch.dict(os.environ, self.environ, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def indexes(self, snapshot):
        return {row['path']: row for row in snapshot['indexes']}

    def fake_git(self, body):
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        script = bin_dir / 'git'
        script.write_text('#!' + sys.executable + '\n' + body)
        script.chmod(0o755)
        os.environ['PATH'] = str(bin_dir) + os.pathsep + self.environ['PATH']

    def test_snapshot_hashes_all_linked_indexes_and_explicit_absence_without_git(self):
        with patch.object(subprocess, 'run', side_effect=AssertionError('no Git discovery')):
            snapshot = self.audit.snapshot_indexes(self.repo)
        rows = self.indexes(snapshot)
        self.assertEqual(set(rows), {str(self.common / 'index'),
                                    str(self.gitdir / 'index'), str(self.other / 'index')})
        self.assertEqual(rows[str(self.gitdir / 'index')], {
            'path': str(self.gitdir / 'index'), 'exists': True, 'size_bytes': 8,
            'sha256': hashlib.sha256(b'\x00before\xff').hexdigest()})
        self.assertEqual(rows[str(self.common / 'index')], {
            'path': str(self.common / 'index'), 'exists': False,
            'size_bytes': None, 'sha256': None})
        self.assertFalse(rows[str(self.other / 'index')]['exists'])

    def test_snapshot_includes_inherited_alternate_index(self):
        alternate = self.root / 'alternate-index'
        os.environ['GIT_INDEX_FILE'] = str(alternate)
        rows = self.indexes(self.audit.snapshot_indexes(self.repo))
        self.assertIn(str(alternate), rows)
        self.assertFalse(rows[str(alternate)]['exists'])

    def test_comparison_detects_same_size_change_creation_removal_and_new_worktree(self):
        before = self.audit.snapshot_indexes(self.repo)
        (self.gitdir / 'index').write_bytes(b'\x00change\xff')
        (self.other / 'index').write_bytes(b'new')
        new = self.common / 'worktrees' / 'new'
        new.mkdir()
        after = self.audit.snapshot_indexes(self.repo)
        changes = self.audit.compare_indexes(before, after)
        self.assertEqual({row['path'] for row in changes}, {
            str(self.gitdir / 'index'), str(self.other / 'index'), str(new / 'index')})
        self.assertEqual(self.audit.compare_indexes(before, before), [])
        (self.gitdir / 'index').unlink()
        removed = self.audit.snapshot_indexes(self.repo)
        changes = self.audit.compare_indexes(after, removed)
        self.assertEqual(changes[0]['before']['exists'], True)
        self.assertEqual(changes[0]['after']['exists'], False)

    def test_failed_git_read_retains_before_after_and_reports_change_without_restoring(self):
        index = self.gitdir / 'index'
        self.fake_git('import os, pathlib, sys\n'
                      'assert os.environ["GIT_OPTIONAL_LOCKS"] == "0"\n'
                      + 'pathlib.Path(' + repr(str(index)) + ').write_bytes(b"after")\n'
                      'sys.stdout.buffer.write(b"out\\x00")\n'
                      'sys.stderr.buffer.write(b"failure")\n'
                      'raise SystemExit(7)\n')
        os.environ['GIT_OPTIONAL_LOCKS'] = '1'
        result = self.audit.audit_git_read(self.repo, ['status', '--porcelain=v1'])
        self.assertEqual(result['returncode'], 7)
        self.assertEqual(base64.b64decode(result['stdout_base64']), b'out\x00')
        self.assertEqual(base64.b64decode(result['stderr_base64']), b'failure')
        self.assertFalse(result['indexes_unchanged'])
        self.assertEqual(len(result['index_changes']), 1)
        self.assertEqual(self.indexes(result['before'])[str(index)]['sha256'],
                         hashlib.sha256(b'\x00before\xff').hexdigest())
        self.assertEqual(self.indexes(result['after'])[str(index)]['sha256'],
                         hashlib.sha256(b'after').hexdigest())
        self.assertEqual(index.read_bytes(), b'after', 'audit must never restore an index')
        json.dumps(result, allow_nan=False)

    def test_missing_git_still_retains_interval_evidence(self):
        with patch.object(subprocess, 'run', side_effect=FileNotFoundError('git unavailable')):
            result = self.audit.audit_git_read(self.repo, ['status', '--porcelain=v1'])
        self.assertIsNone(result['returncode'])
        self.assertIn('git unavailable', result['error'])
        self.assertTrue(result['indexes_unchanged'])
        self.assertEqual(result['before'], result['after'])

    def test_mutating_commands_and_output_or_external_tool_flags_are_refused(self):
        commands = [['reset', '--hard'], ['update-index', '--refresh'], ['checkout', '.'],
                    ['worktree', 'remove', 'other'], ['diff', '--output=result'],
                    ['diff', '--ext-diff'], ['show', '--textconv', 'HEAD:x'],
                    ['cat-file', '--filters', 'HEAD:x']]
        for args in commands:
            with self.subTest(args=args), patch.object(subprocess, 'run') as launch:
                with self.assertRaises(ValueError):
                    self.audit.audit_git_read(self.repo, args)
                launch.assert_not_called()

    def test_git_directory_overrides_are_refused_instead_of_auditing_wrong_repository(self):
        os.environ['GIT_DIR'] = str(self.root / 'unrelated')
        with self.assertRaisesRegex(ValueError, 'GIT_DIR'):
            self.audit.audit_git_read(self.repo, ['status', '--porcelain=v1'])

    def test_real_git_status_preserves_index_bytes(self):
        repo = self.root / 'real'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        (repo / 'source.txt').write_bytes(b'original\n')
        subprocess.run(['git', '-C', str(repo), 'add', 'source.txt'], check=True)
        index = repo / '.git' / 'index'
        raw = index.read_bytes()
        os.utime(repo / 'source.txt', (1, 1))
        result = self.audit.audit_git_read(repo, ['status', '--porcelain=v1'])
        self.assertEqual(result['returncode'], 0)
        self.assertTrue(result['indexes_unchanged'])
        self.assertEqual(index.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
