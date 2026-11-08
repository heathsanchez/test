"""C39 trace parser RED/GREEN boundary tests."""

import unittest

from probe_c39_typed_failure import parse_failure


class FailureTraceTests(unittest.TestCase):
    def test_source_argument_failure(self) -> None:
        record = parse_failure(
            "NUCLEUS_C39_TYPED_FAILURE:head=Const { name: NameId(65), levels: [] }:"
            "spine=5:depth=2:budget=8192:arg=4:stage=data-argument-conversion"
        )
        self.assertEqual(record["arg"], 4)
        self.assertEqual(record["stage"], "data-argument-conversion")

    def test_malformed_or_out_of_bounds_fails_closed(self) -> None:
        for line in (
            "NUCLEUS_C39_TYPED_FAILURE:unknown",
            "NUCLEUS_C39_TYPED_FAILURE:head=Nat.rec:spine=1:depth=0:budget=128:arg=3:stage=left-pi",
            "NUCLEUS_C39_TYPED_FAILURE:head=Nat.rec:spine=1:depth=0:budget=128:arg=0:stage=made-up-proof",
        ):
            with self.assertRaises(ValueError):
                parse_failure(line)


if __name__ == "__main__":
    unittest.main()
