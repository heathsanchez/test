#!/usr/bin/env python3
"""SHA-256 no-zip V1 verification and paired diagnostic."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/lkc_sha256/generated/Submission_v1.lean"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/sha256"
EVIDENCE = ROOT / "sha256-v1-evidence"
INPUTS = [18860801433, 17252521710, 138725260120, 140599404248, 2199121876686, 2199573357346]
SCREEN_INPUTS = INPUTS[:4]
EVIDENCE.mkdir(exist_ok=True)


def save(name, obj):
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2) + "\n")
    print(json.dumps(obj, indent=2), flush=True)


def execute(command, log, cwd=ROOT, timeout=1200):
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
        + "example : Submission.impl 4294967297 = "
          "6974916886958575962243026017989799625410957637305596483321224775681667163855 := by decide +kernel\n"
    )
    code, text = execute(
        ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(audit)],
        "proof.log", cwd=PACKAGE, timeout=1800
    )
    axioms_match = re.search(r"depends on axioms:\s*\[([^\]]*)\]", text)
    axiom_free = "does not depend on any axioms" in text
    axioms = ({x.strip() for x in axioms_match.group(1).split(",") if x.strip()}
              if axioms_match else set())
    passed = code == 0 and (axioms_match is not None or axiom_free)
    passed = passed and axioms <= {"propext", "Quot.sound", "Classical.choice"}

    caught = False
    if passed:
        bad = EVIDENCE / "Negative_v1.lean"
        bad.write_text(
            original
            + "\nexample : Submission.impl 4294967297 = 0 := by decide +kernel\n"
        )
        bad_code, bad_text = execute(
            ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(bad)],
            "negative.log", cwd=PACKAGE, timeout=1800
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
        raise RuntimeError("SHA-256 V1 proof gate failed.")


def qualify():
    code, text = execute(
        ["python3", "evaluation/run.py", "--problem", "sha256",
         "--submission", str(SOURCE), "--timeout", "180"],
        "canonical.log", cwd=UPSTREAM, timeout=3600
    )
    passed = code == 0 and ": accepted" in text
    save("canonical.json", {"accepted": bool(passed), "local_unseeded_only": True})
    if not passed:
        raise RuntimeError("SHA-256 V1 canonical qualification failed.")


def diagnostic(metric, inputs, label):
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli
    out = EVIDENCE / f"{metric}-{label}"
    code = cli.main([
        "diagnostic", "--problem", "sha256", "--submission", str(SOURCE),
        "--metric", metric, "--repetitions", "3", "--timeout", "600",
        "--memory-mb", "4096", "--inputs", *map(str, inputs),
        "--output", str(out)
    ])
    data = json.loads((out / "diagnostic.json").read_text())
    return code, data


def screen():
    code, data = diagnostic("wall-time", SCREEN_INPUTS, "screen")
    if code != 0 or not data.get("complete"):
        raise RuntimeError("SHA-256 small/medium wall screen incomplete")
    result = {
        "metric": "wall-time",
        "inputs": SCREEN_INPUTS,
        "totals": data["totals"],
        "ratio": data["totals"]["candidate"] / data["totals"]["baseline"],
        "reduction_pct": 100 * (1 - data["totals"]["candidate"] / data["totals"]["baseline"]),
        "comparisons": data.get("comparisons"),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "full_contract_complete": False,
        "note": "512-step public diagnostic is a separate resource probe."
    }
    save("wall-screen.json", result)


def resource_probe():
    code, data = diagnostic("wall-time", INPUTS, "full-resource-probe")
    result = {
        "runner_complete": bool(data.get("complete")),
        "returncode": code,
        "inputs": INPUTS,
        "totals": data.get("totals"),
        "comparisons": data.get("comparisons"),
        "runs": data.get("runs"),
        "contract_memory_mb": 4096,
        "classification": "complete" if data.get("complete") else "UNKNOWN_SEARCH_RESOURCE_OBSTRUCTION",
    }
    save("resource-probe.json", result)


def instructions():
    code, data = diagnostic("callgrind", SCREEN_INPUTS, "screen")
    if code != 0 or not data.get("complete"):
        raise RuntimeError("SHA-256 small/medium instruction diagnostic incomplete")
    result = {
        "metric": "callgrind",
        "inputs": SCREEN_INPUTS,
        "totals": data["totals"],
        "ratio": data["totals"]["candidate"] / data["totals"]["baseline"],
        "reduction_pct": 100 * (1 - data["totals"]["candidate"] / data["totals"]["baseline"]),
        "comparisons": data.get("comparisons"),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "official_pmu_measured": False,
        "full_contract_complete": False,
        "local_promotion_eligible": False,
        "note": "Exploratory only until 512-step contract cases complete under the declared 4 GiB envelope."
    }
    proof = json.loads((EVIDENCE / "proof-gate.json").read_text())
    if proof["source_sha256"] != result["source_sha256"]:
        raise RuntimeError("Measured bytes differ from proof-checked bytes")
    save("instruction-verdict.json", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prove", "screen", "resource_probe", "qualify", "instructions"])
    globals()[parser.parse_args().phase]()
