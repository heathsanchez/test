"""RED-first source budget probe contract for the C32 diagnostic arm."""

import unittest

from probe_c32_major_grants import parse_marker


class ProbeC32Tests(unittest.TestCase):
    def test_exact_source_marker(self):
        row = parse_marker(
            "NUCLEUS_C32_MAJOR_GRANT:seq=1:head=NameId(147):"
            "cap=4096:budget=4096:owner=Some(260755)"
        )
        self.assertEqual(row, {"seq": 1, "head": 147, "cap": 4096,
                               "budget": 4096, "owner": 260755})

    def test_reject_unmetered_or_inconsistent(self):
        self.assertRaises(ValueError, parse_marker,
                          "NUCLEUS_C32_MAJOR_GRANT:seq=1:head=NameId(147):"
                          "cap=512:budget=600:owner=Some(2000)")
        self.assertRaises(ValueError, parse_marker,
                          "NUCLEUS_C32_MAJOR_GRANT:seq=1:head=NameId(147):"
                          "cap=512:budget=400:owner=None")

    def test_unrelated_log_line(self):
        self.assertIsNone(parse_marker("NUCLEUS_REPLAY_MAJOR_START:head=NameId(66)"))


if __name__ == "__main__":
    unittest.main()
