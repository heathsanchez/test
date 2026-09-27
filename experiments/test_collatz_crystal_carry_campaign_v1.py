import importlib.util,pathlib,unittest
P=pathlib.Path(__file__).with_name("collatz_crystal_carry_campaign_v1.py")
S=importlib.util.spec_from_file_location("campaign",P); c=importlib.util.module_from_spec(S); S.loader.exec_module(c)
class CampaignTests(unittest.TestCase):
 def test_fixed21_is_rejected_fixture(self):
  x=c.synthetic_late_singleton_fixture()
  self.assertGreater(x["wait"],21)
 def test_adaptive_state_is_not_promoted_from_observed_exit(self):
  self.assertFalse(c.promotion_allowed({"derivation":"next_observed_exit"}))
 def test_bad_graph_requires_exact_successors(self):
  with self.assertRaises(AssertionError): c.bad_kernel([{"id":"x","successors":None}])
 def test_empty_finite_bad_kernel_is_not_universal(self):
  self.assertEqual(c.epistemic_status(True,False),"BOUNDED_BAD_KERNEL_EMPTY")
if __name__=="__main__":unittest.main()
