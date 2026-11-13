#!/usr/bin/env python3
"""C126: original-source N7 function-head budget discriminator on C105 lineage.

Read-only diagnostic research, not a kernel rule, C124 replay, or ACCEPT claim.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


SOURCE_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
PREFIX = "NUCLEUS_C126_N7_HEAD:"
BUDGETS = (65_536, 14_155_776)
KEYS = {"application", "function", "argument", "before", "after", "context",
        "pi_head", "type_proven"}


def parse_traces(stderr: bytes):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        head, value = line[len(PREFIX):].split(":type=", 1)
        fields = dict(piece.split("=", 1) for piece in head.split(":"))
        assert KEYS <= fields.keys(), line
        assert (int(fields["application"]), int(fields["function"]),
                int(fields["argument"])) == (8835, 8805, 8834), line
        before, after = int(fields["before"]), int(fields["after"])
        assert 0 <= after <= before, (before, after)
        assert fields["pi_head"] in ("true", "false")
        assert fields["type_proven"] in ("true", "false")
        rows.append({"context": int(fields["context"]),
                     "before": before, "after": after,
                     "charged": before - after,
                     "pi_head": fields["pi_head"] == "true",
                     "type_proven": fields["type_proven"] == "true",
                     "type_preview": value[:800]})
    return rows


def validate_source(source: bytes):
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA256, "frozen N7 hash mismatch"
    app = None
    for line in source.splitlines():
        row = json.loads(line)
        if row.get("ie") == 8835:
            app = row.get("app")
            break
    assert app == {"fn": 8805, "arg": 8834}, "N7 expression 8835 shape drifted"


def summarize_owner_traces(stderr: bytes):
    """Capture resource-owner counters, not an inferred semantic equivalence."""
    lines = stderr.decode(errors="replace").splitlines()
    prefixes = ("NUCLEUS_C95_PHASE:", "NUCLEUS_C96_OWNER:",
                "NUCLEUS_C97_OWNER:", "NUCLEUS_C97_REPEAT_HEAD:",
                "NUCLEUS_NESTED_REPLAY_FAILURE:", "NUCLEUS_NESTED_RECURSOR_IOTA:")
    counts = {p[:-1]: sum(line.startswith(p) for line in lines) for p in prefixes}
    owners = [line for line in lines if line.startswith("NUCLEUS_C97_OWNER:")]
    def numeric(line, field):
        match = re.search(r"(?:^|:)" + re.escape(field) + r"=(\d+)(?=:|$)", line)
        return int(match.group(1)) if match else 0
    return {"counts": counts,
            "c97_total_spent": sum(numeric(line, "spent") for line in owners),
            "c97_max_spent": max((numeric(line, "spent") for line in owners), default=0),
            "c97_repeated_node_env": sum(numeric(line, "repeat_node_env") for line in owners),
            "c97_repeated_head_pending": sum(numeric(line, "repeat_head_pending") for line in owners),
            "owner_samples": owners[:3] + owners[-3:],
            "nested_failure_samples": [line[:350] for line in lines
                if line.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:")][:6],
            "source_rhs_samples": [line[:350] for line in lines
                if line.startswith("NUCLEUS_NESTED_RECURSOR_IOTA:")][:8]}


def run(binary: Path, source: bytes, budget: int, trace: bool,
        owner_trace: bool = False):
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(NUCLEUS_EXPERIMENTAL_RELEVANCE="1",
               NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR="1")
    if trace:
        env.update(NUCLEUS_C126_N7_TYPE_HEAD="1",
                   NUCLEUS_TRACE_CHECKED_RELEVANCE="1",
                   NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE="1",
                   NUCLEUS_TRACE_DOWNSTREAM="1")
        if owner_trace:
            env.update(NUCLEUS_C95_PHASE_TRACE="1",
                       NUCLEUS_C96_MAJOR_TRACE="1",
                       NUCLEUS_C97_MAJOR_STEP_TRACE="1",
                       NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE="1",
                       NUCLEUS_TRACE_NESTED_RECURSOR_IOTA="1")
    process = subprocess.run([str(binary), str(budget)], input=source,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=env, timeout=240)
    assert process.returncode in (0, 2), (budget, trace, process.returncode,
                                        process.stderr[-500:])
    return process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--budgets", nargs="+", type=int, default=BUDGETS,
                        help="source-native diagnostic budget ladder; original C126 pair is the default")
    parser.add_argument("--owner-trace", action="store_true",
                        help="C128 read-only nested recursor owner phase/cost receipts")
    args = parser.parse_args()
    source = args.source.read_bytes()
    validate_source(source)
    binary = args.binary.resolve()
    observations = []
    assert all(budget > 0 for budget in args.budgets), "budgets must be positive"
    assert len(args.budgets) == len(set(args.budgets)), "repeated budgets obscure the ladder"
    for budget in args.budgets:
        silent = run(binary, source, budget, False)
        observed = run(binary, source, budget, True, args.owner_trace)
        assert (silent.returncode, silent.stdout) == (observed.returncode, observed.stdout), (
            "observer changed the checker verdict or output", budget)
        heads = parse_traces(observed.stderr)
        assert heads, ("source 8835 type-head trace absent", budget)
        stderr_lines = observed.stderr.decode(errors="replace").splitlines()
        row = {"budget": budget,
                             "verdict_exit": observed.returncode,
                             "source_head_records": len(heads),
                             "pi_head_count": sum(r["pi_head"] for r in heads),
                             "proof_relevance_certificates": sum(
                                 s.startswith("NUCLEUS_CHECKED_RELEVANCE:")
                                 for s in stderr_lines),
                             "heads": heads[:8],
                             "last_downstream": [s[:350] for s in stderr_lines
                                                 if "NUCLEUS_DOWNSTREAM:" in s][-2:]}
        if args.owner_trace:
            row["owner_trace"] = summarize_owner_traces(observed.stderr)
        observations.append(row)
    print(json.dumps({"status": "CANDIDATE_C105_SURROGATE_NATIVE_REPLAY",
                      "lineage": "C105 descendant, not recovered C124/C125b source",
                      "source": "original unchanged magma-list-pair-n7",
                      "sha256": SOURCE_SHA256,
                      "configuration": ["NUCLEUS_EXPERIMENTAL_RELEVANCE",
                                        "NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"],
                      "observations": observations}, sort_keys=True))


if __name__ == "__main__":
    main()
