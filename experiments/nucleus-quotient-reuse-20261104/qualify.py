#!/usr/bin/env python3
"""Prospective protected qualification of three source-pinned Quotient rules.

Reuses the prior *independently qualified* List.Perm checker as baseline,
without re-running its expensive source materialization. Every corpus case
and control is matched by exact input identity; UNKNOWN is never promoted.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nucleus-final-proof-spine-20261104"))
import runner
sys.path.insert(0, str(HERE.parent / "nucleus-reuse-20261104"))
import tournament as t
from port import port


def enabled_env(include_exact=True):
    env = t.run_env()
    rules = ["CERTIFIED_QUOT_IOTA", "SOURCE_PROOF_IRREL"]
    if include_exact:
        rules.append("EXACT_PROOF_NEUTRALS")
    for rule in rules:
        env["NUCLEUS_EXPERIMENTAL_" + rule] = "1"
    return env


def read_reference(archive: Path):
    with zipfile.ZipFile(archive) as z:
        summary = json.loads(z.read("qualification.json"))
        rows = json.loads(z.read("candidate/verdicts.json"))
    assert summary["candidate"]["qualified"] is True
    assert summary["candidate"]["counts"] == {"0": 121, "1": 79, "2": 8}
    assert len(rows) == 208
    return summary["candidate"], rows


def run_source(binary: Path, input_file: Path, env: dict, directory: Path, label: str):
    directory.mkdir(parents=True, exist_ok=True)
    with input_file.open("rb") as source:
        result = t.run_group(
            [str(binary)], stdin=source, capture_output=True, env=env, timeout=240
        )
    (directory / (label + ".stderr")).write_bytes(result.stderr)
    return result.returncode


def do_qualification(out: Path, full_input: Path, include_exact=True):
    out.mkdir(parents=True, exist_ok=True)
    reference, reference_rows = read_reference(Path("/tmp/reference-qualified.zip"))
    corpus = Path("/tmp/current208")
    manifest = json.loads((corpus / "inputs-manifest.json").read_text())
    assert len(manifest) == len(reference_rows) == 208
    assert all(
        item["case"] == prior["case"]
        and item["sha256"] == prior["sha256"]
        for item, prior in zip(manifest, reference_rows)
    )
    kernel = runner.materialize(out / "candidate", semantic=True)
    port(Path.cwd(), kernel, out / "candidate/quotient-port.patch", include_exact=include_exact)
    binary, _ = t.build(kernel, out / "candidate")
    assert binary is not None, (out / "candidate/build.log").read_text()[-5000:]
    env = enabled_env(include_exact=include_exact)
    env["NUCLEUS_FROZEN196"] = str(corpus / "inputs")
    baseline = dict(
        previous_binary_sha=reference["binary_sha"],
        source_patch_sha=t.digest(out / "candidate/source.patch"),
        quotient_port_sha=t.digest(out / "candidate/quotient-port.patch"),
        candidate_binary_sha=t.digest(binary),
        flags=sorted(x for x in env if x.startswith("NUCLEUS_")),
        corpus_identity="exact prior independent 208 manifest",
    )
    t.write_json(out / "provenance.json", baseline)

    native = t.native_suite(kernel, env, out / "candidate")
    native_ok = runner.native_nonregression(native, reference["native"])
    rows = t.replay(binary, manifest, corpus, env, out / "candidate/verdicts.json")
    regressions = [
        dict(case=a["case"], before=a["rc"], after=b["rc"])
        for a, b in zip(reference_rows, rows)
        if b["rc"] not in (b["expected"], 2)
        or (a["rc"] != 2 and a["rc"] != b["rc"])
    ]
    listperm = []
    for fixture in sorted((HERE.parent / "nucleus-final-proof-spine-20261104/controls").glob("*.ndjson")):
        rc = run_source(binary, fixture, env, out / "controls", fixture.stem)
        positive = fixture.stem in {
            "same", "proof_last", "dependent_proof_last", "long_prefix_valid"
        }
        listperm.append(dict(case=fixture.stem, rc=rc, passed=rc == 0 if positive else rc in (1, 2)))

    # Two independently edited source declarations: type and value IDs change;
    # no trusted precomputed checker decision enters this test.
    prefix = Path("/tmp/quotient-prefix.ndjson").read_bytes()
    assert hashlib.sha256(prefix).hexdigest() == (
        "4883dc9889b546a1117c25c266bae05a344b6609db5cbbfd846a8d7abc92a907"
    )
    head, last = (
        prefix.rsplit(b"\n", 2)[:2]
        if prefix.endswith(b"\n")
        else prefix.rsplit(b"\n", 1)
    )
    record = json.loads(last)
    assert all(record["thm"][key] == v for key, v in {
        "name": 1911, "type": 16786, "value": 16842
    }.items())
    quotient = []
    for field in (None, "type", "value"):
        data = prefix
        if field:
            modified = json.loads(last)
            modified["thm"][field] = 0
            data = head + b"\n" + json.dumps(modified, separators=(",", ":")).encode() + b"\n"
        file = out / "controls" / ("quotient-" + (field or "authentic") + ".ndjson")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        rc = run_source(binary, file, env, out / "controls", "quotient-" + (field or "authentic"))
        quotient.append(dict(
            case=field or "authentic", sha256=t.digest(file), rc=rc,
            passed=rc == 0 if field is None else rc in (1, 2),
        ))
        file.unlink()

    qualified = not regressions and native_ok and all(x["passed"] for x in listperm + quotient)
    state = dict(
        qualified=qualified, counts={str(rc):sum(x["rc"] == rc for x in rows) for rc in (0, 1, 2)},
        native_nonregression=native_ok, regressions=regressions,
        listperm_controls=listperm, quotient_controls=quotient,
    )
    t.write_json(out / "qualification.json", state)
    assert qualified, state

    assert full_input.exists() and t.digest(full_input) == t.INPUT_SHA
    full_env = dict(env, NUCLEUS_TRACE_DOWNSTREAM="1")
    result = t.measure(binary, full_input, full_env, out / "mathlib", timeout=5400, perf=False)
    stderr = (out / "mathlib/stderr").read_text()
    terminal = re.findall(r"NUCLEUS_DOWNSTREAM:name=(.*?):stage=", stderr)
    next_frontier = (
        runner.extract_frontier(full_input, out / "next-frontier.ndjson", terminal[-1])
        if terminal and not terminal[-1].startswith("<") else None
    )
    summary = dict(
        qualification=state, mathlib_input_sha=t.INPUT_SHA,
        mathlib=result, complete_mathlib_accept=result["rc"] == 0,
        next_frontier=next_frontier,
    )
    t.write_json(out / "summary.json", summary)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mathlib", type=Path, required=True)
    parser.add_argument("--without-exact", action="store_true", help="Omit nonessential exact-source proof-neutral rule")
    args = parser.parse_args()
    do_qualification(args.out.resolve(), args.mathlib.resolve(), include_exact=not args.without_exact)
