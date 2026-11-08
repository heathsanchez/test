"""RED/GREEN: projection receivers enter the same source-certified worklist.

The test does not infer a constructor or forgive any non-ACCEPT verdict.
The original source and selected runtime flags are immutable inputs.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


N7_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
DEFERRED = re.compile(r"^NUCLEUS_PROJECTION_MAJOR_WORKLIST_DEFERRED:.*$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    args = parser.parse_args()
    original = args.input.read_bytes()
    if hashlib.sha256(original).hexdigest() != N7_SHA256:
        raise SystemExit("C18 refused changed original n7")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or any(not k.startswith("NUCLEUS_") for k in flags):
        raise SystemExit("C18 refused changed runtime flags")
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"] = "1"
    process = subprocess.run([str(args.binary.resolve())], input=original,
                             env=env, capture_output=True, timeout=180)
    lines = process.stderr.decode(errors="replace").splitlines()
    deferred = [line for line in lines if DEFERRED.match(line)]
    outcomes = [line for line in lines if line.startswith("NUCLEUS_PROJECTION_MAJOR_EXHAUSTED:")]
    report = {
        "original_sha256": N7_SHA256,
        "global_budget": 262144,
        "rc": process.returncode,
        "worklist_projection_deferred": len(deferred),
        "sample": deferred[:4],
        "projection_exhaustions": len(outcomes),
        "source_result": "ACCEPT" if process.returncode == 0 else "UNKNOWN" if process.returncode == 2 else "UNEXPECTED",
    }
    print(json.dumps(report, indent=2), flush=True)
    if process.returncode not in (0, 2) or not deferred:
        print("C18 RED: unchanged n7 did not enter an independently checked "
              "projection receiver continuation", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
