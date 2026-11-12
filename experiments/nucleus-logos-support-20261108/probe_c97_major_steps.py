#!/usr/bin/env python3
"""C97: source-pinned major exposure loop-step census, never a proof rule."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from probe_c94_owner_phase import SOURCE_HASHES, replay


def collect(stderr: bytes):
    owners = []
    kinds = []
    heads = []
    repeated = []
    for line in stderr.decode(errors="replace").splitlines():
        fields = dict(re.findall(r"([a-z_]+)=(\d+)", line))
        if line.startswith("NUCLEUS_C97_OWNER:"):
            required = {"start", "spent", "major_work", "loops", "unique_node_env", "repeat_node_env",
                        "unique_head_pending", "repeat_head_pending"}
            assert required <= fields.keys(), line
            row = {k: int(v) for k, v in fields.items()}
            assert 0 < row["loops"] <= row["major_work"] <= row["spent"] <= row["start"], row
            assert row["repeat_node_env"] <= row["loops"], row
            assert row["unique_head_pending"] + row["repeat_head_pending"] == row["loops"], row
            owners.append(row)
        elif line.startswith("NUCLEUS_C97_KIND:"):
            assert {"start", "kind", "count"} <= fields.keys(), line
            kinds.append({k: int(v) for k, v in fields.items()})
        elif line.startswith("NUCLEUS_C97_HEAD:"):
            assert {"start", "kind", "source", "count"} <= fields.keys(), line
            heads.append({k: int(v) for k, v in fields.items()})
        elif line.startswith("NUCLEUS_C97_REPEAT_HEAD:"):
            assert {"start", "kind", "source", "count"} <= fields.keys(), line
            repeated.append({k: int(v) for k, v in fields.items()})
    assert owners and kinds and heads, "RED: C97 major-step receipts absent"
    for owner in owners:
        assert sum(v["count"] for v in kinds if v["start"] == owner["start"]) == owner["loops"]
        assert sum(v["count"] for v in heads if v["start"] == owner["start"]) <= owner["loops"]
        assert sum(v["count"] for v in repeated if v["start"] == owner["start"]) <= owner["repeat_head_pending"]
    return owners, kinds, heads, repeated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checker", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    assert hashlib.sha256(source).hexdigest() == SOURCE_HASHES[args.source.stem]
    checker = args.checker.resolve()
    baseline = replay(checker, source, False)
    observed = replay(checker, source, True, observer_flag="NUCLEUS_C97_MAJOR_STEP_TRACE")
    assert baseline.returncode == observed.returncode == 2
    operations = lambda r: next((line for line in reversed(r.stderr.splitlines())
                                 if line.startswith(b'{"declarations":')), None)
    assert operations(baseline) is not None and operations(baseline) == operations(observed)
    owners, kinds, heads, repeated = collect(observed.stderr)
    print(json.dumps({"source": args.source.stem, "sha256": hashlib.sha256(source).hexdigest(),
                      "operations": json.loads(operations(baseline)), "owners": owners,
                      "kinds": kinds, "heads": heads, "repeat_heads": repeated}, sort_keys=True))


if __name__ == "__main__":
    main()
