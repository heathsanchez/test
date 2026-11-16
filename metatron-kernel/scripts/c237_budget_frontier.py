"""C237 exact-source computational frontier, not a soundness promotion.

Replay the unchanged C236 checker binary and unchanged original Arena corpus.
The only experimental dimension is the documented 65,536..69,632
diagnostics-only resource allowance. Distinguish verdict, timeout and error.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from c236_infer_conversion_lineage import parse_trace

C236_SHA = "52ff6dde90bab4a1bf084700287ca0915e0251ad67e4f1f6eab4d1090802fd0c"
C236_BIN_SHA = "129ca2b623ab7e73a4352b6dd43c4b2afb02ea0d8c44e44a7365407487311ff1"
ORIGINAL_ARCHIVE_SHA = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED_SHA = "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
SOURCE_COMMIT = "81d5798317073d38a01e882d2ea89f698ec136da"
BUDGETS = (65536, 65728, 66560, 67584, 69632)
CONTROLS = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)
ADDITIONAL_FLAGS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)
TERMINAL = "NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"


def digest(content):
    return hashlib.sha256(content).hexdigest()


def run(checker, content, env, name, out, timeout=125):
    started = time.monotonic()
    try:
        proc = subprocess.run([str(checker)], input=content, env=env,
                              capture_output=True, timeout=timeout, check=False)
        stderr = proc.stderr.decode(errors="replace")
        stdout = proc.stdout.decode(errors="replace")
        status, verdict = "completed", proc.returncode
    except subprocess.TimeoutExpired as e:
        stderr = (e.stderr or b"").decode(errors="replace")
        stdout = (e.stdout or b"").decode(errors="replace")
        status, verdict = "timeout", None
    (out / (name + ".stderr")).write_text(stderr)
    (out / (name + ".stdout")).write_text(stdout)
    return {
        "case": name, "status": status, "exit": verdict,
        "elapsed_s": round(time.monotonic() - started, 3),
        "source_sha256": digest(content),
        "terminal_original_unknown": stderr.splitlines().count(TERMINAL) == 1,
        "downstream_tail": [line[:260] for line in stderr.splitlines()
                            if line.startswith("NUCLEUS_DOWNSTREAM:")][-2:],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--c236-artifact", type=Path, required=True)
    p.add_argument("--source-archive", type=Path, required=True)
    p.add_argument("--flags", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(exist_ok=True, parents=True)
    if digest(args.c236_artifact.read_bytes()) != C236_SHA:
        raise ValueError("C236 artifact SHA256 not authorized")
    if digest(args.source_archive.read_bytes()) != ORIGINAL_ARCHIVE_SHA:
        raise ValueError("212 original archive SHA256 not authorized")
    with zipfile.ZipFile(args.c236_artifact) as z:
        if z.read("commit.txt").decode().strip() != SOURCE_COMMIT:
            raise ValueError("Binary source identity mismatch")
        checker_bytes = z.read("nucleus")
        if digest(checker_bytes) != C236_BIN_SHA:
            raise ValueError("Checker executable SHA256 mismatch")
        observed = json.loads(z.read("report.json"))
        if [r["exit"] for r in observed["original"]] != [2, 2, 2, 2]:
            raise ValueError("C236 source-observation baseline not qualified")
    executable = args.out / "nucleus"
    executable.write_bytes(checker_bytes)
    executable.chmod(0o755)
    flags = json.loads(args.flags.read_text())["flags"]
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("Changed historical flag set")
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{key}": "1" for key in ADDITIONAL_FLAGS})
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"

    with zipfile.ZipFile(args.source_archive) as source_archive:
        current = {x["case"]: x for x in json.loads(source_archive.read("current212.json"))}
        if len(current) != 212:
            raise ValueError("Original case count changed")
        def original(case):
            blob = source_archive.read("inputs/" + case)
            if digest(blob) != current[case]["sha256"]:
                raise ValueError("Original case bytes changed")
            return blob
        raw = original("good/perf/fueled-chain.ndjson")
        if digest(raw) != FUELED_SHA:
            raise ValueError("Wrong original fueled-chain")
        cases = []
        for budget in BUDGETS:
            if not 65536 <= budget <= 69632:
                raise ValueError("Outside supported C225 budget range")
            selected = env.copy()
            if budget != 65536:
                selected["NUCLEUS_C225_JUDGMENT_STEPS"] = str(budget)
            result = run(executable, raw, selected, f"original_{budget}", args.out)
            result["budget"] = budget
            # Genuine unchanged source must never REJECT or crash.
            if result["exit"] in (1, 3):
                raise ValueError("Invalid verdict for known valid original: " + str(result))
            if budget == 65536 and (
                result["exit"] != 2 or not result["terminal_original_unknown"]
            ):
                raise ValueError("Baseline changed from qualified C236")
            cases.append(result)
            print("C237_FRONTIER", json.dumps(result, sort_keys=True), flush=True)
        # One further inference-ancestry replay at the exact supported C225
        # ceiling distinguishes more global allowance from a remaining local
        # conversion/exposure obstruction. Observer result never decides.
        deep_env = env.copy()
        deep_env["NUCLEUS_C225_JUDGMENT_STEPS"] = "69632"
        deep_env["NUCLEUS_C236_INFER_ANCESTRY"] = "1"
        deep = run(executable, original("good/perf/fueled-chain.ndjson"),
                   deep_env, "original_69632_ancestry", args.out)
        if deep["status"] != "completed" or deep["exit"] != 2 or not deep["terminal_original_unknown"]:
            raise ValueError("High-budget source verdict changed: " + str(deep))
        deep_trace = parse_trace((args.out / (deep["case"] + ".stderr")).read_text())
        terminal_owners = deep_trace["target_owner_conversions"]
        deep["trace_summary"] = {
            "infer_calls": deep_trace["infer_calls"],
            "unknown_infer_calls": deep_trace["unknown_infer_calls"],
            "unknown_conversion_events": deep_trace["unknown_conversion_events"],
            "target_owner_events_total": deep_trace["target_owner_events_total"],
            "terminal_owner": terminal_owners[-1] if terminal_owners else None,
        }
        print("C237_CEILING_ANCESTRY", json.dumps(deep["trace_summary"], sort_keys=True), flush=True)
        # Read-only candidate refinement: capture the actual reducible/full
        # exposure and type constructor at the failing source-owned judgment.
        # This result is not substituted for the checker verdict.
        rigid_env = env.copy()
        rigid_env["NUCLEUS_C225_JUDGMENT_STEPS"] = "69632"
        rigid_env["NUCLEUS_TRACE_RIGID_TYPE_MISMATCH"] = "1"
        rigid_env["NUCLEUS_C223_FIRST_OWNER"] = "1"
        rigid = run(executable, original("good/perf/fueled-chain.ndjson"),
                    rigid_env, "original_69632_rigid", args.out)
        if rigid["status"] != "completed" or rigid["exit"] != 2 or not rigid["terminal_original_unknown"]:
            raise ValueError("Rigid observation changed original source verdict")
        rigid_lines = (args.out / (rigid["case"] + ".stderr")).read_text().splitlines()
        mismatch_lines = [line for line in rigid_lines if line.startswith((
            "NUCLEUS_RIGID_TYPE_MISMATCH:", "NUCLEUS_TYPE_EXPOSURE_UNKNOWN:",
            "NUCLEUS_C223_APP_OWNER:", "NUCLEUS_C223_INFER_UNKNOWN:"
        ))]
        rigid["observed_mismatch_count"] = sum(
            line.startswith("NUCLEUS_RIGID_TYPE_MISMATCH:") for line in mismatch_lines
        )
        rigid["first_observations"] = [line[:1400] for line in mismatch_lines[:30]]
        rigid["last_observations"] = [line[:1400] for line in mismatch_lines[-30:]]
        print("C237_RIGID_OBSERVATIONS", json.dumps({
            "count": len(mismatch_lines),
            "mismatch_count": rigid["observed_mismatch_count"],
            "last": rigid["last_observations"][-8:]
        }, sort_keys=True), flush=True)
        protected = []
        for case in CONTROLS:
            raw_case = original(case)
            for budget in (65536, 69632):
                selected = env.copy()
                if budget != 65536:
                    selected["NUCLEUS_C225_JUDGMENT_STEPS"] = str(budget)
                label = "control_" + case.replace("/", "_").removesuffix(".ndjson") + f"_{budget}"
                result = run(executable, raw_case, selected, label, args.out, timeout=65)
                if result["status"] != "completed" or (
                    result["exit"] != current[case]["expected"]
                    or result["exit"] != current[case]["actual"]
                ):
                    raise ValueError("Original control verdict changed: " + str(result))
                result["source_case"] = case
                result["budget"] = budget
                protected.append(result)
        if len(cases) != len(BUDGETS) or len(protected) != 14:
            raise ValueError("Incomplete C237 experiment")
    report = {
        "status": "WARRANTED_BOUNDED_ONLY_IF_GITHUB_CI_GREEN",
        "source_commit": SOURCE_COMMIT,
        "binary_sha256": C236_BIN_SHA,
        "source_archive_sha256": ORIGINAL_ARCHIVE_SHA,
        "genuine_export_sha256": FUELED_SHA,
        "experiment": "C225 diagnostic budget; same checker and original source",
        "no_semantic_rule_changed": True,
        "frontier": cases, "high_budget_ancestry": deep,
        "rigid_observation": rigid, "protected": protected,
        "full_arena_completion": "UNKNOWN",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("C237_SUMMARY", json.dumps({
        "frontier": [(r["budget"], r["status"], r["exit"]) for r in cases],
        "protected_exits": [r["exit"] for r in protected],
        "qualified_source_commit": SOURCE_COMMIT,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
