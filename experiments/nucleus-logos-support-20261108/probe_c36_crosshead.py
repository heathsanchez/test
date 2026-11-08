"""C36: audit checked recursor replay at an actual different-head obligation."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c35_metered_recursor import ORIGINAL_INPUTS


MARKER = "NUCLEUS_C36_CROSS_HEAD_REPLAY:"
EVENT = re.compile(
    r"NUCLEUS_C36_CROSS_HEAD_REPLAY:depth=(\d+):side=(left|right):"
    r"head=NameId\((\d+)\):grant=(\d+):spent=(\d+):"
    r"remaining=(\d+):outcome=(unknown|same|changed|refuted)"
)


def parse_record(line: str) -> dict | None:
    if not line.startswith(MARKER):
        return None
    match = EVENT.fullmatch(line)
    if match is None:
        raise ValueError(f"malformed C36 source event: {line[:240]}")
    depth, side, head, grant, spent, remaining, outcome = match.groups()
    data = {"depth": int(depth), "side": side, "head": int(head),
            "grant": int(grant), "spent": int(spent),
            "remaining": int(remaining), "outcome": outcome}
    if data["grant"] == 0 or data["spent"] > data["grant"]:
        raise ValueError("unmetered or overdrawn C36 recursor replay")
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True, type=Path)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--flags", required=True, type=Path)
    ap.add_argument("--grant", required=True, type=int)
    ap.add_argument("--stderr", type=Path)
    args = ap.parse_args()

    case = args.input.stem
    digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    if ORIGINAL_INPUTS.get(case) != digest:
        raise ValueError(f"unexpected/changed original: {case}")
    if args.grant not in (512, 2048, 8192, 32768, 131072):
        raise ValueError("unregistered C36 grant")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("the exact 24 selected flags are required")
    env = dict(os.environ)
    env.update(flags)
    for name in (
        "NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE",
        "NUCLEUS_DIAGNOSTIC_C35_ACTUAL_RECURSOR_CHARGE",
        "NUCLEUS_DIAGNOSTIC_C34_FALLBACK_RESERVE_DIVISOR",
        "NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS",
        "NUCLEUS_DIAGNOSTIC_C30_EXACT_MAJOR_CACHE",
        "NUCLEUS_DIAGNOSTIC_C32_RECURSOR_MAJOR_GRANT",
        "NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT",
    ):
        env.pop(name, None)
    env["NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_REPLAY"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_GRANT"] = str(args.grant)
    run = subprocess.run([str(args.binary.resolve())], input=args.input.read_bytes(),
                         env=env, capture_output=True, timeout=180)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"native result outside permitted boundary: rc={run.returncode}")
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    events = [item for line in run.stderr.decode(errors="replace").splitlines()
              if (item := parse_record(line)) is not None]
    if case == "magma-list-pair-n7" and not events:
        raise ValueError("C36 did not exercise the original different-head obligation")
    print(json.dumps({
        "original_case": case, "source_sha256": digest,
        "standard_steps": 262144, "selected_flags": 24,
        "grant_cap": args.grant,
        "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
        "record_count_capped_at_128": len(events),
        "event_classes": dict(Counter(item["outcome"] for item in events)),
        "total_observed_work": sum(item["spent"] for item in events),
        "observed_unused_grants": sum(item["grant"] - item["spent"] for item in events),
        "first_eight": events[:8],
    }, indent=2))


if __name__ == "__main__":
    main()
