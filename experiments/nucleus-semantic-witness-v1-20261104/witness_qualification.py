"""Source-pinned native Nucleus read-witness qualification; no proof reuse.

The witness is deliberately partial. Only the ordinary, freshly executed
Rust Nucleus verdict is evidence for admission; a matching witness never is.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


SOURCE_SCRIPTS = Path(__file__).resolve().parents[1] / "nucleus-mgso-dependency-inventory-20261104"
sys.path.insert(0, str(SOURCE_SCRIPTS))
from qualification import EXPECTED_EXIT, PINNED_FIXTURE_SHA256, RUN_ENV, generate_cases  # noqa: E402
from semantic_inventory import compare  # noqa: E402


READ_PREFIX = b"NUCLEUS_SEMANTIC_READ:"
SUMMARY_PREFIX = b"NUCLEUS_SEMANTIC_SUMMARY:"
VERDICT = {0: "Accept", 1: "Reject", 2: "Unknown", 3: "Error"}
MAX_WITNESS_BYTES = 32 << 20
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _unique_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate witness key: {name}")
        result[name] = value
    return result


def _parse_json(raw):
    value = json.loads(raw, object_pairs_hook=_unique_pairs,
                       parse_constant=lambda token: (_ for _ in ()).throw(
                           ValueError(f"invalid numeric token: {token}")))
    if not isinstance(value, dict):
        raise ValueError("witness record must be an object")
    return value


def _nonnegative(value):
    return type(value) is int and 0 <= value < 2**64


def _authority(record):
    if record.get("verification_reuse_authority") != "NONE" or record.get("proof_skips") != 0:
        raise ValueError("witness acquired proof authority or skipped checking")
    if record.get("read_coverage") != "PARTIAL":
        raise ValueError("witness falsely claimed complete coverage")


def parse_witness_output(source: bytes, returncode: int, stderr: bytes) -> dict:
    """Fail closed on forged/misidentified, out-of-order or incomplete records."""
    if returncode not in VERDICT or not isinstance(source, bytes) or len(stderr) > MAX_WITNESS_BYTES:
        raise ValueError("unsupported native witness result")
    identity = hashlib.sha256(source).hexdigest()
    events, summary = [], None
    for raw in stderr.splitlines():
        if raw.startswith(READ_PREFIX):
            if summary is not None:
                raise ValueError("read appeared after terminal summary")
            event = _parse_json(raw[len(READ_PREFIX):])
            _authority(event)
            if event.get("global_export_sha256") != identity:
                raise ValueError("read source identity mismatch")
            if not (_nonnegative(event.get("index")) and isinstance(event.get("name"), str)
                    and isinstance(event.get("kind"), str)):
                raise ValueError("malformed declaration read identity")
            reads = event.get("constant_reads")
            if not isinstance(reads, list):
                raise ValueError("missing read list")
            for read in reads:
                if not isinstance(read, dict) or set(read) != {"name_id", "present"} \
                        or not _nonnegative(read["name_id"]) or type(read["present"]) is not bool:
                    raise ValueError("malformed kernel constant read")
            if reads != sorted(reads, key=lambda item: (item["name_id"], item["present"])) \
                    or len(reads) != len({(item["name_id"], item["present"]) for item in reads}):
                raise ValueError("unordered or duplicate constant reads")
            events.append(event)
        elif raw.startswith(SUMMARY_PREFIX):
            if summary is not None:
                raise ValueError("multiple witness summaries")
            summary = _parse_json(raw[len(SUMMARY_PREFIX):])
    if summary is None:
        raise ValueError("missing terminal witness summary")
    _authority(summary)
    if summary.get("source_sha256") != identity or not SHA256.fullmatch(summary["source_sha256"]):
        raise ValueError("summary source identity mismatch")
    if summary.get("global_barrier") != "whole-export-sha256":
        raise ValueError("global barrier missing")
    if summary.get("status") != VERDICT[returncode]:
        raise ValueError("native exit code and witness status disagree")
    if not _nonnegative(summary.get("observed_declarations")) \
            or summary["observed_declarations"] != len(events):
        raise ValueError("witness declaration count mismatch")
    if returncode != 0 and events:
        raise ValueError("non-accept export retained admission witnesses")
    indices = [event["index"] for event in events]
    if indices != sorted(set(indices)):
        raise ValueError("duplicate or reordered admissions")
    return {"verdict": summary["status"], "source_sha256": identity,
            "events": events, "authority": "NONE", "proof_skips": 0,
            "global_barrier": summary["global_barrier"], "read_coverage": "PARTIAL"}


def _run(binary: Path, source: bytes, args=()):
    execution = subprocess.run([str(binary), *args], input=source, capture_output=True,
                               env=RUN_ENV, timeout=60, check=False)
    if execution.stdout or execution.returncode not in VERDICT:
        raise ValueError("native Nucleus emitted unexpected stdout or exit")
    return execution


def qualify(binary: Path, fixture: Path, fixtures: Path) -> dict:
    binary = binary.resolve(strict=True)
    fixture = fixture.resolve(strict=True)
    fixtures = fixtures.resolve(strict=True)
    if binary.is_symlink() or not binary.is_file() or binary.open("rb").read(4) != b"\x7fELF":
        raise ValueError("not the native Nucleus ELF")
    source = fixture.read_bytes()
    if hashlib.sha256(source).hexdigest() != PINNED_FIXTURE_SHA256:
        raise ValueError("source fixture drift")
    mutation_results = []
    for case, variant in generate_cases(source):
        plain, witnessed = _run(binary, variant), _run(binary, variant, ("--semantic-read-witness",))
        if plain.returncode != EXPECTED_EXIT[case] or witnessed.returncode != plain.returncode:
            raise ValueError(f"kernel verdict drift in mutation {case}")
        parsed = parse_witness_output(variant, witnessed.returncode, witnessed.stderr)
        if case == "original":
            if not any(event["name"] == "thmProof" and
                       {"name_id": 1, "present": True} in event["constant_reads"]
                       for event in parsed["events"]):
                raise ValueError("missing real theorem environment read")
        mutation_results.append({
            "case": case, "source_sha256": parsed["source_sha256"],
            "native_exit_code": plain.returncode,
            "witnessed_exit_code": witnessed.returncode,
            "admitted_declarations": len(parsed["events"]),
            "observed_constant_reads": sum(len(x["constant_reads"]) for x in parsed["events"]),
            "read_coverage": parsed["read_coverage"], "global_barrier": parsed["global_barrier"],
            "verification_reuse_authority": "NONE", "proof_skips": 0,
        })
    if compare(source, dict(generate_cases(source))["global_quotient_forgery"])["candidate_reuse_count"] != 2:
        raise ValueError("global source counterexample no longer holds")
    paths = sorted(fixtures.glob("*.ndjson"))
    if len(paths) != 55:
        raise ValueError(f"unexpected protected fixture count: {len(paths)}")
    corpus = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError("invalid protected fixture")
        variant = path.read_bytes()
        plain, witnessed = _run(binary, variant), _run(binary, variant, ("--semantic-read-witness",))
        if plain.returncode != witnessed.returncode:
            raise ValueError(f"kernel verdict drift for {path.name}")
        parsed = parse_witness_output(variant, witnessed.returncode, witnessed.stderr)
        corpus.append({"fixture": path.name, "source_sha256": parsed["source_sha256"],
                       "native_exit_code": plain.returncode,
                       "observed_declarations": len(parsed["events"]),
                       "read_coverage": "PARTIAL", "proof_skips": 0})
    census = Counter(row["native_exit_code"] for row in corpus)
    # V3 source-native protected census is a pinned regression contract.
    if dict(census) != {0: 33, 1: 16, 2: 6}:
        raise ValueError(f"protected native verdict census changed: {dict(census)}")
    return {"type": "nucleus.kernel-read-witness-qualification.v1",
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "source_pin": PINNED_FIXTURE_SHA256,
            "mutation_count": len(mutation_results), "protected_fixtures": len(corpus),
            "plain_native_checks": len(mutation_results) + len(corpus),
            "witnessed_native_checks": len(mutation_results) + len(corpus),
            "native_verdict_census": {str(k): count for k, count in sorted(census.items())},
            "verification_reuse_authority": "NONE", "proof_skips": 0,
            "semantic_dependency_completeness": "UNKNOWN",
            "mutations": mutation_results, "corpus": corpus}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.binary, args.fixture, args.fixtures)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("mutations", "corpus")}, sort_keys=True))


if __name__ == "__main__":
    main()
