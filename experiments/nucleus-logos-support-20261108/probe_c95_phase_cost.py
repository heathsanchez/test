#!/usr/bin/env python3
"""Require owner-local charged stage conservation on exact Arena source inputs."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from probe_c94_owner_phase import SOURCE_HASHES, replay


def phase_receipts(stderr: bytes):
    receipts = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith("NUCLEUS_C95_PHASE:"):
            continue
        fields = dict(re.findall(r"([a-z_]+)=(\d+)", line))
        required = ("start", "remaining", "major_work", "telescope_work",
                    "rhs_work", "finish_work", "other_work", "key_work")
        assert all(field in fields for field in required), (required, line)
        row = {name: int(value) for name, value in fields.items()}
        spent = row["start"] - row["remaining"]
        assert spent >= 0
        assert sum(row[x] for x in ("major_work", "telescope_work", "rhs_work",
                                    "finish_work", "other_work")) == spent, row
        assert row["key_work"] <= spent, row
        receipts.append(row)
    assert receipts, "RED: C95 charged stage receipts missing"
    return receipts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checker", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    assert args.source.stem in SOURCE_HASHES
    source = args.source.read_bytes()
    assert hashlib.sha256(source).hexdigest() == SOURCE_HASHES[args.source.stem]
    checker = args.checker.resolve()
    before = replay(checker, source, False)
    after = replay(checker, source, True, observer_flag="NUCLEUS_C95_PHASE_TRACE")
    assert before.returncode == after.returncode == 2
    operations = lambda r: next((line for line in reversed(r.stderr.splitlines())
                                 if line.startswith(b'{"declarations":')), None)
    assert operations(before) is not None and operations(before) == operations(after)
    rows = phase_receipts(after.stderr)
    print(json.dumps({"case": args.source.stem, "source_sha256": hashlib.sha256(source).hexdigest(),
                      "operations": json.loads(operations(before)), "phases": rows}, sort_keys=True))


if __name__ == "__main__":
    main()
