"""Frozen V42 source-boundary contracts on disposable original Git fixtures.

The optional v1 baseline selects the unchanged regular-only snapshot solely for
behavioral RED. These fixtures are admission controls, never prospective tasks.
"""
from __future__ import annotations

import copy
import importlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from . import decisive_native_verify as original


def source():
    baseline = os.environ.get('UDM_SOURCE_V42_BASELINE')
    if baseline not in (None, 'v1'):
        raise ValueError('only the explicit v1 source baseline is supported')
    if baseline == 'v1':
        return original
    return importlib.import_module(__package__ + '.native_source_v42')


class NativeSourceV42Contracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='udm-source-v42-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'source'
        self.repo.mkdir()
        (self.repo / 'data').mkdir()
        (self.repo / 'data/value.txt').write_bytes(b'original data\x00\xff\n')
        (self.repo / 'target.py').write_text('VALUE = 7\n')
        (self.repo / 'pyproject.toml').write_text('[project]\nrequires-python=">=3.11"\n')
        self.git('init', '-q')

    def git(self, *args):
        return subprocess.check_output(['git', '--no-replace-objects', '-C', str(self.repo), *args],
                                       stderr=subprocess.PIPE, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Source Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'frozen source fixture')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def snapshot(self, commit=None):
        return source()._snapshot(self.repo, commit or self.commit())

    def world(self, name='world'):
        root = self.root / name
        root.mkdir()
        return root

    def test_internal_file_symlink_is_inventory_and_executable_alias(self):
        (self.repo / 'alias.py').symlink_to('target.py')
        commit = self.commit()
        identity, files, manifest = self.snapshot(commit)
        self.assertEqual(files['alias.py'], files['target.py'])
        link = next(row for row in manifest if row['path'] == 'alias.py')
        self.assertEqual(link['mode'], '120000')
        self.assertEqual(link['blob'], self.git('rev-parse', commit + ':alias.py').decode().strip())
        self.assertEqual(link['sha256'], original.sha256(b'target.py'))
        self.assertEqual(identity, source().source_identity(self.repo, commit))
        world = self.world()
        source().materialize(world, files, manifest)
        self.assertTrue((world / 'alias.py').is_symlink())
        self.assertEqual(os.readlink(world / 'alias.py'), 'target.py')
        self.assertEqual(source().validate_materialized(world, files, manifest), [])
        result = subprocess.run([sys.executable, '-I', '-B', '-c',
            'import sys;sys.path.insert(0,sys.argv[1]);import alias;assert alias.VALUE==7', str(world)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_inventory_preserves_unparsed_data_and_regular_executable_mode(self):
        (self.repo / 'data/broken.py').write_bytes(b'def invalid(:\n print "legacy"\n')
        tool = self.repo / 'tool.py'
        tool.write_text('VALUE = 1\n')
        tool.chmod(0o755)
        _, files, manifest = self.snapshot()
        self.assertEqual(files['data/broken.py'], (self.repo / 'data/broken.py').read_bytes())
        self.assertEqual(next(row['mode'] for row in manifest if row['path'] == 'tool.py'), '100755')
        world = self.world()
        source().materialize(world, files, manifest)
        self.assertEqual((world / 'tool.py').stat().st_mode & 0o777, 0o755)
        self.assertEqual(source().validate_materialized(world, files, manifest), [])

    def test_snapshot_reads_exact_git_blobs_not_transformed_checkout(self):
        (self.repo / 'alias.py').symlink_to('target.py')
        commit = self.commit()
        before = self.snapshot(commit)
        (self.repo / 'target.py').write_text('VALUE = 999\n')
        (self.repo / 'alias.py').unlink()
        (self.repo / 'alias.py').symlink_to('untracked-host-target.py')
        self.assertEqual(self.snapshot(commit), before)

    def test_raw_link_text_changes_identity_even_when_contents_are_equal(self):
        link = self.repo / 'alias.py'
        link.symlink_to('target.py')
        first, files1, manifest1 = self.snapshot()
        link.unlink()
        link.symlink_to('./target.py')
        second, files2, manifest2 = self.snapshot()
        self.assertEqual(files1, files2)
        self.assertNotEqual(first['tracked_tree_sha256'], second['tracked_tree_sha256'])
        self.assertNotEqual(manifest1, manifest2)

    def test_deterministic_archive_keeps_link_type_raw_target_and_regular_bytes(self):
        (self.repo / 'alias.py').symlink_to('./target.py')
        _, files, manifest = self.snapshot()
        first = source().tracked_archive(files, manifest)
        self.assertEqual(first, source().tracked_archive(files, manifest))
        with tarfile.open(fileobj=io.BytesIO(first), mode='r:gz') as archive:
            link = archive.getmember('alias.py')
            self.assertTrue(link.issym())
            self.assertEqual(link.linkname, './target.py')
            self.assertEqual(archive.extractfile('target.py').read(), files['target.py'])

    def test_gitlink_pointer_is_inventoried_but_never_executable_authority(self):
        parent = self.commit()
        self.git('update-index', '--add', '--cacheinfo', '160000,' + parent + ',opaque')
        tree = self.git('write-tree').decode().strip()
        commit = self.git('-c', 'user.name=Source Fixture', '-c', 'user.email=fixture@example.invalid',
                          'commit-tree', tree, '-p', parent, '-m', 'opaque pointer fixture').decode().strip()
        identity, files, manifest = self.snapshot(commit)
        row = next(item for item in manifest if item['path'] == 'opaque')
        self.assertEqual(row['mode'], '160000')
        self.assertEqual(row['blob'], parent)
        self.assertNotIn('opaque', files)
        self.assertEqual(identity['git_tree'], tree)
        with self.assertRaisesRegex(ValueError, 'UNKNOWN.*GITLINK'):
            source().require_executable(manifest)
        # A host directory cannot silently supply the missing immutable source.
        (self.repo / 'opaque').mkdir()
        (self.repo / 'opaque/__init__.py').write_text('VALUE = 7\n')
        self.assertEqual(self.snapshot(commit)[2], manifest)
        with self.assertRaisesRegex(ValueError, 'UNKNOWN.*GITLINK'):
            source().materialize(self.world(), files, manifest)

    def test_unsafe_unsupported_or_unavailable_links_fail_closed(self):
        cases = (
            ('/etc/passwd', 'absolute'),
            ('../host.py', 'escape'),
            ('.git/config', 'git-administration'),
            ('absent.py', 'dangling'),
            ('data', 'directory-alias'),
            ('alias.py', 'cycle'),
        )
        for target, label in cases:
            with self.subTest(case=label):
                link = self.repo / 'alias.py'
                if link.is_symlink():
                    link.unlink()
                link.symlink_to(target)
                commit = self.commit()
                with self.assertRaises(ValueError):
                    self.snapshot(commit)

    def test_relative_parent_traversal_is_allowed_only_when_proven_internal(self):
        (self.repo / 'data/alias.py').symlink_to('../target.py')
        _, files, manifest = self.snapshot()
        self.assertEqual(files['data/alias.py'], files['target.py'])
        source().materialize(self.world(), files, manifest)

    def test_link_chain_preserves_each_original_raw_target(self):
        (self.repo / 'alias.py').symlink_to('target.py')
        (self.repo / 'second.py').symlink_to('alias.py')
        _, files, manifest = self.snapshot()
        world = self.world()
        source().materialize(world, files, manifest)
        self.assertEqual(os.readlink(world / 'alias.py'), 'target.py')
        self.assertEqual(os.readlink(world / 'second.py'), 'alias.py')
        self.assertEqual(files['second.py'], files['target.py'])
        self.assertEqual(source().validate_materialized(world, files, manifest), [])

    def test_materialized_link_text_swap_is_detected_despite_same_contents(self):
        (self.repo / 'alias.py').symlink_to('target.py')
        _, files, manifest = self.snapshot()
        world = self.world()
        source().materialize(world, files, manifest)
        (world / 'alias.py').unlink()
        (world / 'alias.py').symlink_to('./target.py')
        self.assertIn('alias.py', source().validate_materialized(world, files, manifest))
        with self.assertRaises(ValueError):
            source().validate_materialized(world, files, manifest, strict=True)

    def test_regular_to_link_swap_bytes_and_executable_mode_changes_are_detected(self):
        _, files, manifest = self.snapshot()
        for attack in ('swap', 'bytes', 'mode'):
            with self.subTest(attack=attack):
                world = self.world(attack)
                source().materialize(world, files, manifest)
                target = world / 'target.py'
                if attack == 'swap':
                    target.unlink()
                    target.symlink_to('data/value.txt')
                elif attack == 'bytes':
                    target.write_text('VALUE = 999\n')
                else:
                    target.chmod(0o755)
                self.assertIn('target.py', source().validate_materialized(world, files, manifest))

    def test_forged_or_extra_projection_bytes_are_not_materialization_authority(self):
        (self.repo / 'alias.py').symlink_to('target.py')
        _, files, manifest = self.snapshot()
        for attack in ('regular', 'alias', 'extra'):
            with self.subTest(attack=attack):
                altered = dict(files)
                altered[{'regular': 'target.py', 'alias': 'alias.py', 'extra': 'injected.py'}[attack]] = b'VALUE=999\n'
                with self.assertRaises(ValueError):
                    source().materialize(self.world(attack), altered, manifest)

    def test_checkout_restore_uses_git_blobs_and_never_follows_leaf_links(self):
        _, files, manifest = self.snapshot()
        world = self.world()
        (world / '.git').mkdir()
        (world / 'target.py').write_bytes(b'checkout-filter transformation\n')
        source().materialize(world, files, manifest, tracked_checkout=True)
        self.assertEqual((world / 'target.py').read_bytes(), files['target.py'])
        external = self.root / 'external.py'
        external.write_bytes(b'outside bytes stay intact\n')
        (world / 'target.py').unlink()
        (world / 'target.py').symlink_to(external)
        source().materialize(world, files, manifest, tracked_checkout=True)
        self.assertEqual(external.read_bytes(), b'outside bytes stay intact\n')
        self.assertFalse((world / 'target.py').is_symlink())
        self.assertEqual((world / 'target.py').read_bytes(), files['target.py'])

    def test_checkout_restore_refuses_redirected_parent_and_untracked_content(self):
        _, files, manifest = self.snapshot()
        external = self.root / 'external'
        external.mkdir()
        for attack in ('parent', 'untracked'):
            with self.subTest(attack=attack):
                world = self.world(attack)
                if attack == 'parent':
                    (world / 'data').symlink_to(external, target_is_directory=True)
                else:
                    (world / 'injected.py').write_text('VALUE = 999\n')
                with self.assertRaises(ValueError):
                    source().materialize(world, files, manifest, tracked_checkout=True)
                self.assertEqual(list(external.iterdir()), [])

    def test_overlay_cannot_write_through_link_or_link_parent(self):
        (self.repo / 'alias.py').symlink_to('target.py')
        _, _, manifest = self.snapshot()
        for name in ('alias.py', 'alias.py/test_new.py'):
            with self.subTest(path=name):
                with self.assertRaises(ValueError):
                    source().safe_overlay([name], manifest)

    def test_candidate_cannot_change_alias_or_target_of_protected_test_alias(self):
        (self.repo / 'test_alias.py').symlink_to('target.py')
        _, files, manifest = self.snapshot()
        for name in ('test_alias.py', 'target.py'):
            with self.subTest(path=name):
                candidate = {'replacements': [{'path': name, 'original_sha256': original.sha256(files[name]),
                                               'replacement': 'VALUE = 9\n'}]}
                with self.assertRaises(ValueError):
                    source().validate_candidate(candidate, files, manifest)


if __name__ == '__main__':
    unittest.main()
