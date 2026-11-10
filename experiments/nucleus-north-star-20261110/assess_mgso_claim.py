"""Observation-only claim adequacy control on the existing Nucleus MGSO CLI.

MGSO candidate identity never entails the synthetic intended claim, nor does
it return an ACCEPT verdict in inspection mode. The native checker and the
MGSO store remain unmodified; this is an exact-source experiment only.
"""

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

from assess_claim_fidelity import assess


# Exact source proved by the pinned Lean 4.34.1 workflow. This *synthetic*
# witness may not be promoted under a changed proof file, even if the
# separately exported weaker declaration has byte-identical NDJSON.
PINNED_LEAN_WITNESS_SHA256 = (
    "7765dedab06ed7d6fd83b3f8ed895f444a992506b7cab9c5084f8c94a99ff670"
)


def require_exact_lean_witness_source(source: bytes) -> str:
    digest = hashlib.sha256(source).hexdigest()
    assert digest == PINNED_LEAN_WITNESS_SHA256, (
        "changed Lean separation witness needs new source-qualified adequacy evidence"
    )
    return digest


def parse_synthetic_contract(raw: bytes) -> dict:
    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate synthetic contract key: {key}")
            result[key] = value
        return result

    contract = json.loads(raw, object_pairs_hook=unique_fields)
    assert isinstance(contract, dict), "synthetic contract must be a JSON object"
    return contract


def _line_fields(stderr: str, prefix: str) -> dict[str, str]:
    matches = [line for line in stderr.splitlines() if line.startswith(prefix + ":")]
    assert len(matches) == 1, "missing, repeated or ambiguous MGSO observation"
    fields = {}
    for part in matches[0][len(prefix) + 1:].split(";"):
        key, sep, value = part.partition("=")
        assert sep and key and key not in fields, "invalid or duplicated MGSO observation field"
        fields[key] = value
    return fields


def require_observation(exit_code: int, stderr: str) -> str:
    """A candidate match is only historical identity, never fresh proof."""
    fields = _line_fields(stderr, "NUCLEUS_MGSO_INSPECT")
    assert exit_code == 2
    assert fields.get("status") == "candidate-match"
    assert fields.get("authority") == "none"
    assert fields.get("fresh-check") == "false"
    assert fields.get("declarations", "").isdecimal()
    assert int(fields["declarations"]) >= 1
    return "candidate-match"


def require_stale_inspection(exit_code: int, stderr: str) -> str:
    fields = _line_fields(stderr, "NUCLEUS_MGSO_INSPECT")
    assert exit_code == 2
    assert fields.get("status") == "stale"
    assert fields.get("authority") == "none"
    assert fields.get("fresh-check") == "false"
    assert fields.get("reason")
    return "stale"


def run_checker(binary: str, args: list[str], source: bytes) -> subprocess.CompletedProcess:
    return subprocess.run([binary, *args], input=source, capture_output=True, timeout=90)


def assess_mgso(raw: bytes, lean_log: str, contract: dict,
                lean_source: bytes, binary: str) -> dict:
    lean_source_sha256 = require_exact_lean_witness_source(lean_source)
    claim = assess(raw, lean_log, contract, binary)
    direct = run_checker(binary, [], raw)
    assert direct.returncode == 0, "fresh independent checker refused source"
    with tempfile.TemporaryDirectory(prefix="nucleus-mgso-claim-") as tmp:
        path = pathlib.Path(tmp)
        first = run_checker(binary, ["--mgso-shadow-dir", str(path)], raw)
        assert (first.returncode, first.stdout) == (direct.returncode, direct.stdout), (
            "MGSO changed a fresh verifier verdict or output"
        )
        manifest = path / "root.json"
        assert manifest.is_file(), "ACCEPT generated no MGSO root"
        root_before = hashlib.sha256(manifest.read_bytes()).hexdigest()
        inspected = run_checker(binary, ["--mgso-inspect-dir", str(path)], raw)
        observed = require_observation(
            inspected.returncode, inspected.stderr.decode(errors="replace")
        )
        assert inspected.stdout == b"", "inspection unexpectedly produced proof output"
        drifted = run_checker(binary, ["--mgso-inspect-dir", str(path)], raw + b"\n")
        mutation = require_stale_inspection(
            drifted.returncode, drifted.stderr.decode(errors="replace")
        )
        assert root_before == hashlib.sha256(manifest.read_bytes()).hexdigest(), (
            "inspection unexpectedly changed historical receipt"
        )
    return {
        "status": "BOUNDED_MGSO_SYNTHETIC_CLAIM_SEPARATION",
        "claim_assessment": claim,
        "fresh_nucleus_verdict": "ACCEPT",
        "fresh_shadow_verdict": "ACCEPT",
        "mgso_historical_candidate": observed,
        "mgso_inspection_verdict": "UNKNOWN_EXIT_2",
        "mgso_inspection_authority": "none",
        "modified_export_inspection": mutation,
        "synthetic_intent_adequacy": "REFUTED_BY_LEAN_WITNESS",
        "real_owner_intent_adequacy": "UNKNOWN",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "lean_witness_source_sha256": lean_source_sha256,
        "observed_root_sha256": root_before,
    }


def main(export_path: str, lean_log_path: str, contract_path: str,
         lean_source_path: str, binary: str, report_path: str) -> None:
    report = {"status": "UNKNOWN", "real_owner_intent_adequacy": "UNKNOWN"}
    try:
        report = assess_mgso(
            pathlib.Path(export_path).read_bytes(),
            pathlib.Path(lean_log_path).read_text(),
            parse_synthetic_contract(pathlib.Path(contract_path).read_bytes()),
            pathlib.Path(lean_source_path).read_bytes(),
            binary,
        )
    except Exception as exc:
        report["failure"] = str(exc)
        raise
    finally:
        pathlib.Path(report_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main(*sys.argv[1:])
