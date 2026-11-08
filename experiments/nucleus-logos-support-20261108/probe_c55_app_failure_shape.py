"""C55: bounded, read-only function-type failure states at first bad values.

The checker still independently returns UNKNOWN. These samples identify
whether a failed application arose from UNKNOWN inference or a proved type
whose Pi head was not obtained, without interpreting samples as certificates.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c52_six_loss_census import CASES, parse_downstream
from probe_c54_first_failure_roots import first_failed_value_root


FAILURE = re.compile(
    r"^NUCLEUS_C55_APP_FAILURE:seq=(\d+):app=ExprId\((\d+)\):fun=ExprId\((\d+)\):"
    r"arg=ExprId\((\d+)\):context_depth=(\d+):frame=(\d+):remaining=(\d+):"
    r"state=(.+):source=(.*)$"
)
SUMMARY = re.compile(
    r"^NUCLEUS_C55_APP_SUMMARY:expr=ExprId\((\d+)\):events=(\d+):"
    r"remaining=(\d+):result=(.+)$"
)


def parse_app_observation(stderr: bytes, root: int) -> dict:
    samples = []
    final = []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith("NUCLEUS_C55_APP_FAILURE:"):
            match = FAILURE.fullmatch(line)
            if not match:
                raise ValueError("malformed C55 application failure record")
            seq, app, fun, arg, context_depth, frame, remaining, state, source = match.groups()
            samples.append({
                "seq": int(seq), "app": int(app), "fun": int(fun), "arg": int(arg),
                "context_depth": int(context_depth), "frame": int(frame),
                "remaining": int(remaining), "state": state, "source": source,
            })
        if line.startswith("NUCLEUS_C55_APP_SUMMARY:"):
            match = SUMMARY.fullmatch(line)
            if not match:
                raise ValueError("malformed C55 root summary")
            expr, count, remaining, result = match.groups()
            final.append({
                "root": int(expr), "observed_events": int(count),
                "remaining": int(remaining), "root_result": result,
            })
    if len(final) != 1 or final[0]["root"] != root:
        raise ValueError("missing or wrong C55 failing-declaration profiler")
    if "Unknown" not in final[0]["root_result"]:
        raise ValueError("C55 root result was not the original UNKNOWN")
    if any(b["seq"] <= a["seq"] for a, b in zip(samples, samples[1:])):
        raise ValueError("C55 sampling sequence is not strictly increasing")
    if samples and (samples[0]["seq"] != 0 or samples[-1]["seq"] >= final[0]["observed_events"]):
        raise ValueError("C55 sample counts contradict the terminal counter")
    final[0]["sample_count"] = len(samples)
    final[0]["sampled_states"] = samples[:64]
    final[0]["sample_is_complete"] = len(samples) == final[0]["observed_events"]
    return final[0]


def census(binary: Path, arena: Path, flags_path: Path, c54_path: Path,
           log_dir: Path, timeout: int) -> dict:
    flags = json.loads(flags_path.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("selected 24 source-qualified flags required")
    parent = json.loads(c54_path.read_text())
    if parent.get("all_six_profiled") is not True or parent.get("all_six_unknown") is not True:
        raise ValueError("C54 actual first failure roots must be qualified")
    prev = {c["case"]: c for c in parent["cases"]}
    if set(prev) != set(CASES):
        raise ValueError("missing frozen six-case C54 lineage")
    log_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "diagnostic": "C55 read-only application function-type failure classification",
        "steps_per_case": 262144, "original_artifact_id": 13276400289,
        "proof_rules_changed": False, "observations_are_proofs": False,
        "cases": [],
    }
    for case in CASES:
        source = (arena / "good" / "perf" / (case + ".ndjson")).read_bytes()
        previous = prev[case]
        if hashlib.sha256(source).hexdigest() != previous["source_sha256"]:
            raise ValueError("original source mutated since C54")
        kind, root = first_failed_value_root(source, previous)
        if root != previous["actual_first_failed_value_root"]:
            raise ValueError("C54 first failure root is inconsistent")
        environment = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
        environment.update(flags)
        environment.update({
            "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE": "1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR": str(root),
            "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS": "1",
            "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS": "1",
            "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE": "1",
            "NUCLEUS_TRACE_DOWNSTREAM": "1",
        })
        entry = {"case": case, "declaration_kind": kind,
                 "source_sha256": previous["source_sha256"], "first_failed_root": root,
                 "first_failed_boundary": previous["first_failed_boundary"]}
        try:
            run = subprocess.run([str(binary.resolve()), "262144"], input=source,
                                 capture_output=True, env=environment, timeout=timeout)
        except subprocess.TimeoutExpired:
            entry.update({"verdict": "TIMEOUT_NOT_CHECKER_VERDICT"})
            report["cases"].append(entry)
            continue
        log_dir.joinpath(case + ".stderr").write_bytes(run.stderr)
        if run.returncode != 2 or run.stdout or parse_downstream(run.stderr) != previous["first_failed_boundary"]:
            raise ValueError("C55 terminal checker verdict or boundary changed")
        entry.update({"verdict": "UNKNOWN", "app_failure": parse_app_observation(run.stderr, root)})
        report["cases"].append(entry)
    report["all_six_unknown"] = all(c["verdict"] == "UNKNOWN" for c in report["cases"])
    report["all_six_root_classified"] = all("app_failure" in c for c in report["cases"])
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--arena", required=True, type=Path)
    parser.add_argument("--flags", required=True, type=Path)
    parser.add_argument("--c54", required=True, type=Path)
    parser.add_argument("--logs", required=True, type=Path)
    parser.add_argument("--timeout", default=180, type=int)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        raise ValueError("bounded timeout required")
    r = census(args.binary, args.arena, args.flags, args.c54, args.logs, args.timeout)
    print(json.dumps(r, indent=2))
    if not r["all_six_unknown"] or not r["all_six_root_classified"]:
        raise SystemExit("C55 remains UNKNOWN; incomplete profiling cannot promote a result")


if __name__ == "__main__":
    main()
