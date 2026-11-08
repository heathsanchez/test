"""Compare fixed-fuel source-congruence caps on unchanged Magma n7.

The pre-iota relational source checker itself is unchanged. A successful
diagnostic ACCEPT is not selected-Nucleus qualification: it must first pass
the entire protected forged-proof and valid-source matrix at that same cap.
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
PREFIX = "NUCLEUS_C28_SOURCE_CONGRUENCE:"
PATTERN = re.compile(
    r"NUCLEUS_C28_SOURCE_CONGRUENCE:head=NameId\((\d+)\):depth=(\d+):"
    r"grant=(\d+):spent=(\d+):remaining=(\d+):proved=(true|false):"
    r"first_failed=(None|Some\(\d+\))"
)


def parse_record(line: str) -> dict[str, object] | None:
    if not line.startswith(PREFIX):
        return None
    match = PATTERN.fullmatch(line)
    if not match:
        raise ValueError(f"malformed C33 checked source-trial event: {line[:240]}")
    head, depth, grant, spent, remaining, proven, failure = match.groups()
    head, depth, grant, spent, remaining = map(int, (head, depth, grant, spent, remaining))
    if spent > grant or (proven == "true" and failure != "None"):
        raise ValueError("C33 source congruence reported uncharged or contradictory trial")
    return {"head": head, "depth": depth, "grant": grant,
            "spent": spent, "remaining": remaining, "proved": proven == "true",
            "first_failed": failure}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--binary", required=True, type=Path)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--flags", required=True, type=Path)
    p.add_argument("--cap", type=int, required=True)
    p.add_argument("--stderr", type=Path)
    p.add_argument("--require-cap-effect", action="store_true")
    args = p.parse_args()
    if args.cap not in (512, 768, 1024, 1536, 2048, 4096, 8192):
        raise ValueError("C33 selected cap not in preregistered arms")
    source = args.input.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_N7:
        raise ValueError("C33 source digest is not unchanged original n7")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C33 requires the canonical 24 selected flags")
    env = dict(os.environ)
    env.update(flags)
    env["NUCLEUS_EXPERIMENTAL_PRE_IOTA_SOURCE_CONGRUENCE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C33_SOURCE_CONGRUENCE_GRANT"] = str(args.cap)
    env.pop("NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS", None)
    env.pop("NUCLEUS_DIAGNOSTIC_C30_EXACT_MAJOR_CACHE", None)
    result = subprocess.run([str(args.binary.resolve())], input=source,
                            env=env, capture_output=True, timeout=180)
    if result.returncode not in (0, 2) or result.stdout:
        raise ValueError(f"C33 produced rejected/invalid diagnostic result: rc={result.returncode}")
    if args.stderr:
        args.stderr.write_bytes(result.stderr)
    records = [row for line in result.stderr.decode(errors="replace").splitlines()
               if (row := parse_record(line)) is not None]
    if not records:
        raise ValueError("C33 source congruence did not execute")
    max_grant = max(int(row["grant"]) for row in records)
    if max_grant > args.cap:
        raise ValueError("C33 source trial exceeded selected local cap")
    if args.require_cap_effect and args.cap > 512 and max_grant <= 512:
        raise ValueError("C33 changed cap was not exercised")
    print(json.dumps({
        "source_sha256": digest, "standard_steps": 262144,
        "selected_flags": 24, "congruence_cap": args.cap,
        "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if result.returncode == 0 else "UNKNOWN",
        "rc": result.returncode, "records": len(records),
        "proved": sum(bool(row["proved"]) for row in records),
        "max_actual_grant": max_grant,
        "charged_source_trial_steps": sum(int(row["spent"]) for row in records),
        "source_heads": dict(Counter(str(row["head"]) for row in records)),
        "first_four": records[:4],
    }, indent=2))


if __name__ == "__main__":
    main()
