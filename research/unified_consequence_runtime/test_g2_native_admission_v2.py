"""Independent local adversarial contracts for calibration-only native admission.

Never tests scientific G2, agent comparators or future method transfer.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import g2_native_admission_v2 as admission


class AdmissionV16Controls(unittest.TestCase):
    def setUp(self):
        self.context=tempfile.TemporaryDirectory()
        self.addCleanup(self.context.cleanup)
        self.root=Path(self.context.name)
        self.repo=self.root/'foreign'
        self.repo.mkdir()
        self.out=self.root/'evidence'
        (self.repo/'tests').mkdir()
        (self.repo/'requirements').mkdir()
        (self.repo/'requirements/tests.txt').write_text('pytest==9.0.2\n')
        self.set_test('def test_protected():\n    assert 2 + 2 == 4\n')
        self.git('init','-q')
        self.git('config','user.email','unit@example.invalid')
        self.git('config','user.name','Qualified Test')
        self.commit()
        self.out.mkdir()
        self.write_pin()

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],text=True).strip()

    def commit(self):
        self.git('add','.')
        self.git('commit','-qm','source witness')
        self.sha=self.git('rev-parse','HEAD')
        self.lock=self.git('rev-parse','HEAD:requirements/tests.txt')

    def set_test(self,source):
        (self.repo/'tests/test_warrant.py').write_text(source)

    def write_pin(self,**change):
        pin={'repository':'fixture/foreign','sha':self.sha,'test_paths':['tests'],
             'required_test_prefixes':['tests/test_warrant.py::test_protected'],
             'requirements_blob':self.lock,'scope':'CALIBRATION_ONLY'}
        pin.update(change)
        (self.out/'pin.json').write_text(json.dumps(pin))

    def run_gate(self):
        return admission.execute(self.repo,self.out)

    def test_01_warranted_source_with_real_assertion_passes(self):
        x=self.run_gate()
        self.assertEqual(x['status'],'ADMITTED_NATIVE_PASS_CALIBRATION',x)
        self.assertEqual(x['native_calls'],1)
        self.assertEqual(x['counts'],{'cases':1,'failed':0,'errors':0,'skipped':0})
        self.assertEqual(x['observed_call_nodes'][0]['outcome'],'passed')

    def test_02_original_protected_failure_is_admitted_not_falsely_unknown(self):
        self.set_test('def test_protected():\n    assert 2 + 2 == 5\n')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'ADMITTED_NATIVE_FAIL_PROTECTED_CALIBRATION',x)
        self.assertEqual(x['counts']['failed'],1)

    def test_03_unprotected_failing_test_cannot_be_promoted(self):
        self.set_test('def test_protected():\n    assert True\n\ndef test_unprotected():\n    assert False\n')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION',x)
        self.assertIn('UNKNOWN_UNPROTECTED',x['reason'])

    def test_04_skips_are_incomplete_even_if_suite_exits_zero(self):
        self.set_test('import pytest\n@pytest.mark.skip(reason="not run")\ndef test_protected():\n    assert True\n')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION',x)
        self.assertEqual(x['counts']['skipped'],1)

    def test_05_xfails_are_not_positive_warrants(self):
        self.set_test('import pytest\n@pytest.mark.xfail\ndef test_protected():\n    assert False\n')
        self.commit();self.write_pin()
        self.assertEqual(self.run_gate()['status'],'UNKNOWN_ADMISSION')

    def test_06_collection_error_cannot_be_mislabeled_as_test_case(self):
        self.set_test('import nonexistent_qualified_fixture_package\ndef test_protected():\n    assert True\n')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION',x)
        self.assertTrue(x['collection_errors'])

    def test_07_no_collected_tests_is_unknown(self):
        self.set_test('def a_helper():\n    assert True\n')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertEqual(x['native_calls'],0) # fail before runtime: no declared protected test

    def test_08_missing_assert_is_not_original_protected_evidence(self):
        self.set_test('def test_protected():\n    return 5\n')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertEqual(x['native_calls'],0)

    def test_09_wrong_git_commit_refused_before_test_execution(self):
        self.write_pin(sha='a'*40)
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertEqual(x['native_calls'],0)

    def test_10_tampered_dependency_lock_refused_before_native(self):
        self.write_pin(requirements_blob='f'*40)
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertIn('UNKNOWN_TEST_DEPENDENCY_LOCK',x['reason'])

    def test_11_dirty_tracked_test_refused(self):
        self.set_test('def test_protected():\n    assert False\n')
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertIn('UNKNOWN_TRACKED_SOURCE_DIRTY',x['reason'])

    def test_12_outside_untracked_new_test_not_silently_selected(self):
        (self.repo/'tests/test_extra.py').write_text('def test_extra():\n    assert True\n')
        x=self.run_gate()
        # Unlike a full immutable stage, this lightweight admission must fail closed
        # rather than claim all executed tests are git source-authenticated.
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION',x)

    def test_13_repeat_output_directory_cannot_overwrite_native_receipt(self):
        self.assertEqual(self.run_gate()['status'],'ADMITTED_NATIVE_PASS_CALIBRATION')
        original=(self.out/'admission.json').read_bytes()
        x=self.run_gate()
        self.assertEqual((self.out/'admission.json').read_bytes(),original)
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertIn('UNKNOWN_EVIDENCE_OUTPUT',x['reason'])

    def test_14_unsupported_tracked_symlink_fails_closed(self):
        (self.repo/'elsewhere').write_text('content')
        (self.repo/'linked').symlink_to('elsewhere')
        self.commit();self.write_pin()
        x=self.run_gate()
        self.assertEqual(x['status'],'UNKNOWN_ADMISSION')
        self.assertIn('UNKNOWN_NONREGULAR',x['reason'])


if __name__=='__main__':
    unittest.main()
