import unittest

from collatz_qckn.adapter import CollatzAdapter
from collatz_qckn.authority import Authority
from collatz_qckn.ledger import CausalLedger, LedgerConflict, PromotionRejected
from collatz_qckn.types import Capability


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.adapter=CollatzAdapter("contract")
        self.auth=Authority("contract","verifier")
        self.cap,self.witness=self.adapter.propose_forward_macro(7,7,((1,2,1),),"g1")
        self.ev=self.auth.verify(self.cap,self.witness)

    def test_proposal_is_not_active_until_verified_promotion(self):
        ledger=CausalLedger()
        self.assertEqual(ledger.active_capabilities(),())
        ledger.promote(self.cap,self.ev)
        self.assertEqual(ledger.active_capabilities(),(self.cap,))

    def test_invalid_evidence_cannot_promote(self):
        bad=self.auth.verify(Capability(**{**self.cap.as_dict(),"contract_digest":"stale"}),self.witness)
        with self.assertRaises(PromotionRejected):
            CausalLedger().promote(self.cap,bad)

    def test_revocation_removes_capability(self):
        ledger=CausalLedger()
        ledger.promote(self.cap,self.ev)
        ledger.revoke(self.cap.semantic_id,"ablation")
        self.assertEqual(ledger.active_capabilities(),())

    def test_same_identity_conflicting_payload_refused(self):
        ledger=CausalLedger(); ledger.promote(self.cap,self.ev)
        other=Capability(**{**self.cap.as_dict(),"payload":{**self.cap.payload,"note":"conflict"}})
        other_ev=self.auth.verify(other,self.witness)
        self.assertTrue(other_ev.valid)
        with self.assertRaises(LedgerConflict):
            ledger.promote(other,other_ev)

    def test_inactive_dependency_disables_dependent(self):
        ledger=CausalLedger(); ledger.promote(self.cap,self.ev)
        child=Capability(**{**self.cap.as_dict(),
            "guard_digest":"child-guard",
            "dependencies":(self.cap.semantic_id,),
            "payload":{**self.cap.payload,"child":True}})
        # Evidence is synthetic but bound exactly to the child; ledger only checks authority result.
        child_ev=type(self.ev)(
            capability_id=child.semantic_id,payload_digest=child.payload_digest,valid=True,
            authority_digest=self.ev.authority_digest,contract_digest=self.ev.contract_digest,
            verifier=self.ev.verifier,reason="verified",evidence={})
        ledger.promote(child,child_ev)
        self.assertEqual(len(ledger.active_capabilities()),2)
        ledger.revoke(self.cap.semantic_id,"ancestor ablation")
        self.assertEqual(ledger.active_capabilities(),())

    def test_events_have_deterministic_sorted_projection(self):
        a=CausalLedger(); a.promote(self.cap,self.ev)
        self.assertEqual(tuple(sorted(e.event_id for e in a.events())),
                         tuple(e.event_id for e in a.events()))


if __name__=="__main__":
    unittest.main()
