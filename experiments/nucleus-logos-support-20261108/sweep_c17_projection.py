"""Source-pinned diagnostic sweep of actual borrowed projection work.

No alternative gets extra global fuel or an inferred constructor. A cap that
changes an unchanged valid test to REJECT is a regression, not improvement.
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


ORIGINAL_SHA = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
CAPS = (64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096, 8192)
GRANT = re.compile(r":grant=(\d+):parent=Some\((\d+)\):")
DEPTH = re.compile(r":depth=(\d+):step=")


def run(binary: Path, original: bytes, flags: dict[str, str], cap: int | str) -> dict:
    env = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_PROJECTION_GRANT"] = str(cap)
    t0 = time.monotonic()
    try:
        result = subprocess.run([str(binary)], input=original,
                                capture_output=True, env=env, timeout=180)
        rc = result.returncode
        lines = result.stderr.decode(errors="replace").splitlines()
    except subprocess.TimeoutExpired:
        rc, lines = 124, []
    borrowed = [line for line in lines
                if line.startswith("NUCLEUS_PROJECTION_MAJOR_BORROWED:")]
    pairs = [tuple(int(v) for v in match.groups())
             for line in borrowed if (match := GRANT.search(line))]
    exhausted = [line for line in lines
                 if line.startswith("NUCLEUS_PROJECTION_MAJOR_EXHAUSTED:")]
    depths = [int(match.group(1))
              for line in exhausted if (match := DEPTH.search(line))]
    large = [line for line in lines
             if line.startswith("NUCLEUS_CONVERSION_RECURSOR_PROBE:")
             and "grant=260755:" in line]
    return {"cap": cap, "rc": rc, "seconds": round(time.monotonic() - t0, 3),
            "borrowed_count_sampled": len(borrowed), "grants": pairs[:16],
            "max_exhausted_depth": max(depths, default=None),
            "large_replay_outcomes": large[:2]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    args = parser.parse_args()
    original = args.input.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise SystemExit("C17 refused a changed original Magma n7 input")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or any(not key.startswith("NUCLEUS_") for key in flags):
        raise SystemExit("C17 refused changed selected flags")
    records = [run(args.binary.resolve(), original, flags, cap) for cap in CAPS]
    malformed = run(args.binary.resolve(), original, flags, "not-a-budget")
    outcome = {
        "original_sha256": ORIGINAL_SHA,
        "global_budget": 262144,
        "result_state": "DIAGNOSTIC_ONLY",
        "candidate_caps": list(CAPS),
        "results": records,
        "malformed_control": malformed,
        "accepted_caps": [r["cap"] for r in records if r["rc"] == 0],
    }
    print(json.dumps(outcome, indent=2), flush=True)
    valid = all(r["rc"] in (0, 2) and r["grants"]
                and all(grant <= r["cap"] and grant <= parent
                        for grant, parent in r["grants"])
                for r in records)
    valid &= malformed["rc"] == 2
    if not valid:
        print("C17 RED: a valid source was rejected, timed out, or the "
              "specified borrowed cap was ignored", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
