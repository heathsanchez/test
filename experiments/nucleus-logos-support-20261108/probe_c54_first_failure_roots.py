"""C54: profile the *actual first failing declaration* of six frozen originals.

C52 assumed that the final NDJSON declaration was the failing declaration.
That was false for both theorem exports. C54 resolves the terminal name against
the source's native name table, without rewriting or resynthesizing any proof.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from probe_c50_loss_ledger import parse_loss_events, summarize_losses
from probe_c52_six_loss_census import CASES, parse_downstream


def declared_value_roots(source: bytes) -> dict[str, tuple[str, int]]:
    names = {0: ""}
    result = {}
    for line in source.splitlines():
        record = json.loads(line)
        if "in" in record:
            record_id = record["in"]
            if type(record_id) is not int or record_id in names:
                raise ValueError("malformed or repeated source-name ID")
            part = record.get("str", record.get("num"))
            if not isinstance(part, dict) or part.get("pre") not in names:
                raise ValueError("malformed native source-name predecessor")
            if "str" in part:
                suffix = part["str"]
            elif "i" in part:
                suffix = str(part["i"])
            else:
                raise ValueError("unrecognized native source-name component")
            names[record_id] = names[part["pre"]] + "." + suffix
        for tag in ("thm", "def"):
            if tag in record:
                item = record[tag]
                if item.get("name") not in names or type(item.get("value")) is not int:
                    raise ValueError("unresolved declaration or source expression")
                name = names[item["name"]].removeprefix(".")
                if name in result:
                    raise ValueError("duplicate declaration name")
                result[name] = (tag, item["value"])
    return result


def first_failed_value_root(source: bytes, c52_entry: dict) -> tuple[str, int]:
    failure = c52_entry["first_failed_boundary"]
    if failure["verdict"] != "UNKNOWN":
        raise ValueError("C52 did not observe terminal UNKNOWN")
    stage = failure["stage"]
    if stage not in ("theorem.value", "definition.value"):
        raise ValueError("C54 profiles only failed proof or definition values")
    declaration = declared_value_roots(source).get(failure["source_name"])
    expected_kind = "thm" if stage == "theorem.value" else "def"
    if declaration is None or declaration[0] != expected_kind:
        raise ValueError("C52 first failed name is not a matching native value declaration")
    return declaration


def profile(binary: Path, arena: Path, flags_path: Path, c52_path: Path,
            log_dir: Path, timeout: int) -> dict:
    flags = json.loads(flags_path.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("selected 24 source-qualified flags are required")
    prior = json.loads(c52_path.read_text())
    if prior.get("all_six_unknown") is not True or len(prior.get("cases", [])) != 6:
        raise ValueError("C52 needs a qualified full six-case census")
    if prior.get("compiled_binary_artifact_id") != 13616928035:
        raise ValueError("C52 binary provenance changed")
    existing = {c["case"]: c for c in prior["cases"]}
    if set(existing) != set(CASES):
        raise ValueError("C52 case set does not match unchanged six")
    log_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "diagnostic": "C54 source-qualified first-failed-declaration root profiling",
        "parent_c52_run": 42483411956,
        "original_artifact_id": 13276400289,
        "compiled_binary_artifact_id": 13616928035,
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "steps_per_case": 262144,
        "proof_rules_changed": False,
        "partial_worklist_is_a_proof": False,
        "cases": [],
    }
    if prior.get("binary_sha256") != report["binary_sha256"]:
        raise ValueError("C54 executable differs from native-qualified C52 executable")
    for case in CASES:
        source = (arena / "good" / "perf" / (case + ".ndjson")).read_bytes()
        c52_entry = existing[case]
        if hashlib.sha256(source).hexdigest() != c52_entry["source_sha256"]:
            raise ValueError("C54 input differs from C52's frozen source")
        kind, actual_root = first_failed_value_root(source, c52_entry)
        environment = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
        environment.update(flags)
        environment.update({
            "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE": "1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR": str(actual_root),
            "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS": "1",
            "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS": "1",
            "NUCLEUS_TRACE_DOWNSTREAM": "1",
        })
        entry = {
            "case": case, "source_sha256": c52_entry["source_sha256"],
            "declaration_kind": kind,
            "previous_last_record_root": c52_entry["source_root"],
            "actual_first_failed_value_root": actual_root,
            "root_was_mistargeted": actual_root != c52_entry["source_root"],
            "first_failed_boundary": c52_entry["first_failed_boundary"],
        }
        try:
            completed = subprocess.run([str(binary.resolve()), "262144"], input=source,
                                       capture_output=True, env=environment, timeout=timeout)
        except subprocess.TimeoutExpired:
            entry.update({"verdict": "TIMEOUT_NOT_CHECKER_VERDICT", "profiled": False})
            report["cases"].append(entry)
            continue
        log_dir.joinpath(case + ".stderr").write_bytes(completed.stderr)
        observed_boundary = parse_downstream(completed.stderr)
        if completed.returncode != 2 or completed.stdout or observed_boundary != c52_entry["first_failed_boundary"]:
            raise ValueError("source verdict/first failed obligation changed during diagnostic replay")
        profiled = b"NUCLEUS_C47_INNER_WORK:" in completed.stderr
        losses = parse_loss_events(completed.stderr) if profiled else []
        entry.update({
            "verdict": "UNKNOWN", "profiled": profiled,
            "loss_summary": summarize_losses(losses) if profiled else None,
            "first_64_losses": losses[:64],
        })
        report["cases"].append(entry)
    report["all_six_unknown"] = all(c["verdict"] == "UNKNOWN" for c in report["cases"])
    report["all_six_profiled"] = all(c["profiled"] for c in report["cases"])
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--arena", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    parser.add_argument("--c52", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        raise ValueError("bounded diagnostic timeout required")
    result = profile(args.binary, args.arena, args.flags, args.c52, args.logs, args.timeout)
    print(json.dumps(result, indent=2))
    if not result["all_six_unknown"] or not result["all_six_profiled"]:
        raise SystemExit("C54 cannot qualify unprofiled or non-UNKNOWN original")


if __name__ == "__main__":
    main()
