"""C144: source AST identities, never inferred from an expression frequency."""

import json
import unittest

from probe_c144_hot_ast import inspect_hot_ast


class C144SourceTests(unittest.TestCase):
    def test_hot_node_and_exact_application_parent_role(self):
        source = b"\n".join(json.dumps(row).encode() for row in (
            {"ie": 1, "bvar": 0},
            {"ie": 6, "const": {"name": 12, "levels": []}},
            {"ie": 8, "app": {"fn": 1, "arg": 6}},
            {"ie": 10, "app": {"fn": 6, "arg": 1}},
        ))
        rows = inspect_hot_ast(source, ids=(1, 6))
        self.assertEqual(rows[0]["row"], {"ie": 1, "bvar": 0})
        self.assertEqual(rows[0]["application_parents"], [
            {"parent": 8, "role": "fn"}, {"parent": 10, "role": "arg"}])
        self.assertEqual(rows[1]["application_parents"], [
            {"parent": 8, "role": "arg"}, {"parent": 10, "role": "fn"}])

    def test_duplicate_or_missing_source_ids_are_rejected(self):
        with self.assertRaises(AssertionError):
            inspect_hot_ast(b'{"ie": 1, "bvar": 0}\n', ids=(1, 6))
        with self.assertRaises(AssertionError):
            inspect_hot_ast(b'{"ie": 1, "bvar": 0}\n{"ie": 1, "bvar": 1}\n', ids=(1,))


if __name__ == "__main__":
    unittest.main()
