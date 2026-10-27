"""CPU-only positive/negative mutation controls for shared-offset near ties."""
from array import array
import base64
import hashlib
import sys
import unittest
import zlib

from near_tie_counterfactual import case_sensitivity, BUDGETS
from test_independent_full_logit_replay import exact_bf16_payload


def altered_native_record():
    if sys.byteorder != "little":
        raise RuntimeError("BF16 synthetic test requires little-endian host")
    # Reference top two: index4=5.0, index3=4.9375.
    # GPU top two: index4=5.0, index3=4.96875.
    # Shared +0.046875 to index3 preserves ref winner but flips GPU winner.
    ref_bits = array("H", [0]) * 128256
    gpu_bits = array("H", [0]) * 128256
    for i, word in enumerate((0x3f80, 0x4000, 0x4040, 0x409e, 0x40a0)):
        ref_bits[i] = word
        gpu_bits[i] = 0x409f if i == 3 else word

    def pack(bits):
        raw = bits.tobytes()
        blob = zlib.compress(raw)
        return {"dtype": "bf16-le", "elements": 128256, "raw_bytes": len(raw),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "compressed_bytes": len(blob),
                "zlib_base64": base64.b64encode(blob).decode("ascii")}

    return {"raw_logits_bf16": {"reference": pack(ref_bits),
                                "native": pack(gpu_bits)}}


class NearTieTests(unittest.TestCase):
    def test_matching_native_and_reference_reject_fake_split(self):
        x = exact_bf16_payload()
        with self.assertRaisesRegex(ValueError, "no strict shared-offset split"):
            case_sensitivity({"raw_logits_bf16": {"reference": x, "native": x}})

    def test_exhaustive_split_at_one_challenger(self):
        result = case_sensitivity(altered_native_record())
        self.assertEqual(result["reference_top1"], 4)
        self.assertEqual(result["native_top1"], 4)
        self.assertEqual(result["challenger_index"], 3)
        self.assertAlmostEqual(result["reference_margin"], 0.0625)
        self.assertAlmostEqual(result["native_margin"], 0.03125)
        self.assertAlmostEqual(result["earliest_split_infimum"], 0.03125)
        self.assertAlmostEqual(result["split_interval_upper"], 0.0625)
        self.assertAlmostEqual(result["strict_midpoint_boost"], 0.046875)
        self.assertEqual(result["boosted_reference_top1"], 4)
        self.assertEqual(result["boosted_native_top1"], 3)
        self.assertTrue(result["boosted_winners_differ"])
        self.assertEqual(result["budgets"]["0.05"], "COUNTERFACTUAL_SPLIT_EXISTS")

    def test_no_split_under_smaller_budget(self):
        result = case_sensitivity(altered_native_record())
        self.assertEqual(result["budgets"]["0.05"], "COUNTERFACTUAL_SPLIT_EXISTS")
        self.assertTrue(result["earliest_split_infimum"] > 0.02)

    def test_tampered_vector_rejected(self):
        record = altered_native_record()
        record["raw_logits_bf16"]["native"]["raw_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            case_sensitivity(record)

    def test_nonunique_native_winner_refused(self):
        record = altered_native_record()
        # Synthetic original ref winner and native winner must be identical.
        gpu = record["raw_logits_bf16"]["native"]
        bits = array("H", [0]) * 128256
        for i, word in enumerate((0x3f80, 0x4000, 0x4040, 0x40a1, 0x40a0)):
            bits[i] = word
        raw = bits.tobytes()
        blob = zlib.compress(raw)
        gpu.update({"raw_sha256": hashlib.sha256(raw).hexdigest(),
                    "compressed_bytes": len(blob),
                    "zlib_base64": base64.b64encode(blob).decode("ascii")})
        with self.assertRaisesRegex(ValueError, "already has different top tokens"):
            case_sensitivity(record)


if __name__ == "__main__":
    unittest.main()
