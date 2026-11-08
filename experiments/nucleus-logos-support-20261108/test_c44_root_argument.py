"""C44 fail-closed parser for the actual typed root obligation."""

import json
import unittest

from probe_c44_root_argument import parse_events


class RootArgumentTraceTests(unittest.TestCase):
    def test_extracts_the_necessary_source_type_and_check(self) -> None:
        record = {"expression": 8804, "context_len": 0,
                  "remaining": 261687, "expected": "EquationLHS", "result": "Unknown"}
        stderr = ("NUCLEUS_C44_INFERRED_ARG:" + json.dumps(record) + "\n"
                  + "NUCLEUS_C44_ROOT_CHECK:" + json.dumps(record) + "\n").encode()
        events = parse_events(stderr)
        self.assertEqual(len(events["inferred"]), 1)
        self.assertEqual(events["check"][0]["remaining"], 261687)

    def test_wrong_source_scope_or_fuel_fails_closed(self) -> None:
        for altered in ({"expression": 8835, "context_len": 0, "remaining": 300},
                        {"expression": 8804, "context_len": 1, "remaining": 300},
                        {"expression": 8804, "context_len": 0, "remaining": 262145}):
            with self.assertRaises(ValueError):
                parse_events(("NUCLEUS_C44_ROOT_CHECK:" + json.dumps(altered)).encode())

    def test_absent_events_are_empty_not_success(self) -> None:
        self.assertEqual(parse_events(b"NUCLEUS_APPLICATION_FUNCTION_TYPE:unknown"),
                         {"inferred": [], "check": []})


if __name__ == "__main__":
    unittest.main()
