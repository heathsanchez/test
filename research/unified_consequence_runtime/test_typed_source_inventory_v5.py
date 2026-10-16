"""Frozen native Git mode semantics tests; authored before V5 implementation."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from .decisive_native_verify import _snapshot


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


class TypedGitInventoryV5(unittest.TestCase):
    def setUp(self):
        from . import typed_source_inventory_v5 as candidate
        self.candidate = candidate
        self.temp = tempfile.TemporaryDirectory(prefix='v5-typed-git-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'source'
        self.root.mkdir()
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.name', 'V5 Contract')
        git(self.root, 'config', 'user.email', 'v5@example.invalid')

    def commit(self, gitlink=None):
        git(self.root, 'add', '-A')
        if gitlink:
            git(self.root, 'update-index', '--add', '--cacheinfo',
                '160000,' + gitlink + ',vendor/external')
        git(self.root, 'commit', '-qm', 'freeze exact synthetic Git modes')
        return git(self.root, 'rev-parse', 'HEAD')

    def write(self, path, raw=b'VALUE = 42\n'):
        target=self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

    def link(self, name, target):
        link=self.root / name
        link.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, link)

    def manifest(self, commit):
        return self.candidate.snapshot(self.root, commit)

    def test_regular_and_relative_source_symlink_are_observed_without_changing_original_verifier(self):
        raw=b'Source-preserved documentation\n'
        self.write('docs/README.txt',raw)
        self.write('pkg.py')
        self.link('README.rst','docs/README.txt')
        commit=self.commit()
        with self.assertRaisesRegex(ValueError,'only regular tracked files supported'):
            _snapshot(self.root,commit)
        result=self.manifest(commit)
        self.assertEqual(result['status'],'TYPED_INVENTORY_ONLY')
        self.assertEqual(result['counts'],{'regular':2,'symlink':1,'gitlink':0})
        link=result['links'][0]
        self.assertEqual(link['path'],'README.rst')
        self.assertEqual(link['target'],'docs/README.txt')
        self.assertEqual(link['resolved_path'],'docs/README.txt')
        self.assertEqual(link['resolution'],'INTERNAL_REGULAR_FILE')
        self.assertEqual(link['target_sha256'],hashlib.sha256(b'docs/README.txt').hexdigest())
        original=next(x for x in result['manifest'] if x['path']=='README.rst')
        self.assertEqual(original['mode'],'120000')
        self.assertEqual(original['sha256'],hashlib.sha256(b'docs/README.txt').hexdigest())
        self.assertNotIn('native_warrant',result)

    def test_symlink_chain_resolves_only_inside_the_pinned_tree(self):
        self.write('inside.txt',b'ok')
        self.link('a.txt','b.txt')
        self.link('b.txt','inside.txt')
        commit=self.commit()
        links={x['path']:x for x in self.manifest(commit)['links']}
        self.assertEqual(links['a.txt']['resolution'],'INTERNAL_REGULAR_FILE')
        self.assertEqual(links['a.txt']['resolved_path'],'inside.txt')
        self.assertEqual(links['b.txt']['resolved_path'],'inside.txt')

    def test_absolute_escape_and_loop_never_become_execution_permission(self):
        self.write('pkg.py')
        self.link('absolute.txt','/etc/passwd')
        self.link('escape.txt','../outside.txt')
        self.link('loop1','loop2')
        self.link('loop2','loop1')
        commit=self.commit()
        links={x['path']:x for x in self.manifest(commit)['links']}
        for x in ('absolute.txt','escape.txt'):
            self.assertEqual(links[x]['resolution'],'UNKNOWN_LINK_ESCAPE')
        self.assertEqual(links['loop1']['resolution'],'UNKNOWN_LINK_CYCLE')
        self.assertEqual(links['loop2']['resolution'],'UNKNOWN_LINK_CYCLE')

    def test_directory_symlink_retained_but_not_prequalified(self):
        self.write('docs/guide.txt')
        self.link('alias','docs')
        commit=self.commit()
        link=self.manifest(commit)['links'][0]
        self.assertEqual(link['resolution'],'UNKNOWN_DIRECTORY_LINK')
        self.assertEqual(link['target'],'docs')

    def test_dangling_link_preserves_byte_identity_but_not_native_admission(self):
        self.write('pkg.py')
        self.link('dangling','missing.py')
        commit=self.commit()
        link=self.manifest(commit)['links'][0]
        self.assertEqual(link['resolution'],'UNKNOWN_DANGLING_LINK')
        self.assertEqual(link['target'],'missing.py')

    def test_gitlink_oid_is_retained_as_opaque_and_may_not_grant_import_authority(self):
        self.write('pkg.py')
        sub_oid='b'*40
        commit=self.commit(gitlink=sub_oid)
        with self.assertRaisesRegex(ValueError,'only regular tracked files supported'):
            _snapshot(self.root,commit)
        snapshot=self.manifest(commit)
        self.assertEqual(snapshot['counts'],{'regular':1,'symlink':0,'gitlink':1})
        self.assertEqual(snapshot['gitlinks'][0],{
            'path':'vendor/external', 'commit_oid':sub_oid,
            'status':'OPAQUE_NOT_NATIVE_EXECUTION_AUTHORITY'})
        item=next(x for x in snapshot['manifest'] if x['path']=='vendor/external')
        self.assertEqual(item['mode'],'160000')
        self.assertEqual(item['oid'],sub_oid)
        self.assertEqual(snapshot['status'],'TYPED_INVENTORY_ONLY')

    def test_symlink_into_gitlink_stays_unknown(self):
        self.write('pkg.py')
        self.link('dep.py','vendor/external/pkg.py')
        commit=self.commit(gitlink='c'*40)
        x=self.manifest(commit)['links'][0]
        self.assertEqual(x['resolution'],'UNKNOWN_GITLINK_TARGET')

    def test_immutable_commit_and_symlink_target_mutation_change_evidence(self):
        self.write('docs/a.txt',b'a')
        self.write('docs/b.txt',b'b')
        self.link('README.rst','docs/a.txt')
        first=self.commit()
        before=self.manifest(first)
        (self.root/'README.rst').unlink()
        self.link('README.rst','docs/b.txt')
        second=self.commit()
        after=self.manifest(second)
        self.assertNotEqual(before['manifest_sha256'],after['manifest_sha256'])
        self.assertEqual(before,self.manifest(first))
        self.assertNotEqual(before['git_tree'],after['git_tree'])

    def test_unknown_commit_or_host_file_traversal_is_refused(self):
        self.write('ok.txt',b'ok')
        commit=self.commit()
        with self.assertRaises(ValueError):
            self.candidate.snapshot(self.root,'0'*40)
        invalid=self.root.parent/'outside'
        invalid.mkdir()
        with self.assertRaises(ValueError):
            self.candidate.snapshot(invalid,commit)


if __name__ == '__main__':
    unittest.main()
