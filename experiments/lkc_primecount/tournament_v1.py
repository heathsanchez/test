#!/usr/bin/env python3
"""Primecount direct-recursion V1 verification and instruction diagnostic."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/lkc_primecount/generated/Submission_v1.lean"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/primecount"
EVIDENCE = ROOT / "primecount-v1-evidence"
INPUTS = [50, 100, 150, 300, 600, 1000]
EVIDENCE.mkdir(exist_ok=True)


def save(name, obj):
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2) + "\n")
    print(json.dumps(obj, indent=2), flush=True)


def execute(command, log, cwd=ROOT, timeout=600):
    path = EVIDENCE / log
    with path.open("w") as stream:
        try:
            result = subprocess.run(command, cwd=cwd, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    text = path.read_text(errors="replace")
    print(text[-16000:], flush=True)
    return code, text


def prove():
    original = SOURCE.read_text()
    audit = EVIDENCE / "Audit_v1.lean"
    audit.write_text(
        original
        + "\n#print axioms Submission.impl_correct\n"
        + "example : Submission.impl 0 = 0 := by decide +kernel\n"
        + "example : Submission.impl 10 = 4 := by decide +kernel\n"
        + "example : Submission.impl 50 = 15 := by decide +kernel\n"
    )
    code, text = execute(
        ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(audit)],
        "proof.log", cwd=PACKAGE, timeout=900
    )
    axioms_match = re.search(r"depends on axioms:\s*\[([^\]]*)\]", text)
    axiom_free = "does not depend on any axioms" in text
    axioms = ({x.strip() for x in axioms_match.group(1).split(",") if x.strip()}
              if axioms_match else set())
    passed = code == 0 and (axioms_match is not None or axiom_free)
    passed = passed and axioms <= {"propext", "Quot.sound", "Classical.choice"}

    mutation = EVIDENCE / "Negative_v1.lean"
    caught = False
    if passed:
        mutation.write_text(original + "\nexample : Submission.impl 10 = 5 := by decide +kernel\n")
        bad_code, bad_text = execute(
            ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(mutation)],
            "negative.log", cwd=PACKAGE, timeout=900
        )
        caught = bad_code not in (0, 124) and "error:" in bad_text
        passed = passed and caught

    verdict = {
        "proof_pass": passed,
        "negative_control_rejected": caught,
        "returncode": code,
        "axioms": sorted(axioms),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    }
    save("proof-gate.json", verdict)
    if not passed:
        raise RuntimeError("Primecount V1 proof gate failed.")


def qualify():
    code, text = execute(
        ["python3", "evaluation/run.py", "--problem", "primecount",
         "--submission", str(SOURCE), "--timeout", "180"],
        "canonical.log", cwd=UPSTREAM, timeout=2400
    )
    passed = code == 0 and ": accepted" in text
    save("canonical.json", {
        "accepted": bool(passed),
        "local_unseeded_only": True,
        "returncode": code,
    })
    if not passed:
        raise RuntimeError("Primecount V1 canonical qualification failed.")


def instructions():
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli

    out = EVIDENCE / "instruction-diagnostic"
    code = cli.main([
        "diagnostic", "--problem", "primecount",
        "--submission", str(SOURCE),
        "--metric", "callgrind", "--repetitions", "3",
        "--timeout", "600", "--memory-mb", "4096",
        "--inputs", *map(str, INPUTS),
        "--output", str(out),
    ])
    data = json.loads((out / "diagnostic.json").read_text())
    if code != 0 or not data.get("complete"):
        raise RuntimeError("Primecount instruction diagnostic incomplete.")
    result = {
        "official_pmu_measured": False,
        "development_metric": "callgrind",
        "inputs": INPUTS,
        "totals": data.get("totals"),
        "comparisons": data.get("comparisons"),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    }
    save("instruction-verdict.json", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prove", "qualify", "instructions"])
    globals()[parser.parse_args().phase]()
