"""Finite environment preparation checks; never fetch or install packages."""
import copy
import gzip
import hashlib
import importlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock


MODULE = 'research.unified_consequence_runtime.native_environment_v2'


class NativeEnvironmentV2(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
                             'versioned environment preparation module is required')
        self.environment = importlib.import_module(MODULE)

    @staticmethod
    def manifest(files):
        return [{'path': name, 'mode': '100755' if name.endswith('.sh') else '100644',
                 'sha256': hashlib.sha256(raw).hexdigest(), 'blob': 'a' * 40}
                for name, raw in files.items()]

    def test_archive_preserves_tracked_bytes_modes_and_canonical_names(self):
        files = {'z archival.txt': b'commit=$Format:%H$\n\x00\xff',
                 'scripts/check.sh': b'#!/bin/sh\nexit 0\n'}
        raw = self.environment.tracked_archive(files, self.manifest(files))
        self.assertEqual(raw[4:8], b'\0' * 4, 'gzip must not contain a creation timestamp')
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
            self.assertEqual(archive.getnames(), sorted(files))
            for member in archive:
                self.assertTrue(member.isfile())
                self.assertEqual(archive.extractfile(member).read(), files[member.name])
                self.assertEqual(member.mode, 0o755 if member.name.endswith('.sh') else 0o644)
                self.assertEqual((member.uid, member.gid, member.uname, member.gname, member.mtime),
                                 (0, 0, '', '', 0))

    def test_archive_is_deterministic_across_source_and_manifest_order(self):
        files = {'z.txt': b'z\n', 'a.txt': b'a\n'}
        manifest = self.manifest(files)
        first = self.environment.tracked_archive(files, manifest)
        second = self.environment.tracked_archive(dict(reversed(list(files.items()))), list(reversed(manifest)))
        self.assertEqual(first, second)
        self.assertTrue(gzip.decompress(first))

    def test_archive_rejects_incomplete_duplicate_or_inconsistent_manifest(self):
        files = {'a.txt': b'tracked bytes\n'}
        manifest = self.manifest(files)
        invalid = [[], manifest * 2, [{**manifest[0], 'sha256': '0' * 64}],
                   [{**manifest[0], 'path': 'other.txt'}],
                   [{**manifest[0], 'mode': '120000'}]]
        for rows in invalid:
            with self.subTest(manifest=rows), self.assertRaises(ValueError):
                self.environment.tracked_archive(files, rows)
        with self.assertRaises(ValueError):
            self.environment.tracked_archive({**files, 'extra.txt': b'extra'}, manifest)

    def test_archive_rejects_unsafe_source_names(self):
        for name in ('../escape', '/absolute', './relative', 'a/../escape', 'a\\escape'):
            files = {name: b'bytes'}
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.environment.tracked_archive(files, self.manifest(files))

    def test_tag_refs_include_only_targets_in_the_base_ancestry(self):
        ancestor, older, future = 'a' * 40, 'b' * 40, 'c' * 40
        annotated_object, future_object = 'd' * 40, 'e' * 40
        raw = '\n'.join([
            f'{future_object}\trefs/tags/v-future',
            f'{future}\trefs/tags/v-future^{{}}',
            f'{annotated_object}\trefs/tags/v-annotated',
            f'{ancestor}\trefs/tags/v-annotated^{{}}',
            f'{older}\trefs/tags/v-lightweight',
            f'{future}\trefs/tags/v-future-lightweight',
        ]) + '\n'
        self.assertEqual(self.environment.ancestor_tag_refs(raw, {ancestor, older}), [
            {'ref': 'refs/tags/v-annotated', 'tag_object': annotated_object, 'target': ancestor},
            {'ref': 'refs/tags/v-lightweight', 'tag_object': older, 'target': older},
        ])

    def test_annotated_tag_eligibility_uses_peeled_target_not_tag_object(self):
        tag_object, future = 'a' * 40, 'b' * 40
        raw = f'{tag_object}\trefs/tags/v1\n{future}\trefs/tags/v1^{{}}\n'
        self.assertEqual(self.environment.ancestor_tag_refs(raw, {tag_object}), [])

    def test_tag_parser_rejects_malformed_unsafe_duplicate_or_orphan_refs(self):
        commit = 'a' * 40
        bad = ['not-a-sha\trefs/tags/v1\n',
               f'{commit}\trefs/heads/main\n',
               f'{commit}\trefs/tags/../escape\n',
               f'{commit}\trefs/tags/v1.lock\n',
               f'{commit}\trefs/tags/v1 extra\n',
               f'{commit}\trefs/tags/v1^{{}}\n',
               f'{commit}\trefs/tags/v1\n' * 2,
               f'{commit}\trefs/tags/v1\n{commit}\trefs/tags/v1^{{}}\n{commit}\trefs/tags/v1^{{}}\n',
               f'{commit}\trefs/tags/v1\textra\n']
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.environment.ancestor_tag_refs(raw, {commit})
        self.assertEqual(self.environment.ancestor_tag_refs('', {commit}), [])

    @staticmethod
    def policy():
        return {'schema': 'UDM_NATIVE_EXECUTION_POLICY_V2', 'collection_seconds': 60,
                'execution_seconds': 600, 'pytest_version': '8.4.1', 'plugins': []}

    def assert_invalid_provision(self, *, packages=None, policy=None):
        spec = {'repo': 'owner/repo', 'base_commit': 'a' * 40, 'head_commit': 'b' * 40,
                'files': [{'filename': 'tests/test_pkg.py', 'status': 'modified'}]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'environment'
            with mock.patch.object(self.environment, '_command', side_effect=AssertionError('invalid input reached subprocess')):
                with self.assertRaises(ValueError):
                    self.environment.provision(spec, root, 'c' * 64,
                        policy=self.policy() if policy is None else policy,
                        packages=['pytest==8.4.1'] if packages is None else packages)
            self.assertFalse(root.exists(), 'validation must precede evidence directory creation')

    def test_invalid_package_requests_are_rejected_before_filesystem_or_subprocess(self):
        for packages in ([], ['pytest'], ['pytest>=8'], ['-r requirements.txt'],
                         ['https://example.invalid/pkg.whl'], ['pytest==8.4.1;python_version>="3"'],
                         ['pytest==8.4.1', 'pytest==8.3.5'], ['pytest==8.4.1', 'PyTeSt==8.4.1'],
                         ['pytest==8.4.1', 'some_pkg==1.0', 'some-pkg==1.0'],
                         ['pytest==8.4.1', 'broken==1..0'], ['pytest==8.4.1', 'broken==1.0+'],
                         ['pytest==8.4.1', 'broken-==1.0'],
                         ['other==1.0'], ['pytest==8.3.5'], 'pytest==8.4.1'):
            with self.subTest(packages=packages):
                self.assert_invalid_provision(packages=packages)

    def test_invalid_policies_are_rejected_before_filesystem_or_subprocess(self):
        changes = [{'schema': 'UDM_NATIVE_EXECUTION_POLICY_V1'}, {'unexpected': True},
                   {'collection_seconds': True}, {'collection_seconds': 0}, {'execution_seconds': 601},
                   {'pytest_version': ''}, {'pytest_version': '../8.4.1'}, {'plugins': {}},
                   {'plugins': [{'module': 'plugin', 'distribution': 'missing', 'version': '1.0'}]},
                   {'plugins': [{'module': 'plugin', 'distribution': 'pytest', 'version': '8.3.5'}]},
                   {'plugins': [{'module': 'plugin', 'distribution': 'pytest', 'version': '8.4.1', 'extra': True}]},
                   {'plugins': [{'module': 'plugin', 'distribution': 'pytest', 'version': '8.4.1'}] * 2}]
        for change in changes:
            policy = {**copy.deepcopy(self.policy()), **change}
            with self.subTest(change=change):
                self.assert_invalid_provision(policy=policy)
        policy = self.policy(); del policy['pytest_version']
        self.assert_invalid_provision(policy=policy)


if __name__ == '__main__':
    unittest.main()
