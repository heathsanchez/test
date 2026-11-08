"""Red/green native diagnostic for the caller-owned recursor probe route.

The original valid Magma n7 must remain UNKNOWN for a read-only observer.
But the trace must identify which qualified source recursor got which budget.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


SHA = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    parser.add_argument("--require-owner-event", action="store_true",
                        help="C11: require the exact failure's owner/budget trace")
    args = parser.parse_args()
    original = args.input.read_bytes()
    if hashlib.sha256(original).hexdigest() != SHA:
        raise SystemExit("C10 refused changed Magma n7 original")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or any(not key.startswith("NUCLEUS_") for key in flags):
        raise SystemExit("C10 refused non-selected run flags")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
    environment.update(flags)
    environment["NUCLEUS_TRACE_REPLAY_CACHE"] = "1"
    environment["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"] = "1"
    started = time.monotonic()
    try:
        result = subprocess.run([str(args.binary.resolve())], input=original,
                                capture_output=True, env=environment, timeout=180)
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        raise SystemExit("C10 native route probe timed out")
    output = result.stderr.decode(errors="replace").splitlines()
    routes = [line for line in output if line.startswith("NUCLEUS_CONVERSION_RECURSOR_PROBE:")]
    exhausted = [line for line in output if line.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:")]
    owned_failures = [line for line in exhausted if ":stage=" in line and ":entry_budget=" in line]
    record = {"experiment": "C10-source-recursor-caller-budget-route", "original_sha256": SHA,
              "exit_code": exit_code, "seconds": round(time.monotonic() - started, 3),
              "route_count": len(routes), "route_sample": routes[:12],
              "nested_failure_sample": exhausted[:3],
              "owned_failures": owned_failures[:3]}
    print(json.dumps(record), flush=True)
    if exit_code != 2 or not routes:
        print("C10 RED: observer must explain the unchanged UNKNOWN route", file=sys.stderr)
        return 1
    if args.require_owner_event and not owned_failures:
        print("C11 RED: terminal recursor failure did not identify its work owner", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
