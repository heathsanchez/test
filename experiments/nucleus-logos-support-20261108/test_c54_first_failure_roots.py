"""C54 native name resolution and fail-closed source-boundary fixtures."""

import json
import unittest

from probe_c54_first_failure_roots import declared_value_roots, first_failed_value_root


def source_bytes(*records):
    return b"".join((json.dumps(item) + "\n").encode() for item in records)


class FirstFailedRootTests(unittest.TestCase):
    def setUp(self):
        self.source = source_bytes(
            {"in": 1, "str": {"pre": 0, "str": "chain9_datF"}},
            {"in": 2, "str": {"pre": 0, "str": "chain12_datF"}},
            {"thm": {"name": 1, "value": 10707}},
            {"thm": {"name": 2, "value": 16167}},
        )

    def entry(self, name="chain9_datF", stage="theorem.value", verdict="UNKNOWN"):
        return {"first_failed_boundary": {"source_name": name, "stage": stage, "verdict": verdict}}

    def test_targets_first_failing_declaration_not_last_record(self):
        self.assertEqual(first_failed_value_root(self.source, self.entry()), ("thm", 10707))

    def test_nested_string_and_numeral_native_names(self):
        src = source_bytes(
            {"in": 1, "str": {"pre": 0, "str": "_private"}},
            {"in": 2, "str": {"pre": 1, "str": "Init"}},
            {"in": 3, "num": {"pre": 2, "i": 0}},
            {"in": 4, "str": {"pre": 3, "str": "proof"}},
            {"thm": {"name": 4, "value": 156494}},
        )
        self.assertEqual(declared_value_roots(src), {"_private.Init.0.proof": ("thm", 156494)})

    def test_missing_name_fails_closed(self):
        with self.assertRaises(ValueError):
            first_failed_value_root(self.source, self.entry(name="missing"))

    def test_mismatched_declaration_kind_fails_closed(self):
        with self.assertRaises(ValueError):
            first_failed_value_root(self.source, self.entry(stage="definition.value"))

    def test_proven_or_unprofiled_boundary_is_not_accepted(self):
        with self.assertRaises(ValueError):
            first_failed_value_root(self.source, self.entry(verdict="ACCEPT"))
        with self.assertRaises(ValueError):
            first_failed_value_root(self.source, self.entry(stage="theorem.proposition"))

    def test_duplicate_declared_name_fails_closed(self):
        with self.assertRaises(ValueError):
            declared_value_roots(source_bytes(
                {"in": 1, "str": {"pre": 0, "str": "x"}},
                {"thm": {"name": 1, "value": 1}},
                {"thm": {"name": 1, "value": 2}},
            ))


if __name__ == "__main__":
    unittest.main()
