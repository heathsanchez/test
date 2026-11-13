#!/usr/bin/env python3
"""C125 surrogate: inspect captured projection targets on the C105 source line.

This is NOT a replay of the unrecovered C124 commit. It establishes only the
native observations made by this separately named C105-descended instrument.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from probe_c94_owner_phase import SOURCE_HASHES, replay


SOURCE = "magma-list-pair-n21"
PREFIX = "NUCLEUS_C125_PROJ_BINDING:"
CONTROLS = (
    ("nucleus-universe-reconcile-20261104/inputs/renamed-pprod-forged-fields.ndjson",
     "33993418d305e980e224d6102be2fc61ee9c02be1c8c23ccce00a406616ba6d6", 1),
    ("nucleus-universe-reconcile-20261104/inputs/renamed-pprod-forged-motive.ndjson",
     "2eb5034aa01b1591cc99577bacc50095e3d8e80709172175f569e1f481f680de", 2),
    ("nucleus-quotient-reuse-20261104/heldout/mutated.ndjson",
     "a4425142910417814594d555ccec8ac1b29bbe8d18f12993f20fa1c0253fd692", 1),
)
NUMBER_FIELDS = (
    "owner_start", "spent", "depth", "recursor", "terminal_expr",
    "terminal_env", "terminal_levels", "links", "target_expr",
    "binding_node", "payload_expr", "payload_env", "payload_levels",
)


def operation_line(run):
    return next((line for line in reversed(run.stderr.splitlines())
                 if line.startswith(b'{"declarations":')), None)


def source_bytes(path: Path) -> bytes:
    if path.suffix == ".zst":
        result = subprocess.run(["zstd", "-dc", str(path)], capture_output=True,
                                check=True)
        return result.stdout
    return path.read_bytes()


def assert_frozen_syntax(data: bytes) -> None:
    expr = {}
    for line in data.splitlines():
        row = json.loads(line)
        if row.get("ie") in (1, 811, 7194, 7198):
            expr[row["ie"]] = row
    assert expr[1].get("bvar") == 0
    assert expr[811].get("proj", {}).get("struct") == 1
    assert expr[811]["proj"].get("idx") == 0
    assert expr[7194].get("app") == {"fn": 811, "arg": 7193}
    assert expr[7198].get("app") == {"fn": 7194, "arg": 7197}


def receipts(stderr: bytes):
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        head, payload = line[len(PREFIX):].split(":payload=", 1)
        fields = dict(part.split("=", 1) for part in head.split(":"))
        assert set(NUMBER_FIELDS) | {"binding_kind", "outcome"} <= fields.keys(), line
        row = {k: int(fields[k]) for k in NUMBER_FIELDS}
        row.update(binding_kind=fields["binding_kind"], outcome=fields["outcome"],
                   payload_sha256=hashlib.sha256(payload.encode()).hexdigest())
        assert row["terminal_expr"] == 7198 and row["target_expr"] == 1
        assert row["links"] == 2, "source chain diverged from C123 observation"
        rows.append(row)
    assert rows, "RED: native C125 projection target receipts absent"
    return rows


def summarize(rows):
    mid = [r for r in rows if 128 <= r["spent"] <= 511 and r["outcome"] == "nested"]
    # These two counts are the independent C124 frozen-source expectation.
    # Mismatch means this C105-derived experiment did NOT reproduce C124's P
    # population and must not be promoted as a C125 answer.
    assert len(mid) == 80, ("C124 population not recovered", len(mid), len(rows))
    assert sum(r["spent"] for r in mid) == 26132, "C124 charge not recovered"
    assert all(r["binding_node"] != 0 for r in mid), "missing captured target binding"
    by_owner = Counter(r["owner_start"] for r in mid)
    return {
        "mid_projection_calls": len(mid),
        "mid_projection_charged": sum(r["spent"] for r in mid),
        "owner_counts": dict(sorted(by_owner.items())),
        "unique_terminal_frames": len({r["terminal_env"] for r in mid}),
        "unique_target_binding_nodes": len({r["binding_node"] for r in mid}),
        "unique_payload_fingerprints": len({r["payload_sha256"] for r in mid}),
        "binding_kinds": dict(Counter(r["binding_kind"] for r in mid)),
        "payload_closure_shapes": [
            {"expr": expr, "levels": levels, "count": count}
            for (expr, levels), count in sorted(Counter(
                (r["payload_expr"], r["payload_levels"]) for r in mid
                if r["binding_kind"] == "closure").items())
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checker", type=Path)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    data = source_bytes(args.source)
    digest = hashlib.sha256(data).hexdigest()
    assert digest == SOURCE_HASHES[SOURCE], "frozen source bytes changed"
    assert_frozen_syntax(data)
    checker = args.checker.resolve()
    before = replay(checker, data, False)
    after = replay(checker, data, True, "NUCLEUS_C125_PROJ_BINDING_TRACE")
    assert before.returncode == after.returncode == 2, (before.returncode, after.returncode)
    assert before.stdout == after.stdout
    assert operation_line(before) is not None
    assert operation_line(before) == operation_line(after), "observer changed kernel operations"
    rows = receipts(after.stderr)
    summary = summarize(rows)
    controls = []
    for relative, expected_hash, expected_code in CONTROLS:
        control = (Path(__file__).resolve().parents[1] / relative).read_bytes()
        assert hashlib.sha256(control).hexdigest() == expected_hash
        old = replay(checker, control, False)
        new = replay(checker, control, True, "NUCLEUS_C125_PROJ_BINDING_TRACE")
        assert old.returncode == new.returncode == expected_code
        assert old.stdout == new.stdout
        assert operation_line(old) == operation_line(new)
        controls.append({"source": relative, "verdict_exit": expected_code})
    print(json.dumps({
        "epistemic_status": "CANDIDATE_UNTIL_NATIVE_REPLAY",
        "lineage": "C105-descended surrogate; NOT exact C124 source",
        "source": SOURCE, "source_sha256": digest,
        "verdict": "UNKNOWN", "operations": json.loads(operation_line(before)),
        "projection": summary, "controls": controls,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
