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
EDGE_PREFIX = "NUCLEUS_C129_APP_EDGE:"
ARG_PREFIX = "NUCLEUS_C130_APP_ARG:"
CONVERSION_INFER_PREFIX = "NUCLEUS_C131_ARG_INFER:"
CONVERSION_RELATION_PREFIX = "NUCLEUS_C131_ARG_CONVERT:"


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


def source_app_edges(source: bytes):
    """The exact exported AST, not guessed function-spine associations."""
    return {row["ie"]: row["app"] for line in source.splitlines()
            if (row := json.loads(line)).get("ie") is not None
            and isinstance(row.get("app"), dict)}


def parse_app_edges(stderr: bytes, source_edges):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(EDGE_PREFIX):
            continue
        fields = dict(item.split("=", 1) for item in line[len(EDGE_PREFIX):].split(":"))
        app, fun, arg = (int(fields[key]) for key in ("app", "fun", "arg"))
        assert source_edges.get(app) == {"fn": fun, "arg": arg}, line
        before, after = int(fields["before"]), int(fields["after"])
        assert before >= after >= 0, line
        assert fields["pi_head"] in ("true", "false"), line
        assert fields["type_proven"] in ("true", "false"), line
        rows.append({"app": app, "fun": fun, "arg": arg, "context": int(fields["context"]),
                     "charged": before - after, "before": before, "after": after,
                     "pi_head": fields["pi_head"] == "true",
                     "type_proven": fields["type_proven"] == "true"})
    return rows


def parse_arg_obligations(stderr: bytes, source_edges):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(ARG_PREFIX):
            continue
        record, judgment = line[len(ARG_PREFIX):].split(":judgment=", 1)
        fields = dict(item.split("=", 1) for item in record.split(":"))
        app, fun, arg = (int(fields[key]) for key in ("app", "fun", "arg"))
        assert (app, fun, arg) == (8805, 8753, 8804), line
        assert source_edges.get(app) == {"fn": fun, "arg": arg}, line
        before, after = int(fields["before"]), int(fields["after"])
        assert before >= after >= 0, line
        state = fields["state"]
        assert state in ("PROVEN", "UNKNOWN", "REFUTED"), line
        assert judgment.startswith(state.title()), line
        rows.append({"app": app, "fun": fun, "arg": arg, "context": int(fields["context"]),
                     "before": before, "after": after, "charged": before - after,
                     "state": state, "judgment_preview": judgment[:500]})
    return rows


def parse_conversion_stages(stderr: bytes, source_edges):
    """C131 stage receipts; source identity and stage status are not verdicts."""
    assert source_edges.get(8805) == {"fn": 8753, "arg": 8804}
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith(CONVERSION_INFER_PREFIX):
            record, descriptions = line[len(CONVERSION_INFER_PREFIX):].split(":inferred=", 1)
            inferred, expected = descriptions.split(":expected=", 1)
            fields = dict(item.split("=", 1) for item in record.split(":"))
            assert int(fields["expr"]) == 8804 and int(fields["context"]) == 0, line
            assert fields["state"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
            assert inferred.startswith(fields["state"].title()), line
            before, after = int(fields["before"]), int(fields["after"])
            assert before >= after >= 0, line
            rows.append({"stage": "infer", "state": fields["state"],
                         "frame": int(fields["frame"]), "before": before,
                         "after": after, "charged": before - after,
                         "inferred_preview": inferred[:700], "expected_preview": expected[:700]})
        elif line.startswith(CONVERSION_RELATION_PREFIX):
            record, judgment = line[len(CONVERSION_RELATION_PREFIX):].split(":judgment=", 1)
            fields = dict(item.split("=", 1) for item in record.split(":"))
            assert int(fields["expr"]) == 8804 and int(fields["context"]) == 0, line
            assert fields["state"] in ("PROVEN", "UNKNOWN", "REFUTED"), line
            assert judgment.startswith(fields["state"].title()), line
            rows.append({"stage": "convert", "state": fields["state"],
                         "frame": int(fields["frame"]), "fuel": int(fields["fuel"]),
                         "judgment_preview": judgment[:700]})
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
        owner_trace: bool = False, app_trace: bool = False,
        arg_trace: bool = False, conversion_trace: bool = False):
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
        if app_trace:
            env["NUCLEUS_C129_APP_EDGE"] = "1"
        if arg_trace:
            env["NUCLEUS_C130_APP_ARG"] = "1"
        if conversion_trace:
            env["NUCLEUS_C131_ARG_CONVERT"] = "1"
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
    parser.add_argument("--app-trace", action="store_true",
                        help="C129 read-only source application dependency chain")
    parser.add_argument("--arg-trace", action="store_true",
                        help="C130 read-only source application argument obligation")
    parser.add_argument("--conversion-trace", action="store_true",
                        help="C131 separate source argument type inference and conversion")
    args = parser.parse_args()
    source = args.source.read_bytes()
    validate_source(source)
    exact_edges = source_app_edges(source)
    binary = args.binary.resolve()
    observations = []
    assert all(budget > 0 for budget in args.budgets), "budgets must be positive"
    assert len(args.budgets) == len(set(args.budgets)), "repeated budgets obscure the ladder"
    for budget in args.budgets:
        silent = run(binary, source, budget, False)
        observed = run(binary, source, budget, True, args.owner_trace,
                       args.app_trace, args.arg_trace, args.conversion_trace)
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
        if args.app_trace:
            edges = parse_app_edges(observed.stderr, exact_edges)
            assert any(e["app"] == 8805 for e in edges), ("source 8805 edge absent", budget)
            row["source_app_edges"] = edges[:512]
            row["source_app_edge_count"] = len(edges)
        if args.arg_trace:
            obligations = parse_arg_obligations(observed.stderr, exact_edges)
            assert obligations, ("source 8805 argument obligation absent", budget)
            row["source_arg_obligations"] = obligations[:8]
        if args.conversion_trace:
            stages = parse_conversion_stages(observed.stderr, exact_edges)
            assert any(s["stage"] == "infer" for s in stages), ("inference receipt absent", budget)
            # A type-inference UNKNOWN must *not* invent a conversion call.
            # Conversion is attempted only on a PROVEN inferred type.
            if any(s["stage"] == "infer" and s["state"] == "PROVEN" for s in stages):
                assert any(s["stage"] == "convert" for s in stages), (
                    "proven inference without expected conversion receipt", budget)
            row["source_arg_conversion_stages"] = stages[:24]
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
