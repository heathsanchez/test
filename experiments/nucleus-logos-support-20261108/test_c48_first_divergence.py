"""Fail-closed parsing and causal sequence comparison for C48 Rust traces."""

import json
import unittest

from probe_c48_first_divergence import parse_trace, first_divergence


def line(sequence, stage, detail="probe", major=4677):
    return ("NUCLEUS_C48_EVENT:" + json.dumps({
        "seq": sequence, "stage": stage, "recursor": 66,
        "major_expr": major, "major_env": 789,
        "depth": 3, "owner_remaining": 900,
        "detail": detail,
    })).encode()


class ExactSourceTransitionTests(unittest.TestCase):
    def test_only_source_emitted_records_are_accepted(self):
        observed = parse_trace(line(0, "enter") + b"\n" + line(1, "major-result", "unknown"))
        self.assertEqual([event["stage"] for event in observed], ["enter", "major-result"])
        self.assertEqual(observed[1]["detail"], "unknown")

    def test_rejects_outside_source_scope_sequence_and_fuel(self):
        for corrupt in (
            {"seq": 512}, {"seq": -1}, {"owner_remaining": -1},
            {"major_expr": -1}, {"depth": -1}, {"stage": "made-up"},
        ):
            record = json.loads(line(0, "enter").split(b":", 1)[1])
            record.update(corrupt)
            with self.subTest(corrupt=corrupt), self.assertRaises(ValueError):
                parse_trace(b"NUCLEUS_C48_EVENT:" + json.dumps(record).encode())

    def test_first_structural_difference_ignores_fuel_only(self):
        failed = parse_trace(b"\n".join([
            line(0, "enter"), line(1, "major-result", "stuck"),
        ]))
        accepted = parse_trace(b"\n".join([
            line(0, "enter"), line(1, "major-result", "constructor"),
        ]))
        result = first_divergence(failed, accepted)
        self.assertEqual(result["shared_prefix"], 1)
        self.assertEqual(result["failed_next"]["detail"], "stuck")
        self.assertEqual(result["accepted_next"]["detail"], "constructor")

    def test_missing_observation_is_not_a_qualification(self):
        self.assertEqual(parse_trace(b"diagnostic_steps=262144:verdict=Unknown"), [])
        self.assertIsNone(first_divergence([], [])["failed_next"])


if __name__ == "__main__":
    unittest.main()
