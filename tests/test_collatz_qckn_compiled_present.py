import unittest

from collatz_qckn.adapter import CollatzAdapter
from collatz_qckn.authority import Authority
from collatz_qckn.compiled_present import CompiledPresent
from collatz_qckn.ledger import CausalLedger


class CompiledPresentTest(unittest.TestCase):
    def make_ledger(self):
        adapter=CollatzAdapter("contract")
        auth=Authority("contract","verifier")
        cap,w=adapter.propose_forward_macro(7,7,((1,2,1),),"raw-history-should-not-serialize")
        ev=auth.verify(cap,w)
        ledger=CausalLedger(); ledger.promote(cap,ev)
        return ledger,cap

    def test_canonical_roundtrip_and_digest(self):
        ledger,cap=self.make_ledger()
        present=CompiledPresent.compile(ledger)
        text=present.to_text()
        restored=CompiledPresent.from_text(text)
        self.assertEqual(restored.to_text(),text)
        self.assertEqual(restored.digest,present.digest)
        self.assertEqual(
            tuple(x.semantic_id for x in restored.capabilities),
            (cap.semantic_id,),
        )
        self.assertEqual(restored.capabilities[0].payload,cap.payload)

    def test_raw_provenance_is_not_active_serialized_history(self):
        ledger,_=self.make_ledger()
        text=CompiledPresent.compile(ledger).to_text()
        self.assertNotIn("raw-history-should-not-serialize",text)

    def test_revoked_capability_absent_after_restart(self):
        ledger,cap=self.make_ledger()
        ledger.revoke(cap.semantic_id,"ablation")
        restored=CompiledPresent.from_text(CompiledPresent.compile(ledger).to_text())
        self.assertEqual(restored.capabilities,())

    def test_insertion_order_does_not_change_text(self):
        adapter=CollatzAdapter("contract")
        auth=Authority("contract","verifier")
        c1,w1=adapter.propose_forward_macro(7,7,((1,2,1),),"p1")
        c2,w2=adapter.propose_forward_macro(15,1,((4,4,1),),"p2")
        e1=auth.verify(c1,w1); e2=auth.verify(c2,w2)
        a=CausalLedger(); a.promote(c1,e1); a.promote(c2,e2)
        b=CausalLedger(); b.promote(c2,e2); b.promote(c1,e1)
        self.assertEqual(CompiledPresent.compile(a).to_text(),
                         CompiledPresent.compile(b).to_text())


if __name__=="__main__":
    unittest.main()
