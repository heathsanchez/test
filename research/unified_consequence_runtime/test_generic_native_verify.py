"""Verifier boundary contracts using local git fixtures, not scientific tasks."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class GenericNativeVerifierContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker_path = Path(__file__).with_name('generic_native_verify.py')

    def setUp(self):
        self.assertTrue(self.worker_path.exists(), 'generic native verifier is not implemented')
        self.v = importlib.import_module('research.unified_consequence_runtime.generic_native_verify')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root/'repo'; self.repo.mkdir()
        self.git('init', '-q')
        (self.repo/'src/sample').mkdir(parents=True)
        (self.repo/'tests').mkdir()
        (self.repo/'src/sample/__init__.py').write_text('VALUE = 1\n')
        (self.repo/'tests/test_native.py').write_text('from sample import VALUE\ndef test_value(): assert VALUE == 1\n')
        self.freeze()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def freeze(self):
        self.git('add', '.')
        self.git('-c','user.name=Contract Fixture','-c','user.email=fixture@example.invalid',
                 'commit','-qm','fixture')
        commit = self.git('rev-parse','HEAD').decode().strip()
        identity = self.v.source_identity(self.repo, commit)
        env = self.v.environment_identity(sys.executable)
        self.contract = {'schema':self.v.SCHEMA, 'repository':'local/contract-fixture',
            'repo_path':str(self.repo), 'commit':commit, **identity,
            'interpreter':sys.executable, 'environment_sha256':self.v.fingerprint(env),
            'protocol_binding':'1'*64, 'horizon_seconds':7}

    def run_native(self, replacements=(), contract=None):
        return self.v.verify(contract or self.contract, {'replacements':list(replacements)}, self.root/'out')

    def replacement(self, path='src/sample/__init__.py', value='VALUE = 2\n'):
        return {'path':path, 'original_sha256':self.v.sha256((self.repo/path).read_bytes()),
                'replacement':value}

    def test_real_native_pass_binds_tree_environment_junit_and_import(self):
        result = self.run_native()
        self.assertEqual(result['status'],'PASS_NATIVE')
        self.assertEqual(result['junit']['passed'],1)
        self.assertEqual(result['junit']['errors'],0)
        self.assertEqual(result['source']['tracked_tree_sha256'],self.contract['tracked_tree_sha256'])
        self.assertEqual(result['environment_sha256'],self.contract['environment_sha256'])
        self.assertEqual(result['protocol_binding'],self.contract['protocol_binding'])
        self.assertIn('src/sample/__init__.py',[x['path'] for x in result['import_manifest']])
        self.assertEqual(result['costs']['native_calls'],1)
        self.assertEqual(result['costs']['horizon_seconds'],7)
        self.assertEqual(result['runner_sha256'],self.v.sha256(self.worker_path.read_bytes()))

    def test_baseline_failure_and_executable_candidate_success(self):
        (self.repo/'tests/test_native.py').write_text('from sample import VALUE\ndef test_value(): assert VALUE == 2\n')
        self.freeze()
        self.assertEqual(self.run_native()['status'],'FAIL_NATIVE')
        result = self.run_native([self.replacement()])
        self.assertEqual(result['status'],'PASS_NATIVE')
        self.assertEqual(result['junit']['passed'],1)
        self.assertEqual((self.repo/'src/sample/__init__.py').read_text(),'VALUE = 1\n')

    def test_skips_only_are_unknown(self):
        (self.repo/'tests/test_native.py').write_text('import pytest\n@pytest.mark.skip(reason="fixture")\ndef test_skip(): pass\n')
        self.freeze()
        self.assertEqual(self.run_native()['status'],'UNKNOWN_NO_TEST_EXECUTION')

    def test_candidate_cannot_hide_module_failure_with_partial_skip(self):
        (self.repo/'tests/test_unrelated.py').write_text('def test_unrelated(): assert True\n')
        self.freeze()
        self.assertEqual(self.run_native()['junit']['passed'],2)
        candidate=self.replacement(value='import pytest\npytest.skip("candidate suppression", allow_module_level=True)\nVALUE = 1\n')
        result=self.run_native([candidate])
        self.assertEqual(result['junit']['passed'],1)
        self.assertEqual(result['junit']['skipped'],1)
        self.assertEqual(result['status'],'UNKNOWN_PARTIAL_SKIP')

    def test_collection_errors_are_unknown_not_candidate_failure(self):
        (self.repo/'tests/test_native.py').write_text('import unavailable_contract_fixture\n')
        self.freeze()
        self.assertEqual(self.run_native()['status'],'UNKNOWN_NATIVE_ERROR')

    def test_empty_collection_is_unknown(self):
        (self.repo/'tests/test_native.py').write_text('# no tests\n')
        self.freeze()
        self.assertEqual(self.run_native()['status'],'UNKNOWN_NO_TEST_EXECUTION')

    def test_timeout_is_unknown_with_exact_charged_horizon(self):
        (self.repo/'tests/test_native.py').write_text('import time\ndef test_wait(): time.sleep(30)\n')
        self.freeze()
        result = self.run_native()
        self.assertEqual(result['status'],'UNKNOWN_TIMEOUT')
        self.assertEqual(result['costs']['horizon_seconds'],7)
        self.assertGreaterEqual(result['costs']['native_seconds'],7)
        self.assertLess(result['costs']['native_seconds'],12)

    def test_test_and_configuration_mutation_denied(self):
        for name in ('tests/test_native.py','conftest.py','pyproject.toml','.github/workflows/check.py'):
            with self.subTest(path=name):
                with self.assertRaisesRegex(ValueError,'production|tracked'):
                    self.run_native([{'path':name,'original_sha256':'0'*64,'replacement':'pass\n'}])

    def test_suffix_named_native_test_cannot_be_candidate(self):
        path='native_test.py'; (self.repo/path).write_text('def test_native(): assert False\n')
        self.freeze()
        with self.assertRaisesRegex(ValueError,'production'):
            self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_tracked_pytest_shadow_cannot_forge_native_warrant(self):
        (self.repo/'tests/test_native.py').write_text('def test_native(): assert False\n')
        (self.repo/'pytest.py').write_text('''from pathlib import Path
def main(args):
    path=next(x.split('=',1)[1] for x in args if x.startswith('--junitxml='))
    Path(path).write_text('<testsuites><testsuite><testcase name="forged"/></testsuite></testsuites>')
    return 0
''')
        self.freeze()
        result=self.run_native()
        self.assertEqual(result['status'],'FAIL_NATIVE')
        self.assertEqual(result['junit']['failures'],1)
        self.assertNotIn('pytest.py',[x['path'] for x in result['import_manifest']])
        self.assertEqual(result['pytest_import'],result['environment']['pytest_import'])

    def test_custom_native_test_pattern_cannot_be_candidate(self):
        path='src/sample/authority.py';(self.repo/path).write_text('def test_native(): assert False\n')
        (self.repo/'pytest.ini').write_text('[pytest]\npython_files = authority.py\n')
        self.freeze()
        with self.assertRaisesRegex(ValueError,'production'):
            self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_all_standard_configs_protect_custom_native_test_patterns(self):
        path='src/sample/authority.py';(self.repo/path).write_text('def test_native(): assert False\n')
        configurations={'pytest.ini':'[pytest]\npython_files = authority.py\n',
            '.pytest.ini':'[pytest]\npython_files = authority.py\n',
            'tox.ini':'[pytest]\npython_files = authority.py\n',
            'setup.cfg':'[tool:pytest]\npython_files = authority.py\n',
            'pyproject.toml':'[tool.pytest.ini_options]\npython_files = ["authority.py"]\n'}
        for name,source in configurations.items():
            for other in configurations:
                (self.repo/other).unlink(missing_ok=True)
            (self.repo/name).write_text(source);self.freeze()
            with self.subTest(configuration=name):
                with self.assertRaisesRegex(ValueError,'production'):
                    self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_malformed_native_test_configuration_refused(self):
        (self.repo/'pytest.ini').write_text('not a valid ini configuration\n');self.freeze()
        with self.assertRaisesRegex(ValueError,'UNKNOWN_INTERFACE'):
            self.run_native()

    def test_quoted_ini_native_test_patterns_remain_protected(self):
        path='src/sample/authority.py';(self.repo/path).write_text('def test_native(): assert False\n')
        (self.repo/'pytest.ini').write_text('[pytest]\npython_files = "authority.py"\n');self.freeze()
        with self.assertRaisesRegex(ValueError,'production'):
            self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_addopts_cannot_supply_unprotected_authoritative_test(self):
        path='authority.py';(self.repo/path).write_text('def test_native(): assert False\n')
        (self.repo/'pytest.ini').write_text('[pytest]\naddopts = authority.py\n');self.freeze()
        with self.assertRaisesRegex(ValueError,'UNKNOWN_INTERFACE'):
            self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_testpaths_cannot_supply_unprotected_authoritative_test(self):
        path='authority.py';(self.repo/path).write_text('def test_native(): assert False\n')
        (self.repo/'pytest.ini').write_text('[pytest]\ntestpaths = authority.py\n');self.freeze()
        with self.assertRaisesRegex(ValueError,'production'):
            self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_testpaths_descendants_are_protected(self):
        path='src/sample/authority.py';(self.repo/path).write_text('def test_native(): assert False\n')
        (self.repo/'pyproject.toml').write_text('[tool.pytest.ini_options]\ntestpaths = ["src/sample"]\n');self.freeze()
        with self.assertRaisesRegex(ValueError,'production'):
            self.run_native([self.replacement(path,'def test_native(): pass\n')])

    def test_relative_repo_contract_does_not_allow_output_inside_source(self):
        import os
        previous=Path.cwd();os.chdir(self.root)
        try:
            contract={**self.contract,'repo_path':'repo'}
            with self.assertRaisesRegex(ValueError,'outside source'):
                self.v.verify(contract,{'replacements':[]},self.repo/'generated-evidence')
        finally:
            os.chdir(previous)

    def test_forged_original_blob_rejected(self):
        candidate = self.replacement(); candidate['original_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'original'):
            self.run_native([candidate])

    def test_nonempty_unchanged_replacement_is_sham_not_development(self):
        candidate=self.replacement(value=(self.repo/'src/sample/__init__.py').read_text())
        with self.assertRaisesRegex(ValueError,'unchanged'):
            self.run_native([candidate])

    def test_wrong_tree_and_commit_rejected(self):
        for key in ('tracked_tree_sha256','git_tree','commit'):
            contract = dict(self.contract); contract[key]='0'*(64 if key=='tracked_tree_sha256' else 40)
            with self.subTest(key=key):
                with self.assertRaises(ValueError): self.run_native(contract=contract)

    def test_wrong_budget_and_injected_configuration_rejected(self):
        for change in ({'horizon_seconds':8},{'pytest_args':['tests/test_native.py']},
                       {'environment_sha256':'0'*64},{'protocol_binding':'not-a-digest'}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError): self.run_native(contract={**self.contract,**change})

    def test_unsafe_and_duplicate_candidate_paths_rejected(self):
        for path in ('../escape.py','/absolute.py','src/../escape.py','src\\escape.py'):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    self.run_native([{'path':path,'original_sha256':'0'*64,'replacement':'pass'}])
        candidate=self.replacement()
        with self.assertRaisesRegex(ValueError,'duplicate'): self.run_native([candidate,candidate])

    def test_symlink_source_rejected(self):
        (self.repo/'src/link.py').symlink_to('../sample/__init__.py')
        with self.assertRaisesRegex(ValueError,'regular|symlink'): self.freeze()

    def test_untracked_and_ignored_python_cannot_affect_native_import(self):
        (self.repo/'src/sample.py').write_text('raise RuntimeError("untracked import")\n')
        (self.repo/'conftest.py').write_text('raise RuntimeError("untracked hook")\n')
        self.assertEqual(self.run_native()['status'],'PASS_NATIVE')

    def test_runtime_test_mutation_is_not_native_warrant(self):
        candidate=self.replacement(value='from pathlib import Path\nPath("tests/test_native.py").write_text("def test_forged(): pass\\n")\nVALUE = 1\n')
        self.assertEqual(self.run_native([candidate])['status'],'UNKNOWN_SOURCE_MUTATION')

    def test_missing_interpreter_is_unknown_environment(self):
        contract={**self.contract,'interpreter':str(self.root/'missing-python')}
        result=self.run_native(contract=contract)
        self.assertEqual(result['status'],'UNKNOWN_ENVIRONMENT')
        self.assertEqual(result['costs']['native_calls'],0)

    def test_redirected_receipt_path_is_rejected(self):
        out=self.root/'out';out.mkdir()
        elsewhere=self.root/'do-not-write';elsewhere.write_text('protected')
        (out/'receipt.json').symlink_to(elsewhere)
        with self.assertRaisesRegex(ValueError,'output'):
            self.run_native()
        self.assertEqual(elsewhere.read_text(),'protected')

    def test_git_replace_cannot_change_frozen_tree(self):
        original=self.contract['commit']
        (self.repo/'src/sample/__init__.py').write_text('VALUE = 9\n')
        self.git('add','.')
        self.git('-c','user.name=Contract Fixture','-c','user.email=fixture@example.invalid',
                 'commit','-qm','replacement')
        other=self.git('rev-parse','HEAD').decode().strip()
        self.git('replace',original,other)
        self.assertEqual(self.run_native()['status'],'PASS_NATIVE')


if __name__ == '__main__':
    unittest.main()
