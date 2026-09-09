import tempfile
import unittest
from pathlib import Path

from open_development.external_minif2f_entry import (
    ExternalMiniF2FAdapter, extract_candidates, freeze_source,
)
from open_development.runtime import Developer, EvidenceStore, Obligation


VALID_SPLIT_EXAMPLE = """
theorem algebra_binomnegdiscrineq_10alt28asqp1 (a : ℝ) : 10 * a ≤ 28 * a ^ 2 + 1 := by
  sorry
"""

SYNTHETIC_HELDOUT = """
theorem synthetic_global_quadratic (x : ℝ) : 4 * x ≤ 4 * x ^ 2 + 1 := by
  sorry
"""


class ExternalMiniF2FProtocolTests(unittest.TestCase):
    def test_validation_split_parser_is_narrow_and_exact(self):
        candidates = extract_candidates(VALID_SPLIT_EXAMPLE)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["name"], "algebra_binomnegdiscrineq_10alt28asqp1")
        self.assertEqual(candidates[0]["polynomial"], {"0": "1", "1": "-10", "2": "28"})

    def test_frozen_source_can_only_reach_global_task_after_requalification(self):
        train = extract_candidates(VALID_SPLIT_EXAMPLE)[0]
        heldout = extract_candidates(SYNTHETIC_HELDOUT)[0]
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.sqlite"
            frozen = freeze_source(state_path, "a" * 40)
            store = EvidenceStore(state_path)
            adapter = ExternalMiniF2FAdapter(frozen["K_A"], frozen["K_A_fingerprint"])
            cold = Developer(store, adapter).run(Obligation(adapter.name, train, 0, "method"))
            self.assertEqual(cold.verdict, "unknown")
            self.assertEqual(cold.evidence.residual["class"], "GLOBAL_ROLE_REQUALIFICATION_REQUIRED")
            warm = Developer(store, adapter).run(Obligation(adapter.name, train, 2, "method"))
            self.assertEqual(warm.verdict, "verified")
            self.assertEqual(len(warm.retained), 2)
            role, child = warm.retained
            store.close()
            store = EvidenceStore(state_path)
            adapter = ExternalMiniF2FAdapter(frozen["K_A"], frozen["K_A_fingerprint"])
            future = Developer(store, adapter).run(Obligation(adapter.name, heldout, 0, "method"))
            self.assertEqual(future.verdict, "verified")
            self.assertEqual(future.evidence.certificate["execution_trace"],
                             [child, role, frozen["K_A"]])
            store.close()

    def test_parser_rejects_answers_and_multivariable_headers(self):
        text = """
theorem answer_tagged (x : ℝ) : x ^ 2 ≥ answer(0) := by sorry
theorem two_vars (x y : ℝ) : x ^ 2 + y ^ 2 ≥ 0 := by sorry
"""
        self.assertEqual(extract_candidates(text), [])


if __name__ == "__main__":
    unittest.main()
