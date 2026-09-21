#!/usr/bin/env python3
"""Protected V1 versus structural V6/V7 Mertens tournament.

All candidates are general algorithms. No precomputed answers or input-specific
branches are used. The pinned public benchmark is used read-only as a diagnostic
engine; Callgrind Ir is a development proxy, not an official PMU score.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "experiments/lkc_mertens/generated"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/mertens"
EVIDENCE = ROOT / "mertens-v6-evidence"
INPUTS = [25, 50, 80, 150, 300, 500]
VARIANTS = ["v6", "v7"]
EVIDENCE.mkdir(exist_ok=True)


def save(name, obj):
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2) + "\n")
    print(json.dumps(obj, indent=2), flush=True)


def execute(command, log, cwd=ROOT, timeout=600):
    path = EVIDENCE / log
    with path.open("w") as stream:
        try:
            result = subprocess.run(
                command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    text = path.read_text(errors="replace")
    print(text[-16000:], flush=True)
    return code, text


def prove():
    gates = {}
    for version in ["v1", *VARIANTS]:
        source = SOURCES / f"Submission_{version}.lean"
        original = source.read_text()
        audit = EVIDENCE / f"Audit_{version}.lean"
        audit.write_text(
            original
            + "\n#print axioms Submission.impl_correct\n"
            + "example : Submission.impl 0 = 0 := by decide +kernel\n"
            + "example : Submission.impl 1 = 1 := by decide +kernel\n"
            + "example : Submission.impl 10 = -1 := by decide +kernel\n"
        )
        cmd = [
            "lake",
            "env",
            "lean",
            "-DautoImplicit=false",
            "-DwarningAsError=true",
            str(audit),
        ]
        code, text = execute(cmd, f"proof-{version}.log", cwd=PACKAGE)
        axioms_match = re.search(r"depends on axioms:\s*\[([^\]]*)\]", text)
        axiom_free = "does not depend on any axioms" in text
        axioms = (
            {x.strip() for x in axioms_match.group(1).split(",") if x.strip()}
            if axioms_match
            else set()
        )
        passed = code == 0 and (axioms_match is not None or axiom_free)
        passed = passed and axioms <= {"propext", "Quot.sound", "Classical.choice"}
        gates[version] = {
            "proof_pass": passed,
            "returncode": code,
            "axioms": sorted(axioms),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        if passed:
            mutation = EVIDENCE / f"Negative_{version}.lean"
            mutation.write_text(
                original + "\nexample : Submission.impl 0 = 1 := by decide +kernel\n"
            )
            bad_code, bad_text = execute(
                [*cmd[:-1], str(mutation)], f"negative-{version}.log", cwd=PACKAGE
            )
            caught = (
                bad_code not in (0, 124)
                and "error:" in bad_text
                and "decide" in bad_text
            )
            gates[version]["negative_control_rejected"] = caught
            gates[version]["proof_pass"] = passed and caught
        save("proof-gates.json", gates)
    if not gates["v1"]["proof_pass"]:
        raise RuntimeError("Protected V1 failed proof/audit control; stop.")
    if not any(gates[v]["proof_pass"] for v in VARIANTS):
        raise RuntimeError("No structural challenger passed; keep V1.")


def diagnostic(version, metric, output_name):
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli
    from lkc_bench import diagnostic as engine

    base = SOURCES / "Submission_v1.lean"
    original = engine.official_baseline
    engine.official_baseline = lambda problem: base
    try:
        out = EVIDENCE / output_name
        command = [
            "diagnostic",
            "--problem",
            "mertens",
            "--submission",
            str(SOURCES / f"Submission_{version}.lean"),
            "--metric",
            metric,
            "--repetitions",
            "3",
            "--timeout",
            "600",
            "--memory-mb",
            "4096",
            "--inputs",
            *map(str, INPUTS),
            "--output",
            str(out),
        ]
        code = cli.main(command)
    finally:
        engine.official_baseline = original
    data = json.loads((out / "diagnostic.json").read_text())
    data["baseline"] = "custom-protected-mertens-v1"
    data["source_selection_note"] = (
        "Only official_baseline callback overridden; pinned timing engine unmodified."
    )
    (out / "diagnostic.json").write_text(json.dumps(data, indent=2) + "\n")
    if code != 0 or not data.get("complete") or data["inputs"] != INPUTS:
        raise RuntimeError(f"{version} has incomplete {metric} diagnostic")
    if data["repetitions"] != 3 or data["metric"] != metric:
        raise RuntimeError("Unexpected metric/repetition contract")
    if {r["role"] for r in data["runs"]} != {"baseline", "candidate"}:
        raise RuntimeError("Missing source roles")
    for run in data["runs"]:
        if len(run["cases"]) != len(INPUTS):
            raise RuntimeError("Missing cases")
        for case in run["cases"]:
            if case["status"] != "complete" or len(case["samples"]) != 3:
                raise RuntimeError("Missing successful repetitions")
    b, c = data["totals"]["baseline"], data["totals"]["candidate"]
    if not isinstance(b, (int, float)) or not isinstance(c, (int, float)) or min(b, c) <= 0:
        raise RuntimeError("Invalid totals")
    return {
        "version": version,
        "metric": metric,
        "baseline": b,
        "candidate": c,
        "reduction_pct": 100 * (1 - c / b),
        "ratio": c / b,
        "source_sha256": hashlib.sha256(
            (SOURCES / f"Submission_{version}.lean").read_bytes()
        ).hexdigest(),
        "per_case": data["comparisons"],
    }


def screen():
    gates = json.loads((EVIDENCE / "proof-gates.json").read_text())
    results = []
    for version in VARIANTS:
        if not gates[version]["proof_pass"]:
            continue
        result = diagnostic(version, "wall-time", f"wall-{version}")
        results.append(result)
        save("wall-screen.json", results)
    selected = min(results, key=lambda x: x["ratio"])
    save(
        "selected.json",
        {
            "version": selected["version"],
            "selection_metric": "wall-time-only-screen",
            "promoted": False,
            "screen": selected,
        },
    )


def qualify():
    selected = json.loads((EVIDENCE / "selected.json").read_text())["version"]
    source = SOURCES / f"Submission_{selected}.lean"
    code, text = execute(
        [
            "python3",
            "evaluation/run.py",
            "--problem",
            "mertens",
            "--submission",
            str(source),
            "--timeout",
            "180",
        ],
        "canonical.log",
        cwd=UPSTREAM,
        timeout=1800,
    )
    passed = (
        code == 0
        and ": accepted" in text
        and re.search(r"Computation replay T:.*complete", text) is not None
    )
    passed = passed and all(re.search(rf"n={n}: OK\b", text) for n in INPUTS)
    save(
        "canonical.json",
        {
            "version": selected,
            "accepted_complete": bool(passed),
            "local_unseeded_only": True,
            "returncode": code,
        },
    )
    if not passed:
        raise RuntimeError("Canonical qualification incomplete; keep V1.")


def instructions():
    selected = json.loads((EVIDENCE / "selected.json").read_text())["version"]
    qualification = json.loads((EVIDENCE / "canonical.json").read_text())
    if not qualification["accepted_complete"] or qualification["version"] != selected:
        raise RuntimeError("Missing canonical qualification")
    result = diagnostic(selected, "callgrind", "instruction-final")
    gates = json.loads((EVIDENCE / "proof-gates.json").read_text())
    if result["source_sha256"] != gates[selected]["source_sha256"]:
        raise RuntimeError("Measured bytes differ from proof-checked bytes")
    promote = result["candidate"] < result["baseline"]
    result.update(
        local_promotion_eligible=promote,
        official_pmu_measured=False,
        selected_champion=selected if promote else "v1",
    )
    save("instruction-verdict.json", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prove", "screen", "qualify", "instructions"])
    globals()[parser.parse_args().phase]()
