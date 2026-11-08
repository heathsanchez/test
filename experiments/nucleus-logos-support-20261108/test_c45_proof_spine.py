"""C45 must preserve exact-source scope and uncertainty in child traces."""

import json
import unittest

from probe_c45_proof_spine import parse_spine


class ProofSpineObserverTests(unittest.TestCase):
    def test_retains_failed_child_without_promoting_it(self):
        event = {"expression": 8803, "function": 8802, "argument": 1477,
                 "context_len": 0, "remaining": 261688,
                 "result": "Unknown { residual: ResidualId(\"source\") }",
                 "domain": "Term(...)"}
        self.assertEqual(parse_spine(("NUCLEUS_C45_PROOF_ARG:" + json.dumps(event)).encode()), [event])

    def test_wrong_source_application_or_extra_fuel_fails_closed(self):
        base = {"expression": 8803, "function": 8802, "argument": 1477,
                "context_len": 0, "remaining": 261688,
                "result": "Unknown { residual: ResidualId(\"source\") }",
                "domain": "Term(...)"}
        for changes in ({"expression": 8835}, {"context_len": 1},
                        {"remaining": 262145}, {"remaining": -1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                parse_spine(("NUCLEUS_C45_PROOF_ARG:" + json.dumps(base | changes)).encode())

    def test_missing_trace_is_not_forged(self):
        self.assertEqual(parse_spine(b"NUCLEUS_C44_ROOT_CHECK:{}\n"), [])


if __name__ == "__main__":
    unittest.main()
