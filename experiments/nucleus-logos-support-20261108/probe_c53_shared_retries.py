"""Fail-closed readout of source-owned failed-recursion roots across Machines."""

import json

PREFIX = "NUCLEUS_C53_SHARED_FAILED:"
STAGES = {"owner-exhausted", "major-exposure", "projected-source-field", "no-constructor", "rhs-exposure"}


def parse_shared_retries(stderr: bytes) -> list[dict]:
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        e = json.loads(line.removeprefix(PREFIX))
        if len(rows) >= 256 or type(e.get("seq")) is not int or e["seq"] != len(rows):
            raise ValueError("C53 unbounded or out-of-sequence event")
        if e.get("stage") not in STAGES or e.get("goal") not in {"completed", "one-step"}:
            raise ValueError("C53 unknown stage or goal")
        for key in ("recursor", "shared_failed_roots", "machine_failed_roots"):
            if type(e.get(key)) is not int or e[key] < 0:
                raise ValueError(f"C53 invalid {key}")
        if type(e.get("shared_cache")) is not bool:
            raise ValueError("C53 cache owner flag missing")
        prior = e.get("shared_prior_failure")
        if prior is not None and (type(prior) is not int or prior < 0 or prior >= e["shared_failed_roots"]):
            raise ValueError("C53 invalid exact source prior")
        if e["shared_failed_roots"] > e["seq"]:
            raise ValueError("C53 stored history outruns failures")
        rows.append(e)
    return rows


def summarize_shared_retries(rows: list[dict]) -> dict:
    repeated = [x for x in rows if x["shared_prior_failure"] is not None]
    return {
        "observed_failure_exits": len(rows),
        "cross_machine_exact_retries": len(repeated),
        "repeat_prior_indices": sorted({x["shared_prior_failure"] for x in repeated}),
        "shared_cache_used": all(x["shared_cache"] for x in rows),
        "machine_ledger_nonempty_count": sum(x["machine_failed_roots"] > 0 for x in rows),
        "possibly_truncated": len(rows) >= 256,
        "unfinished_frames_are_proof": False,
    }
