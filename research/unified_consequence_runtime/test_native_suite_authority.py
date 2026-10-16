"""Externally frozen native-suite contracts on local Git/pytest fixtures only."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research.unified_consequence_runtime import generic_native_verify as verifier
from research.unified_consequence_runtime.native_frontier import NativeFrontierRuntime
from research.unified_consequence_runtime.test_native_frontier import MemoryMachine


class NativeSuiteAuthorityContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment=verifier.fingerprint(verifier.environment_identity(sys.executable))
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.repo=self.root/'source';self.repo.mkdir()
        self.git('init','-q')
        (self.repo/'src/sample').mkdir(parents=True);(self.repo/'tests').mkdir()
        (self.repo/'src/sample/__init__.py').write_text('VALUE = 42\n')
        (self.repo/'pytest.ini').write_text('[pytest]\naddopts = -q\n')
        (self.repo/'tests/test_native.py').write_text('def test_old(): assert True\n')
        self.base=self.commit()
        (self.repo/'tests/test_native.py').write_text('from sample import VALUE\ndef test_old(): assert True\ndef test_new(): assert VALUE == 42\n')
        self.refresh()
    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.PIPE)
    def commit(self):
        self.git('add','.');self.git('-c','user.name=Suite Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
        return self.git('rev-parse','HEAD').decode().strip()
    def refresh(self):
        commit=self.commit()
        self.contract={'schema':verifier.SCHEMA,'repository':'local/suite-fixture','repo_path':str(self.repo),
            'commit':commit,**verifier.source_identity(self.repo,commit),'interpreter':sys.executable,
            'environment_sha256':self.environment,'protocol_binding':'e'*64,'horizon_seconds':7}
        self.authority=verifier.derive_native_suite_authority(self.repo,self.base,commit,'e'*64,repository='local/suite-fixture')
    def run_native(self,authority=None,candidate=None):
        return verifier.verify(self.contract,candidate or {'replacements':[]},self.root/'runs',
            native_suite_authority=self.authority if authority is None else authority)
    def test_declared_addopts_stay_immutable_and_full_original_plus_new_suite_runs(self):
        self.assertEqual(self.authority['required_test_nodes'],['tests/test_native.py::test_new','tests/test_native.py::test_old'])
        self.assertEqual(self.authority['config_sha256'],{'pytest.ini':verifier.sha256((self.repo/'pytest.ini').read_bytes())})
        result=self.run_native()
        self.assertEqual(result['status'],'PASS_NATIVE')
        self.assertEqual(result['junit']['passed'],2)
        self.assertEqual(sorted(result['executed_test_nodes']),self.authority['required_test_nodes'])
        self.assertEqual(result['native_suite_authority_sha256'],verifier.fingerprint(self.authority))
        self.assertEqual((self.repo/'pytest.ini').read_text(),'[pytest]\naddopts = -q\n')
    def test_authority_and_generated_wheel_work_together_without_overriding_addopts(self):
        from research.unified_consequence_runtime.test_generated_build_materialization import BACKEND
        from research.unified_consequence_runtime.generic_build_materialization import materialize
        (self.repo/'pyproject.toml').write_text('[build-system]\nrequires = []\nbuild-backend = "fixture_backend"\nbackend-path = ["."]\n')
        (self.repo/'fixture_backend.py').write_text(BACKEND)
        (self.repo/'tests/test_native.py').write_text('from sample._version import GENERATED_VALUE\ndef test_old(): assert True\ndef test_new(): assert GENERATED_VALUE == 42\n')
        self.refresh()
        built=materialize(self.repo,self.root/'build',python=sys.executable)
        result=verifier.verify(self.contract,{'replacements':[]},self.root/'combined',
            generated_wheel_evidence=built['generated_wheel_evidence'],native_suite_authority=self.authority)
        self.assertEqual(result['status'],'PASS_NATIVE')
        self.assertEqual(result['junit']['passed'],2)
        self.assertEqual(result['costs']['build_calls'],1)
        self.assertEqual(result['generated_module_count'],1)
    def test_old_no_authority_still_refuses_nonempty_addopts(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN_INTERFACE'):
            verifier.verify(self.contract,{'replacements':[]},self.root/'old')
    def test_declared_k_old_deselection_cannot_hide_new_assertion(self):
        (self.repo/'pytest.ini').write_text('[pytest]\naddopts = -k test_old\n');self.refresh()
        result=self.run_native()
        self.assertEqual(result['junit']['passed'],1)
        self.assertEqual(result['status'],'UNKNOWN_REQUIRED_ASSERTION')
        self.assertIn('tests/test_native.py::test_new',result['deselected_test_nodes'])
    def test_partial_parameter_deselection_cannot_hide_required_case(self):
        (self.repo/'tests/test_native.py').write_text('import pytest\n@pytest.mark.parametrize("value", [1, 2], ids=["first", "second"])\ndef test_new(value): assert value > 0\n')
        (self.repo/'pytest.ini').write_text('[pytest]\naddopts = -k first\n');self.refresh()
        result=self.run_native()
        self.assertEqual(result['junit']['passed'],1)
        self.assertEqual(result['status'],'UNKNOWN_REQUIRED_ASSERTION')
        self.assertEqual(result['deselected_test_nodes'],['tests/test_native.py::test_new[second]'])
    def test_required_skip_and_testpaths_exclusion_never_promote(self):
        (self.repo/'tests/test_native.py').write_text('import pytest\ndef test_old(): assert True\n@pytest.mark.skip(reason="fixture")\ndef test_new(): assert False\n');self.refresh()
        result=self.run_native()
        self.assertEqual(result['status'],'UNKNOWN_REQUIRED_ASSERTION')
        self.assertEqual(result['junit']['skipped'],1)
    def test_executed_required_assertion_failure_remains_native_failure(self):
        (self.repo/'tests/test_native.py').write_text('def test_old(): assert True\ndef test_new(): assert False\n');self.refresh()
        result=self.run_native()
        self.assertEqual(result['status'],'FAIL_NATIVE')
        self.assertEqual(result['junit']['failures'],1)
        self.assertIn('tests/test_native.py::test_new',result['executed_test_nodes'])
    def test_declared_collection_authority_overrides_are_not_supported(self):
        for opts in ('-o python_files=authority.py','-c hidden.ini','--rootdir=other','authority.py','-p unsafe'):
            (self.repo/'pytest.ini').write_text('[pytest]\naddopts = '+opts+'\n')
            commit=self.commit()
            with self.subTest(opts=opts),self.assertRaisesRegex(ValueError,'UNKNOWN_INTERFACE'):
                verifier.derive_native_suite_authority(self.repo,self.base,commit,'e'*64,repository='local/suite-fixture')
    def test_forged_weaker_required_set_wrong_source_protocol_config_or_test_hash_refused(self):
        variants=[{**self.authority,'required_test_nodes':['tests/test_native.py::test_old']},
            {**self.authority,'source_commit':self.base},{**self.authority,'baseline_commit':'0'*40},
            {**self.authority,'protocol_binding':'f'*64},{**self.authority,'repository':'other/task'},
            {**self.authority,'config_sha256':{}},{**self.authority,'test_source_sha256':{}}]
        for wrong in variants:
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):self.run_native(wrong)
    def test_candidate_cannot_edit_required_assertions_or_native_config_or_supply_authority(self):
        for name in ('tests/test_native.py','pytest.ini'):
            with self.subTest(path=name),self.assertRaisesRegex(ValueError,'production|tracked'):
                self.run_native(candidate={'replacements':[{'path':name,'original_sha256':verifier.sha256((self.repo/name).read_bytes()),'replacement':'pass\n'}]})
        with self.assertRaises(ValueError):
            self.run_native(candidate={'replacements':[],'native_suite_authority':self.authority})
    def test_unchanged_or_empty_test_delta_cannot_grant_authority(self):
        with self.assertRaises(ValueError):
            verifier.derive_native_suite_authority(self.repo,self.base,self.base,'e'*64,repository='local/suite-fixture')
    def test_conditional_nested_or_dynamic_tests_are_unsupported_contracts(self):
        sources=['def test_old(): assert True\nif True:\n def test_new(): assert False\n',
            'def test_old():\n def test_nested(): assert False\n assert True\n',
            'def test_old(): assert True\nglobals()["test_new"] = lambda: None\n',
            'def test_old(): assert True\ntest_alias = lambda: None\n']
        for source in sources:
            (self.repo/'tests/test_native.py').write_text(source);commit=self.commit()
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'UNKNOWN_SUITE_CONTRACT'):
                verifier.derive_native_suite_authority(self.repo,self.base,commit,'e'*64,repository='local/suite-fixture')
    def test_class_fixture_changes_conservatively_require_all_class_test_methods(self):
        (self.repo/'tests/test_native.py').write_text('import pytest\n@pytest.mark.parametrize("value", [1,2])\nclass TestNative:\n def test_a(self,value): assert value>0\n def test_b(self,value): assert value<3\n');self.refresh()
        self.assertEqual(self.authority['required_test_nodes'],['tests/test_native.py::TestNative::test_a','tests/test_native.py::TestNative::test_b'])
        self.assertEqual(self.run_native()['junit']['passed'],4)
    def test_runtime_authority_is_descriptor_bound_and_freshly_reverified(self):
        machine=MemoryMachine();runtime=NativeFrontierRuntime(machine,self.contract,self.root/'runtime',native_suite_authority=self.authority)
        key=runtime.admit({'replacements':[]});receipt,_=runtime.execute(key)
        self.assertEqual(receipt['native_suite_authority_sha256'],verifier.fingerprint(self.authority))
        cap=machine.descriptor(key)
        self.assertEqual(cap.source['native_suite_authority_sha256'],verifier.fingerprint(self.authority))
        runtime.native_suite_authority['required_test_nodes']=['tests/test_native.py::test_old']
        with self.assertRaises(ValueError):runtime.execute(key)
    def test_native_receipt_cannot_omit_required_execution_evidence(self):
        machine=MemoryMachine();runtime=NativeFrontierRuntime(machine,self.contract,self.root/'receipt-runtime',native_suite_authority=self.authority)
        result=runtime.observe();candidate={'replacements':[]}
        for change in ({'native_suite_authority_sha256':'0'*64},{'executed_test_nodes':['tests/test_native.py::test_old']},
                       {'deselected_test_nodes':['tests/test_native.py::test_new']}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                runtime._receipt({**result,**change},candidate)

if __name__=='__main__':unittest.main()
