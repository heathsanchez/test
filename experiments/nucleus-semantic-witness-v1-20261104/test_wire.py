"""Contract tests for the native witness stream; no checker outcomes are mocked."""

import hashlib
import json
import unittest

from witness_qualification import parse_witness_output


SOURCE = b"pinned-source-bytes\n"
SHA = hashlib.sha256(SOURCE).hexdigest()


def line(prefix, payload):
    return f"{prefix}:{json.dumps(payload, sort_keys=True)}\n".encode()


def summary(status="Accept", *, observed=1, sha=SHA, skips=0, authority="NONE"):
    return line("NUCLEUS_SEMANTIC_SUMMARY", {
        "status": status,
        "source_sha256": sha,
        "observed_declarations": observed,
        "read_coverage": "PARTIAL",
        "global_barrier": "whole-export-sha256",
        "verification_reuse_authority": authority,
        "proof_skips": skips,
    })


def read(*, sha=SHA, skips=0):
    return line("NUCLEUS_SEMANTIC_READ", {
        "index": 1,
        "name": "thmProof",
        "kind": "theorem",
        "constant_reads": [{"name_id": 1, "present": True}],
        "global_export_sha256": sha,
        "read_coverage": "PARTIAL",
        "verification_reuse_authority": "NONE",
        "proof_skips": skips,
    })


class NativeWireTests(unittest.TestCase):
    def test_valid_acceptance_reports_a_source_pinned_actual_read(self):
        result = parse_witness_output(SOURCE, 0, read() + summary())
        self.assertEqual(result["verdict"], "Accept")
        self.assertEqual(result["source_sha256"], SHA)
        self.assertEqual(result["events"][0]["constant_reads"],
                         [{"name_id": 1, "present": True}])
        self.assertEqual(result["authority"], "NONE")

    def test_global_barrier_cannot_be_omitted_or_changed(self):
        with self.assertRaisesRegex(ValueError, "source identity"):
            parse_witness_output(SOURCE, 0, read(sha="0" * 64) + summary())
        with self.assertRaisesRegex(ValueError, "source identity"):
            parse_witness_output(SOURCE, 0, read() + summary(sha="0" * 64))

    def test_no_proof_skip_or_accept_from_rejected_source(self):
        for payload in (read(skips=1) + summary(),
                        read() + summary(skips=1),
                        read() + summary(authority="ACCEPT")):
            with self.assertRaisesRegex(ValueError, "authority"):
                parse_witness_output(SOURCE, 0, payload)
        with self.assertRaisesRegex(ValueError, "non-accept"):
            parse_witness_output(SOURCE, 1, read() + summary("Reject", observed=1))
        result = parse_witness_output(SOURCE, 1, summary("Reject", observed=0))
        self.assertEqual(result["events"], [])

    def test_refuse_inconsistent_event_counts_and_missing_summary(self):
        with self.assertRaisesRegex(ValueError, "count"):
            parse_witness_output(SOURCE, 0, read() + summary(observed=2))
        with self.assertRaisesRegex(ValueError, "summary"):
            parse_witness_output(SOURCE, 0, read())


if __name__ == "__main__":
    unittest.main()
