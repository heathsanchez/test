#!/usr/bin/env python3
"""Post-freeze encounters for V6 meta-generator development."""
from __future__ import annotations

from typing import Any, Dict

from basis import Carrier
from kernel import Authority, Request


def authority(current: int, delta: int, required_size: int, name: str) -> Authority:
    def evaluate(carrier: Carrier) -> Dict[str, Any]:
        if carrier.size != required_size:
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": abs(carrier.size - required_size),
                "witness": {
                    "reason": "carrier_size_mismatch",
                    "target": name,
                    "got_size": carrier.size,
                },
            }

        rows = carrier.values()
        # Generic finite-carrier identity/equality semantics are replayed here.
        bad = [
            x for x in rows
            if x[0] != carrier.carrier_id
            or type(x[1]) is not int
            or not (0 <= x[1] < carrier.size)
        ]
        return {
            "accepted": not bad,
            "protected_ok": True,
            "loss": len(bad),
            "witness": {
                "target": name,
                "rows_checked": len(rows),
                "carrier_id": carrier.carrier_id,
                "bad_values": bad[:4],
            },
        }

    return Authority(
        evaluate=evaluate,
        coherent=lambda: True,
        residual=lambda: {
            "kind": "certified_basis_obstruction",
            "basis_obstruction_certified": True,
            "current": int(current),
            "delta": int(delta),
            # Required size is intentionally omitted from the residual.
        },
    )


A1 = authority(2, 1, 3, "encounter_1")
A2 = authority(3, 2, 5, "encounter_2")
A3 = authority(5, 4, 9, "future_separator")
A4 = authority(9, 6, 15, "transfer_reuse")


def requests():
    return {
        "e1": Request(
            "e1", A1, max_meta_cost=2, search_complete=True, allow_meta_search=True
        ),
        "e2": Request(
            "e2", A2, max_meta_cost=3, search_complete=True, allow_meta_search=True
        ),
        "e3": Request(
            "e3", A3, max_meta_cost=3, search_complete=True, allow_meta_search=True
        ),
        "e4_reuse": Request(
            "e4_reuse", A4, max_meta_cost=0, search_complete=False, allow_meta_search=False
        ),
        "e4_cold_zero": Request(
            "e4_cold_zero", A4, max_meta_cost=0, search_complete=False, allow_meta_search=False
        ),
        "e4_cold_search": Request(
            "e4_cold_search", A4, max_meta_cost=3, search_complete=True, allow_meta_search=True
        ),
        "e2_incomplete": Request(
            "e2_incomplete", A2, max_meta_cost=2, search_complete=False, allow_meta_search=True
        ),
    }
