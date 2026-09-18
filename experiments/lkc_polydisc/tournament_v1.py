#!/usr/bin/env python3
"""Polydisc fixed-sign V1 verification and paired diagnostic."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/lkc_polydisc/generated/Submission_v1.lean"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/polydisc"
EVIDENCE = ROOT / "polydisc-v1-evidence"
INPUTS = [19337098, 9225987, 6476047012455, 10487306645701,
          5042242704654352709, 4530401864863699852]
EVIDENCE.mkdir(exist_ok=True)


def save(name, obj):
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2) + "\n")
    print(json.dumps(obj, indent=2), flush=True)


def execute(command, log, cwd=ROOT, timeout=1800):
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
        + "example : Submission.impl 0 = "
          "(-1437475373221515423615709146748564172609479315133942550011246093047173337258904221338662563268181154344436806624326331905334612913874200226104057144892486060212832 : Int) := by decide +kernel\n"
    )
    code, text = execute(
        ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(audit)],
        "proof.log", cwd=PACKAGE, timeout=2400
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
        bad.write_text(original + "\nexample : Submission.impl 0 = (0 : Int) := by decide +kernel\n")
        bad_code, bad_text = execute(
            ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(bad)],
            "negative.log", cwd=PACKAGE, timeout=2400
        )
        caught = bad_code not in (0, 124) and "error:" in bad_text
        passed = passed and caught

    verdict = {
        "proof_pass": passed,
        "negative_control_rejected": caught,
        "axioms": sorted(axioms),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    }
    save("proof-gate.json", verdict)
    if not passed:
        raise RuntimeError("Polydisc V1 proof gate failed.")


def qualify():
    code, text = execute(
        ["python3", "evaluation/run.py", "--problem", "polydisc",
         "--submission", str(SOURCE), "--timeout", "180"],
        "canonical.log", cwd=UPSTREAM, timeout=5400
    )
    passed = code == 0 and ": accepted" in text
    save("canonical.json", {"accepted": bool(passed), "local_unseeded_only": True})
    if not passed:
        raise RuntimeError("Polydisc V1 canonical qualification failed.")


def diagnostic(metric):
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli
    out = EVIDENCE / f"{metric}-diagnostic"
    code = cli.main([
        "diagnostic", "--problem", "polydisc", "--submission", str(SOURCE),
        "--metric", metric, "--repetitions", "3", "--timeout", "900",
        "--memory-mb", "4096", "--inputs", *map(str, INPUTS),
        "--output", str(out)
    ])
    data = json.loads((out / "diagnostic.json").read_text())
    if code != 0 or not data.get("complete"):
        raise RuntimeError(f"incomplete Polydisc {metric} diagnostic")
    return {
        "metric": metric,
        "totals": data["totals"],
        "ratio": data["totals"]["candidate"] / data["totals"]["baseline"],
        "reduction_pct": 100 * (1 - data["totals"]["candidate"] / data["totals"]["baseline"]),
        "comparisons": data.get("comparisons"),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    }


def screen():
    save("wall-screen.json", diagnostic("wall-time"))


def instructions():
    result = diagnostic("callgrind")
    proof = json.loads((EVIDENCE / "proof-gate.json").read_text())
    if proof["source_sha256"] != result["source_sha256"]:
        raise RuntimeError("Measured bytes differ from proof-checked bytes")
    result.update(official_pmu_measured=False,
                  local_promotion_eligible=result["ratio"] < 1.0)
    save("instruction-verdict.json", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prove", "screen", "qualify", "instructions"])
    globals()[parser.parse_args().phase]()
