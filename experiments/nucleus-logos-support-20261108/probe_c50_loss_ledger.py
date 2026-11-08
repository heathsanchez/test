"""Fail-closed decoder for bounded, observer-only Nucleus C50 loss events.

An unfinished worklist is never a conversion or proof certificate.
"""

import json

PREFIX = "NUCLEUS_C50_LOST:"
STAGES = {
    "owner-exhausted", "major-exposure", "projected-source-field",
    "rhs-exposure", "no-constructor", "projected-receiver",
}


def parse_loss_events(stderr: bytes) -> list[dict]:
    rows = []
    for line in stderr.decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        event = json.loads(line.removeprefix(PREFIX))
        if event.get("seq") != len(rows) or len(rows) >= 256:
            raise ValueError("C50 loss event escaped bounded monotonic sequence")
        if event.get("stage") not in STAGES:
            raise ValueError("C50 loss event has unknown failure stage")
        fields = (
            "recursor", "major_expr", "major_env", "parents",
            "finish_parents", "major_parents", "projected_parents",
            "active", "resolved", "owner_remaining",
        )
        for field in fields:
            value = event.get(field)
            if type(value) is not int or value < 0:
                raise ValueError(f"C50 loss event has invalid {field}")
        if event["parents"] != sum(event[f] for f in (
            "finish_parents", "major_parents", "projected_parents"
        )):
            raise ValueError("C50 pending continuation frames do not sum")
        rows.append(event)
    return rows


def summarize_losses(rows: list[dict]) -> dict:
    pending = [row for row in rows if row["parents"] > 0]
    return {
        "observed_failure_exits": len(rows),
        "with_pending_parents": len(pending),
        "first_pending_stage": pending[0]["stage"] if pending else None,
        "maximum_pending_parents": max((e["parents"] for e in rows), default=0),
        "maximum_completed_children_in_pending_stack": max(
            (e["finish_parents"] for e in pending), default=0
        ),
        "possibly_truncated": len(rows) >= 256,
        "partial_state_is_a_proof": False,
    }
