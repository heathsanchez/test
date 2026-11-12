#!/usr/bin/env python3
"""Observe source binding categories of actual, owner-charged recursor majors."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from probe_c94_owner_phase import SOURCE_HASHES, replay


def receipts(stderr: bytes):
    owners = []
    groups = []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith("NUCLEUS_C96_OWNER:"):
            d = dict(re.findall(r"([a-z_]+)=(\d+)", line))
            assert all(k in d for k in ("start", "spent", "major_work", "demands")), line
            owners.append({k: int(v) for k, v in d.items()})
        elif line.startswith("NUCLEUS_C96_MAJOR:"):
            d = dict(re.findall(r"([a-z_]+)=(\d+)", line))
            assert all(k in d for k in ("start", "recursor", "kind", "bound_expr",
                                         "count", "charged", "unknown", "nested",
                                         "chain_steps", "chain_max", "chain_capped")), line
            row = {k: int(v) for k, v in d.items()}
            assert row["unknown"] + row["nested"] <= row["count"], row
            assert row["chain_steps"] >= row["chain_max"], row
            assert row["chain_capped"] <= row["count"], row
            groups.append(row)
    assert owners and groups, "RED: source binding cost receipts missing"
    for owner in owners:
        assert owner["major_work"] <= owner["spent"]
        assert sum(g["charged"] for g in groups if g["start"] == owner["start"]) <= owner["major_work"]
    return owners, groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checker", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    assert args.source.stem in SOURCE_HASHES
    source = args.source.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    assert digest == SOURCE_HASHES[args.source.stem]
    checker = args.checker.resolve()
    baseline = replay(checker, source, False)
    observed = replay(checker, source, True, observer_flag="NUCLEUS_C96_MAJOR_TRACE")
    assert baseline.returncode == observed.returncode == 2
    ops = lambda x: next((line for line in reversed(x.stderr.splitlines())
                          if line.startswith(b'{"declarations":')), None)
    assert ops(baseline) is not None and ops(baseline) == ops(observed)
    owners, groups = receipts(observed.stderr)
    print(json.dumps({"source": args.source.stem, "sha256": digest,
                      "operations": json.loads(ops(baseline)), "owners": owners,
                      "groups": groups}, sort_keys=True))


if __name__ == "__main__":
    main()
