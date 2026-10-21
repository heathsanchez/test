"""Supplementary bytecode-omission regression discovered during V42 review.

These controls supplement the unchanged preimplementation freeze. They do not
retroactively become part of that freeze or evidence of prospective learning.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from . import native_source_v42 as source


class NativeSourceV42BytecodeRegressions(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='udm-source-v42-bytecode-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root/'source'
        self.repo.mkdir()
        self.git('init', '-q')
        (self.repo/'target.py').write_bytes(b'VALUE = 7\n')

    def git(self, *args):
        return subprocess.check_output(['git', '--no-replace-objects', '-C', str(self.repo), *args],
            stderr=subprocess.PIPE, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))

    def snapshot(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Source Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'supplementary bytecode omission fixture')
        return source.snapshot(self.repo, self.git('rev-parse', 'HEAD').decode().strip())

    def test_worker_omits_regular_bytecode_but_preserves_full_inventory(self):
        (self.repo/'stale.pyc').write_bytes(b'not executable bytecode\x00\xff')
        identity, files, manifest = self.snapshot()
        world = self.root/'world'
        source.materialize(world, files, manifest, skip_bytecode=True)
        self.assertFalse((world/'stale.pyc').exists())
        self.assertTrue((world/'target.py').is_file())
        self.assertIn('stale.pyc', files)
        self.assertEqual(identity['tracked_tree_sha256'], source.fingerprint(manifest))
        self.assertEqual(source.validate_materialized(world, files, manifest, skip_bytecode=True), [])
        (world/'stale.pyc').write_bytes(files['stale.pyc'])
        self.assertEqual(source.validate_materialized(world, files, manifest, skip_bytecode=True), ['stale.pyc'])

    def test_alias_to_omitted_bytecode_has_no_worker_execution_authority(self):
        (self.repo/'stale.pyc').write_bytes(b'VALUE = 7\n')
        (self.repo/'alias.py').symlink_to('stale.pyc')
        _, files, manifest = self.snapshot()
        retained = self.root/'retained'
        source.materialize(retained, files, manifest)
        self.assertTrue((retained/'alias.py').is_symlink())
        with self.assertRaisesRegex(ValueError, 'UNKNOWN.*OMITTED_BYTECODE'):
            source.materialize(self.root/'worker', files, manifest, skip_bytecode=True)
        self.assertFalse((self.root/'worker').exists())

    def test_alias_chain_cannot_hide_omitted_intermediate_bytecode_alias(self):
        (self.repo/'intermediate.pyc').symlink_to('target.py')
        (self.repo/'alias.py').symlink_to('intermediate.pyc')
        _, files, manifest = self.snapshot()
        self.assertEqual(files['alias.py'], files['target.py'])
        retained = self.root/'retained'
        source.materialize(retained, files, manifest)
        self.assertEqual(os.readlink(retained/'alias.py'), 'intermediate.pyc')
        self.assertEqual(source.validate_materialized(retained, files, manifest), [])
        with self.assertRaisesRegex(ValueError, 'UNKNOWN.*OMITTED_BYTECODE'):
            source.materialize(self.root/'worker', files, manifest, skip_bytecode=True)
        self.assertFalse((self.root/'worker').exists())


if __name__ == '__main__':
    unittest.main()
