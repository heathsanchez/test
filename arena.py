#!/usr/bin/env python3
"""Frozen Arena launch configuration for the independent Nucleus checker.

The input is passed unchanged. Inputs beyond this release's byte allowance
are explicitly declined before invoking the checker. No input names, hashes,
expected verdicts, or external proof checkers are consulted at runtime.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

MAX_INPUT_BYTES = 10 * 1024 * 1024


def main():
    root = Path(__file__).resolve().parent
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        print("NUCLEUS_DECLINED: input byte allowance", file=sys.stderr)
        return 2
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("NUCLEUS_", "METATRON_"))}
    env.update(json.loads((root / "arena-flags.json").read_text()))
    # Preserve the binary's raw verdict, including errors or termination.
    proc = subprocess.run([str(root / "target/release/metatron-kernel")],
                          input=raw, env=env)
    return proc.returncode if proc.returncode >= 0 else 128 - proc.returncode


if __name__ == "__main__":
    sys.exit(main())
