import json
from pathlib import Path
import tempfile
import unittest

from open_development import (Developer, EvidenceStore, Obligation,
                              ProofCompositionAdapter)

STAGES = json.loads((Path(__file__).resolve().parents[1] / "examples/proof.json").read_text())["stages"]


class CompositionGrowthTests(unittest.TestCase):
    def obligation(self, stage, budget):
        return Obligation("proof-composition", stage, budget, "method")

    def test_three_generation_constructor_program_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "growth.sqlite"
            store = EvidenceStore(path)
            adapter = ProofCompositionAdapter()
            # Matched cold crystal: O2 cannot be reached even with search budget.
            cold = Developer(store, adapter).run(self.obligation(STAGES[1], 0))
            self.assertEqual(cold.verdict, "unknown")
            first = Developer(store, adapter).run(self.obligation(STAGES[0], 2))
            self.assertEqual(first.verdict, "verified")
            self.assertEqual(len(first.retained), 2)
            store.close()

            # The retained constructor builds a distinct O2 program, which is
            # independently admitted as C2 and depends on C1.
            store = EvidenceStore(path)
            warm = Developer(store, adapter).run(self.obligation(STAGES[1], 1))
            self.assertEqual(warm.verdict, "verified")
            self.assertEqual(len(warm.retained), 1)
            self.assertEqual(warm.evidence.certificate["program"]["kind"], "product")
            c2 = store.state()["capabilities"][warm.retained[0]]
            self.assertEqual(c2["repair"]["dependencies"], [first.retained[0]])

            # Unlisted O3 reuses C2 after another restart with no acquisition.
            third = {"polynomial": {"0": "-6", "1": "5", "2": "-1"},
                     "domain": ["interval", "2", "3"]}
            store.close()
            store = EvidenceStore(path)
            reuse = Developer(store, adapter).run(self.obligation(third, 0))
            self.assertEqual(reuse.verdict, "verified")
            self.assertEqual(reuse.retained, ())
            self.assertEqual(reuse.evidence.certificate["retained_program"], warm.retained[0])

            removed = store.revoke(first.retained[0], "constructor ancestry ablation")
            self.assertEqual(set(removed), set(first.retained + warm.retained))
            again = Developer(store, adapter).run(self.obligation(third, 0))
            self.assertEqual(again.verdict, "unknown")
            store.close()

    def test_unreachable_outside_bounded_composition(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp) / "unknown.sqlite")
            adapter = ProofCompositionAdapter()
            target = {"polynomial": {"0": "-1", "3": "1"}, "domain": ["ray"]}
            result = Developer(store, adapter).run(self.obligation(target, 1))
            self.assertEqual(result.verdict, "unknown")
            self.assertEqual(result.retained, ())
            store.close()

    def test_constructor_authority_is_source_bound(self):
        adapter = ProofCompositionAdapter()
        self.assertTrue(adapter.verifier_id.startswith("exact-proof-program-replay-v1:"))
        self.assertEqual(len(adapter.verifier_id.rsplit(":", 1)[1]), 64)

    def test_program_cannot_claim_an_unrelated_dependency(self):
        from open_development import CapabilityContract, Repair
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp) / "dependency.sqlite")
            adapter = ProofCompositionAdapter()
            first = Developer(store, adapter).run(self.obligation(STAGES[0], 1))
            self.assertEqual(len(first.retained), 1)  # constructor only at this budget
            forged = Repair("capability", "forged", {"program_shape": "product(monomial,square)"},
                            adapter.name, ("unrelated",), adapter.program_contract)
            evidence = adapter.verify(store.state(), self.obligation(STAGES[0], 1), forged)
            self.assertEqual(evidence.verdict, "refuted")
            wrong_type = Repair("capability", "wrong-type",
                                {"program_shape": "product(monomial,square)"}, adapter.name,
                                (first.retained[0],),
                                CapabilityContract("Wrong", "Wrong", "Wrong", "Wrong"))
            evidence = adapter.verify(store.state(), self.obligation(STAGES[0], 1), wrong_type)
            self.assertEqual(evidence.verdict, "refuted")
            store.close()
