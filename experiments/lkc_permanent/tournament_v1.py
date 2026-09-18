#!/usr/bin/env python3
"""Permanent wrapper-inline V1-V3 tournament."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "experiments/lkc_permanent/generated"
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache/upstream"
PACKAGE = UPSTREAM / "evaluation/problems/permanent"
EVIDENCE = ROOT / "permanent-v1-evidence"
VARIANTS = ["v1", "v2", "v3"]
INPUTS = [
    28064292647, 26230790088, 26754739663, 28361232070, 29556043951,
    53794586207, 54079857374, 54224806958, 51875434732, 54751654040,
    71077100717, 72835838140, 72703668916, 70268834944, 69508517010,
]
EVIDENCE.mkdir(exist_ok=True)


def save(name, obj):
    (EVIDENCE / name).write_text(json.dumps(obj, indent=2) + "\n")
    print(json.dumps(obj, indent=2), flush=True)


def execute(command, log, cwd=ROOT, timeout=900):
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
    gates = {}
    for v in VARIANTS:
        src = SOURCES / f"Submission_{v}.lean"
        original = src.read_text()
        audit = EVIDENCE / f"Audit_{v}.lean"
        audit.write_text(
            original
            + "\n#print axioms Submission.impl_correct\n"
            + "example : Submission.impl 0 = 1 := by decide +kernel\n"
            + "example : Submission.impl 8589934592 = 2 := by decide +kernel\n"
            + "example : Submission.impl 12884901889 = 6 := by decide +kernel\n"
        )
        code, text = execute(
            ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(audit)],
            f"proof-{v}.log", cwd=PACKAGE, timeout=1200
        )
        axioms_match = re.search(r"depends on axioms:\s*\[([^\]]*)\]", text)
        axiom_free = "does not depend on any axioms" in text
        axioms = ({x.strip() for x in axioms_match.group(1).split(",") if x.strip()}
                  if axioms_match else set())
        passed = code == 0 and (axioms_match is not None or axiom_free)
        passed = passed and axioms <= {"propext", "Quot.sound", "Classical.choice"}
        caught = False
        if passed:
            bad = EVIDENCE / f"Negative_{v}.lean"
            bad.write_text(original + "\nexample : Submission.impl 12884901889 = 5 := by decide +kernel\n")
            bad_code, bad_text = execute(
                ["lake", "env", "lean", "-DautoImplicit=false", "-DwarningAsError=true", str(bad)],
                f"negative-{v}.log", cwd=PACKAGE, timeout=1200
            )
            caught = bad_code not in (0, 124) and "error:" in bad_text
            passed = passed and caught
        gates[v] = {
            "proof_pass": passed,
            "negative_control_rejected": caught,
            "axioms": sorted(axioms),
            "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest()
        }
        save("proof-gates.json", gates)
    if not any(g["proof_pass"] for g in gates.values()):
        raise RuntimeError("No Permanent inline candidate passed.")


def diagnostic(version, metric, label):
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli
    out = EVIDENCE / f"{metric}-{label}"
    code = cli.main([
        "diagnostic", "--problem", "permanent",
        "--submission", str(SOURCES / f"Submission_{version}.lean"),
        "--metric", metric, "--repetitions", "3",
        "--timeout", "600", "--memory-mb", "8192",
        "--inputs", *map(str, INPUTS), "--output", str(out)
    ])
    data = json.loads((out / "diagnostic.json").read_text())
    if code != 0 or not data.get("complete"):
        raise RuntimeError(f"{version}: incomplete {metric} diagnostic")
    return {
        "version": version,
        "metric": metric,
        "totals": data["totals"],
        "ratio": data["totals"]["candidate"] / data["totals"]["baseline"],
        "reduction_pct": 100 * (1 - data["totals"]["candidate"] / data["totals"]["baseline"]),
        "comparisons": data.get("comparisons"),
        "source_sha256": hashlib.sha256((SOURCES / f"Submission_{version}.lean").read_bytes()).hexdigest(),
    }


def screen():
    gates = json.loads((EVIDENCE / "proof-gates.json").read_text())
    results = []
    for v in VARIANTS:
        if gates[v]["proof_pass"]:
            results.append(diagnostic(v, "wall-time", v))
            save("wall-screen.json", results)
    selected = min(results, key=lambda x: x["ratio"])
    save("selected.json", {"version": selected["version"], "screen": selected})


def qualify():
    selected = json.loads((EVIDENCE / "selected.json").read_text())["version"]
    src = SOURCES / f"Submission_{selected}.lean"
    code, text = execute(
        ["python3", "evaluation/run.py", "--problem", "permanent",
         "--submission", str(src), "--timeout", "180"],
        "canonical.log", cwd=UPSTREAM, timeout=3600
    )
    passed = code == 0 and ": accepted" in text
    save("canonical.json", {"version": selected, "accepted": bool(passed), "local_unseeded_only": True})
    if not passed:
        raise RuntimeError("Permanent selected candidate failed canonical acceptance.")


def instructions():
    selected = json.loads((EVIDENCE / "selected.json").read_text())["version"]
    can = json.loads((EVIDENCE / "canonical.json").read_text())
    if not can["accepted"] or can["version"] != selected:
        raise RuntimeError("Missing canonical gate")
    result = diagnostic(selected, "callgrind", "selected")
    gates = json.loads((EVIDENCE / "proof-gates.json").read_text())
    if gates[selected]["source_sha256"] != result["source_sha256"]:
        raise RuntimeError("Measured bytes differ from proof-checked bytes")
    result.update(official_pmu_measured=False,
                  local_promotion_eligible=result["ratio"] < 1.0)
    save("instruction-verdict.json", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prove", "screen", "qualify", "instructions"])
    globals()[parser.parse_args().phase]()
