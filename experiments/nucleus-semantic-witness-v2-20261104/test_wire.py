"""Test fail-closed V2 native witness output, not source text."""

import hashlib
import json
import unittest

from wire_qualification import parse_v2


SOURCE = b'{"meta":{"format":{"version":"3.1.0"}}}\n'
SHA = hashlib.sha256(SOURCE).hexdigest()


def sample_record():
    return {
        "status": "Accept", "source_sha256": SHA,
        "global_barrier": "whole-export-sha256", "read_coverage": "PARTIAL",
        "semantic_dependency_completeness": "UNKNOWN",
        "verification_reuse_authority": "NONE", "proof_skips": 0,
        "global": {
            "source_resolution_reads": [{"table": "expression", "access": "point", "id": 0, "present": True}],
            "preflight_reads": [],
            "guards": [{"stage": "quotient-source-ownership", "result": "PASS"}],
        },
        "declarations": [{
            "index": 0, "name": "p", "kind": "theorem", "global_export_sha256": SHA,
            "constant_reads": [{"name_id": 1, "present": True}],
            "table_reads": [{"table": "expression", "access": "point", "id": 3, "present": True}],
            "environment_reads": [{"channel": "constant", "name_id": 1, "present": True}],
            "read_coverage": "PARTIAL", "verification_reuse_authority": "NONE", "proof_skips": 0,
        }],
    }


def wire(data):
    return b"NUCLEUS_SEMANTIC_V2:" + json.dumps(data, separators=(",", ":")).encode() + b"\n"


class WireTests(unittest.TestCase):
    def test_complete_sample_is_read_as_bounded_observation(self):
        data = parse_v2(SOURCE, 0, wire(sample_record()))
        self.assertEqual(data["source_sha256"], SHA)
        self.assertEqual(len(data["declarations"]), 1)
        self.assertEqual(data["verification_reuse_authority"], "NONE")

    def test_reject_forged_authority_and_identity(self):
        for field, value in [("verification_reuse_authority", "ACCEPT"),
                             ("proof_skips", 1), ("source_sha256", "0" * 64),
                             ("global_barrier", "local-only")]:
            bad = sample_record()
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_v2(SOURCE, 0, wire(bad))

    def test_reject_missing_required_global_guard_and_bad_tables(self):
        bad = sample_record()
        bad["global"]["guards"] = []
        with self.assertRaises(ValueError):
            parse_v2(SOURCE, 0, wire(bad))
        bad = sample_record()
        bad["declarations"][0]["table_reads"][0]["present"] = "yes"
        with self.assertRaises(ValueError):
            parse_v2(SOURCE, 0, wire(bad))

    def test_reject_nonaccept_admissions_and_duplicate_json_keys(self):
        bad = sample_record()
        bad["status"] = "Reject"
        with self.assertRaises(ValueError):
            parse_v2(SOURCE, 1, wire(bad))
        with self.assertRaises(ValueError):
            parse_v2(SOURCE, 0, b'NUCLEUS_SEMANTIC_V2:{"status": "Accept", "status": "Reject"}\n')

    def test_invalid_or_missing_line_fails_closed(self):
        for stderr in [b"", b"hello\n", wire(sample_record()) + wire(sample_record())]:
            with self.subTest(stderr=stderr[:24]), self.assertRaises(ValueError):
                parse_v2(SOURCE, 0, stderr)


if __name__ == "__main__":
    unittest.main()
