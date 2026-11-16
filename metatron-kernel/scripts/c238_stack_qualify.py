"""C238: source-locked independent kernel 128-MiB thread-stack qualification.

No kernel rule changes. Compare the original 212 source/expected verdicts,
two builds of the same 128-MiB stack-capacity commit, and the exact 4,000-lambda
app-lam witness previously aborting on the unmodified C234/C236 binaries.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

ARCHIVE_SHA = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
APP_SHA = "552d6e8398f579fcf59ab9abd8187fc7a8a037697da66c129aacb4cc1b9dd414"
ADDITIONAL_FLAGS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)
PROTECTED = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)

def sha(content):
    return hashlib.sha256(content).hexdigest()

def replay(executable, source, environment, case, timeout=220):
    t = time.monotonic()
    try:
        p = subprocess.run([str(executable)], input=source, env=environment,
                           capture_output=True, timeout=timeout, check=False)
        stderr = p.stderr.decode(errors="replace")
        stdout = p.stdout.decode(errors="replace")
        code, status = p.returncode, "completed"
    except subprocess.TimeoutExpired as e:
        stderr = (e.stderr or b"").decode(errors="replace")
        stdout = (e.stdout or b"").decode(errors="replace")
        code, status = None, "timeout"
    return {
        "case": case, "exit": code, "status": status,
        "duration_s": round(time.monotonic() - t, 3),
        "source_sha256": sha(source),
        "stack_overflow": "has overflowed its stack" in stderr,
        "downstream_tail": [x[:400] for x in stderr.splitlines()
                            if x.startswith("NUCLEUS_DOWNSTREAM:")][-2:],
        "stderr_tail": stderr[-900:] if code is None or code not in (0, 1, 2) else "",
        "stdout_tail": stdout[-200:] if stdout else "",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--flags", type=Path, required=True)
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--diagnostics", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if sha(a.archive.read_bytes()) != ARCHIVE_SHA:
        raise ValueError("Original 212-export source archive digest mismatch")
    flags = json.loads(a.flags.read_text())["flags"]
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("Unqualified source feature set")
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}": "1" for k in ADDITIONAL_FLAGS})
    env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    binaries = {"release": a.release, "diagnostics": a.diagnostics}
    with zipfile.ZipFile(a.archive) as z:
        baseline = {x["case"]: x for x in json.loads(z.read("current212.json"))}
        if len(baseline) != 212 or Counter(x["actual"] for x in baseline.values()) != Counter({0:122,1:84,2:6}):
            raise ValueError("Original verdict population changed")
        def source(name):
            b = z.read("inputs/" + name)
            if sha(b) != baseline[name]["sha256"]:
                raise ValueError("Original source bytes changed: " + name)
            return b
        app = source("good/perf/app-lam.ndjson")
        if sha(app) != APP_SHA:
            raise ValueError("Not the genuine app-lam")
        target_results = []
        for label, exe in binaries.items():
            row = replay(exe, app, env, f"good/perf/app-lam.ndjson::{label}", 75)
            row["build"] = label
            print("C238_DEEP_STACK", json.dumps(row, sort_keys=True), flush=True)
            target_results.append(row)
        # Always run the complete 212-case release gate; a special fixture
        # alone never establishes corpus safety.  Retain every UNKNOWN and
        # fatal attempt in the output, including if another case aborts.
        outcomes = []
        for case in sorted(baseline):
            row = replay(a.release, source(case), env, case, 240)
            row.update(expected=baseline[case]["expected"],
                       original_actual=baseline[case]["actual"],
                       build="release")
            outcomes.append(row)
            if row["status"] != "completed" or row["exit"] != baseline[case]["actual"]:
                print("C238_DELTA", json.dumps(row, sort_keys=True), flush=True)
            elif len(outcomes) % 24 == 0:
                print("C238_PROGRESS", f"{len(outcomes)}/212", flush=True)
        protected = []
        for case in PROTECTED:
            row = replay(a.diagnostics, source(case), env, case, 60)
            row.update(expected=baseline[case]["expected"],
                       original_actual=baseline[case]["actual"],
                       build="diagnostics")
            protected.append(row)
        population = Counter(row["exit"] for row in outcomes)
        deviations = [row for row in outcomes if row["status"] != "completed"
                      or row["exit"] != row["original_actual"]]
        target_mismatch = [row for row in target_results
                           if row["status"] != "completed" or row["exit"] != 0]
        control_mismatch = [row for row in protected
                            if row["status"] != "completed" or row["exit"] != row["original_actual"]]
        report = {
            "status": "BOUNDED_FULL212_QUALIFICATION" if not (
                deviations or target_mismatch or control_mismatch) else "NOT_QUALIFIED",
            "source_archive_sha256": ARCHIVE_SHA,
            "app_lam_sha256": APP_SHA,
            "stack_size_mib": 128, "no_logical_rule_change": True,
            "target": target_results,
            "release_population": {str(k): v for k,v in sorted(population.items())},
            "deviations": deviations,
            "diagnostics_protected": protected,
            "release_all": outcomes,
            "complete_mathlib_acceptance": "NOT_TESTED",
        }
        (a.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print("C238_SUMMARY", json.dumps({
            "state": report["status"], "total": len(outcomes),
            "population": report["release_population"],
            "app_lam": [r["exit"] for r in target_results],
            "release_deviations": len(deviations),
            "diagnostic_control_deviations": len(control_mismatch),
        }, sort_keys=True), flush=True)
        if report["status"] == "NOT_QUALIFIED":
            raise ValueError("Full-source 128-MiB release safety gate failed")

if __name__ == "__main__":
    main()
