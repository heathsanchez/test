#!/usr/bin/env python3
"""Protected Polydisc V1 versus PRS multiply-square V2."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "experiments/lkc_polydisc/generated"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/polydisc"
EVIDENCE = ROOT / "polydisc-v2-evidence"
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
    src = SOURCES / "Submission_v2.lean"
    original = src.read_text()
    audit = EVIDENCE / "Audit_v2.lean"
    audit.write_text(
        original
        + "\n#print axioms Submission.impl_correct\n"
        + "example : Submission.impl 0 = discSpec 0 := by decide +kernel\n"
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
        bad = EVIDENCE / "Negative_v2.lean"
        bad.write_text(original + "\nexample : Submission.impl 0 = (0 : Int) := by decide +kernel\n")
        bad_code, bad_text = execute(
            ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(bad)],
            "negative.log", cwd=PACKAGE, timeout=2400
        )
        caught = bad_code not in (0,124) and "error:" in bad_text
        passed = passed and caught
    verdict = {
        "proof_pass": passed,
        "negative_control_rejected": caught,
        "axioms": sorted(axioms),
        "candidate_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "baseline_sha256": hashlib.sha256((SOURCES / "Submission_v1.lean").read_bytes()).hexdigest()
    }
    save("proof-gate.json", verdict)
    if not passed:
        raise RuntimeError("Polydisc V2 proof gate failed")


def diagnostic(metric, label):
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli
    from lkc_bench import diagnostic as engine
    baseline = SOURCES / "Submission_v1.lean"
    original = engine.official_baseline
    engine.official_baseline = lambda problem: baseline
    try:
        out = EVIDENCE / f"{metric}-{label}"
        code = cli.main([
            "diagnostic", "--problem", "polydisc",
            "--submission", str(SOURCES / "Submission_v2.lean"),
            "--metric", metric, "--repetitions", "3",
            "--timeout", "900", "--memory-mb", "4096",
            "--inputs", *map(str, INPUTS), "--output", str(out)
        ])
    finally:
        engine.official_baseline = original
    data=json.loads((out/"diagnostic.json").read_text())
    if code != 0 or not data.get("complete"):
        raise RuntimeError(f"Polydisc V2 incomplete {metric} diagnostic")
    return {
        "metric":metric,"baseline":"protected-polydisc-v1","totals":data["totals"],
        "ratio":data["totals"]["candidate"]/data["totals"]["baseline"],
        "reduction_pct":100*(1-data["totals"]["candidate"]/data["totals"]["baseline"]),
        "comparisons":data.get("comparisons"),
        "candidate_sha256":hashlib.sha256((SOURCES/"Submission_v2.lean").read_bytes()).hexdigest(),
        "baseline_sha256":hashlib.sha256(baseline.read_bytes()).hexdigest()
    }


def screen():
    save("wall-screen.json", diagnostic("wall-time","v1-v2"))


def qualify():
    src=SOURCES/"Submission_v2.lean"
    code,text=execute(["python3","evaluation/run.py","--problem","polydisc",
                       "--submission",str(src),"--timeout","180"],
                      "canonical.log",cwd=UPSTREAM,timeout=5400)
    passed=code==0 and ": accepted" in text
    save("canonical.json",{"accepted":bool(passed),"local_unseeded_only":True})
    if not passed: raise RuntimeError("Polydisc V2 canonical qualification failed")


def instructions():
    if not json.loads((EVIDENCE/"canonical.json").read_text())["accepted"]:
        raise RuntimeError("Missing canonical gate")
    result=diagnostic("callgrind","v1-v2")
    proof=json.loads((EVIDENCE/"proof-gate.json").read_text())
    if proof["candidate_sha256"] != result["candidate_sha256"] or proof["baseline_sha256"] != result["baseline_sha256"]:
        raise RuntimeError("Measured bytes drifted")
    result.update(official_pmu_measured=False,
                  local_promotion_eligible=result["ratio"]<1.0,
                  selected_champion="v2" if result["ratio"]<1.0 else "v1")
    save("instruction-verdict.json",result)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=["prove","screen","qualify","instructions"])
    globals()[parser.parse_args().phase]()
