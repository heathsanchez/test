#!/usr/bin/env python3
"""Fibonacci multiply-square V1: proof/canonical gate and paired diagnostics."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/lkc_fib/generated/Submission_v1.lean"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/fib"
EVIDENCE = ROOT / "fib-v1-evidence"
INPUTS = [5000, 10000, 20000, 40000, 80000, 150000]
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
        + "example : Submission.impl 10 = 55 := by decide +kernel\n"
        + "example : Submission.impl 100 = 354224848179261915075 := by decide +kernel\n"
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
        mutation.write_text(original + "\nexample : Submission.impl 10 = 54 := by decide +kernel\n")
        bad_code, bad_text = execute(
            ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(mutation)],
            "negative.log", cwd=PACKAGE, timeout=900
        )
        caught = bad_code not in (0, 124) and "error:" in bad_text
        passed = passed and caught

    verdict = {
        "proof_pass": passed,
        "negative_control_rejected": caught,
        "axioms": sorted(axioms),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    }
    save("proof-gate.json", verdict)
    if not passed:
        raise RuntimeError("Fibonacci V1 proof gate failed.")


def qualify():
    code, text = execute(
        ["python3", "evaluation/run.py", "--problem", "fib",
         "--submission", str(SOURCE), "--timeout", "180"],
        "canonical.log", cwd=UPSTREAM, timeout=2400
    )
    passed = code == 0 and ": accepted" in text
    save("canonical.json", {"accepted": bool(passed), "local_unseeded_only": True})
    if not passed:
        raise RuntimeError("Fibonacci V1 canonical qualification failed.")


def diagnostic_against(baseline_path: Path, label: str, metric: str):
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli
    from lkc_bench import diagnostic as engine
    original = engine.official_baseline
    engine.official_baseline = lambda problem: baseline_path
    try:
        out = EVIDENCE / f"{metric}-{label}"
        code = cli.main([
            "diagnostic", "--problem", "fib", "--submission", str(SOURCE),
            "--metric", metric, "--repetitions", "3", "--timeout", "600",
            "--memory-mb", "4096", "--inputs", *map(str, INPUTS),
            "--output", str(out)
        ])
    finally:
        engine.official_baseline = original
    data = json.loads((out / "diagnostic.json").read_text())
    if code != 0 or not data.get("complete"):
        raise RuntimeError(f"incomplete {metric} diagnostic against {label}")
    return {
        "baseline_label": label,
        "metric": metric,
        "totals": data["totals"],
        "total_baseline_over_candidate": data.get("total_baseline_over_candidate"),
        "comparisons": data.get("comparisons"),
    }


def screen():
    starter = UPSTREAM / "problems/fib/Submission.lean"
    example = BENCH / "benchmarks/1-fib/official/Submission.lean"
    results = [
        diagnostic_against(starter, "starter-Nat.fastFib", "wall-time"),
        diagnostic_against(example, "official-example", "wall-time"),
    ]
    save("wall-screen.json", results)


def instructions():
    starter = UPSTREAM / "problems/fib/Submission.lean"
    example = BENCH / "benchmarks/1-fib/official/Submission.lean"
    results = [
        diagnostic_against(starter, "starter-Nat.fastFib", "callgrind"),
        diagnostic_against(example, "official-example", "callgrind"),
    ]
    save("instruction-verdict.json", {
        "official_pmu_measured": False,
        "candidate_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "results": results
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prove", "qualify", "screen", "instructions"])
    globals()[parser.parse_args().phase]()
