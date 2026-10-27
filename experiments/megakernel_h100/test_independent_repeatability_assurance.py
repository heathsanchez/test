"""Offline controls for repeated H100 GPU output interpretation."""
import copy
import unittest
from independent_repeatability_assurance import audit, PLAN
from test_independent_full_logit_replay import authentic_shape_sample


def repeated_fixture():
    original = authentic_shape_sample()
    template = original["checks"]["seed0_rr"]
    checks = {}
    for rep in (1, 2, 3):
        for sched in ("rr", "dag"):
            c = copy.deepcopy(template)
            c["scheduler"] = sched
            c["input_seed"] = 0
            checks[f"rep{rep}_{sched}"] = c
    return {
        "schema": "mathgraph-h100-differential-v1",
        "probe_kind": "repeat_seed0",
        "status": "REPEATABILITY_OBSERVATIONS_RECORDED",
        "source_pin": original["source_pin"],
        "runpod_status": "COMPLETED",
        "runpod_job_id": "synthetic-repeatability-job",
        "sm_count": 132,
        "gpu_name": "NVIDIA H100 80GB HBM3",
        "repetition_plan": list(PLAN),
        "checks": checks,
    }


class RepeatabilityTests(unittest.TestCase):
    def setUp(self):
        self.data = repeated_fixture()

    def test_repeated_full_vectors(self):
        result = audit(self.data)
        self.assertEqual(result["cases_checked"], 6)
        self.assertEqual(result["status"], "REFERENCE_AND_INPUT_REPEATABILITY_ESTABLISHED")
        self.assertTrue(result["all_six_native_winners_equal"])
        for name in ("rr", "dag"):
            self.assertTrue(result["by_scheduler"][name]["native_bitwise_repeatable"])

    def test_missing_repeat_rejected(self):
        del self.data["checks"]["rep3_dag"]
        with self.assertRaises(ValueError):
            audit(self.data)

    def test_initial_input_sample_mismatch_not_promoted(self):
        self.data["checks"]["rep3_dag"]["initial_state_sample_sha256"] = "b" * 64
        result = audit(self.data)
        self.assertEqual(result["status"], "REFERENCE_OR_SAMPLED_INPUT_NONREPEATABLE")

    def test_corrupt_raw_native_hash_rejected(self):
        self.data["checks"]["rep1_rr"]["raw_logits_bf16"]["native"]["raw_sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            audit(self.data)

    def test_forged_top_token_rejected(self):
        self.data["checks"]["rep2_dag"]["logit_choice"]["native_top1"] = 0
        with self.assertRaises(ValueError):
            audit(self.data)

    def test_source_provenance_rejected(self):
        self.data["checks"]["rep2_rr"]["source_commit"] = "0" * 40
        with self.assertRaises(ValueError):
            audit(self.data)

    def test_wrong_scheduler_rejected(self):
        self.data["checks"]["rep2_dag"]["scheduler"] = "rr"
        with self.assertRaises(ValueError):
            audit(self.data)


if __name__ == "__main__":
    unittest.main()
