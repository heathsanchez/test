"""Source-only admission fixtures; no target repository or native PASS oracle."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from .decisive_task_admission import is_test, overlay_author_tests, _commit_overlay, _validate_spec
from .generic_native_verify import _snapshot


class AdmissionSourceTests(unittest.TestCase):
    def test_test_paths_are_python_only_and_canonical(self):
        for name in ('tests/test_api.py', 'pkg/test_api.py', 'pkg/api_test.py', 'conftest.py'):
            self.assertTrue(is_test(name), name)
        for name in ('src/pkg.py', 'test.py', 'tests/data.json', '../tests/test_a.py', '/tests/test_a.py', 'tests\\test_a.py'):
            self.assertFalse(is_test(name), name)

    def test_overlay_changes_tests_and_preserves_every_production_byte(self):
        base={'pkg.py': b'PRODUCTION\n', 'tests/test_pkg.py': b'OLD\n', 'pyproject.toml': b'[build-system]\n'}
        augmented=overlay_author_tests(base, {'tests/test_pkg.py': b'NEW\n', 'tests/test_added.py': b'ADDED\n'})
        self.assertEqual(base['tests/test_pkg.py'], b'OLD\n')
        self.assertEqual(augmented['tests/test_pkg.py'], b'NEW\n')
        self.assertEqual(augmented['pkg.py'],base['pkg.py'])
        self.assertEqual(augmented['pyproject.toml'],base['pyproject.toml'])
        self.assertEqual(augmented['tests/test_added.py'],b'ADDED\n')

    def test_overlay_refuses_production_or_path_traversal_or_nonbytes(self):
        for overlay in ({'pkg.py':b'WIN'}, {'../tests/test_a.py':b'WIN'}, {'tests/test_a.py':'text'}, {}):
            with self.assertRaises(ValueError): overlay_author_tests({'pkg.py':b'OLD'},overlay)

    def test_metadata_validation_rejects_unpinned_or_deleted_source(self):
        valid={'repo':'owner/repo','base_commit':'a'*40,'head_commit':'b'*40,
               'files':[{'filename':'tests/test_pkg.py','status':'modified'}]}
        self.assertEqual(_validate_spec(valid),('owner/repo','a'*40,'b'*40,['tests/test_pkg.py']))
        for update in ({'base_commit':'main'},{'repo':'owner/repo;bad'},
                       {'files':[{'filename':'tests/test_pkg.py','status':'removed'}]},
                       {'files':[{'filename':'pkg.py','status':'modified'}]}):
            with self.assertRaises(ValueError):_validate_spec({**valid,**update})

    def test_augmented_git_commit_is_deterministic_and_preserves_original_tree(self):
        def git(repo,*args,env=None):
            return subprocess.check_output(['git','-C',str(repo),*args],env=env,stderr=subprocess.PIPE).decode().strip()
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary)/'source';repo.mkdir();git(repo,'init','-q')
            (repo/'pkg.py').write_bytes(b'VALUE = 1\n');(repo/'tests').mkdir()
            (repo/'tests/test_pkg.py').write_bytes(b'def test_pkg():\n    assert True\n')
            git(repo,'add','.')
            env={**os.environ,'GIT_AUTHOR_DATE':'2000-01-01T00:00:00+0000','GIT_COMMITTER_DATE':'2000-01-01T00:00:00+0000'}
            git(repo,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture',env=env)
            base=git(repo,'rev-parse','HEAD');original=_snapshot(repo,base)
            overlay={'tests/test_pkg.py':b'def test_pkg():\n    assert 1 == 1\n',
                     'tests/test_added.py':b'def test_added():\n    assert 2 == 2\n'}
            first=_commit_overlay(repo,base,overlay);a=_snapshot(repo,first)
            git(repo,'reset','--hard',base)
            second=_commit_overlay(repo,base,overlay);b=_snapshot(repo,second)
            self.assertEqual(first,second);self.assertEqual(a,b)
            self.assertEqual(a[1]['pkg.py'],original[1]['pkg.py'])
            self.assertEqual(git(repo,'rev-parse',first+'^'),base)
            self.assertEqual(a[1]['tests/test_added.py'],overlay['tests/test_added.py'])
            from .generic_native_verify import derive_native_suite_authority,sha256
            authority=derive_native_suite_authority(repo,base,first,'c'*64,repository='fixture/source')
            self.assertEqual(authority['source_commit'],first)
            self.assertEqual(authority['baseline_commit'],base)
            self.assertEqual(authority['protocol_binding'],'c'*64)
            self.assertEqual(authority['required_test_nodes'],['tests/test_added.py::test_added','tests/test_pkg.py::test_pkg'])
            self.assertEqual(authority['test_source_sha256'],{name:sha256(raw) for name,raw in overlay.items()})


if __name__=='__main__':unittest.main()
