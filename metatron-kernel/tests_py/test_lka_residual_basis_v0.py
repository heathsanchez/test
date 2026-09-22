import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "lka_residual_basis_v0.py"
spec = importlib.util.spec_from_file_location("lka_residual_basis_v0", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class ResidualBasisTests(unittest.TestCase):
    def test_exact_min_cover_prefers_smallest_lexicographic_basis(self):
        # Universe {0,1,2}; a+b covers all in two, c+d also covers in two.
        edges = {
            "a": 0b011,
            "b": 0b100,
            "c": 0b101,
            "d": 0b010,
        }
        basis = mod.exact_min_cover(3, edges)
        self.assertEqual(basis, ["a", "b"])

    def test_discordant_pairs_are_same_current_different_target(self):
        dummy = Path("/tmp/x")
        cases = [
            mod.Case(1, dummy, 0, 2, {}),
            mod.Case(2, dummy, 1, 2, {}),
            mod.Case(3, dummy, 0, 0, {}),
            mod.Case(4, dummy, 1, 1, {}),
        ]
        self.assertEqual(mod.discordant_pairs(cases), [(0, 1)])

    def test_feature_observation_separates_residual(self):
        dummy = Path("/tmp/x")
        cases = [
            mod.Case(1, dummy, 0, 2, {"f": "left", "g": 1}),
            mod.Case(2, dummy, 1, 2, {"f": "right", "g": 1}),
        ]
        pairs = mod.discordant_pairs(cases)
        edges = mod.candidate_edges(cases, pairs, ["f", "g"])
        self.assertEqual(edges["f"], 1)
        self.assertNotIn("g", edges)
        self.assertEqual(mod.exact_min_cover(1, mod.dedupe_edges(edges)), ["f"])

    def test_blind_ids_hide_feature_names(self):
        dummy = Path("/tmp/x")
        cases = [
            mod.Case(1, dummy, 0, 2, {"secret_semantic_name": 0}),
            mod.Case(2, dummy, 1, 2, {"secret_semantic_name": 1}),
        ]
        public, hidden = mod.build_public_hidden(cases, ["secret_semantic_name"])
        blob = mod.canonical(public)
        self.assertNotIn("secret_semantic_name", blob)
        self.assertIn("secret_semantic_name", mod.canonical(hidden))
        self.assertEqual(public["commitment"], mod.digest(hidden))

    def test_sham_preserves_current_class_marginals(self):
        dummy = Path("/tmp/x")
        cases = [
            mod.Case(1, dummy, 0, 2, {"f": 0}),
            mod.Case(2, dummy, 1, 2, {"f": 1}),
            mod.Case(3, dummy, 0, 2, {"f": 2}),
        ]
        sham = mod.deterministic_sham(cases, ["f"])
        self.assertEqual(
            sorted(c.features["f"] for c in cases),
            sorted(c.features["f"] for c in sham),
        )


if __name__ == "__main__":
    unittest.main()
