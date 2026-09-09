import json
from pathlib import Path
import tempfile
import unittest

from open_development import Developer, EvidenceStore, Obligation, ProofCompositionAdapter

STAGES = json.loads((Path(__file__).resolve().parents[1] / "examples/proof.json").read_text())["stages"]


class CompositionGrowthTests(unittest.TestCase):
    def obligation(self, stage, budget):
        return Obligation("proof-composition", stage, budget, "method")

    def test_first_acquisition_makes_heldout_task_reachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "growth.sqlite"
            store = EvidenceStore(path)
            adapter = ProofCompositionAdapter()
            # Matched cold crystal: O2 cannot be reached even with search budget.
            cold = Developer(store, adapter).run(self.obligation(STAGES[1], 0))
            self.assertEqual(cold.verdict, "unknown")
            first = Developer(store, adapter).run(self.obligation(STAGES[0], 1))
            self.assertEqual(first.verdict, "verified")
            self.assertEqual(len(first.retained), 1)
            store.close()

            # Restarted warm crystal: O2 uses the retained constructor to build
            # a different program, with zero further acquisition budget.
            store = EvidenceStore(path)
            warm = Developer(store, adapter).run(self.obligation(STAGES[1], 0))
            self.assertEqual(warm.verdict, "verified")
            self.assertEqual(warm.retained, ())
            self.assertEqual(warm.evidence.certificate["program"]["kind"], "product")
            removed = store.revoke(first.retained[0], "constructor removal ablation")
            self.assertEqual(removed, first.retained)
            again = Developer(store, adapter).run(self.obligation(STAGES[1], 0))
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
