"""Qualify an actual Nucleus String postflight downgrade, without proof reuse.

The V2 observation protocol remains partial and cannot admit cached proofs.
This script compares two *fresh* native runs and reruns the pinned 7+55 suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


V2_DIR = Path(__file__).resolve().parents[1] / "nucleus-semantic-witness-v2-20261104"
sys.path.insert(0, str(V2_DIR))
from wire_qualification import PINNED_FIXTURE_SHA256, RUN_ENV, parse_v2, qualify_v2  # noqa: E402


POSTFLIGHT_STAGE = "postflight-string-literal-qualification"
UNQUALIFIED_SUFFIX = b'{"ie":999,"strVal":"unqualified"}\n'
DOWNGRADE_TRACE = (
    b"NUCLEUS_DOWNSTREAM:name=<string-literal-guard>:stage=string-literal-guard:"
    b"inner=Accept:verdict=Unknown"
)
SHA = re.compile(r"^[a-f0-9]{64}$")


def _last_guard(packet: dict, expected: str) -> None:
    guards = packet.get("global", {}).get("guards")
    if not isinstance(guards, list) or not guards or guards[-1] != {
        "stage": POSTFLIGHT_STAGE, "result": expected,
    } or sum(row.get("stage") == POSTFLIGHT_STAGE for row in guards) != 1:
        raise ValueError(f"missing or misordered executed postflight {expected} guard")


def _bulk_expression_in_both_phases(packet: dict) -> None:
    global_trace = packet.get("global", {})
    if not any(row.get("table") == "expression" and row.get("access") == "bulk"
               for row in global_trace.get("preflight_reads", [])):
        raise ValueError("outer semantic scan not in preflight phase")
    if not any(row.get("table") == "expression" and row.get("access") == "bulk"
               for row in global_trace.get("source_resolution_reads", [])):
        raise ValueError("parser validation scan omitted from source resolution")


def validate_pair(original: dict, downgraded: dict) -> dict:
    """Validate independently parsed native records; never infer proof authority."""
    for packet in (original, downgraded):
        if packet.get("verification_reuse_authority") != "NONE" or packet.get("proof_skips") != 0 \
                or packet.get("read_coverage") != "PARTIAL" \
                or packet.get("semantic_dependency_completeness") != "UNKNOWN" \
                or packet.get("global_barrier") != "whole-export-sha256":
            raise ValueError("unwarranted authority or missing whole-export guard")
        _bulk_expression_in_both_phases(packet)
    first, second = original.get("source_sha256"), downgraded.get("source_sha256")
    if not isinstance(first, str) or not isinstance(second, str) \
            or not SHA.fullmatch(first) or not SHA.fullmatch(second) or first == second:
        raise ValueError("source identity stale or malformed")
    if original.get("status") != "Accept" or downgraded.get("status") != "Unknown" \
            or not original.get("declarations") or downgraded.get("declarations"):
        raise ValueError("verdict/admission pair does not isolate final downgrade")
    _last_guard(original, "PASS")
    _last_guard(downgraded, "DEFER")
    if original["global"]["guards"][:-1] != downgraded["global"]["guards"][:-1]:
        raise ValueError("an earlier global guard changed, confounding downgrade")
    return {
        "verdict_pair": ["Accept", "Unknown"],
        "postflight_pair": ["PASS", "DEFER"],
        "source_sha256_pair": [first, second],
        "original_admissions": len(original["declarations"]),
        "nonaccept_admissions": 0,
        "global_preflight_guards_before_postflight": len(original["global"]["guards"]) - 1,
        "verification_reuse_authority": "NONE", "proof_skips": 0,
    }


def _native(binary: Path, source: bytes, flag: str | None = None, diagnostic: bool = False):
    env = dict(RUN_ENV)
    if diagnostic:
        env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    args = [str(binary)] + ([flag] if flag else [])
    run = subprocess.run(args, input=source, capture_output=True, env=env,
                         check=False, timeout=60)
    if run.stdout or run.returncode not in (0, 1, 2, 3):
        raise ValueError("native Nucleus invocation violated exit/output protocol")
    return run


def qualify(binary: Path, fixture: Path, fixtures: Path) -> dict:
    binary = binary.resolve(strict=True)
    fixture = fixture.resolve(strict=True)
    fixtures = fixtures.resolve(strict=True)
    if not binary.is_file() or binary.is_symlink() or binary.open("rb").read(4) != b"\x7fELF":
        raise ValueError("not a native independent Rust Nucleus ELF")
    source = fixture.read_bytes()
    if hashlib.sha256(source).hexdigest() != PINNED_FIXTURE_SHA256:
        raise ValueError("original source drift")
    appended = source + UNQUALIFIED_SUFFIX
    results = []
    for name, payload, expected in (("original", source, 0), ("unqualified_unused_string", appended, 2)):
        plain = _native(binary, payload)
        witnessed = _native(binary, payload, "--semantic-read-witness-v2")
        if plain.returncode != expected or witnessed.returncode != expected:
            raise ValueError(f"independent native verdict mismatch: {name}")
        packet = parse_v2(payload, witnessed.returncode, witnessed.stderr)
        results.append(packet)
    pair = validate_pair(*results)
    diagnostic = _native(binary, appended, diagnostic=True)
    if diagnostic.returncode != 2 or DOWNGRADE_TRACE not in diagnostic.stderr:
        raise ValueError("independent native downstream trace did not confirm inner ACCEPT")
    controls = qualify_v2(binary, fixture, fixtures)
    if controls["mutation_count"] != 7 or controls["protected_fixtures"] != 55 \
            or controls["plain_native_checks"] != 62 or controls["witnessed_native_checks"] != 62 \
            or controls["proof_skips"] != 0:
        raise ValueError("prior V2 bounded native qualification regressed")
    return {
        "type": "nucleus.executed-postflight-global-read.v1",
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "source_pin": PINNED_FIXTURE_SHA256,
        "pair": pair,
        "independent_inner_accept_trace": True,
        "new_plain_native_checks": 3,
        "new_witnessed_native_checks": 2,
        "protected_v2_plain_checks": controls["plain_native_checks"],
        "protected_v2_witnessed_checks": controls["witnessed_native_checks"],
        "protected_v2_census": controls["native_verdict_census"],
        "global_barrier": "whole-export-sha256",
        "read_coverage": "PARTIAL",
        "semantic_dependency_completeness": "UNKNOWN",
        "verification_reuse_authority": "NONE", "proof_skips": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = qualify(args.binary, args.fixture, args.fixtures)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
