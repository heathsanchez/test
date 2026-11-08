"""C45: meter the *actual* n7 source proof application's first failing child.

The observer cannot turn a successful subjudgment into final ACCEPT; only the
unchanged Rust checker may issue the verdict. Every record comes from Rust.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from probe_c44_root_argument import EXPECTED_SOURCE


PREFIX = "NUCLEUS_C45_PROOF_ARG:"
SOURCE_APPLICATION_IDS = {8754, 8796, 8797, 8799, 8800, 8801, 8802, 8803, 8804}


def parse_spine(stderr: bytes) -> list[dict]:
    events = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        event = json.loads(line.removeprefix(PREFIX))
        if event.get("expression") not in SOURCE_APPLICATION_IDS or event.get("context_len") != 0:
            raise ValueError("C45 record escaped the frozen n7 proof-application spine")
        remaining = event.get("remaining")
        if not isinstance(remaining, int) or not 0 <= remaining <= 262144:
            raise ValueError("C45 record exceeds the standard allowance")
        if not isinstance(event.get("result"), str) or not isinstance(event.get("domain"), str):
            raise ValueError("C45 missing independent Rust source-typing result")
        events.append(event)
    return events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--flags", required=True, type=Path)
    parser.add_argument("--stderr", type=Path)
    parser.add_argument("--require-spine", action="store_true")
    args = parser.parse_args()
    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if args.input.name != "magma-list-pair-n7.ndjson" or digest != EXPECTED_SOURCE:
        raise ValueError("C45 accepts only the unchanged original Magma n7 source")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C45 selected source-qualified flags are not exact")
    env = {key: value for key, value in os.environ.items() if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C44_ROOT_ARGUMENT"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C45_PROOF_SPINE"] = "1"
    run = subprocess.run([str(args.binary.resolve())], input=data, env=env,
                         capture_output=True, timeout=120)
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"outside verifier verdict boundary: {run.returncode}")
    events = parse_spine(run.stderr)
    if args.require_spine and not events:
        raise ValueError("C45 independent child argument check was not observed")
    print(json.dumps({"case": args.input.stem, "source_sha256": digest,
                      "budget": 262144, "proof_rules_changed": False,
                      "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
                      "children": events}, indent=2))


if __name__ == "__main__":
    main()
