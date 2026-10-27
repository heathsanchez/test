"""Mutation controls for bounded H100 consequence witness assurance (CPU only)."""
import copy
import hashlib
import json
import unittest
from independent_consequence_assurance import audit, load_json, PIN, PLAN, FIELDS, SIZES, ATOL, RTOL


def fixture():
    checks = {}
    for key in PLAN:
        seed = int(key.split("_")[0][4:])
        sched = key.split("_")[1]
        fields = {}
        failures = []
        for name in FIELDS:
            bad = 1 if name == "hidden_states" and seed == 21 else 0
            m = {"elements": SIZES[name], "nonfinite": 0,
                 "violations": bad, "max_abs_diff": 0.06 if bad else 0.02}
            if bad:
                m["first_violations"] = [{
                    "flat_index": 17, "reference": 0.0, "gpu": 0.06,
                    "abs_error": 0.06, "allowed_error": 0.05
                }]
                failures.append("mismatch:" + name)
            fields[name] = m
        checks[key] = {
            "source_commit": PIN, "tracked_worktree_clean": True,
            "input_seed": seed, "input_seed_override_calls": 1,
            "initial_state_sample_sha256": hashlib.sha256(str(seed).encode()).hexdigest(),
            "scheduler": sched, "fixture_layers": 16, "executed_layers": 16,
            "lm_head_exercised": True, "fields_compared": list(FIELDS),
            "tolerances": {"atol": ATOL, "rtol": RTOL},
            "pyvm_completed_calls": 1, "fields": fields,
            "reasons": failures, "passed": not failures,
            "logit_choice": {
                "reference_top1": 4, "native_top1": 4, "top1_equal": True,
                "reference_top1_margin": 0.1, "native_top1_margin": 0.1,
                "reference_top5": [4, 3, 2, 1, 0],
                "native_top5": [4, 3, 2, 1, 0],
                "candidate_logits": [{"index": i, "reference": 0.1 * (i+1),
                                     "native": 0.1 * (i+1)} for i in range(5)],
            },
        }
    return {"schema": "mathgraph-h100-differential-v1",
            "source_pin": PIN, "probe_kind": "consequence_variants",
            "status": "CONSEQUENCE_VARIANTS_RECORDED",
            "runpod_status": "COMPLETED", "runpod_job_id": "synthetic-job",
            "gpu_name": "NVIDIA H100 80GB HBM3", "sm_count": 132,
            "diagnostic_plan": list(PLAN), "checks": checks}


class ConsequenceAuditTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def test_good_report(self):
        v = audit(self.data)
        self.assertEqual(v["cases_checked"], 6)
        self.assertEqual(v["top_token_differences"], 0)
        self.assertEqual(v["status"], "BOUNDED_WITNESSES_CONSISTENT_NOT_RAW_FULL_TENSOR_REPLAY")

    def test_missing_case_rejected(self):
        del self.data["checks"]["seed21_dag"]
        with self.assertRaises(ValueError): audit(self.data)

    def test_forged_seed_rejected(self):
        self.data["checks"]["seed7_rr"]["input_seed"] = 0
        with self.assertRaises(ValueError): audit(self.data)

    def test_missing_seed_provenance_rejected(self):
        self.data["checks"]["seed7_rr"]["input_seed_override_calls"] = 0
        with self.assertRaises(ValueError): audit(self.data)

    def test_change_tolerance_rejected(self):
        self.data["checks"]["seed7_rr"]["tolerances"]["atol"] = 0.2
        with self.assertRaises(ValueError): audit(self.data)

    def test_forged_pass_rejected(self):
        self.data["checks"]["seed21_rr"]["passed"] = True
        with self.assertRaises(ValueError): audit(self.data)

    def test_mismatched_scheduler_inputs_rejected(self):
        self.data["checks"]["seed7_dag"]["initial_state_sample_sha256"] = "f" * 64
        with self.assertRaises(ValueError): audit(self.data)

    def test_repeated_seed_fingerprints_rejected(self):
        sha = self.data["checks"]["seed0_rr"]["initial_state_sample_sha256"]
        for scheduler in ("rr", "dag"):
            self.data["checks"]["seed7_" + scheduler]["initial_state_sample_sha256"] = sha
        with self.assertRaises(ValueError): audit(self.data)

    def test_forged_witness_rejected(self):
        self.data["checks"]["seed21_rr"]["fields"]["hidden_states"]["first_violations"][0]["allowed_error"] = 0.04
        with self.assertRaises(ValueError): audit(self.data)

    def test_top_token_difference_detected(self):
        x = self.data["checks"]["seed7_rr"]["logit_choice"]
        x["native_top1"] = 3
        x["top1_equal"] = False
        x["native_top5"] = [3, 4, 2, 1, 0]
        x["candidate_logits"] = [
            {"index": i, "reference": (i+1)*0.1, "native": (0.6 if i == 3 else 0.4 if i == 4 else (i+1)*0.1)}
            for i in range(5)]
        x["native_top1_margin"] = 0.2
        # Different top1 and consistent bounded paired values are recorded.
        v = audit(self.data)
        self.assertEqual(v["top_token_differences"], 1)

    def test_top_margin_forgery_rejected(self):
        self.data["checks"]["seed0_rr"]["logit_choice"]["reference_top1_margin"] = 0.5
        with self.assertRaises(ValueError): audit(self.data)

    def test_top5_order_forgery_rejected(self):
        self.data["checks"]["seed0_rr"]["logit_choice"]["reference_top5"] = [0, 4, 2, 1, 3]
        with self.assertRaises(ValueError): audit(self.data)

    def test_invalid_source_rejected(self):
        self.data["source_pin"] = "0" * 40
        with self.assertRaises(ValueError): audit(self.data)


if __name__ == "__main__":
    unittest.main()
