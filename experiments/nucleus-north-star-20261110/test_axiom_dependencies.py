"""Regression tests for an observation-only export axiom inventory."""

import json
import unittest

from axiom_dependencies import trace_axioms


ROWS = [
    {"meta": {"exporter": {"name": "lean4export", "version": "3.1.0"}, "format": {"version": "3.1.0"}, "lean": {"version": "4.34.1", "githash": "frozen"}}},
    {"in": 1, "str": {"pre": 0, "str": "P"}},
    {"in": 2, "str": {"pre": 0, "str": "givenP"}},
    {"in": 3, "str": {"pre": 0, "str": "fromGiven"}},
    {"in": 4, "str": {"pre": 0, "str": "fromTheorem"}},
    {"in": 5, "str": {"pre": 0, "str": "unrelated"}},
    {"ie": 0, "sort": 0},
    {"axiom": {"name": 1, "type": 0, "levelParams": []}},
    {"ie": 1, "const": {"name": 1, "us": []}},
    {"axiom": {"name": 2, "type": 1, "levelParams": []}},
    {"ie": 2, "const": {"name": 2, "us": []}},
    {"thm": {"name": 3, "type": 1, "value": 2, "all": [3], "levelParams": []}},
    {"ie": 3, "const": {"name": 3, "us": []}},
    {"thm": {"name": 4, "type": 1, "value": 3, "all": [4], "levelParams": []}},
    {"axiom": {"name": 5, "type": 0, "levelParams": []}},
]


def export(rows=ROWS):
    return ("\n".join(json.dumps(r, separators=(",", ":")) for r in rows) + "\n").encode()


class TestAxiomDependencies(unittest.TestCase):
    def test_transitive_proof_dependency_includes_type_and_proof_axioms(self):
        result = trace_axioms(export(), "fromTheorem")
        self.assertEqual(result["status"], "BOUNDED")
        self.assertEqual(result["explicit_axioms"], ["P", "givenP"])
        self.assertNotIn("unrelated", result["explicit_axioms"])
        self.assertEqual(len(result["source_sha256"]), 64)

    def test_direct_axiom_is_traced(self):
        result = trace_axioms(export(), "fromGiven")
        self.assertEqual(result["status"], "BOUNDED")
        self.assertEqual(result["explicit_axioms"], ["P", "givenP"])

    def test_axiom_type_dependencies_are_not_lost(self):
        # A theorem of P uses hQ : Q and impl : Q → P. Q does not occur in
        # the theorem's statement, but is a transitive assumption.
        extra = [
            {"in": 6, "str": {"pre": 0, "str": "Q"}},
            {"in": 7, "str": {"pre": 0, "str": "hQ"}},
            {"in": 8, "str": {"pre": 0, "str": "impl"}},
            {"in": 9, "str": {"pre": 0, "str": "combined"}},
            {"ie": 4, "const": {"name": 6, "us": []}},
            {"axiom": {"name": 6, "type": 0, "levelParams": []}},
            {"axiom": {"name": 7, "type": 4, "levelParams": []}},
            {"ie": 5, "forallE": {"binderInfo": "default", "name": 6, "type": 4, "body": 1}},
            {"axiom": {"name": 8, "type": 5, "levelParams": []}},
            {"ie": 6, "const": {"name": 8, "us": []}},
            {"ie": 7, "const": {"name": 7, "us": []}},
            {"ie": 8, "app": {"fn": 6, "arg": 7}},
            {"thm": {"name": 9, "type": 1, "value": 8, "all": [9], "levelParams": []}},
        ]
        result = trace_axioms(export(ROWS + extra), "combined")
        self.assertEqual(result["status"], "BOUNDED")
        self.assertEqual(result["explicit_axioms"], ["P", "Q", "hQ", "impl"])

    def test_removing_proof_axiom_does_not_silently_report_clean(self):
        missing = [r for r in ROWS if not ("axiom" in r and r["axiom"]["name"] == 2)]
        result = trace_axioms(export(missing), "fromTheorem")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("givenP", result["reason"])

    def test_unknown_expression_constructor_withholds_closure(self):
        bad = [dict(r) for r in ROWS]
        bad[10] = {"ie": 2, "mystery": {"value": 1}}
        result = trace_axioms(export(bad), "fromTheorem")
        self.assertEqual(result["status"], "UNKNOWN")

    def test_changed_source_changes_identity_even_when_deps_are_equal(self):
        first = trace_axioms(export(), "fromGiven")
        changed = export(ROWS + [{"in": 6, "str": {"pre": 0, "str": "newName"}}])
        second = trace_axioms(changed, "fromGiven")
        self.assertEqual(first["explicit_axioms"], second["explicit_axioms"])
        self.assertNotEqual(first["source_sha256"], second["source_sha256"])

    def test_unknown_export_version_withholds_closure(self):
        bad = [dict(r) for r in ROWS]
        bad[0] = {"meta": {"format": {"version": "9.9.9"}}}
        self.assertEqual(trace_axioms(export(bad), "fromGiven")["status"], "UNKNOWN")

    def test_duplicate_json_key_does_not_silently_change_proof(self):
        bad = export().replace(b'"value":2,"all"', b'"value":2,"value":0,"all"')
        self.assertNotEqual(bad, export())
        self.assertEqual(trace_axioms(bad, "fromGiven")["status"], "UNKNOWN")

    def test_extra_unrecognized_expression_field_withholds_closure(self):
        bad = [dict(r) for r in ROWS]
        bad[10] = {"ie": 2, "const": {"name": 2, "us": []}, "mystery": 0}
        self.assertEqual(trace_axioms(export(bad), "fromGiven")["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
