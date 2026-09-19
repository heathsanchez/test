import hashlib
import json
import unittest

from emit_qckn_flash_event import build_event, canonical


class CollatzFlashEventEmitterTests(unittest.TestCase):
    def test_scoped_redundancy_obstruction_is_content_bound(self):
        evidence, event = build_event(
            source_commit="0123456789abcdef0123456789abcdef01234567"
        )
        evidence_text = canonical(evidence)
        self.assertEqual(event["event_kind"], "obstruction_admission")
        self.assertEqual(
            event["source_evidence_sha256"],
            hashlib.sha256(evidence_text.encode()).hexdigest(),
        )
        self.assertEqual(
            event["payload_sha256"],
            hashlib.sha256(canonical(event["payload"]).encode()).hexdigest(),
        )
        self.assertEqual(evidence["arms"]["isolated"]["T_calls"], 1501097)
        self.assertEqual(evidence["arms"]["flash"]["T_calls"], 208613)
        self.assertEqual(evidence["arms"]["guarded"]["T_calls"], 17401)
        self.assertEqual(
            evidence["verdict"],
            "PASS_BOUNDED_PROPAGATION_NO_ADVANTAGE_OVER_UPFRONT_GUARD",
        )
        obs = event["payload"]["obstruction"]
        self.assertEqual(obs["expected_output"], "new-strict-advantage")
        self.assertEqual(obs["actual_output"], "redundant-policy-order")
        self.assertIn("manual-review", obs["provenance"])
        text = canonical(event)
        self.assertEqual(text, canonical(json.loads(text)))

    def test_source_commit_must_be_full_sha(self):
        with self.assertRaises(ValueError):
            build_event(source_commit="bad")


if __name__ == "__main__":
    unittest.main()
