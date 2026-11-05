import unittest
from receipt_schema import controls_equal
class ReceiptTests(unittest.TestCase):
 def setUp(self):
  self.rich=dict(file='binder-info.ndjson',expected=0,rc=0,sha256='9d9ff9041cd712f86e78c5d2d2d7253bb144321f83dda2d8246b57ec3c8d65b0',pass_=True,stderr='')
  self.legacy=dict(case='nat-original.ndjson',rc=0,pass_=True)
 def test_mixed_real_schemas_compare_independent_of_completion_order(self):
  self.assertTrue(controls_equal([self.rich,self.legacy],[self.legacy,self.rich|dict(stderr='different diagnostics')]))
 def test_changed_verdict_is_not_unchanged(self):
  self.assertFalse(controls_equal([self.legacy],[self.legacy|dict(rc=2)]))
 def test_changed_hashed_input_is_not_unchanged(self):
  self.assertFalse(controls_equal([self.rich],[self.rich|dict(sha256='0'*64)]))
 def test_missing_control_is_not_unchanged(self):
  self.assertFalse(controls_equal([self.rich,self.legacy],[self.rich]))
if __name__=='__main__':unittest.main()
