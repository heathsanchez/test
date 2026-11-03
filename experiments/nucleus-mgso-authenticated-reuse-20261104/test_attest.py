"""Independent negative controls for MGSO historical reuse authorization."""

from __future__ import annotations

import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

import attest
import native_controls


COMMIT = "a" * 40
SOURCE = b"{\"kind\":\"fixture\"}\n"
ROOT = b'{"mgso":"candidate"}\n'
BINARY = (b"#!/usr/bin/env python3\n"
          b"import sys\n"
          b"_ = sys.stdin.buffer.read()\n"
          b"sys.stderr.write('NUCLEUS_MGSO_INSPECT:status=candidate-match;authority=none;fresh-check=false;declarations=1\\n')\n"
          b"sys.exit(2)\n")


def fixture(*, binary=BINARY, root=ROOT, source=SOURCE, flags=None, report_override=None):
    report = {"schema": attest.SCHEMA, "status": "WARRANTED_BOUNDED",
              "scope": "whole-export-exact-binary-source-config",
              "kernel_exit_code": 0, "source_sha256": attest.digest(source),
              "binary_sha256": attest.digest(BINARY),
              "root_sha256": attest.digest(ROOT), "flags": flags or {}}
    if report_override:
        report.update(report_override)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as z:
        z.writestr("nucleus", binary)
        z.writestr("store/root.json", root)
        z.writestr("report.json", json.dumps(report))
    archive = buffer.getvalue()
    metadata = {
        "run": {"id": 501, "run_attempt": 1, "head_sha": COMMIT,
                "head_branch": attest.BRANCH, "path": attest.WORKFLOW,
                "event": "push", "status": "in_progress", "conclusion": None,
                "repository": {"full_name": attest.REPO}},
        "jobs": [{"id": 801, "name": attest.PRODUCER_JOB, "run_id": 501,
                  "status": "completed", "conclusion": "success"}],
        "artifacts": [{"id": 1001, "name": attest.ARTIFACT_NAME,
                       "expired": False, "digest": "sha256:" + attest.digest(archive),
                       "workflow_run": {"id": 501, "head_sha": COMMIT}}],
    }
    pin = {"run_id": 501, "attempt": 1, "commit": COMMIT, "completed": False}
    return metadata, pin, archive


class HistoricalReuseTests(unittest.TestCase):
    def test_matching_authenticated_history_is_only_bounded_reuse(self):
        metadata, pin, archive = fixture()
        outcome = attest.evaluate(metadata, pin, archive, SOURCE, {})
        self.assertEqual(outcome["status"], "REUSABLE_BOUNDED")
        self.assertFalse(outcome["fresh_check"])
        self.assertEqual(outcome["kernel_invocations_in_reader"], 0)
        self.assertEqual(outcome["historical_kernel_result"], "ACCEPT")

    def test_changed_source_or_flag_is_unknown(self):
        metadata, pin, archive = fixture()
        for source, env in ((SOURCE + b" ", {}), (SOURCE, {"NUCLEUS_X": "1"})):
            with self.subTest(source=source, flags=env):
                result = attest.evaluate(metadata, pin, archive, source, env)
                self.assertEqual(result["status"], "UNKNOWN")

    def test_bad_producer_metadata_is_unknown(self):
        for category in ("run_status", "run_sha", "producer_job", "artifact_expired",
                         "wrong_artifact_run", "wrong_artifact_digest"):
            metadata, pin, archive = fixture()
            if category == "run_status":
                metadata["run"]["status"] = "completed"
            elif category == "run_sha":
                metadata["run"]["head_sha"] = "b" * 40
            elif category == "producer_job":
                metadata["jobs"][0]["conclusion"] = "failure"
            elif category == "artifact_expired":
                metadata["artifacts"][0]["expired"] = True
            elif category == "wrong_artifact_run":
                metadata["artifacts"][0]["workflow_run"]["id"] = 999
            else:
                metadata["artifacts"][0]["digest"] = "sha256:" + "0" * 64
            with self.subTest(category=category):
                result = attest.evaluate(metadata, pin, archive, SOURCE, {})
                self.assertEqual(result["status"], "UNKNOWN")

    def test_corrupt_binary_and_root_fail_closed(self):
        for kw in ({"binary": BINARY + b"#forged\n"},
                   {"root": ROOT + b"#forged\n"}):
            metadata, pin, archive = fixture(**kw)
            with self.subTest(corruption=list(kw)):
                result = attest.evaluate(metadata, pin, archive, SOURCE, {})
                self.assertEqual(result["status"], "UNKNOWN")

    def test_producer_report_cannot_claim_a_nonzero_checker_verdict(self):
        metadata, pin, archive = fixture(report_override={"kernel_exit_code": 2})
        result = attest.evaluate(metadata, pin, archive, SOURCE, {})
        self.assertEqual(result["status"], "UNKNOWN")

    def test_graph_corruption_after_digest_validation_is_unknown(self):
        metadata, pin, archive = fixture()

        def corrupt(directory: Path):
            (directory / "store/root.json").write_text("invalid root")

        # This fake inspector is intentionally dishonest; the independent
        # root remeasurement must still catch a post-measurement mutation.
        self.assertEqual(attest.evaluate(metadata, pin, archive, SOURCE, {},
                                        before_inspect=corrupt)["status"], "UNKNOWN")

    def test_duplicate_json_keys_are_not_accepted(self):
        with self.assertRaises(ValueError):
            attest.strict_json(b'{"status":"WARRANTED_BOUNDED","status":"ACCEPT"}')

    def test_completed_cross_run_must_have_successful_run(self):
        metadata, pin, archive = fixture()
        pin["completed"] = True
        self.assertEqual(attest.evaluate(metadata, pin, archive, SOURCE, {})["status"], "UNKNOWN")
        metadata["run"]["status"] = "completed"
        metadata["run"]["conclusion"] = "success"
        self.assertEqual(attest.evaluate(metadata, pin, archive, SOURCE, {})["status"],
                         "REUSABLE_BOUNDED")

    def test_modified_zip_requires_new_external_github_digest(self):
        metadata, pin, archive = fixture()
        self.assertIsNotNone(attest.validate_metadata(metadata, pin, archive + b"x"))

    def test_forged_digest_targets_named_producer_even_if_reader_artifact_comes_first(self):
        metadata, pin, archive = fixture()
        reader_artifact = {"id": 4001, "name": "reader-evidence", "digest": "sha256:" + "f" * 64}
        metadata["artifacts"].insert(0, reader_artifact)
        forged = native_controls.forge_producer_artifact_digest(metadata)
        self.assertEqual(forged["artifacts"][0], reader_artifact)
        self.assertEqual(attest.validate_metadata(forged, pin, archive),
                         "PRODUCER_ARTIFACT_DIGEST_OR_PROVENANCE_MISMATCH")

    def test_artifact_download_uses_github_cli_authenticated_redirect(self):
        metadata, _, archive = fixture()
        class Result:
            returncode = 0
            stdout = archive
            stderr = b""
        with patch("attest.subprocess.run", return_value=Result()) as run:
            raw = attest.github_archive(metadata, "read-token")
        self.assertEqual(raw, archive)
        self.assertEqual(run.call_args.args[0],
                         ["gh", "api", "repos/heathsanchez/test/actions/artifacts/1001/zip"])
        self.assertEqual(run.call_args.kwargs["env"]["GH_TOKEN"], "read-token")


if __name__ == "__main__":
    unittest.main()
