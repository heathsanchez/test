import unittest

from collatz_qckn.adapter import CollatzAdapter
from collatz_qckn.types import CapabilityKind


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.adapter=CollatzAdapter(contract_digest="contract-v1")

    def test_propose_forward_macro_is_only_a_proposal(self):
        cap,witness=self.adapter.propose_forward_macro(
            source=7, start_m=7, word=((1,2,1),), provenance="train"
        )
        self.assertEqual(cap.kind,CapabilityKind.FORWARD_DESCENT_MACRO)
        self.assertEqual(witness["path_min"],5)
        self.assertLess(witness["path_min"],7)

    def test_apply_capability_replays_exact_path(self):
        cap,_=self.adapter.propose_forward_macro(7,7,((1,2,1),),"train")
        result=self.adapter.apply_capability(cap,source=7,start_m=7)
        self.assertTrue(result["applicable"])
        self.assertEqual(result["path_min"],5)
        self.assertTrue(result["lower_merge"])


if __name__=="__main__":
    unittest.main()
