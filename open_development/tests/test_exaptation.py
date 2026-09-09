import unittest

from open_development.exaptation import qualify


class ProspectiveExaptationTests(unittest.TestCase):
    def test_requalification_opens_causal_heldout_lineage(self):
        result = qualify()
        self.assertEqual(result["outcome"], "VERIFIED_EXAPTATION")
        self.assertEqual(result["classification"],
                         {"reuse": False, "exaptation": True, "expansion": False})
        self.assertEqual(result["cold_boundary"], "unknown")
        self.assertEqual(result["cold_residual"], "ROLE_REQUALIFICATION_REQUIRED")
        self.assertEqual(result["heldout_zero_acquisition_budget"], "verified")
        self.assertEqual(result["heldout_execution_trace"],
                         [result["K_C"], result["K_B"], result["source_A"]["id"]])
        self.assertTrue(result["source_distinct_realization"]["same_behavioral_class"])
        self.assertTrue(result["source_distinct_realization"]["not_available_to_developer"])
        self.assertEqual(result["controls"]["missing_source_body"], "unknown")
        self.assertEqual(result["controls"]["unrelated_capability_removal"], "verified")
        self.assertEqual(result["controls"]["raw_history_only_same_budget"], "unknown")
        self.assertEqual(result["controls"]["restored_requalified_lineage"], "verified")


if __name__ == "__main__":
    unittest.main()
