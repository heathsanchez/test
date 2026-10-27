"""Independent mutation controls for observed top-1 error-envelope warrants."""
import copy
import unittest
from top1_decision_warrant import PIN, qualify


def synthetic_report():
    return {
        "source_pin": PIN, "sm_count": 132, "runpod_status": "COMPLETED",
        "checks": {"rr_16": {
            "source_commit": PIN, "fixture_layers": 16, "executed_layers": 16,
            "lm_head_exercised": True, "pyvm_completed_calls": 1,
            "logit_choice": {"reference_top1": 7, "native_top1": 7, "reference_top1_margin": 0.10},
            "fields": {"logits": {"elements": 128256, "nonfinite": 0,
                                   "max_abs_diff": 0.03, "violations": 12}},
        }}
    }


class DecisionWarrantTests(unittest.TestCase):
    def test_bound_proves_observation_specific_action_stability(self):
        c = qualify(synthetic_report(), "rr_16")
        self.assertEqual(c["status"], "BOUNDED_ENVELOPE_STABILITY_CERTIFIED")
        self.assertEqual(c["required_margin_strictly_greater_than"], 0.06)
        self.assertFalse(c["future_input_guarantee"])

    def test_matching_token_is_not_automatically_certified(self):
        r = synthetic_report()
        r["checks"]["rr_16"]["fields"]["logits"]["max_abs_diff"] = 0.06
        self.assertEqual(qualify(r, "rr_16")["status"], "OBSERVED_MATCH_ENVELOPE_INCONCLUSIVE")

    def test_equality_at_bound_not_admitted(self):
        r = synthetic_report()
        r["checks"]["rr_16"]["logit_choice"]["reference_top1_margin"] = 0.06
        self.assertEqual(qualify(r, "rr_16")["status"], "OBSERVED_MATCH_ENVELOPE_INCONCLUSIVE")

    def test_different_top_token_is_rejected(self):
        r = synthetic_report()
        r["checks"]["rr_16"]["logit_choice"]["native_top1"] = 8
        self.assertEqual(qualify(r, "rr_16")["status"], "REJECTED_ACTION_DISAGREEMENT")

    def test_wrong_pin_no_warrant(self):
        r = synthetic_report()
        r["source_pin"] = "0" * 40
        self.assertEqual(qualify(r, "rr_16")["status"], "UNKNOWN_RUN_PROVENANCE")

    def test_unexecuted_reference_no_warrant(self):
        r = synthetic_report()
        r["checks"]["rr_16"]["pyvm_completed_calls"] = 0
        self.assertEqual(qualify(r, "rr_16")["status"], "UNKNOWN_REFERENCE_UNEXECUTED")

    def test_partial_layer_not_full_model_warrant(self):
        r = synthetic_report()
        r["checks"]["rr_16"]["executed_layers"] = 8
        self.assertEqual(qualify(r, "rr_16")["status"], "UNKNOWN_NOT_FULL_LMHEAD_SCOPE")

    def test_nonfinite_no_warrant(self):
        r = synthetic_report()
        r["checks"]["rr_16"]["fields"]["logits"]["nonfinite"] = 1
        self.assertEqual(qualify(r, "rr_16")["status"], "UNKNOWN_NONFINITE")

    def test_missing_and_invalid_evidence_no_warrant(self):
        r = synthetic_report()
        del r["checks"]["rr_16"]["logit_choice"]
        self.assertEqual(qualify(r, "rr_16")["status"], "UNKNOWN_NO_LOGIT_OBSERVATION")
        r = synthetic_report()
        r["checks"]["rr_16"]["fields"]["logits"]["max_abs_diff"] = float("nan")
        self.assertEqual(qualify(r, "rr_16")["status"], "UNKNOWN_INVALID_NUMERIC_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
