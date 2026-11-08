"""Replay six original arena cases with source-owned measured recursor work.

Only the diagnostic C35 flag changes recursor trial accounting. The same
qualified recursor implementation and same global judgment budget are used.
No diagnostic ACCEPT is selected qualification without protected replay.
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


ORIGINAL_INPUTS = {
    "fueled-chain": "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a",
    "grind-ring-5": "e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f",
    "magma-list-pair-n7": "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35",
    "magma-list-pair-n21": "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84",
    "magma-list-deep-n21": "b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526",
    "magma-list-deep-n36": "6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac",
}
MARKER = "NUCLEUS_C35_RECURSOR_CHARGE:"
PATTERN = re.compile(
    r"NUCLEUS_C35_RECURSOR_CHARGE:depth=(\d+):left=(true|false):"
    r"grant=(\d+):spent=(\d+):remaining=(\d+):changed=(true|false)"
)


def parse_record(line: str) -> dict[str, int | bool] | None:
    if not line.startswith(MARKER):
        return None
    match = PATTERN.fullmatch(line)
    if not match:
        raise ValueError(f"malformed C35 metered recursor event: {line[:240]}")
    depth, is_left, grant, spent, remaining, changed = match.groups()
    out: dict[str, int | bool] = {
        "depth": int(depth), "left": is_left == "true", "grant": int(grant),
        "spent": int(spent), "remaining": int(remaining), "changed": changed == "true",
    }
    if out["spent"] > out["grant"] or out["grant"] == 0:
        raise ValueError("C35 recursor owner spent more than grant")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--binary", required=True, type=Path)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--flags", required=True, type=Path)
    p.add_argument("--mode", required=True, choices=("plain", "source", "combined"))
    p.add_argument("--stderr", type=Path)
    args = p.parse_args()
    case = args.input.stem
    digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    if ORIGINAL_INPUTS.get(case) != digest:
        raise ValueError(f"C35 original source changed or unregistered: {case}")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C35 requires exact canonical 24 flags")
    env = dict(os.environ)
    env.update(flags)
    for key in ("NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS", "NUCLEUS_DIAGNOSTIC_C30_EXACT_MAJOR_CACHE",
                "NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE",
                "NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT",
                "NUCLEUS_DIAGNOSTIC_C34_FALLBACK_RESERVE_DIVISOR"):
        env.pop(key, None)
    env["NUCLEUS_DIAGNOSTIC_C35_ACTUAL_RECURSOR_CHARGE"] = "1"
    if args.mode != "plain":
        env["NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE"] = "1"
    if args.mode == "combined":
        env["NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT"] = "2048"
        env["NUCLEUS_DIAGNOSTIC_C34_FALLBACK_RESERVE_DIVISOR"] = "2"
    run = subprocess.run([str(args.binary.resolve())], input=args.input.read_bytes(),
                         env=env, capture_output=True, timeout=180)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"C35 invalid native result rc={run.returncode}, case={case}")
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    records = [r for line in run.stderr.decode(errors="replace").splitlines()
               if (r := parse_record(line)) is not None]
    if case == "magma-list-pair-n7" and not records:
        raise ValueError("C35 metered recursor did not execute on original n7")
    print(json.dumps({
        "original_case": case, "source_sha256": digest,
        "standard_steps": 262144, "selected_flags": 24, "mode": args.mode,
        "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
        "record_count_capped_at_128": len(records),
        "changed_recursor_results": sum(bool(r["changed"]) for r in records),
        "actual_charged": sum(int(r["spent"]) for r in records),
        "unused_budget_returned": sum(int(r["grant"]) - int(r["spent"]) for r in records),
        "fully_unspent_trials": sum(int(r["spent"]) == 0 for r in records),
        "first_four": records[:4],
    }, indent=2))


if __name__ == "__main__":
    main()
