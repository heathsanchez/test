"""C44: source-hashed n7 necessary `And.intro` first-proof obligation.

Requires *actual* Rust trace records, not patterns manufactured by this
script. A missing record is an experiment failure, never proof evidence.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


EXPECTED_SOURCE = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
PREFIXES = {"NUCLEUS_C44_INFERRED_ARG:": "inferred",
            "NUCLEUS_C44_ROOT_CHECK:": "check"}


def parse_events(stderr: bytes) -> dict:
    events = {key: [] for key in PREFIXES.values()}
    for line in stderr.decode(errors="replace").splitlines():
        for prefix, category in PREFIXES.items():
            if not line.startswith(prefix):
                continue
            row = json.loads(line.removeprefix(prefix))
            if row.get("expression") != 8804 or row.get("context_len") != 0:
                raise ValueError("C44 trace escaped its immutable root argument")
            if "remaining" not in row or not isinstance(row["remaining"], int):
                raise ValueError("C44 trace missing metered allowance")
            if row["remaining"] > 262144:
                raise ValueError("C44 trace invented extra fuel")
            events[category].append(row)
    return events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    parser.add_argument("--require", action="store_true")
    parser.add_argument("--stderr", type=Path)
    args = parser.parse_args()
    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if args.input.name != "magma-list-pair-n7.ndjson" or digest != EXPECTED_SOURCE:
        raise ValueError("C44 requires the exact unchanged original n7 export")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C44 selected flags are incomplete or contaminated")
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C44_ROOT_ARGUMENT"] = "1"
    run = subprocess.run([str(args.binary.resolve())], input=data,
                         capture_output=True, env=env, timeout=120)
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"outside verifier verdict boundary: {run.returncode}")
    events = parse_events(run.stderr)
    if args.require and (not events["inferred"] or not events["check"]):
        raise ValueError("C44 root argument was not observed")
    print(json.dumps({"case": args.input.stem, "sha256": digest,
                      "budget": 262144, "proof_rules_changed": False,
                      "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
                      "events": events}, indent=2))


if __name__ == "__main__":
    main()
