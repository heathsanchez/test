"""CPU mutation controls for pairwise H100 BF16 repeatability."""
from array import array
import base64
import hashlib
import sys
import unittest
import zlib

from independent_repeat_variance import audit
from test_independent_repeatability_assurance import repeated_fixture


def modify_one_native_logit(report, key, index=10, bits=0x3c00):
    if sys.byteorder != "little":
        raise RuntimeError("synthetic bitwise test requires little endian")
    case = report["checks"][key]
    raw = case["raw_logits_bf16"]["native"]
    vector = array("H")
    vector.frombytes(zlib.decompress(base64.b64decode(raw["zlib_base64"])))
    vector[index] = bits  # BF16 0.0078125
    payload = vector.tobytes()
    compressed = zlib.compress(payload)
    raw.update({
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "compressed_bytes": len(compressed),
        "zlib_base64": base64.b64encode(compressed).decode("ascii"),
    })
    case["fields"]["logits"]["max_abs_diff"] = 0.0078125


class VarianceTests(unittest.TestCase):
    def setUp(self):
        self.report = repeated_fixture()

    def test_identical_raw_outputs_are_stable(self):
        r = audit(self.report)
        self.assertEqual(r["status"], "NATIVE_BF16_OUTPUTS_BITWISE_REPEATABLE_IN_SAMPLE")
        self.assertTrue(r["reference_logit_bits_equal"])
        for sched in ("rr", "dag"):
            self.assertEqual(r["by_scheduler"][sched]["max_changed_elements"], 0)

    def test_one_changed_native_word_detected_without_token_flip(self):
        modify_one_native_logit(self.report, "rep3_dag")
        r = audit(self.report)
        self.assertEqual(r["status"], "NATIVE_BF16_OUTPUTS_NONREPEATABLE_TOP1_STABLE")
        self.assertEqual(r["by_scheduler"]["dag"]["max_changed_elements"], 1)
        self.assertEqual(r["by_scheduler"]["dag"]["max_run_to_run_abs_difference"], 0.0078125)
        self.assertEqual(r["by_scheduler"]["rr"]["max_changed_elements"], 0)
        self.assertTrue(r["all_six_top1_winners_equal"])

    def test_unstable_reference_not_promoted_to_native_variance(self):
        self.report["checks"]["rep2_rr"]["initial_state_sample_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "sampled initial state"):
            audit(self.report)

    def test_corrupt_raw_hash_rejected(self):
        modify_one_native_logit(self.report, "rep3_dag")
        self.report["checks"]["rep3_dag"]["raw_logits_bf16"]["native"]["raw_sha256"] = "0"*64
        with self.assertRaises(ValueError):
            audit(self.report)

    def test_missing_case_rejected(self):
        del self.report["checks"]["rep3_dag"]
        with self.assertRaises(ValueError):
            audit(self.report)


if __name__ == "__main__":
    unittest.main()
