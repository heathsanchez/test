import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "lka_residual_basis_v0.py"
spec = importlib.util.spec_from_file_location("lka_residual_basis_v0", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
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

    def test_symbolic_universe_order(self):
        zero = ("zero",)
        u = ("param", 7)
        self.assertTrue(mod.level_lt_term(zero, ("succ", zero)))
        self.assertTrue(mod.level_lt_term(u, ("succ", u)))
        self.assertFalse(mod.level_lt_term(u, u))

    def test_field_universe_prop_is_impredicative(self):
        records = [
            {"ie": 1, "sort": 0},
            {"ie": 2, "sort": 3},
            {"ie": 3, "sort": 0},
            {"ie": 4, "const": {"name": 10, "us": []}},
            {"ie": 5, "forallE": {"type": 2, "body": 4}},
            {"il": 3, "succ": 0},
            {
                "inductive": {
                    "types": [{
                        "name": 10, "type": 1, "numParams": 0, "numIndices": 0,
                        "levelParams": [], "ctors": [11], "all": [10],
                        "numNested": 0, "isRec": False, "isUnsafe": False,
                        "isReflexive": False
                    }],
                    "ctors": [{
                        "name": 11, "type": 5, "numParams": 0, "numFields": 1,
                        "levelParams": [], "induct": 10, "cidx": 0, "isUnsafe": False
                    }],
                    "recs": []
                }
            },
        ]
        exprs = mod.expr_refs(records)
        levels = mod.level_refs(records)
        self.assertEqual(
            mod.field_universe_admissibility(records, exprs, levels),
            "not_applicable",
        )

    def test_field_universe_same_level_type_is_refuted(self):
        records = [
            {"ie": 1, "sort": 3},
            {"ie": 2, "sort": 3},
            {"ie": 4, "const": {"name": 10, "us": []}},
            {"ie": 5, "forallE": {"type": 2, "body": 4}},
            {"il": 3, "succ": 0},
            {
                "inductive": {
                    "types": [{
                        "name": 10, "type": 1, "numParams": 0, "numIndices": 0,
                        "levelParams": [], "ctors": [11], "all": [10],
                        "numNested": 0, "isRec": False, "isUnsafe": False,
                        "isReflexive": False
                    }],
                    "ctors": [{
                        "name": 11, "type": 5, "numParams": 0, "numFields": 1,
                        "levelParams": [], "induct": 10, "cidx": 0, "isUnsafe": False
                    }],
                    "recs": []
                }
            },
        ]
        exprs = mod.expr_refs(records)
        levels = mod.level_refs(records)
        self.assertEqual(
            mod.field_universe_admissibility(records, exprs, levels),
            "refuted",
        )

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
