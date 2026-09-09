from pathlib import Path
import tempfile
import unittest

from open_development import Developer, EvidenceStore, NativeConstructorAdapter, Obligation
from open_development.native_constructor import (TARGET, constructor_candidates,
                                                  old_closure_certificate, unique_survivors)


TREE = {"label": "root", "children": [
    {"label": "b", "children": []},
    {"label": "a", "children": [{"label": "leaf", "children": []}]},
]}


class NativeConstructorIntegrationTests(unittest.TestCase):
    def obligation(self, target, budget):
        return Obligation("native-constructor", target, budget, "method")

    def test_exact_frozen_grammars_replay(self):
        self.assertEqual(old_closure_certificate(), {
            "enumerated": 7882, "maximum_direct_arity": 5,
            "deciding_array_arity": 6, "budget_independent": True})
        self.assertEqual(len(constructor_candidates()), 237)
        self.assertEqual(unique_survivors(), (TARGET,))

    def test_constructor_persists_transfers_and_enables_dependent_acquisition(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "native.sqlite"
            store = EvidenceStore(path)
            adapter = NativeConstructorAdapter()
            source = {"task": "source", "package": "@esri/arcgis-rest-portal@4.11.0"}
            cold = Developer(store, adapter).run(self.obligation(source, 0))
            self.assertEqual(cold.verdict, "unknown")
            self.assertEqual(cold.evidence.residual["class"], "OLD_GRAMMAR_INADEQUATE")
            acquired = Developer(store, adapter).run(self.obligation(source, 237))
            self.assertEqual(acquired.verdict, "verified")
            self.assertEqual(len(acquired.retained), 1)
            constructor = acquired.retained[0]
            store.close()

            store = EvidenceStore(path)
            transfer = Developer(store, adapter).run(self.obligation(
                {"task": "transfer", "package": "tdesign-vue-next@1.20.5"}, 0))
            self.assertEqual(transfer.verdict, "verified")
            fold_task = {"task": "acquire-fold", "tree": TREE, "expected": 4}
            fold = Developer(store, adapter).run(self.obligation(fold_task, 1))
            self.assertEqual(fold.verdict, "verified")
            self.assertEqual(len(fold.retained), 1)
            self.assertEqual(store.state()["capabilities"][fold.retained[0]]["repair"]["dependencies"],
                             [constructor])
            store.close()

            heldout_tree = {"label": "x", "children": [TREE, {"label": "z", "children": []}]}
            store = EvidenceStore(path)
            heldout = Developer(store, adapter).run(self.obligation(
                {"task": "heldout-fold", "tree": heldout_tree, "expected": 6}, 0))
            self.assertEqual(heldout.verdict, "verified")
            removed = store.revoke(constructor, "nested constructor ablation")
            self.assertEqual(set(removed), {constructor, fold.retained[0]})
            again = Developer(store, adapter).run(self.obligation(
                {"task": "heldout-fold", "tree": heldout_tree, "expected": 6}, 0))
            self.assertEqual(again.verdict, "unknown")
            store.close()


if __name__ == "__main__":
    unittest.main()
