"""Mutation tests for independent H100 depth-report audit, no GPU needed."""
import copy
import json
import unittest

from independent_depth_assurance import audit, no_duplicate_keys, PIN, PLAN, ELEMENTS, TOLERANCE


def sample_report():
    checks = {}
    for key in PLAN:
        depth = int(key.split("_")[1])
        fields = ("hidden_states", "k_cache", "v_cache") + (("logits",) if depth == 16 else ())
        failures = []
        metrics = {}
        for name in fields:
            nbad = 0
            if depth >= 12 and name == "hidden_states":
                nbad = 3
            if depth == 16 and name == "logits":
                nbad = 2
            row = {"elements": ELEMENTS[name], "violations": nbad,
                   "nonfinite": 0, "max_abs_diff": 0.1 if nbad else 0.01}
            if nbad:
                row["first_violations"] = [
                    {"flat_index": 0, "reference": 0.2, "gpu": 0.3,
                     "abs_error": 0.1, "allowed_error": 0.07}]
                failures.append("mismatch:" + name)
            metrics[name] = row
        checks[key] = {
            "source_commit": PIN, "tracked_worktree_clean": True,
            "fixture_layers": 16, "executed_layers": depth,
            "lm_head_exercised": depth == 16,
            "fields_compared": list(fields),
            "tolerances": dict(TOLERANCE),
            "pyvm_completed_calls": 1, "fields": metrics,
            "reasons": failures, "passed": not bool(failures),
            "logit_choice": ({"reference_top1": 7, "native_top1": 7,
                              "top1_equal": True, "reference_top1_margin": 0.2}
                             if depth == 16 else None),
        }
    return {"schema": "mathgraph-h100-differential-v1",
            "status": "DIAGNOSTIC_RECORDED", "probe_kind": "depth_diagnostic",
            "source_pin": PIN, "gpu_name": "NVIDIA H100 80GB HBM3",
            "sm_count": 132, "runpod_status": "COMPLETED", "runpod_job_id": "sample-job",
            "diagnostic_plan": list(PLAN), "checks": checks}


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.report = sample_report()

    def test_consistent_report(self):
        out = audit(self.report)
        self.assertEqual(out["cases_checked"], 7)
        self.assertEqual(out["first_observed_rr_failure_depth"], 12)
        self.assertTrue(out["full16_top1_equal"]["dag_16"])
        self.assertIn("NOT_RAW", out["status"])

    def test_source_pin_mutation(self):
        self.report["source_pin"] = "0" * 40
        with self.assertRaises(ValueError): audit(self.report)

    def test_wrong_tolerance(self):
        self.report["checks"]["rr_12"]["tolerances"]["atol"] = 0.2
        with self.assertRaises(ValueError): audit(self.report)

    def test_false_pass_rejected(self):
        self.report["checks"]["rr_12"]["passed"] = True
        with self.assertRaises(ValueError): audit(self.report)

    def test_missing_case_rejected(self):
        del self.report["checks"]["dag_16"]
        with self.assertRaises(ValueError): audit(self.report)

    def test_replayed_coverage_rejected(self):
        self.report["checks"]["rr_8"]["executed_layers"] = 4
        with self.assertRaises(ValueError): audit(self.report)

    def test_forged_top1_label_rejected(self):
        self.report["checks"]["dag_16"]["logit_choice"]["native_top1"] = 11
        with self.assertRaises(ValueError): audit(self.report)

    def test_bad_witness_arithmetic(self):
        self.report["checks"]["rr_12"]["fields"]["hidden_states"]["first_violations"][0]["abs_error"] = 0.01
        with self.assertRaises(ValueError): audit(self.report)

    def test_missing_witness(self):
        del self.report["checks"]["rr_12"]["fields"]["hidden_states"]["first_violations"]
        with self.assertRaises(ValueError): audit(self.report)

    def test_forged_witness_allowance_rejected(self):
        self.report["checks"]["rr_12"]["fields"]["hidden_states"]["first_violations"][0]["allowed_error"] = 0.06
        with self.assertRaises(ValueError): audit(self.report)

    def test_out_of_range_top_token_rejected(self):
        choice = self.report["checks"]["dag_16"]["logit_choice"]
        choice["reference_top1"] = 128256
        choice["native_top1"] = 128256
        with self.assertRaises(ValueError): audit(self.report)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"a":1,"a":2}', object_pairs_hook=no_duplicate_keys)


if __name__ == "__main__":
    unittest.main()
