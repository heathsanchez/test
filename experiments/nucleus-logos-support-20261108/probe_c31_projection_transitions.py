"""Replay frozen Magma n7 and census actual, metered PProd major projections.

C31 is observer-only. Its records are not an ACCEPT or a reduction rule.
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
PREFIX = "NUCLEUS_C31_PROJECTION:"


def parse_record(line: str) -> dict[str, object] | None:
    if not line.startswith(PREFIX):
        return None
    parts = re.fullmatch(
        r"NUCLEUS_C31_PROJECTION:seq=(\d+):depth=(\d+):step=(\d+)"
        r":source=(.*?):origin=(.*?):receiver=(.*?):result=(.*?)"
        r":owner_before=Some\((\d+)\):owner_after=Some\((\d+)\)"
        r":charged=Some\((\d+)\)",
        line,
    )
    if not parts:
        raise ValueError(f"unparseable C31 source event: {line[:500]}")
    seq, depth, step, source, origin, receiver, result, before, after, charged = parts.groups()
    before_num, after_num, charge_num = int(before), int(after), int(charged)
    assert before_num >= after_num and charge_num == before_num - after_num
    return {
        "seq": int(seq), "depth": int(depth), "step": int(step),
        "source": source, "origin": origin, "receiver": receiver,
        "result": result, "charged": charge_num,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--binary", required=True, type=Path)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--flags", required=True, type=Path)
    p.add_argument("--stderr", type=Path)
    p.add_argument("--keyless", action="store_true")
    p.add_argument("--require-records", action="store_true")
    args = p.parse_args()
    source = args.input.read_bytes()
    actual_hash = hashlib.sha256(source).hexdigest()
    if actual_hash != EXPECTED_N7:
        raise ValueError("C31 source is not the unchanged original n7")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C31 flags do not match 24 enabled canonical flags")
    env = dict(os.environ)
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C31_PROJECTED_TRANSITIONS"] = "1"
    if args.keyless:
        env["NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS"] = "1"
    else:
        env.pop("NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS", None)
    result = subprocess.run(
        [str(args.binary.resolve())], input=source, env=env,
        capture_output=True, timeout=180, check=False,
    )
    if result.returncode != 2 or result.stdout:
        raise ValueError(f"observer changed original UNKNOWN: rc={result.returncode}")
    if args.stderr:
        args.stderr.write_bytes(result.stderr)
    events = [record for line in result.stderr.decode(errors="replace").splitlines()
              if (record := parse_record(line)) is not None]
    if args.require_records and not events:
        raise ValueError("C31 source projection observer was not exercised")
    by_origin = Counter((event["source"], event["origin"]) for event in events)
    counts = Counter(event["result"] for event in events)
    charges = {status: sum(int(event["charged"]) for event in events
                           if event["result"] == status) for status in counts}
    summary = {
        "input_sha256": actual_hash, "standard_steps": 262144,
        "flags_count": len(flags), "keyless_diagnostic": args.keyless,
        "verdict": "UNKNOWN", "record_count": len(events),
        "exact_source_state_count": len(by_origin),
        "repeated_source_state_count": sum(n > 1 for n in by_origin.values()),
        "result_classes": dict(counts), "inclusive_charged_by_result": charges,
        "max_observed_depth": max((event["depth"] for event in events), default=0),
        "first_ten": events[:10],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
