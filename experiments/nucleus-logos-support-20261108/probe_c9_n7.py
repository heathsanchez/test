"""C9's unchanged-original red/green test for the qualified Nat.rec path.

Only a native ACCEPT under the selected 262,144-step flags makes this test
green. An UNKNOWN or REJECT is evidence *against* this narrow intervention.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ORIGINAL_N7_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    args = parser.parse_args()
    original = args.input.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if digest != ORIGINAL_N7_SHA256:
        raise SystemExit("C9 refused changed original n7 input")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or any(not k.startswith("NUCLEUS_") for k in flags):
        raise SystemExit("C9 refused non-selected run flags")
    environment = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    environment.update(flags)
    started = time.monotonic()
    try:
        outcome = subprocess.run([str(args.binary.resolve())], input=original,
                                 capture_output=True, env=environment, timeout=180)
        rc = outcome.returncode
    except subprocess.TimeoutExpired:
        rc = 124
    row = {"experiment": "C9-major-probe", "original": "magma-list-pair-n7",
           "sha256": digest, "expected": "ACCEPT", "exit_code": rc,
           "seconds": round(time.monotonic() - started, 3),
           "qualified": rc == 0}
    print(json.dumps(row), flush=True)
    if rc != 0:
        print("C9 RED: unchanged valid n7 still not ACCEPT under selected budget", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
