"""Validate exact-root failure recurrence reported by diagnostic-only C51.

The Rust observer compares full Neutral values, including exact captured
closures, environments and level substitutions, under one immutable Machine.
Only the equality result is a diagnostic hint; it never licenses reduction.
"""

import json

PREFIX = "NUCLEUS_C51_FAILED_ROOT:"
STAGES = {
    "owner-exhausted", "major-exposure", "projected-source-field",
    "rhs-exposure", "no-constructor",
}


def parse_retries(stderr: bytes) -> list[dict]:
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        record = json.loads(line.removeprefix(PREFIX))
        if len(rows) >= 256 or type(record.get("seq")) is not int or record["seq"] != len(rows):
            raise ValueError("C51 recurrence escaped bounded ordered event sequence")
        if record.get("stage") not in STAGES or record.get("goal") not in {"completed", "one-step"}:
            raise ValueError("C51 recurrence has unknown stage or goal")
        for field in ("recursor", "entry_budget", "entry_owner", "spine_len", "stored_failed_roots"):
            n = record.get(field)
            if type(n) is not int or n < 0:
                raise ValueError(f"C51 invalid {field}")
        prior = record.get("prior_failure")
        if prior is not None and (type(prior) is not int or prior < 0 or prior >= record["seq"]):
            raise ValueError("C51 invalid prior exact failure")
        if record["stored_failed_roots"] > record["seq"]:
            raise ValueError("C51 failed-root ledger ahead of stream")
        rows.append(record)
    return rows


def summarize_retries(rows: list[dict]) -> dict:
    repeated = [row for row in rows if row["prior_failure"] is not None]
    return {
        "failed_requests": len(rows),
        "exact_failed_root_retries": len(repeated),
        "prior_indices": sorted({row["prior_failure"] for row in repeated}),
        "max_repeated_entry_budget": max((row["entry_budget"] for row in repeated), default=0),
        "possibly_truncated": len(rows) >= 256,
        "partial_state_is_a_proof": False,
    }
