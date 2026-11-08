"""Run a source-frozen scalar recursor-major allowance diagnostic.

Only the local source-exposure request changes; the global Nucleus judgment
budget and checker rules remain the same. A local ACCEPT is not a release
qualification until protected/regression controls run with the same cap.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


EXPECTED_N7 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
PREFIX = "NUCLEUS_C32_MAJOR_GRANT:"
REGEX = re.compile(
    r"NUCLEUS_C32_MAJOR_GRANT:seq=(\d+):head=NameId\((\d+)\):"
    r"cap=(\d+):budget=(\d+):owner=Some\((\d+)\)"
)


def parse_marker(line: str) -> dict[str, int] | None:
    if not line.startswith(PREFIX):
        return None
    match = REGEX.fullmatch(line)
    if match is None:
        raise ValueError(f"C32 marker malformed: {line[:240]}")
    seq, head, cap, budget, owner = (int(n) for n in match.groups())
    if not (0 <= budget <= cap and budget <= owner):
        raise ValueError("C32 source budget exceeds recorded cap/owner")
    return {"seq": seq, "head": head, "cap": cap,
            "budget": budget, "owner": owner}


def main() -> None:
    arg = argparse.ArgumentParser()
    arg.add_argument("--binary", type=Path, required=True)
    arg.add_argument("--input", type=Path, required=True)
    arg.add_argument("--flags", type=Path, required=True)
    arg.add_argument("--cap", type=int, required=True)
    arg.add_argument("--stderr", type=Path)
    arg.add_argument("--require-markers", action="store_true")
    args = arg.parse_args()
    if args.cap not in (512, 768, 1024, 1536, 2048, 4096, 8192, 16384):
        raise ValueError("C32 cap is not a predeclared test arm")
    source = args.input.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_N7:
        raise ValueError("C32 target source differs from the frozen original")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C32 flags differ from the canonical 24")
    env = dict(os.environ)
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C32_RECURSOR_MAJOR_GRANT"] = str(args.cap)
    env.pop("NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS", None)
    env.pop("NUCLEUS_DIAGNOSTIC_C30_EXACT_MAJOR_CACHE", None)
    result = subprocess.run([str(args.binary.resolve())], input=source,
                            env=env, capture_output=True, timeout=180)
    if result.returncode not in (0, 2) or result.stdout:
        raise ValueError(f"C32 produced unqualified rejected/invalid result: {result.returncode}")
    if args.stderr:
        args.stderr.write_bytes(result.stderr)
    records = [record for line in result.stderr.decode(errors="replace").splitlines()
               if (record := parse_marker(line)) is not None]
    if args.require_markers and not records:
        raise ValueError("C32 marker not exercised in native binary")
    if any(row["cap"] != args.cap for row in records):
        raise ValueError("C32 marker did not respect selected local cap")
    print(json.dumps({
        "original_sha256": digest, "global_steps": 262144,
        "cap": args.cap, "selected_flags": 24,
        "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if result.returncode == 0 else "UNKNOWN",
        "rc": result.returncode, "observations": len(records),
        "head_counts": dict(Counter(str(row["head"]) for row in records)),
        "first_five": records[:5],
    }, indent=2))


if __name__ == "__main__":
    main()
