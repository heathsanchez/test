"""Independently qualify opt-in, phase-separated Nucleus V2 decision reads.

Every status comes from a freshly executed native checker. A V2 observation
has zero proof-reuse authority regardless of how well its source IDs match.
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


HERE = Path(__file__).resolve()
V1 = HERE.parents[1] / "nucleus-semantic-witness-v1-20261104"
V3 = HERE.parents[1] / "nucleus-mgso-dependency-inventory-20261104"
sys.path.insert(0, str(V1))
sys.path.insert(0, str(V3))
from qualification import EXPECTED_EXIT, PINNED_FIXTURE_SHA256, RUN_ENV, generate_cases  # noqa: E402
from semantic_inventory import compare  # noqa: E402


PREFIX = b"NUCLEUS_SEMANTIC_V2:"
EXIT = {0: "Accept", 1: "Reject", 2: "Unknown", 3: "Error"}
HEX_SHA = re.compile(r"^[a-f0-9]{64}$")
MAX_WITNESS_BYTES = 32 << 20
GUARD_OUTCOMES = {"PASS", "REJECT", "DEFER"}


def _object_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate JSON key: {name}")
        result[name] = value
    return result


def _parse_json(raw):
    return json.loads(raw, object_pairs_hook=_object_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def _uint(value):
    return type(value) is int and 0 <= value < (1 << 64)


def _authority(record):
    if record.get("verification_reuse_authority") != "NONE" or record.get("proof_skips") != 0:
        raise ValueError("witness acquired proof authority")
    if record.get("read_coverage") != "PARTIAL":
        raise ValueError("unwarranted complete read coverage")


def _tables(rows):
    if not isinstance(rows, list):
        raise ValueError("missing table read set")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"table", "access", "id", "present"}:
            raise ValueError("malformed table read")
        if row["table"] not in {"name", "level", "expression", "declaration"}:
            raise ValueError("invalid table kind")
        if row["access"] == "point":
            if not _uint(row["id"]) or type(row["present"]) is not bool:
                raise ValueError("bad point lookup")
        elif row["access"] == "bulk":
            if row["id"] is not None or row["present"] is not None:
                raise ValueError("bulk scan falsely reduced to one key")
        else:
            raise ValueError("invalid table access")
    ordering = lambda row: (row["table"], row["access"], -1 if row["id"] is None else row["id"],
                            -1 if row["present"] is None else int(row["present"]))
    if rows != sorted(rows, key=ordering) or len({ordering(x) for x in rows}) != len(rows):
        raise ValueError("unordered or duplicate table events")


def _environment(rows):
    if not isinstance(rows, list):
        raise ValueError("missing environment reads")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"channel", "name_id", "present"}:
            raise ValueError("malformed environment read")
        if not isinstance(row["channel"], str) or not row["channel"]:
            raise ValueError("missing environment channel")
        if row["name_id"] is not None and not _uint(row["name_id"]):
            raise ValueError("bad environment key")
        if row["present"] is not None and type(row["present"]) is not bool:
            raise ValueError("bad environment membership")
    ordering = lambda row: (row["channel"], -1 if row["name_id"] is None else row["name_id"],
                            -1 if row["present"] is None else int(row["present"]))
    if rows != sorted(rows, key=ordering) or len({ordering(x) for x in rows}) != len(rows):
        raise ValueError("unordered or duplicate environment events")


def _constants(rows):
    if not isinstance(rows, list):
        raise ValueError("missing constant reads")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"name_id", "present"} \
                or not _uint(row["name_id"]) or type(row["present"]) is not bool:
            raise ValueError("malformed constant read")
    ordering = lambda row: (row["name_id"], row["present"])
    if rows != sorted(rows, key=ordering) or len({ordering(x) for x in rows}) != len(rows):
        raise ValueError("unordered or duplicate constant reads")


def parse_v2(source: bytes, returncode: int, stderr: bytes):
    """Parse one native summary and reject forged claims or incomplete identities."""
    if type(source) is not bytes or returncode not in EXIT or type(stderr) is not bytes \
            or len(stderr) > MAX_WITNESS_BYTES:
        raise ValueError("unsupported witness input")
    records = [row[len(PREFIX):] for row in stderr.splitlines() if row.startswith(PREFIX)]
    if len(records) != 1:
        raise ValueError("missing or duplicate terminal V2 record")
    packet = _parse_json(records[0])
    if not isinstance(packet, dict):
        raise ValueError("non-object witness")
    identity = hashlib.sha256(source).hexdigest()
    _authority(packet)
    if packet.get("semantic_dependency_completeness") != "UNKNOWN" or \
            packet.get("global_barrier") != "whole-export-sha256":
        raise ValueError("unsafe dependency completeness or barrier")
    if packet.get("source_sha256") != identity or not HEX_SHA.fullmatch(identity):
        raise ValueError("source SHA mismatch")
    if packet.get("status") != EXIT[returncode]:
        raise ValueError("exit and status differ")
    global_trace = packet.get("global")
    if not isinstance(global_trace, dict) or set(global_trace) != {
        "source_resolution_reads", "preflight_reads", "guards"
    }:
        raise ValueError("missing global read scope")
    _tables(global_trace["source_resolution_reads"])
    _tables(global_trace["preflight_reads"])
    guards = global_trace["guards"]
    if not isinstance(guards, list):
        raise ValueError("missing global guard decisions")
    stages = []
    for guard in guards:
        if not isinstance(guard, dict) or set(guard) != {"stage", "result"} \
                or not isinstance(guard["stage"], str) or not guard["stage"] \
                or guard["result"] not in GUARD_OUTCOMES:
            raise ValueError("invalid global guard")
        stages.append(guard["stage"])
    if len(stages) != len(set(stages)):
        raise ValueError("duplicate global guard")
    if returncode == 0 and not any(x == {
        "stage": "quotient-source-ownership", "result": "PASS"
    } for x in guards):
        raise ValueError("accepted export lacks global guard admission")
    if any(guard["result"] == "REJECT" for guard in guards) and returncode == 0:
        raise ValueError("global guard rejects an accepted export")
    declarations = packet.get("declarations")
    if not isinstance(declarations, list) or (returncode != 0 and declarations):
        raise ValueError("provisional admissions survived failed export")
    indices = []
    for declaration in declarations:
        if not isinstance(declaration, dict) or not _uint(declaration.get("index")) \
                or not isinstance(declaration.get("name"), str) \
                or not isinstance(declaration.get("kind"), str):
            raise ValueError("bad declaration identity")
        if declaration.get("global_export_sha256") != identity:
            raise ValueError("local declaration stale source")
        _authority(declaration)
        _tables(declaration.get("table_reads"))
        _environment(declaration.get("environment_reads"))
        _constants(declaration.get("constant_reads"))
        indices.append(declaration["index"])
    if indices != sorted(set(indices)):
        raise ValueError("duplicate or out-of-order admissions")
    return packet


def _run(binary, source, flag=None):
    command = [str(binary)]
    if flag:
        command.append(flag)
    p = subprocess.run(command, input=source, capture_output=True, env=RUN_ENV,
                       timeout=60, check=False)
    if p.stdout or p.returncode not in EXIT:
        raise ValueError("native Nucleus output/exit violates protocol")
    return p


def qualify_v2(binary: Path, fixture: Path, fixtures: Path):
    binary = binary.resolve(strict=True)
    fixture = fixture.resolve(strict=True)
    fixtures = fixtures.resolve(strict=True)
    if binary.is_symlink() or not binary.is_file() or binary.open("rb").read(4) != b"\x7fELF":
        raise ValueError("not native Nucleus ELF")
    source = fixture.read_bytes()
    if hashlib.sha256(source).hexdigest() != PINNED_FIXTURE_SHA256:
        raise ValueError("source fixture drift")
    cases = list(generate_cases(source))
    if len(cases) != 7:
        raise ValueError("mutation case count drift")
    mutations = []
    for name, data in cases:
        plain = _run(binary, data)
        witnessed = _run(binary, data, "--semantic-read-witness-v2")
        if plain.returncode != EXPECTED_EXIT[name] or witnessed.returncode != plain.returncode:
            raise ValueError(f"native checker verdict drift: {name}")
        packet = parse_v2(data, witnessed.returncode, witnessed.stderr)
        if name == "original":
            if not any(x.get("name") == "thmProof" and
                       any(read.get("table") == "expression" and read.get("access") == "point"
                           for read in x["table_reads"]) and
                       {"channel": "constant", "name_id": 1, "present": True} in x["environment_reads"]
                       for x in packet["declarations"]):
                raise ValueError("missing genuine theorem decision-path reads")
        if name == "global_quotient_forgery":
            if packet["declarations"] or {"stage": "quotient-source-ownership", "result": "REJECT"} \
                    not in packet["global"]["guards"]:
                raise ValueError("missed global quotient falsifier")
        mutations.append({"case": name, "source_sha256": packet["source_sha256"],
                          "native_exit": plain.returncode,
                          "observed_declarations": len(packet["declarations"]),
                          "global_guards": packet["global"]["guards"], "proof_skips": 0})
    if compare(source, dict(cases)["global_quotient_forgery"])["candidate_reuse_count"] != 2:
        raise ValueError("V3 theorem-local falsifier changed")
    paths = sorted(fixtures.glob("*.ndjson"))
    if len(paths) != 55:
        raise ValueError(f"protected corpus count changed: {len(paths)}")
    corpus = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError("invalid fixture")
        data = path.read_bytes()
        plain = _run(binary, data)
        witnessed = _run(binary, data, "--semantic-read-witness-v2")
        if plain.returncode != witnessed.returncode:
            raise ValueError(f"native witness verdict drift: {path.name}")
        packet = parse_v2(data, witnessed.returncode, witnessed.stderr)
        corpus.append({"fixture": path.name, "source_sha256": packet["source_sha256"],
                       "native_exit": plain.returncode,
                       "observed_declarations": len(packet["declarations"]),
                       "proof_skips": 0})
    census = Counter(row["native_exit"] for row in corpus)
    if dict(census) != {0: 33, 1: 16, 2: 6}:
        raise ValueError(f"protected corpus census drift: {dict(census)}")
    return {
        "type": "nucleus.kernel-semantic-decision-witness.v2",
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "source_pin": PINNED_FIXTURE_SHA256,
        "mutation_count": len(mutations), "protected_fixtures": len(corpus),
        "plain_native_checks": len(mutations) + len(corpus),
        "witnessed_native_checks": len(mutations) + len(corpus),
        "native_verdict_census": {str(key): count for key, count in sorted(census.items())},
        "read_coverage": "PARTIAL", "semantic_dependency_completeness": "UNKNOWN",
        "global_barrier": "whole-export-sha256", "verification_reuse_authority": "NONE",
        "proof_skips": 0, "mutations": mutations, "corpus": corpus,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--fixtures", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = qualify_v2(args.binary, args.fixture, args.fixtures)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"mutations", "corpus"}}, sort_keys=True))


if __name__ == "__main__":
    main()
