"""Compare two source-owned recursor decision streams on unchanged n7.

No diagnostic equality is promoted to checker authority. Only the Rust
executable's unchanged independent verdict is reported as such.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c50_loss_ledger import parse_loss_events, summarize_losses


N7_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
PREFIX = "NUCLEUS_C48_EVENT:"
STAGES = {"enter", "major-result", "projected-major", "constructor"}
LIMIT = 512
COMPARE_FIELDS = ("stage", "recursor", "major_expr", "major_env", "depth", "detail")


def first_content_divergence(failed: list[dict], accepted: list[dict]) -> dict:
    """Observer-only source-content grouping; no digest licenses a proof."""
    shared = 0
    for left, right in zip(failed, accepted):
        left_detail = re.sub(r"env=\d+", "env=<capture>", left["detail"])
        right_detail = re.sub(r"env=\d+", "env=<capture>", right["detail"])
        fields = ("stage", "recursor", "major_expr", "depth", "major_env_content_fingerprint")
        if any(left.get(f) != right.get(f) for f in fields) or left_detail != right_detail:
            break
        shared += 1
    return {
        "shared_prefix": shared,
        "failed_next": failed[shared] if shared < len(failed) else None,
        "accepted_next": accepted[shared] if shared < len(accepted) else None,
        "possibly_truncated": len(failed) >= LIMIT or len(accepted) >= LIMIT,
        "hash_is_not_source_equality": True,
    }


def parse_trace(stderr: bytes) -> list[dict]:
    events = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        record = json.loads(line.removeprefix(PREFIX))
        sequence = record.get("seq")
        if not isinstance(sequence, int) or sequence != len(events) or sequence >= LIMIT:
            raise ValueError("C48 event sequence escaped the bounded source trace")
        if record.get("stage") not in STAGES:
            raise ValueError("C48 recorded an unknown source stage")
        for key in ("recursor", "major_expr", "major_env", "depth", "owner_remaining"):
            value = record.get(key)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"C48 source record lacks nonnegative {key}")
        if not isinstance(record.get("detail"), str) or len(record["detail"]) > 400:
            raise ValueError("C48 recorded an unbounded source outcome")
        events.append(record)
    return events


def first_divergence(failed: list[dict], accepted: list[dict]) -> dict:
    shared = 0
    for left, right in zip(failed, accepted):
        if any(left[field] != right[field] for field in COMPARE_FIELDS):
            break
        shared += 1
    return {
        "shared_prefix": shared,
        "failed_next": failed[shared] if shared < len(failed) else None,
        "accepted_next": accepted[shared] if shared < len(accepted) else None,
        "possibly_truncated": len(failed) >= LIMIT or len(accepted) >= LIMIT,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--flags", required=True, type=Path)
    parser.add_argument("--stderr-dir", required=True, type=Path)
    parser.add_argument("--require-events", action="store_true")
    parser.add_argument("--c49-content-fingerprint", action="store_true")
    parser.add_argument("--c50-loss-ledger", action="store_true")
    args = parser.parse_args()
    original = args.input.read_bytes()
    source_sha = hashlib.sha256(original).hexdigest()
    if args.input.name != "magma-list-pair-n7.ndjson" or source_sha != N7_SHA256:
        raise ValueError("C48 must use the exact unchanged original Magma n7 export")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C48 requires the exact selected 24 source-qualified flags")
    args.stderr_dir.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR"] = "8837"
    env["NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS"] = "1"
    if args.c49_content_fingerprint:
        env["NUCLEUS_DIAGNOSTIC_C49_CONTENT_FINGERPRINT"] = "1"
    if args.c50_loss_ledger:
        env["NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS"] = "1"
    results = {}
    for label, steps in (("standard", 262144), ("accepted_diagnostic", 14155776)):
        run = subprocess.run(
            [str(args.binary.resolve()), str(steps)], input=original,
            capture_output=True, env=env, timeout=240,
        )
        if run.returncode not in (0, 2) or run.stdout:
            raise ValueError(f"C48 diagnostic crossed verifier verdict boundary: {run.returncode}")
        args.stderr_dir.joinpath(f"c48-{label}.stderr").write_bytes(run.stderr)
        events = parse_trace(run.stderr)
        if args.require_events and not events:
            raise ValueError(f"C48 missing source transitions in {label}")
        results[label] = {
            "steps": steps,
            "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
            "events": events,
        }
        if args.c50_loss_ledger:
            losses = parse_loss_events(run.stderr)
            results[label]["c50_loss_events"] = losses
    if results["standard"]["verdict"] != "UNKNOWN":
        raise ValueError("C48 standard verdict changed unexpectedly")
    if results["accepted_diagnostic"]["verdict"] != "ACCEPT_DIAGNOSTIC_ONLY":
        raise ValueError("C48 expected high-budget differential control did not accept")
    left = results["standard"]["events"]
    right = results["accepted_diagnostic"]["events"]
    report = {
        "case": args.input.stem,
        "source_sha256": source_sha,
        "proof_rules_changed": False,
        "standard": {k: v for k, v in results["standard"].items() if k not in ("events", "c50_loss_events")},
        "accepted_diagnostic": {k: v for k, v in results["accepted_diagnostic"].items() if k not in ("events", "c50_loss_events")},
        "event_counts": {"standard": len(left), "accepted_diagnostic": len(right)},
        "first_divergence": first_divergence(left, right),
        "standard_first_64": left[:64],
        "accepted_first_64": right[:64],
    }
    if args.c49_content_fingerprint:
        report["c49_content_divergence"] = first_content_divergence(left, right)
        report["c49_fingerprints_observer_only"] = True
    if args.c50_loss_ledger:
        report["c50_loss_summary"] = {
            label: summarize_losses(results[label]["c50_loss_events"])
            for label in ("standard", "accepted_diagnostic")
        }
        report["c50_first_64_losses"] = {
            label: results[label]["c50_loss_events"][:64]
            for label in ("standard", "accepted_diagnostic")
        }
        report["c50_partial_state_is_a_proof"] = False
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
