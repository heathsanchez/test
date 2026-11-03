"""Source-stable candidate identities: correctness tests against real Lean exports."""

from pathlib import Path
import json
import unittest

from semantic_inventory import InventoryError, compare, inventory


FIXTURES = Path(__file__).resolve().parents[2] / "metatron-kernel/tests/fixtures"
SOURCE = (FIXTURES / "good-theorem-use.ndjson").read_bytes()


def records(source=SOURCE):
    return [json.loads(line) for line in source.splitlines()]


def encode(rows):
    return b"".join(json.dumps(x, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode() + b"\n" for x in rows)


class SemanticInventoryTests(unittest.TestCase):
    def test_genuine_export_has_typed_non_authorizing_dependencies(self):
        report = inventory(SOURCE)
        self.assertEqual(report["type"], "nucleus.dependency_candidate.v1")
        self.assertEqual(report["authority"], "NONE")
        self.assertEqual(report["complete_kernel_dependency_closure"], "UNKNOWN")
        self.assertEqual(report["proof_skips"], 0)
        self.assertEqual([r["name"] for r in report["declarations"]],
                         ["pImpliesP", "thmProof"])
        self.assertEqual(report["declarations"][0]["direct_references"], [])
        self.assertEqual(report["declarations"][1]["direct_references"], ["pImpliesP"])
        self.assertEqual(report["declarations"][1]["direct_dependencies"],
                         [report["declarations"][0]["semantic_id"]])

    def test_later_rename_preserves_first_shape_not_legacy_root(self):
        changed = SOURCE.replace(b'"str":"thmProof"', b'"str":"thmProofChanged"')
        outcome = compare(SOURCE, changed)
        self.assertEqual(outcome["unchanged_semantic_names"], ["pImpliesP"])
        self.assertEqual(outcome["new_or_changed_names"], ["thmProofChanged"])
        self.assertEqual(outcome["removed_names"], ["thmProof"])
        self.assertEqual(outcome["candidate_reuse_count"], 1)
        self.assertEqual(outcome["verification_reuse_authority"], "NONE")

    def test_exporter_integer_renumber_preserves_semantic_fingerprints(self):
        rows = records()
        for row in rows:
            if row.get("in") == 4:
                row["in"] = 44
            if "thm" in row and row["thm"]["name"] == 4:
                row["thm"]["name"] = 44
                row["thm"]["all"] = [44]
        outcome = compare(SOURCE, encode(rows))
        self.assertEqual(outcome["candidate_reuse_count"], 2)
        self.assertEqual(outcome["new_or_changed_names"], [])
        self.assertEqual(outcome["verification_reuse_authority"], "NONE")

    def test_changed_earlier_body_invalidates_downstream_support(self):
        rows = records()
        for row in rows:
            if row.get("ie") == 5:
                row["lam"]["name"] = 2  # only binder label, still kernel-valid
        original = inventory(SOURCE)["declarations"]
        changed = inventory(encode(rows))["declarations"]
        self.assertNotEqual(original[0]["semantic_id"], changed[0]["semantic_id"])
        self.assertEqual(original[1]["semantic_id"], changed[1]["semantic_id"])
        self.assertNotEqual(original[1]["support_id"], changed[1]["support_id"])

    def test_invalid_quotient_suffix_changes_global_kernel_verdict_not_earlier_shape(self):
        rows = records()
        rows.append({"in": 10, "str": {"pre": 0, "str": "NotQuot"}})
        rows.append({"quot": {"kind": "type", "levelParams": [], "name": 10, "type": 0}})
        changed = inventory(encode(rows))
        original = inventory(SOURCE)
        self.assertEqual([r["semantic_id"] for r in changed["declarations"][:2]],
                         [r["semantic_id"] for r in original["declarations"]])
        self.assertEqual(changed["complete_kernel_dependency_closure"], "UNKNOWN")
        self.assertEqual(changed["authority"], "NONE")

    def test_self_const_reference_refuses_forward_dependency(self):
        rows = records()
        for row in rows:
            if row.get("ie") == 11:
                row["const"]["name"] = 4
        with self.assertRaisesRegex(InventoryError, "not previously established"):
            inventory(encode(rows))

    def test_duplicate_name_id_fails_closed(self):
        rows = records()
        rows.append({"in": 4, "str": {"pre": 0, "str": "duplicate"}})
        with self.assertRaisesRegex(InventoryError, "duplicate"):
            inventory(encode(rows))

    def test_unknown_source_structure_fails_closed(self):
        rows = records()
        rows.append({"mystery": {"unverified": True}})
        with self.assertRaisesRegex(InventoryError, "unsupported"):
            inventory(encode(rows))

    def test_missing_expression_and_cycle_fail_closed(self):
        rows = records()
        for row in rows:
            if row.get("ie") == 5:
                row["lam"]["body"] = 123456
        with self.assertRaisesRegex(InventoryError, "missing expression"):
            inventory(encode(rows))
        rows = records()
        for row in rows:
            if row.get("ie") == 5:
                row["lam"]["body"] = 5
        with self.assertRaisesRegex(InventoryError, "cyclic expression"):
            inventory(encode(rows))

    def test_duplicate_json_keys_are_rejected(self):
        bad = SOURCE + b'{"in":321,"in":322,"str":{"pre":0,"str":"a"}}\n'
        with self.assertRaisesRegex(InventoryError, "duplicate JSON key"):
            inventory(bad)

    def test_distinct_structured_names_do_not_alias_when_display_is_same(self):
        extra = [
            {"in": 20, "str": {"pre": 0, "str": "x.y"}},
            {"in": 21, "str": {"pre": 0, "str": "x"}},
            {"in": 22, "str": {"pre": 21, "str": "y"}},
            {"axiom": {"name": 20, "levelParams": [], "type": 0}},
            {"axiom": {"name": 22, "levelParams": [], "type": 0}},
        ]
        before = inventory(encode(records() + extra))
        self.assertEqual([r["name"] for r in before["declarations"][-2:]],
                         ["x.y", "x.y"])
        self.assertEqual(len({r["name_key"] for r in before["declarations"]}), 4)
        changed = json.loads(json.dumps(extra))
        changed[0]["str"]["str"] = "x.z"
        comparison = compare(encode(records() + extra), encode(records() + changed))
        self.assertEqual(comparison["candidate_reuse_count"], 3)

    def test_inductive_fixture_is_not_treated_as_opaque_safely_reusable_proof(self):
        export = (FIXTURES / "good-closed-record-3.ndjson").read_bytes()
        report = inventory(export)
        self.assertGreaterEqual(len(report["declarations"]), 3)
        self.assertEqual(report["complete_kernel_dependency_closure"], "UNKNOWN")
        self.assertEqual(report["authority"], "NONE")
        self.assertIn("inductive", [r["kind"] for r in report["declarations"]])

    def test_native_3_1_0_optional_parser_fields_remain_source_observations(self):
        for name in ("sparse-name-index.ndjson", "good-direct-recursive-alias.ndjson",
                     "protected-false-index.ndjson"):
            with self.subTest(fixture=name):
                report = inventory((FIXTURES / name).read_bytes())
                self.assertEqual(report["authority"], "NONE")
                self.assertGreaterEqual(len(report["declarations"]), 1)


if __name__ == "__main__":
    unittest.main()
