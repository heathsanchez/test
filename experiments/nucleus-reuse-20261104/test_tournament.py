import unittest
import sys,time,tempfile
from pathlib import Path
from tournament import qualifies, select_winner, INPUT_SHA, validate_baseline, native_target_valid, run_group

class AdmissionTests(unittest.TestCase):
    def row(self, **changes):
        r=dict(name='candidate',parity=True,native_parity=True,mathlib_rc=0,reference_mathlib_rc=0,input_sha=INPUT_SHA,instructions=[90,91,89],reference_instructions=[100,100,100])
        r.update(changes)
        return r
    def test_unknown_full_input_never_wins(self):
        self.assertFalse(qualifies(self.row(mathlib_rc=2)))
    def test_wrong_verdict_never_wins(self):
        self.assertFalse(qualifies(self.row(parity=False)))
    def test_incomplete_reference_never_qualifies_a_win(self):
        self.assertFalse(qualifies(self.row(reference_mathlib_rc=2)))
    def test_missing_instruction_counter_never_wins(self):
        self.assertFalse(qualifies(self.row(instructions=[])))
    def test_incompatible_input_never_wins(self):
        self.assertFalse(qualifies(self.row(input_sha='different')))
    def test_one_losing_pair_blocks_promotion(self):
        self.assertFalse(qualifies(self.row(instructions=[90,101,89])))
    def test_selects_only_a_qualified_winner(self):
        fast=self.row(name='false-fast',mathlib_rc=2,instructions=[1,1,1])
        valid=self.row()
        self.assertEqual(select_winner([fast,valid])['name'],'candidate')
    def test_preserves_unknown_when_none_qualify(self):
        self.assertIsNone(select_winner([self.row(mathlib_rc=2)]))

class BoundaryTests(unittest.TestCase):
    def test_opposing_wrong_verdicts_cannot_preserve_qualified_baseline(self):
        rows=[dict(case='valid',expected=0,rc=1),dict(case='invalid',expected=1,rc=0)]
        with self.assertRaises(ValueError):validate_baseline(rows,expected_count=2,expected_unknown=set())
    def test_changed_unknown_membership_cannot_pass_by_histogram(self):
        rows=[dict(case='a',expected=0,rc=0),dict(case='b',expected=0,rc=2)]
        with self.assertRaises(ValueError):validate_baseline(rows,expected_count=2,expected_unknown={'a'})
    def test_native_crash_is_not_a_failed_test(self):
        self.assertFalse(native_target_valid(-9,'test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s'))
    def test_native_summary_must_account_for_all_tests(self):
        self.assertFalse(native_target_valid(0,'running 2 tests\ntest a ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s'))
    def test_timeout_kills_descendants(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/'survived'
            child="import time,pathlib;time.sleep(.4);pathlib.Path("+repr(str(marker))+").write_text('bad')"
            parent="import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',"+repr(child)+"]);time.sleep(5)"
            result=run_group([sys.executable,'-c',parent],timeout=.15,capture_output=True)
            self.assertEqual(result.returncode,124)
            time.sleep(.5)
            self.assertFalse(marker.exists())

if __name__=='__main__':unittest.main()
