#!/usr/bin/env python3
"""Run the Rust regressions with the original source-qualified test flags."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("NUCLEUS_", "METATRON_"))}
    env.update({"RUST_MIN_STACK": "67108864",
                "NUCLEUS_EXPERIMENTAL_RELEVANCE": "1",
                "NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA": "1",
                "NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR": "1"})
    result = subprocess.run(["cargo", "test", "--locked", *sys.argv[1:]],
                            cwd=Path(__file__).resolve().parents[1], env=env)
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


if __name__ == "__main__":
    sys.exit(main())
