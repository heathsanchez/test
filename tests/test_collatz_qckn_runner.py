import unittest

from collatz_qckn.adapter import CollatzAdapter
from collatz_qckn.authority import Authority
from collatz_qckn.compiled_present import CompiledPresent
from collatz_qckn.ledger import CausalLedger
from collatz_qckn.runner import run_arm, sham_present


class RunnerTest(unittest.TestCase):
    def fixture(self):
        adapter=CollatzAdapter("contract")
        authority=Authority("contract","verifier")
        cap,w=adapter.propose_forward_macro(7,7,((1,2,1),),"training")
        ev=authority.verify(cap,w)
        ledger=CausalLedger(); ledger.promote(cap,ev)
        present=CompiledPresent.from_text(CompiledPresent.compile(ledger).to_text())
        future=({"source":11,"start_m":7},)
        return adapter,authority,cap,ledger,present,future

    def test_restarted_warm_reuses_with_zero_discovery(self):
        adapter,authority,cap,ledger,present,future=self.fixture()
        warm=run_arm("WARM",adapter,future,present=present)
        self.assertEqual(warm.authoritative_hits,1)
        self.assertEqual(warm.discovery_calls,0)

    def test_raw_history_is_not_active_memory(self):
        adapter,authority,cap,ledger,present,future=self.fixture()
        raw=run_arm("RAW_HISTORY",adapter,future,raw_history=(cap,))
        self.assertEqual(raw.authoritative_hits,0)

    def test_sham_same_shape_has_no_authoritative_hit(self):
        adapter,authority,cap,ledger,present,future=self.fixture()
        sham=run_arm("SHAM",adapter,future,present=sham_present(present))
        self.assertEqual(len(sham_present(present).capabilities),len(present.capabilities))
        self.assertEqual(sham.authoritative_hits,0)

    def test_ancestor_ablation_restores_cold_active_behavior(self):
        adapter,authority,cap,ledger,present,future=self.fixture()
        cold=run_arm("COLD",adapter,future)
        ledger.revoke(cap.semantic_id,"ancestor ablation")
        ablated=CompiledPresent.from_text(CompiledPresent.compile(ledger).to_text())
        arm=run_arm("ANCESTOR_ABLATION",adapter,future,present=ablated)
        self.assertEqual(arm.authoritative_hits,cold.authoritative_hits)
        self.assertEqual(arm.active_capabilities,0)


if __name__=="__main__":
    unittest.main()
