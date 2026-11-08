"""Bounded diagnostic for reserving fallback work after checked source trials.

C34 changes only the work allocation of C28's optional sufficient equality
check. An ACCEPT here is diagnostic until the full protected matrix passes.
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

from c33_probe import EXPECTED_N7, parse_record


MARKER = "NUCLEUS_C34_FALLBACK_RESERVE:"
PATTERN = re.compile(
    r"NUCLEUS_C34_FALLBACK_RESERVE:head=NameId\((\d+)\):depth=(\d+):"
    r"divisor=(\d+):reserve=(\d+):cap=(\d+):grant=(\d+):"
    r"spent=(\d+):remaining=(\d+):proved=(true|false)"
)


def parse_reserve(line: str) -> dict[str, int | bool] | None:
    if not line.startswith(MARKER):
        return None
    match = PATTERN.fullmatch(line)
    if not match:
        raise ValueError(f"malformed C34 source reserve event: {line[:240]}")
    head, depth, divisor, reserve, cap, grant, spent, remaining, proven = match.groups()
    out: dict[str, int | bool] = dict(zip(
        ("head", "depth", "divisor", "reserve", "cap", "grant", "spent", "remaining"),
        map(int, (head, depth, divisor, reserve, cap, grant, spent, remaining)),
    ))
    out["proved"] = proven == "true"
    if out["divisor"] not in (2, 3, 4, 8):
        raise ValueError("unregistered C34 reserve divisor")
    if out["spent"] > out["grant"] or out["remaining"] < out["reserve"]:
        raise ValueError("C34 trial borrowed or spent fallback-reserved work")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--binary", required=True, type=Path)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--flags", required=True, type=Path)
    p.add_argument("--cap", type=int, required=True, choices=(512, 1024, 2048))
    p.add_argument("--divisor", type=int, required=True, choices=(2, 3, 4, 8))
    p.add_argument("--stderr", type=Path)
    args = p.parse_args()
    if hashlib.sha256(args.input.read_bytes()).hexdigest() != EXPECTED_N7:
        raise ValueError("C34 input differs from unchanged original Magma n7")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C34 requires all 24 canonical selected flags")
    env = dict(os.environ)
    env.update(flags)
    env["NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT"] = str(args.cap)
    env["NUCLEUS_DIAGNOSTIC_C34_FALLBACK_RESERVE_DIVISOR"] = str(args.divisor)
    env.pop("NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS", None)
    env.pop("NUCLEUS_DIAGNOSTIC_C30_EXACT_MAJOR_CACHE", None)
    run = subprocess.run([str(args.binary.resolve())], input=args.input.read_bytes(),
                         env=env, capture_output=True, timeout=180)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"C34 invalid native result rc={run.returncode}")
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    lines = run.stderr.decode(errors="replace").splitlines()
    source = [r for line in lines if (r := parse_record(line)) is not None]
    reserve = [r for line in lines if (r := parse_reserve(line)) is not None]
    if not source or len(source) != len(reserve):
        raise ValueError("C34 failed to produce paired source and reserve records")
    if not any(int(row["reserve"]) >= 128 for row in reserve):
        raise ValueError("C34 reservation was never consequential")
    for a, b in zip(source, reserve):
        for key in ("head", "depth", "grant", "spent", "remaining", "proved"):
            if a[key] != b[key]:
                raise ValueError("C34 reserve and C33 source events disagree")
        if b["cap"] != args.cap or b["divisor"] != args.divisor:
            raise ValueError("C34 exercised a different preregistered arm")
    print(json.dumps({
        "source_sha256": EXPECTED_N7, "standard_steps": 262144,
        "selected_flags": 24, "congruence_cap": args.cap,
        "fallback_reserve_divisor": args.divisor,
        "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
        "records": len(reserve),
        "source_proved": sum(bool(row["proved"]) for row in reserve),
        "failed_with_fallback_128": sum(not row["proved"] and int(row["remaining"]) >= 128 for row in reserve),
        "failed_with_fallback_512": sum(not row["proved"] and int(row["remaining"]) >= 512 for row in reserve),
        "failed_with_zero_work": sum(not row["proved"] and int(row["remaining"]) == 0 for row in reserve),
        "charged_source_steps": sum(int(row["spent"]) for row in reserve),
        "source_heads": dict(Counter(str(row["head"]) for row in reserve)),
        "first_four": reserve[:4],
    }, indent=2))


if __name__ == "__main__":
    main()
