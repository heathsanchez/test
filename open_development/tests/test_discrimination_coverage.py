"""Internal fixtures only; no scientific corpus checkout required."""
import copy
from hashlib import sha1, sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from open_development import discrimination_coverage as coverage
from open_development.discrimination_coverage import pool_audit, OUTCOME
from open_development.external_minif2f_entry import freeze_source
from open_development.runtime import digest, EvidenceStore


class CoverageTests(unittest.TestCase):
    def test_audit_identity_and_history_fail_closed(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            external = path / "external"
            source = freeze_source(path / "state.sqlite", "a" * 40)
            manifest = {"source_commit": "a" * 40, "selection_nonce": "1:1",
                        "canonical_parent_commit": coverage.PARENT,
                        "external_path_absent": True, "files": coverage.source_identity(root),
                        "retained_source": source}
            manifest["digest"] = digest(manifest)
            test_file = external / coverage.TEST_PATH
            test_file.parent.mkdir(parents=True)
            data = b"theorem fixture (x : \xe2\x84\x9d) : 0 \xe2\x89\xa4 x ^ 2 + 1 := by\n"
            test_file.write_bytes(data)
            blob = sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            run = lambda m: coverage.audit(root, external, path / "state.sqlite", m, "a" * 40, "1:1")
            with patch.object(coverage.subprocess, "check_output", return_value=coverage.CORPUS_COMMIT), \
                    patch.object(coverage, "TEST_BLOB_SHA1", blob), \
                    patch.object(coverage, "FILE_SHA256", sha256(data).hexdigest()):
                self.assertTrue(run(manifest)["history_unchanged"])
                for key, value in [("source_commit", "b" * 40), ("selection_nonce", "2:1"),
                                   ("canonical_parent_commit", "c" * 40),
                                   ("external_path_absent", False), ("files", {})]:
                    changed = {**manifest, key: value}
                    changed["digest"] = digest({k: v for k, v in changed.items() if k != "digest"})
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        run(changed)
                with self.assertRaisesRegex(ValueError, "tampered freeze"):
                    run({**manifest, "digest": "0" * 64})
                with patch.object(coverage.subprocess, "check_output", return_value="b" * 40):
                    with self.assertRaisesRegex(ValueError, "corpus identity"):
                        run(manifest)
                store = EvidenceStore(path / "state.sqlite")
                store.revoke(source["K_A"], "fixture mutation")
                store.close()
                with self.assertRaisesRegex(ValueError, "mutated source state"):
                    run(manifest)

    def test_empty_pool_is_unknown_not_expansion(self):
        result = pool_audit("", "1:1")
        self.assertEqual(result["outcome"], OUTCOME)
        self.assertEqual(result["candidate_count"], 0)
        self.assertFalse(result["v4_eligible"])

    def test_unsupported_statement_is_not_scored_unknown(self):
        result = pool_audit("theorem fixture (x : ℝ) : Real.exp x > 0 := by\n", "1:1")
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["initial_state_route_counts"]["UNKNOWN"], 0)

    def test_eligible_pool_cannot_license_expansion(self):
        text = "\n".join(f"theorem fixture_{i} (x : ℝ) : 0 ≤ x ^ 2 + {i+1} := by"
                         for i in range(16))
        result = pool_audit(text, "1:1")
        self.assertEqual(result["candidate_count"], 16)
        self.assertEqual(result["missing_classes"], ["REUSE", "EXPANSION", "UNKNOWN"])
        self.assertTrue(all(r["expansion_ruled_out"] for r in result["administrator_rows"]))
        self.assertEqual(result["scoring_admissions"], [])
        self.assertEqual(result["route_predictions"], [])
        self.assertEqual(result["scored_tasks"], 0)
        self.assertFalse(result["v4_eligible"])

    def test_nonce_deterministic_not_manual_selection(self):
        text = "\n".join(f"theorem fixture_{i} (x : ℝ) : 0 ≤ x ^ 2 + {i+1} := by"
                         for i in range(16))
        first = pool_audit(text, "1:1")
        self.assertEqual(first, pool_audit(text, "1:1"))
        second = pool_audit(text, "2:1")
        self.assertEqual(first["candidate_pool_digest"], second["candidate_pool_digest"])
        self.assertNotEqual(first["administrator_rows"], second["administrator_rows"])


if __name__ == "__main__":
    unittest.main()
