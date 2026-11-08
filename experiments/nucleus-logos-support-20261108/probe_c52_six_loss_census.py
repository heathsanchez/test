"""Source-frozen, observer-only C50 failure-state census over all six UNKNOWNs.

Each input comes from the pinned original Lean Kernel Arena 207 artifact. The
binary is the C50 native-tested artifact. An UNKNOWN remains UNKNOWN; a logged
partial recursor frame never becomes a proof or a verdict.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c50_loss_ledger import parse_loss_events, summarize_losses


CASES = (
    "fueled-chain",
    "grind-ring-5",
    "magma-list-pair-n7",
    "magma-list-pair-n21",
    "magma-list-deep-n21",
    "magma-list-deep-n36",
)
DOWNSTREAM = re.compile(
    r"^NUCLEUS_DOWNSTREAM:name=(.+):stage=([^:]+):verdict=(UNKNOWN|REJECT):reason=(.+)$"
)


def parse_downstream(stderr: bytes) -> dict:
    found = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith("NUCLEUS_DOWNSTREAM:"):
            continue
        match = DOWNSTREAM.fullmatch(line)
        if not match:
            raise ValueError("malformed terminal checker-boundary record")
        name, stage, verdict, reason = match.groups()
        found.append({"source_name": name, "stage": stage, "verdict": verdict, "reason": reason})
    if len(found) != 1:
        raise ValueError("expected exactly one independently recorded terminal boundary")
    return found[0]


def frozen_case_names() -> tuple[str, ...]:
    return CASES


def declaration_kind(source: bytes) -> str:
    lines = source.rstrip(b"\n").split(b"\n")
    if len(lines) < 2:
        raise ValueError("missing original export records")
    final = json.loads(lines[-1])
    declarations = [final[tag] for tag in ("def", "thm") if tag in final]
    if len(declarations) != 1 or not isinstance(declarations[0], dict):
        raise ValueError("last original record is not a definition or theorem")
    return "def" if "def" in final else "thm"


def declaration_root(source: bytes) -> int:
    kind = declaration_kind(source)
    definition = json.loads(source.rstrip(b"\n").split(b"\n")[-1])[kind]
    root = definition.get("value")
    if type(root) is not int or root <= 0:
        raise ValueError("original declaration has no positive source root")
    return root


def census(binary: Path, arena: Path, flags_path: Path, log_dir: Path,
           timeout: int) -> dict:
    flags = json.loads(flags_path.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("must preserve selected 24 source-qualified flags")
    log_dir.mkdir(parents=True, exist_ok=True)
    binary_bytes = binary.read_bytes()
    report = {
        "diagnostic": "C50 loss events over six unchanged original inputs",
        "steps_per_case": 262144,
        "original_artifact_id": 13276400289,
        "compiled_binary_artifact_id": 13616928035,
        "binary_sha256": hashlib.sha256(binary_bytes).hexdigest(),
        "proof_rules_changed": False,
        "partial_state_is_a_proof": False,
        "cases": [],
    }
    for case in CASES:
        source_file = arena / "good" / "perf" / (case + ".ndjson")
        source = source_file.read_bytes()
        root = declaration_root(source)
        kind = declaration_kind(source)
        env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(flags)
        env.update({
            "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE": "1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR": str(root),
            "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS": "1",
            "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS": "1",
            "NUCLEUS_TRACE_DOWNSTREAM": "1",
        })
        entry = {
            "case": case,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "source_root": root,
            "declaration_kind": kind,
            "steps": 262144,
        }
        try:
            run = subprocess.run(
                [str(binary.resolve()), "262144"], input=source,
                capture_output=True, env=env, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            entry.update({"verdict": "TIMEOUT_NOT_CHECKER_VERDICT", "timeout_seconds": timeout})
            report["cases"].append(entry)
            continue
        log_dir.joinpath(case + ".stderr").write_bytes(run.stderr)
        if run.stdout or run.returncode not in (0, 2):
            raise ValueError(f"{case}: diagnostic executable escaped strict verdict channel")
        failure_boundary = parse_downstream(run.stderr)
        if failure_boundary["verdict"] != "UNKNOWN" or run.returncode != 2:
            raise ValueError(f"{case}: terminal boundary and process verdict disagree")
        profiled = b"NUCLEUS_C47_INNER_WORK:" in run.stderr
        losses = parse_loss_events(run.stderr) if profiled else []
        entry.update({
            "verdict": "ACCEPT_UNEXPECTED_REQUIRES_PROTECTION" if run.returncode == 0 else "UNKNOWN",
            "scope": "C47_SOURCE_ROOT_PROFILED" if profiled else "UNPROFILED_ENTRY_PATH",
            "first_failed_boundary": failure_boundary,
            "loss_summary": summarize_losses(losses) if profiled else None,
            "first_64_losses": losses[:64],
        })
        report["cases"].append(entry)
    report["all_six_unknown"] = all(c["verdict"] == "UNKNOWN" for c in report["cases"])
    report["all_six_profiled"] = all(c.get("loss_summary") is not None for c in report["cases"])
    report["all_definitions_profiled"] = all(
        c["loss_summary"] is not None for c in report["cases"]
        if c["declaration_kind"] == "def"
    )
    report["theorems_unprofiled"] = [
        c["case"] for c in report["cases"]
        if c["declaration_kind"] == "thm" and c["loss_summary"] is None
    ]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--arena", required=True, type=Path)
    parser.add_argument("--flags", required=True, type=Path)
    parser.add_argument("--logs", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 600:
        raise ValueError("bounded per-original timeout required")
    report = census(args.binary, args.arena, args.flags, args.logs, args.timeout)
    print(json.dumps(report, indent=2))
    if not report["all_six_unknown"] or not report["all_definitions_profiled"]:
        raise SystemExit("C52 census incomplete: retain UNKNOWN or TIMEOUT, never promote")


if __name__ == "__main__":
    main()
