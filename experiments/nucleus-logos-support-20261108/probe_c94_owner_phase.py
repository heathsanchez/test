#!/usr/bin/env python3
"""Source-pinned, observer-equivalent replay of the charged recursor worklist.

This is a *diagnostic* probe. C94 phase receipts never authorize a verdict.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


SOURCE_HASHES = {
    "magma-list-pair-n7": "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35",
    "magma-list-pair-n21": "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84",
}


def replay(executable: Path, source: bytes, observer: bool,
           observer_flag: str = "NUCLEUS_C94_PHASE_TRACE") -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update({
        "NUCLEUS_EXPERIMENTAL_RELEVANCE": "1",
        "NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA": "1",
        "METATRON_KERNEL_DIAGNOSTICS": "1",
    })
    if observer:
        env[observer_flag] = "1"
    return subprocess.run([str(executable)], input=source, capture_output=True,
                          timeout=120, env=env, check=False)


def parse_phase_receipts(stderr: bytes):
    receipts = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith("NUCLEUS_C94_PHASE:"):
            continue
        fields = dict(re.findall(r"([a-z_]+)=(\d+)", line))
        for required in ("start", "remaining", "entered", "resumed", "completed",
                         "local_hits", "global_hits", "max_depth", "key_work",
                         "bvar_majors", "bvar_repeats"):
            assert required in fields, (required, line)
        entry = {name: int(value) for name, value in fields.items()}
        assert entry["remaining"] <= entry["start"], entry
        assert entry["completed"] <= entry["entered"], entry
        assert entry["key_work"] <= entry["start"] - entry["remaining"], entry
        assert entry["bvar_repeats"] <= entry["bvar_majors"], entry
        # A cache hit and a final budget-exhausted demand need no worklist entry.
        assert entry["bvar_majors"] <= (entry["entered"] + entry["local_hits"]
                                        + entry["global_hits"] + 1), entry
        receipts.append(entry)
    return receipts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checker", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    name = args.source.stem
    assert name in SOURCE_HASHES, f"unqualified source {name}"
    source = args.source.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    assert digest == SOURCE_HASHES[name], (name, digest)
    checker = args.checker.resolve()
    base = replay(checker, source, observer=False)
    observed = replay(checker, source, observer=True)
    assert base.returncode == observed.returncode == 2, (name, base.returncode, observed.returncode)
    # Rust's operation counters must not be affected by a diagnostic observer.
    last_json = lambda r: next((line for line in reversed(r.stderr.splitlines())
                                 if line.startswith(b'{"declarations":')), None)
    assert last_json(base) is not None and last_json(base) == last_json(observed), "observer changed source work"
    receipts = parse_phase_receipts(observed.stderr)
    assert receipts, "RED: owner-local phase receipts missing"
    print(json.dumps({
        "source": name, "sha256": digest, "verdict": "UNKNOWN",
        "operations": json.loads(last_json(base)), "phase_receipts": receipts,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
