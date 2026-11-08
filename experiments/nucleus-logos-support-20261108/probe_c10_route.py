"""Red/green native diagnostic for the caller-owned recursor probe route.

The original valid Magma n7 must remain UNKNOWN for a read-only observer.
But the trace must identify which qualified source recursor got which budget.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
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
    parser.add_argument("--require-caller-event", action="store_true",
                        help="C12: require terminal caller location and replay goal")
    parser.add_argument("--require-large-replay-outcome", action="store_true",
                        help="C13: classify large-budget Bool-vs-Decidable checked replay")
    parser.add_argument("--require-projection-major-boundary", action="store_true",
                        help="C14: classify value and stage at exhausted major owner")
    parser.add_argument("--require-bounded-projection", action="store_true",
                        help="C15: prove the candidate's bounded source projection path ran")
    parser.add_argument("--allow-accepted", action="store_true",
                        help="C15: valid exact original may improve from UNKNOWN to ACCEPT")
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
    caller_failures = [line for line in owned_failures
                       if ":caller=" in line and ":replay_goal=" in line]
    large_replay_outcomes = []
    for line in routes:
        if ":route=certified-bool-constructor:" not in line or ":outcome=" not in line:
            continue
        grant = re.search(r":grant=(\d+):", line)
        if grant and int(grant.group(1)) >= 100_000:
            large_replay_outcomes.append(line)
    projection_major_boundaries = []
    bounded_projection_events = []
    for line in output:
        if line.startswith("NUCLEUS_PROJECTION_MAJOR_BOUNDED:"):
            bounded_projection_events.append(line)
        if not line.startswith("NUCLEUS_PROJECTION_MAJOR_EXHAUSTED:"):
            continue
        grant = re.search(r":entry_budget=(\d+):", line)
        if grant and int(grant.group(1)) >= 100_000:
            projection_major_boundaries.append(line)
    record = {"experiment": "C10-source-recursor-caller-budget-route", "original_sha256": SHA,
              "exit_code": exit_code, "seconds": round(time.monotonic() - started, 3),
              "route_count": len(routes), "route_sample": routes[:12],
              "nested_failure_sample": exhausted[:3],
              "owned_failures": owned_failures[:3],
              "caller_failures": caller_failures[:3],
              "large_replay_outcomes": large_replay_outcomes[:3],
              "projection_major_boundaries": projection_major_boundaries[:3],
              "bounded_projection_events": bounded_projection_events[:16]}
    print(json.dumps(record), flush=True)
    allowed_exit_codes = (0, 2) if args.allow_accepted else (2,)
    if exit_code not in allowed_exit_codes or (not routes and not args.allow_accepted):
        print("C10 RED: observer must explain the unchanged UNKNOWN route", file=sys.stderr)
        return 1
    if args.require_bounded_projection and not bounded_projection_events:
        print("C15 RED: bounded projection candidate did not execute", file=sys.stderr)
        return 1
    if args.require_owner_event and not owned_failures:
        print("C11 RED: terminal recursor failure did not identify its work owner", file=sys.stderr)
        return 1
    if args.require_caller_event and not caller_failures:
        print("C12 RED: terminal recursor failure did not identify its caller", file=sys.stderr)
        return 1
    if args.require_large_replay_outcome and not large_replay_outcomes:
        print("C13 RED: large checked Decidable replay's residual is missing", file=sys.stderr)
        return 1
    if args.require_projection_major_boundary and not projection_major_boundaries:
        print("C14 RED: exhausted major's actual source value and step are missing", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
