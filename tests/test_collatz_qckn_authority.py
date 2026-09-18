import unittest

from collatz_qckn.adapter import CollatzAdapter
from collatz_qckn.authority import Authority
from collatz_qckn.types import Capability


class AuthorityTest(unittest.TestCase):
    def setUp(self):
        self.adapter=CollatzAdapter(contract_digest="contract-v1")
        self.authority=Authority(contract_digest="contract-v1",verifier="collatz-exact-v1")

    def test_valid_macro_verifies_independently(self):
        cap,witness=self.adapter.propose_forward_macro(7,7,((1,2,1),),"train")
        ev=self.authority.verify(cap,witness)
        self.assertTrue(ev.valid)
        self.assertEqual(ev.capability_id,cap.semantic_id)

    def test_altered_word_fails_replay(self):
        cap,witness=self.adapter.propose_forward_macro(7,7,((1,2,1),),"train")
        bad=Capability(**{**cap.as_dict(),"payload":{**cap.payload,"word":[[1,1,1]]}})
        ev=self.authority.verify(bad,witness)
        self.assertFalse(ev.valid)

    def test_stale_contract_fails(self):
        cap,witness=self.adapter.propose_forward_macro(7,7,((1,2,1),),"train")
        bad=Capability(**{**cap.as_dict(),"contract_digest":"stale"})
        ev=self.authority.verify(bad,witness)
        self.assertFalse(ev.valid)
        self.assertIn("contract",ev.reason)


if __name__=="__main__":
    unittest.main()
