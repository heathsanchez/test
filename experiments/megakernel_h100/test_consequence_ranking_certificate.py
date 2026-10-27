"""CPU-only positive, negative and mutation controls for conditional rank theorem."""
import copy
import unittest

from consequence_ranking_certificate import certify
from test_independent_consequence_assurance import fixture


class RankingCertificateTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def test_positive_all_six(self):
        r = certify(self.data)
        self.assertEqual(r["cases_checked"], 6)
        self.assertEqual(r["cases_with_sufficient_ranking_margin"], 6)
        self.assertFalse(r["raw_full_tensor_independently_replayed"])

    def test_one_sided_proof_stronger_than_two_epsilon(self):
        case = self.data["checks"]["seed0_rr"]
        case["fields"]["logits"]["max_abs_diff"] = 0.06
        r = certify(self.data)["cases"]["seed0_rr"]
        self.assertTrue(r["conditional_stability_certificate"])
        self.assertFalse(r["conservative_two_epsilon_test"])

    def test_insufficient_margin_stays_unknown(self):
        case = self.data["checks"]["seed0_rr"]
        case["fields"]["logits"]["max_abs_diff"] = 0.15
        r = certify(self.data)["cases"]["seed0_rr"]
        self.assertFalse(r["conditional_stability_certificate"])
        self.assertTrue(r["observed_top1_equal"])

    def test_inconsistent_token_label_rejected(self):
        case = self.data["checks"]["seed0_rr"]["logit_choice"]
        case["top1_equal"] = False
        with self.assertRaises(ValueError): certify(self.data)

    def test_forged_global_error_below_witness_rejected(self):
        case = self.data["checks"]["seed21_rr"]["fields"]["hidden_states"]
        case["max_abs_diff"] = 0.02
        with self.assertRaises(ValueError): certify(self.data)

    def test_missing_scheduler_pair_rejected(self):
        del self.data["checks"]["seed21_dag"]
        with self.assertRaises(ValueError): certify(self.data)


if __name__ == "__main__":
    unittest.main()
