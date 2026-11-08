"""Classify failed checked telescopes without affecting source qualification."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c35_metered_recursor import ORIGINAL_INPUTS

STAGES = {
    "entry-guard", "identical-spines", "different-head-shape",
    "different-head-or-universe-arity", "universe-equality", "source-declaration",
    "universe-parameters", "left-pi", "right-pi", "left-argument-inference",
    "right-argument-inference", "left-argument-type", "right-argument-type",
    "data-argument-conversion", "left-body-instantiation", "right-body-instantiation",
}
FAIL = re.compile(
    r"NUCLEUS_C39_TYPED_FAILURE:head=(.+?):spine=(\d+):depth=(\d+):"
    r"budget=(\d+):arg=(\d+):stage=([\w-]+)"
)


def parse_failure(line: str) -> dict | None:
    if not line.startswith("NUCLEUS_C39_TYPED_FAILURE:"):
        return None
    match = FAIL.fullmatch(line)
    if match is None:
        raise ValueError("C39 stage record is malformed")
    head, spine, depth, budget, arg, stage = match.groups()
    if stage not in STAGES or int(arg) >= int(spine) and stage != "entry-guard":
        raise ValueError("C39 stage record violates the source telescope")
    return {"head": head, "spine": int(spine), "depth": int(depth),
            "budget": int(budget), "arg": int(arg), "stage": stage}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    parser.add_argument("--stderr", type=Path)
    parser.add_argument("--require-observation", action="store_true")
    args = parser.parse_args()
    original = args.input.read_bytes()
    source_hash = hashlib.sha256(original).hexdigest()
    if ORIGINAL_INPUTS.get(args.input.stem) != source_hash:
        raise ValueError("C39 requires exact original source, not a modified theorem")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C39 requires the selected independent Nucleus flags")
    env = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C39_TYPED_FAILURE"] = "1"
    result = subprocess.run([str(args.binary.resolve())], input=original,
                            env=env, capture_output=True, timeout=180)
    if args.stderr:
        args.stderr.write_bytes(result.stderr)
    if result.returncode not in (0, 2) or result.stdout:
        raise ValueError(f"out-of-boundary verdict: {result.returncode}")
    failures = [record for line in result.stderr.decode(errors="replace").splitlines()
                if (record := parse_failure(line)) is not None]
    if args.require_observation and not failures:
        raise ValueError("C39 diagnostic was not exercised")
    counts = Counter(record["stage"] for record in failures)
    print(json.dumps({"case": args.input.stem, "source_sha256": source_hash,
                      "standard_steps": 262144, "qualified_rules_changed": False,
                      "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if result.returncode == 0 else "UNKNOWN",
                      "failure_records": len(failures), "failure_stages": dict(counts),
                      "first_20_failures": failures[:20]}, indent=2))


if __name__ == "__main__":
    main()
