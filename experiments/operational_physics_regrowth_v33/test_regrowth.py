import os
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(__file__))

from core import discover_positivity, discover_parallel_product, discover_sequential_algebra, run_all


class PositivityRegrowthTests(unittest.TestCase):
    def test_composition_failure_forces_full_principal_minor_rule(self):
        r = discover_positivity()
        self.assertEqual(r["selected_rule"], "all_principal_minors_nonnegative")
        self.assertGreaterEqual(r["composition_residual_count"], 1)
        w = r["residuals"][0]
        self.assertLess(Fraction(w["joint_weight"]), 0)
        self.assertTrue(w["candidate_passes_local_subset_tests"])
        self.assertTrue(w["candidate_passes_proper_principal_minors"])
        self.assertFalse(w["candidate_passes_all_principal_minors"])

    def test_positivity_ablation_admits_bad_model(self):
        r = discover_positivity()
        self.assertTrue(r["ablation_local_only_admits_counterexample"])
        self.assertTrue(r["positive_controls_preserved"])


class ParallelProductTests(unittest.TestCase):
    def test_operational_laws_force_unique_product(self):
        r = discover_parallel_product()
        self.assertEqual(r["survivor_count"], 1)
        self.assertEqual(r["selected_coefficients"], [0, 0, 0, 1])
        self.assertEqual(r["selected_formula"], "a*b")
        self.assertTrue(r["associative_on_probe_set"])
        self.assertTrue(r["kronecker_basis_replay"])

    def test_removing_null_law_restores_alternatives(self):
        r = discover_parallel_product()
        self.assertGreater(r["ablation_without_null_laws_survivor_count"], 1)


class SequentialRegrowthTests(unittest.TestCase):
    def test_order_sensitive_future_forces_full_linear_operator_family(self):
        r = discover_sequential_algebra()
        self.assertEqual(r["selected_family"], "full_2d_linear")
        self.assertTrue(r["order_sensitive"])
        self.assertNotEqual(r["AB_signature"], r["BA_signature"])
        self.assertFalse(r["scalar_family_sufficient"])
        self.assertFalse(r["diagonal_family_sufficient"])
        self.assertTrue(r["full_family_sufficient"])

    def test_sequential_result_does_not_claim_quantum_algebra(self):
        r = discover_sequential_algebra()
        self.assertFalse(r["quantum_algebra_forced"])
        self.assertIn("not forced", r["frontier"].lower())


class AggregateTests(unittest.TestCase):
    def test_aggregate_verdict(self):
        r = run_all()
        self.assertEqual(r["verdict"], "PASS_BOUNDED_OPERATIONAL_REGROWTH_V33")
        self.assertEqual(r["forced"], [
            "positive_semidefinite_pairing_rule",
            "multiplicative_parallel_product",
            "noncommutative_linear_sequential_operators",
        ])
        self.assertIn("Born", r["not_derived"])
        self.assertIn("complex Hilbert space", r["not_derived"])


if __name__ == "__main__":
    unittest.main()
