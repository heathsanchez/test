import unittest

from open_development.residual import ResidualEnvelope


class ResidualEnvelopeTests(unittest.TestCase):
    def envelope(self):
        return ResidualEnvelope(
            residual_class="ROLE_REQUALIFICATION_REQUIRED",
            diagnosis="capability_failure",
            verifier_certified_witness={"checked": True},
            closure_id="a" * 64,
            budget_id="b" * 64,
            necessary_constraint={"role": "factor-pair"},
            version_space_id="c" * 64,
            evidence_strength="replay-certified",
            domain_payload={"class": "ROLE_REQUALIFICATION_REQUIRED"},
            source="d" * 64,
            source_fingerprint="e" * 64,
            constraint={"role": "factor-pair"},
        )

    def test_round_trip(self):
        env = self.envelope()
        parsed = ResidualEnvelope.from_mapping(env.to_mapping())
        self.assertEqual(parsed, env)
        self.assertEqual(env.to_mapping()["type"], "ResidualEnvelope/v1")
        self.assertEqual(env.to_mapping()["class"], "ROLE_REQUALIFICATION_REQUIRED")

    def test_missing_witness_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "witness"):
            ResidualEnvelope(
                residual_class="X", diagnosis="capability_failure",
                verifier_certified_witness=None, closure_id="a", budget_id="b",
                necessary_constraint={"x": 1}, version_space_id="c",
                evidence_strength="replay-certified")

    def test_unknown_diagnosis_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "diagnosis"):
            ResidualEnvelope(
                residual_class="X", diagnosis="mystery",
                verifier_certified_witness={"checked": True}, closure_id="a", budget_id="b",
                necessary_constraint={"x": 1}, version_space_id="c",
                evidence_strength="replay-certified")


if __name__ == "__main__":
    unittest.main()
