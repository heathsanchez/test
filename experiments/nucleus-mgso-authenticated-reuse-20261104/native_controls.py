"""Real Nucleus binary controls for the authenticated MGSO reader in CI."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys

import attest


def forge_producer_artifact_digest(metadata: dict) -> dict:
    """Mutate the *named producer*, never another run's reader artifact."""
    forged = copy.deepcopy(metadata)
    target = [artifact for artifact in forged["artifacts"]
              if artifact.get("name") == attest.ARTIFACT_NAME]
    assert len(target) == 1
    target[0]["digest"] = "sha256:" + "0" * 64
    return forged


def forge_producer_job_failure(metadata: dict) -> dict:
    """Invalidate only the completed proof producer, not a reader job."""
    forged = copy.deepcopy(metadata)
    target = [job for job in forged["jobs"]
              if job.get("name") == attest.PRODUCER_JOB]
    assert len(target) == 1
    target[0]["conclusion"] = "failure"
    return forged


def main() -> int:
    if len(sys.argv) not in (4, 5) or (len(sys.argv) == 5 and sys.argv[4] != "--completed"):
        raise SystemExit("usage: native_controls.py RUN_ID SHA SOURCE [--completed]")
    run_id, commit, source_path = int(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    completed = len(sys.argv) == 5
    token = os.environ["GITHUB_TOKEN"]
    metadata = attest.github_metadata(run_id, token)
    archive = attest.github_archive(metadata, token)
    pin = {"run_id": run_id, "commit": commit, "attempt": 1, "completed": completed}
    source = source_path.read_bytes()
    current_env = dict(os.environ)
    checks = {}

    def record(label, result, expected):
        checks[label] = result["status"]
        assert result["status"] == expected, (label, result)

    record("authenticated_exact_reuse", attest.evaluate(metadata, pin, archive, source,
                                                       current_env), "REUSABLE_BOUNDED")
    record("source_byte_mutation", attest.evaluate(metadata, pin, archive, source + b" ",
                                                    current_env), "UNKNOWN")
    record("config_flag_mutation", attest.evaluate(metadata, pin, archive, source,
                                                   current_env | {"NUCLEUS_PROVENANCE_DRIFT": "1"}),
           "UNKNOWN")
    forged = forge_producer_job_failure(metadata)
    assert attest.validate_metadata(forged, pin, archive) == "PRODUCER_JOB_NOT_AUTHENTICATED"
    record("forged_successful_job", attest.evaluate(forged, pin, archive, source,
                                                    current_env), "UNKNOWN")
    forged = forge_producer_artifact_digest(metadata)
    assert (attest.validate_metadata(forged, pin, archive)
            == "PRODUCER_ARTIFACT_DIGEST_OR_PROVENANCE_MISMATCH")
    record("forged_artifact_digest", attest.evaluate(forged, pin, archive, source,
                                                     current_env), "UNKNOWN")

    def mutate_object(directory: Path):
        objects = sorted((directory / "store/objects").glob("*.mgso"))
        assert objects
        first = objects[0]
        first.write_bytes(first.read_bytes() + b"corrupt")

    record("forged_graph_object", attest.evaluate(metadata, pin, archive, source,
                                                  current_env, before_inspect=mutate_object),
           "UNKNOWN")
    result = {"status": "WARRANTED_BOUNDED" if all(
                  value == ("REUSABLE_BOUNDED" if key == "authenticated_exact_reuse" else "UNKNOWN")
                  for key, value in checks.items()) else "UNKNOWN",
              "cases": checks, "count": len(checks),
              "no_fresh_kernel_invocation": True,
              "proof_authority": "PINNED_COMPLETED_GITHUB_RUN" if completed
              else "PINNED_SAME_RUN_COMPLETED_GITHUB_JOB"}
    Path("/tmp/nucleus-mgso-reader-summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "WARRANTED_BOUNDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
