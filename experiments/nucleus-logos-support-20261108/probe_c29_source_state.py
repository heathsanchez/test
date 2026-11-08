"""C29 RED/GREEN: observe source captures in the unchanged qualified recursor worklist.

Only reports source identity and lexical shape. It cannot decide equality,
provide a constructor, grant fuel, or promote an UNKNOWN proof.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


N7_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
MARKER = re.compile(
    r"^NUCLEUS_C29_MAJOR_STEP:seq=(\d+):head=NameId\((\d+)\):"
    r"depth=(\d+):requested=(true|false):resumed=(true|false):"
    r"root_expr=ExprId\((\d+)\):root_env=(\d+):"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--flags", type=Path, required=True)
    parser.add_argument("--stderr", type=Path)
    args = parser.parse_args()
    original = args.input.read_bytes()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != N7_SHA256:
        raise SystemExit(f"C29 refused modified original n7: {actual_sha}")
    flags = json.loads(args.flags.read_text())
    if len(flags) != 24 or any(not key.startswith("NUCLEUS_") for key in flags):
        raise SystemExit("C29 refused changed selected runtime flags")
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("NUCLEUS_")}
    env.update(flags)
    env["NUCLEUS_DIAGNOSTIC_NO_REPLAY_KEYS"] = "1"
    env["NUCLEUS_DIAGNOSTIC_C29_HEAD"] = "147"
    process = subprocess.run([str(args.binary.resolve())], input=original,
                             env=env, capture_output=True, timeout=150)
    if args.stderr is not None:
        args.stderr.parent.mkdir(parents=True, exist_ok=True)
        args.stderr.write_bytes(process.stderr)
    lines = process.stderr.decode(errors="replace").splitlines()
    records = []
    for line in lines:
        match = MARKER.match(line)
        if match:
            seq, head, depth, requested, resumed, expr, source_env = match.groups()
            records.append({
                "seq": int(seq), "head": int(head), "depth": int(depth),
                "requested": requested == "true", "resumed": resumed == "true",
                "root_expr": int(expr), "root_env": int(source_env),
                "source_chain": line[match.end():],
            })
    deep = [record for record in records if record["depth"] >= 32]
    root_pairs = {(record["root_expr"], record["root_env"]) for record in records}
    exprs = {record["root_expr"] for record in records}
    report = {
        "experiment": "C29_SOURCE_STATE_OBSERVER_ONLY",
        "original_sha256": N7_SHA256,
        "source_input_unchanged": True,
        "selected_flags": len(flags),
        "global_budget": 262144,
        "head_filter": 147,
        "keyless_replay": True,
        "verdict": "UNKNOWN" if process.returncode == 2 else f"EXIT_{process.returncode}",
        "exit_code": process.returncode,
        "observations": len(records),
        "deep_observations": len(deep),
        "max_depth": max((record["depth"] for record in records), default=None),
        "distinct_root_expr_ids": len(exprs),
        "distinct_root_expr_env_id_pairs": len(root_pairs),
        "repeated_root_expr_env_pairs": len(records) - len(root_pairs),
        "identity_not_semantic_equality": True,
        "first_records": records[:8],
        "deep_records": deep[:80],
    }
    print(json.dumps(report, indent=2), flush=True)
    if process.returncode != 2 or not records or not deep:
        print("C29 RED: unchanged n7 UNKNOWN must expose qualified head 147 "
              "at nested depth >=32 with diagnostic-only source captures", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
