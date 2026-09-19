import hashlib
import json
import unittest

from emit_qckn_flash_event import build_event, build_shared_normalized_event, canonical


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

    def test_shared_normalized_equivalence_emits_bounded_capability(self):
        evidence, event = build_shared_normalized_event(
            source_commit="0123456789abcdef0123456789abcdef01234567"
        )
        evidence_text = canonical(evidence)
        self.assertEqual(event["event_kind"], "capability_admission")
        self.assertEqual(
            event["event_id"],
            "collatz:shared-normalized-equivalence:k8-r4:v1",
        )
        self.assertEqual(
            event["source_evidence_sha256"],
            hashlib.sha256(evidence_text.encode()).hexdigest(),
        )
        self.assertEqual(
            event["payload_sha256"],
            hashlib.sha256(canonical(event["payload"]).encode()).hexdigest(),
        )
        self.assertEqual(evidence["equivalence"]["K"], 8)
        self.assertEqual(evidence["equivalence"]["R"], 4)
        self.assertEqual(evidence["equivalence"]["comparisons"], 80)
        self.assertEqual(evidence["equivalence"]["residual"], 16)
        self.assertEqual(evidence["scout"]["K"], 12)
        self.assertEqual(evidence["scout"]["R"], 8)
        self.assertEqual(evidence["scout"]["closed"], 75)
        self.assertEqual(evidence["scout"]["unresolved"], 69)
        self.assertEqual(
            evidence["claim_boundary"],
            "bounded shared-normalized equivalence and scout evidence only; no Collatz termination claim",
        )
        cap = event["payload"]["capability"]
        self.assertEqual(
            cap["semantics"],
            [["K8-R4", "equivalent-to-reference"]],
        )
        self.assertEqual(
            cap["certificate_id"],
            "run:35063857334/jobs:104689752490,104689796559",
        )

    def test_source_commit_must_be_full_sha(self):
        with self.assertRaises(ValueError):
            build_event(source_commit="bad")
        with self.assertRaises(ValueError):
            build_shared_normalized_event(source_commit="bad")


if __name__ == "__main__":
    unittest.main()
