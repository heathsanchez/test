import unittest
from tournament import qualifies, select_winner, INPUT_SHA

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

if __name__=='__main__':unittest.main()
