"""C37: give source-certified cross-head replay the caller's entire remaining fuel.

This is diagnostic only. The six original proofs, 24 selected flags, and
262144-step global resource budget are unchanged.
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

from probe_c35_metered_recursor import ORIGINAL_INPUTS
from probe_c36_crosshead import parse_record


MARKER = "NUCLEUS_C37_ROOT_REASON:"
EVENT = re.compile(
    r"NUCLEUS_C37_ROOT_REASON:depth=(\d+):head=NameId\((\d+)\):"
    r"grant=(\d+):spent=(\d+):remaining=(\d+):reason=([a-z0-9-]+)"
)


def parse_reason_event(line: str) -> dict | None:
    if not line.startswith(MARKER):
        return None
    match = EVENT.fullmatch(line)
    if match is None:
        raise ValueError(f"invalid C37 source reason event: {line[:240]}")
    depth, head, grant, spent, remaining, reason = match.groups()
    result = {"depth": int(depth), "head": int(head),
              "grant": int(grant), "spent": int(spent),
              "remaining": int(remaining), "reason": reason}
    if not result["grant"] or result["spent"] > result["grant"]:
        raise ValueError("C37 has an invalid source-work accounting event")
    result["exhausted"] = result["spent"] == result["grant"]
    return result


def reconcile_events(reasons: list[dict], c36: list[dict]) -> None:
    """C36 caps its log at 128; C37's reason observer need not.

    Only a saturated, exactly 128-record C36 log may have extra C37
    events. Every observed C36 charge must still match its C37 audit.
    """
    if len(c36) > 128 or len(reasons) < len(c36):
        raise ValueError("missing metered C37 replay audit")
    if len(c36) < 128 and len(reasons) != len(c36):
        raise ValueError("unexpected unmetered C37 replay audit")
    for reason, charge in zip(reasons, c36):
        if any(reason[key] != charge[key] for key in
               ("depth", "head", "grant", "spent", "remaining")):
            raise ValueError("C37 audit does not match C36 metered source result")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--flags", type=Path, required=True)
    ap.add_argument("--stderr", type=Path)
    args = ap.parse_args()

    case = args.input.stem
    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if ORIGINAL_INPUTS.get(case) != digest:
        raise ValueError(f"not the original source-frozen proof: {case}")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("expected exactly 24 selected proof-rule flags")
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({
        "NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_REPLAY": "1",
        "NUCLEUS_DIAGNOSTIC_C36_CROSS_HEAD_GRANT": "262144",
        "NUCLEUS_DIAGNOSTIC_C37_FULL_OWNER": "1",
    })
    run = subprocess.run([str(args.binary.resolve())], input=data,
                         env=env, capture_output=True, timeout=180)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"outside protected verdict boundary: rc={run.returncode}")
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    lines = run.stderr.decode(errors="replace").splitlines()
    reasons = [item for line in lines
               if (item := parse_reason_event(line)) is not None]
    c36 = [item for line in lines if (item := parse_record(line)) is not None]
    if case == "magma-list-pair-n7" and not reasons:
        raise ValueError("full-owner replay was not reached on original n7")
    reconcile_events(reasons, c36)
    print(json.dumps({
        "case": case, "source_sha256": digest,
        "standard_steps": 262144, "selected_flags": 24,
        "diagnostic_only": True,
        "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
        "cross_head_events": len(reasons),
        "reasons": dict(Counter(event["reason"] for event in reasons)),
        "exhausted": sum(event["exhausted"] for event in reasons),
        "last_events": reasons[-8:],
    }, indent=2))


if __name__ == "__main__":
    main()
