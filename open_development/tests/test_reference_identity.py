from pathlib import Path
import tempfile
import unittest

from open_development import (Developer, EvidenceStore, Obligation,
                              ReferenceIdentityAdapter)
from open_development.reference_identity import (TARGET, candidate_passes, candidates,
                                                 decode_graph, graph_observation,
                                                 oracle_roundtrip, unique_survivors)


SOURCE = {"labels": ["root", "same", "same", "shared"],
          "edges": [[1, 2], [3], [3], [0]], "root": 0}
TRANSFER = {"labels": ["entry", "left", "right", "loop"],
            "edges": [[1, 2], [3], [3], [3]], "root": 0}
DEPENDENT = {"labels": ["r", "a", "b", "sink"],
             "edges": [[1, 2], [2], [1, 3], [3]], "root": 0}
HELDOUT = {"labels": ["p", "q", "r", "u", "v"],
           "edges": [[1], [2], [0, 3], [4], [3]], "root": 0}
HELDOUT_FORK = {"labels": ["root", "left", "right"],
                "edges": [[1, 2], [], []], "root": 0}


class ReferenceIdentityIntegrationTests(unittest.TestCase):
    def obligation(self, target, budget):
        return Obligation("reference-identity", target, budget, "method")

    def test_frozen_low_level_grammar_has_unique_survivor(self):
        self.assertEqual(len(candidates()), 12)
        self.assertEqual(unique_survivors(), (TARGET,))
        self.assertTrue(candidate_passes(TARGET))
        self.assertFalse(candidate_passes(("identity", "none", False)))
        self.assertFalse(candidate_passes(("tag", "preorder", True)))
        self.assertFalse(candidate_passes(("identity", "postorder", True)))

    def test_independent_stdlib_oracles_preserve_frozen_observation(self):
        for spec, oracle in ((SOURCE, "pickle-protocol-5"), (TRANSFER, "deepcopy")):
            source = decode_graph(spec)
            self.assertEqual(graph_observation(oracle_roundtrip(source, oracle)),
                             graph_observation(source))

    def test_constructor_persists_enables_scc_and_cascades_on_revoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reference.sqlite"
            adapter = ReferenceIdentityAdapter()
            store = EvidenceStore(path)
            source = {"task": "source", "oracle": "pickle-protocol-5", "graph": SOURCE}
            cold = Developer(store, adapter).run(self.obligation(source, 0))
            self.assertEqual(cold.verdict, "unknown")
            self.assertEqual(cold.evidence.residual["class"], "REFERENCE_FORM_MISSING")
            acquired = Developer(store, adapter).run(self.obligation(source, 12))
            self.assertEqual(acquired.verdict, "verified")
            self.assertEqual(len(acquired.retained), 1)
            constructor = acquired.retained[0]
            store.close()

            store = EvidenceStore(path)
            transfer = Developer(store, adapter).run(self.obligation(
                {"task": "transfer", "oracle": "deepcopy", "graph": TRANSFER}, 0))
            self.assertEqual(transfer.verdict, "verified")
            dependent = Developer(store, adapter).run(self.obligation(
                {"task": "acquire-scc", "graph": DEPENDENT, "expected": [1, 1, 2]}, 1))
            self.assertEqual(dependent.verdict, "verified")
            self.assertEqual(len(dependent.retained), 1)
            procedure = dependent.retained[0]
            self.assertEqual(store.state()["capabilities"][procedure]["repair"]["dependencies"],
                             [constructor])
            store.close()

            lineage = []
            stages = [
                ("acquire-condensation", (3, [(0, 1), (1, 2)])),
                ("acquire-generations", [[0], [1], [2]]),
                ("acquire-semiconnected", True),
            ]
            for task, expected in stages:
                store = EvidenceStore(path)
                result = Developer(store, adapter).run(self.obligation(
                    {"task": task, "graph": DEPENDENT, "expected": expected}, 1))
                self.assertEqual(result.verdict, "verified")
                self.assertEqual(len(result.retained), 1)
                lineage.extend(result.retained)
                store.close()

            store = EvidenceStore(path)
            heldout = Developer(store, adapter).run(self.obligation(
                {"task": "heldout-scc", "graph": HELDOUT, "expected": [2, 3]}, 0))
            self.assertEqual(heldout.verdict, "verified")
            self.assertEqual(heldout.retained, ())
            heldout_lineage = Developer(store, adapter).run(self.obligation(
                {"task": "heldout-semiconnected", "graph": HELDOUT_FORK,
                 "expected": False}, 0))
            self.assertEqual(heldout_lineage.verdict, "verified")
            removed = store.revoke(constructor, "reference constructor ancestor ablation")
            self.assertEqual(set(removed), {constructor, procedure, *lineage})
            again = Developer(store, adapter).run(self.obligation(
                {"task": "heldout-scc", "graph": HELDOUT, "expected": [2, 3]}, 0))
            self.assertEqual(again.verdict, "unknown")
            again_lineage = Developer(store, adapter).run(self.obligation(
                {"task": "heldout-semiconnected", "graph": HELDOUT_FORK,
                 "expected": False}, 0))
            self.assertEqual(again_lineage.verdict, "unknown")
            store.close()


if __name__ == "__main__":
    unittest.main()
