"""C38: test earlier checked typed neutral congruence on frozen originals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c35_metered_recursor import ORIGINAL_INPUTS


MARKER = "NUCLEUS_C38_TYPED_SPINE:"
EVENT = re.compile(
    r"NUCLEUS_C38_TYPED_SPINE:head=NameId\((\d+)\):spine=(\d+):"
    r"depth=(\d+):proof_erasures=(true|false):result=(proven|unknown)"
)


def parse_congruence(line: str) -> dict | None:
    if not line.startswith(MARKER):
        return None
    m = EVENT.fullmatch(line)
    if m is None:
        raise ValueError("unrecognized C38 typed-congruence evidence")
    head, spine, depth, erased, result = m.groups()
    if not int(spine):
        raise ValueError("zero-argument congruence is not C38 evidence")
    return {"head": int(head), "spine": int(spine), "depth": int(depth),
            "proof_erasures": erased == "true", "result": result}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--flags", type=Path, required=True)
    ap.add_argument("--stderr", type=Path)
    ap.add_argument("--require-attempt", action="store_true")
    args = ap.parse_args()

    data = args.input.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    name = args.input.stem
    if ORIGINAL_INPUTS.get(name) != digest:
        raise ValueError("C38 may run only an unchanged original proof")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("C38 requires exact selected source flags")
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE"] = "1"
    run = subprocess.run([str(args.binary.resolve())], input=data,
                         capture_output=True, env=env, timeout=180)
    if run.returncode not in (0, 2) or run.stdout:
        raise ValueError(f"outside verifier verdict boundary: {run.returncode}")
    if args.stderr:
        args.stderr.write_bytes(run.stderr)
    lines = run.stderr.decode(errors="replace").splitlines()
    attempts = [x for x in lines if x.startswith("NUCLEUS_C38_EARLY_ATTEMPT:")]
    if args.require_attempt and not attempts:
        raise ValueError("C38 was not exercised by the unchanged original")
    outcomes = [item for line in lines
                if (item := parse_congruence(line)) is not None]
    print(json.dumps({"case": name, "source_sha256": digest,
                      "global_steps": 262144, "selected_flags": 24,
                      "diagnostic_only": True,
                      "verdict": "ACCEPT_DIAGNOSTIC_ONLY" if run.returncode == 0 else "UNKNOWN",
                      "attempts_observed": len(attempts),
                      "new_typed_certificates": sum(x["result"] == "proven" and not x["proof_erasures"] for x in outcomes),
                      "typed_results": outcomes[:30]}, indent=2))


if __name__ == "__main__":
    main()
