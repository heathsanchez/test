"""C55 observer grammar, sampling boundaries, and fail-closed controls."""

import unittest

from probe_c55_app_failure_shape import parse_app_observation


class AppFailureShapeTests(unittest.TestCase):
    def sample(self, seq=0, state="inference-unknown:application-function-type"):
        return (f"NUCLEUS_C55_APP_FAILURE:seq={seq}:app=ExprId(55):fun=ExprId(32):"
                f"arg=ExprId(30):context_depth=3:frame=77:remaining=128:state={state}:source=\n").encode()

    def summary(self, root=10707, events=1, verdict='Unknown { residual: ResidualId("application-function-type") }'):
        return (f"NUCLEUS_C55_APP_SUMMARY:expr=ExprId({root}):events={events}:"
                f"remaining=0:result={verdict}\n").encode()

    def test_first_sample_and_summary(self):
        r = parse_app_observation(self.sample() + self.summary(), 10707)
        self.assertEqual((r["observed_events"], r["sample_count"]), (1, 1))
        self.assertTrue(r["sample_is_complete"])

    def test_proven_term_state(self):
        first = self.sample(state="inference-proven-term").replace(b':source=\n', b':source=expr=ExprId(7):env=4\n')
        r = parse_app_observation(first + self.summary(), 10707)
        self.assertEqual(r["sampled_states"][0]["state"], "inference-proven-term")
        self.assertEqual(r["sampled_states"][0]["source"], "expr=ExprId(7):env=4")

    def test_power_of_two_sampling_is_partial_not_false_completion(self):
        r = parse_app_observation(self.sample(0) + self.sample(7) + self.summary(events=16), 10707)
        self.assertEqual(r["observed_events"], 16)
        self.assertFalse(r["sample_is_complete"])

    def test_root_or_verdict_changed_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_app_observation(self.sample() + self.summary(root=999), 10707)
        with self.assertRaises(ValueError):
            parse_app_observation(self.sample() + self.summary(verdict="Proven"), 10707)

    def test_missing_summary_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_app_observation(self.sample(), 10707)

    def test_duplicate_sample_sequence_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_app_observation(self.sample() + self.sample() + self.summary(events=2), 10707)

    def test_no_applications_is_legitimate_zero(self):
        r = parse_app_observation(self.summary(events=0), 10707)
        self.assertTrue(r["sample_is_complete"])


if __name__ == "__main__":
    unittest.main()
